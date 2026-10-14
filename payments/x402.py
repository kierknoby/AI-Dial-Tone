"""AI Dial-Tone x402 v2 *upfront* payment admission (development reference).

A human/operator authorises a single, bounded destination. A payer receives a
standard HTTP x402 v2 PaymentRequired challenge and submits a PaymentPayload.
Only a trusted, INJECTED facilitator that reports durable settlement can cause
an ephemeral, one-use call admission to be issued. This module does NOT connect
any blockchain, mint wallets, price currency conversions or place phone calls.

Why upfront? An actual phone call is an irreversible, metered action. The x402
'exact' upfront flow settles BEFORE access is granted. Payment may be taken even
if a later call fails; a separate refund/dispute procedure is essential before
any paid service could be launched. 'exact' represents a FIXED price, not
per-second usage. Do not substitute /verify for /settle. Do not use an in-memory
registry for production payment replay protection.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

BASE_MAINNET = 'eip155:8453'
BASE_SEPOLIA = 'eip155:84532'
USDC_BASE = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
USDC_SEPOLIA = '0x036CbD53842c5426634e7929541eC2318f3dCF7e'
SUPPORTED_USDC = {BASE_MAINNET: USDC_BASE, BASE_SEPOLIA: USDC_SEPOLIA}
ADDRESS = re.compile(r'0x[a-fA-F0-9]{40}\Z')
TX = re.compile(r'0x[a-fA-F0-9]{64}\Z')
UK_GEOGRAPHIC = re.compile(r'\+44[12][0-9]{9}\Z')
MAX_HEADER_BYTES = 12_288
MAX_MANDATES = 128


class GateError(Exception):
    """Safe error with a stable machine-readable code, never payment payloads."""
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def ensure(ok, code):
    if not ok:
        raise GateError(code)


@dataclass(frozen=True)
class GateConfig:
    """No defaults for receiving address or network: must be operator supplied."""
    resource_origin: str
    network: str
    asset: str
    pay_to: str
    operator_secret: str
    max_timeout_seconds: int = 60
    settlement_timeout_seconds: float = 8.0

    def __post_init__(self):
        u = urlsplit(self.resource_origin)
        ensure(u.scheme == 'https' and bool(u.hostname) and not (u.username or
               u.password or u.query or u.fragment or u.path not in ('', '/') or u.port),
               'INVALID_RESOURCE_ORIGIN')
        ensure(self.network in SUPPORTED_USDC, 'UNSUPPORTED_NETWORK')
        ensure(isinstance(self.asset, str) and
               self.asset.lower() == SUPPORTED_USDC[self.network].lower(), 'ASSET_MUST_BE_NATIVE_BASE_USDC')
        ensure(isinstance(self.pay_to, str) and bool(ADDRESS.fullmatch(self.pay_to)) and
               int(self.pay_to[2:], 16) != 0, 'INVALID_PAYEE_ADDRESS')
        ensure(isinstance(self.operator_secret, str) and len(self.operator_secret) >= 32,
               'OPERATOR_SECRET_TOO_SHORT')
        ensure(type(self.max_timeout_seconds) is int and 5 <= self.max_timeout_seconds <= 300,
               'INVALID_PAYMENT_TIMEOUT')
        ensure(type(self.settlement_timeout_seconds) in (int, float) and
               0 < self.settlement_timeout_seconds <= 30, 'INVALID_SETTLEMENT_TIMEOUT')


def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


class X402Gate:
    """Loopback-only research decision engine; NOT a stand-alone production paywall.

    facilitator must expose ``async settle(payment_payload, requirements)``.
    Its implementation is a critical trust boundary; it MUST authenticate and
    check on-chain proof, token, recipient, amount and network. A test fixture
    is no substitute for a trusted facilitator. All state is process-local.
    """
    def __init__(self, config: GateConfig, facilitator, *, clock=time.time):
        ensure(callable(getattr(facilitator, 'settle', None)), 'FACILITATOR_REQUIRED')
        self.config = config
        self.facilitator = facilitator
        self.clock = clock
        self._operator_hash = hashlib.sha256(config.operator_secret.encode()).digest()
        self._mandates = {}
        self._permits = {}
        self._fingerprints = set()
        self._transactions = set()
        self._lock = asyncio.Lock()

    def _require_operator(self, bearer):
        ensure(isinstance(bearer, str) and hmac.compare_digest(
            hashlib.sha256(bearer.encode()).digest(), self._operator_hash), 'OPERATOR_UNAUTHORISED')

    async def operator_approve(self, *, bearer, destination, max_seconds, amount_atomic,
                               expires_in_seconds=90):
        """Server/operator-only entry point, never callable by an AI agent token.

        The secret authenticates the operator locally, NOT human identity/consent.
        Future deployment requires real accounts, consent and durable approval.
        """
        self._require_operator(bearer)
        ensure(isinstance(destination, str) and bool(UK_GEOGRAPHIC.fullmatch(destination)),
               'DESTINATION_NOT_PERMITTED')
        ensure(type(max_seconds) is int and 10 <= max_seconds <= 120, 'INVALID_CALL_DURATION')
        # Laboratory-only ceiling; 6-decimal USDC units, not GBP or FX conversion.
        ensure(type(amount_atomic) is int and 1 <= amount_atomic <= 10_000_000,
               'INVALID_FIXED_PRICE')
        ensure(type(expires_in_seconds) is int and 10 <= expires_in_seconds <= 300,
               'INVALID_MANDATE_EXPIRY')
        async with self._lock:
            ensure(len(self._mandates) < MAX_MANDATES, 'MANDATE_CAPACITY_REACHED')
            key = secrets.token_urlsafe(24)
            self._mandates[key] = {
                'destination': destination, 'max_seconds': max_seconds,
                'amount': str(amount_atomic), 'expires_at': self.clock() + expires_in_seconds,
                'state': 'approved', 'permit': None, 'transaction': None,
            }
            return {'mandate_id': key, 'expires_at': self._mandates[key]['expires_at'],
                    'destination': destination, 'max_seconds': max_seconds,
                    'amount_atomic': str(amount_atomic), 'currency': 'USDC',
                    'price_model': 'fixed_upfront_no_automatic_refund'}

    def _record(self, mandate_id):
        ensure(isinstance(mandate_id, str) and mandate_id in self._mandates, 'UNKNOWN_MANDATE')
        m = self._mandates[mandate_id]
        ensure(self.clock() < m['expires_at'], 'MANDATE_EXPIRED')
        return m

    def _requirements(self, mandate):
        return {
            'scheme': 'exact', 'network': self.config.network,
            'amount': mandate['amount'], 'asset': self.config.asset,
            'payTo': self.config.pay_to,
            'maxTimeoutSeconds': self.config.max_timeout_seconds,
            'extra': {'name': 'USDC', 'version': '2', 'paymentFlow': 'upfront'},
        }

    def _resource(self, mandate_id):
        return {'url': self.config.resource_origin.rstrip('/') + '/v1/call-permits/' + mandate_id,
                'description': 'One fixed-price, human-authorised AI call admission',
                'mimeType': 'application/json'}

    async def challenge(self, mandate_id):
        """Return actual x402 v2 HTTP 402 signalling, not a fabricated paid state."""
        async with self._lock:
            mandate = self._record(mandate_id)
            ensure(mandate['state'] == 'approved', 'MANDATE_NOT_PAYABLE')
            required = {'x402Version': 2, 'error': 'PAYMENT-SIGNATURE header is required',
                        'resource': self._resource(mandate_id),
                        'accepts': [self._requirements(mandate)], 'extensions': {}}
            encoded = base64.b64encode(json.dumps(required, separators=(',', ':')).encode()).decode()
            return {'status': 402, 'headers': {'PAYMENT-REQUIRED': encoded},
                    'body': {'code': 'PAYMENT_REQUIRED', 'settlement_available': False,
                             'research_component_only': True}}

    @staticmethod
    def _parse_signature(header):
        ensure(isinstance(header, str) and 1 <= len(header) <= MAX_HEADER_BYTES and
               header.isascii(), 'INVALID_PAYMENT_SIGNATURE_HEADER')
        try:
            data = base64.b64decode(header, validate=True)
            ensure(0 < len(data) <= MAX_HEADER_BYTES, 'INVALID_PAYMENT_SIGNATURE_HEADER')
            message = json.loads(data.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
                                 object_pairs_hook=_reject_duplicate_keys)
        except (ValueError, UnicodeError, binascii.Error, TypeError, json.JSONDecodeError):
            raise GateError('INVALID_PAYMENT_SIGNATURE_HEADER') from None
        ensure(isinstance(message, dict) and type(message.get('x402Version')) is int and
               message['x402Version'] == 2, 'UNSUPPORTED_X402_VERSION')
        ensure(isinstance(message.get('accepted'), dict) and
               isinstance(message.get('payload'), dict) and bool(message['payload']),
               'MALFORMED_PAYMENT_PAYLOAD')
        return message

    async def settle_and_admit(self, mandate_id, payment_signature_header):
        """Upfront: settle durably FIRST; return permit only on trusted success.

        On timeout or unknown outcome the mandate stays unresolved. Never retry
        the same payment blindly: a prior settlement could have succeeded.
        """
        payload = self._parse_signature(payment_signature_header)
        fingerprint = hashlib.sha256(payment_signature_header.encode('ascii')).hexdigest()
        async with self._lock:
            m = self._record(mandate_id)
            ensure(m['state'] == 'approved', 'MANDATE_ALREADY_USED')
            ensure(fingerprint not in self._fingerprints, 'PAYMENT_REPLAY')
            required = self._requirements(m)
            ensure(payload['accepted'] == required, 'PAYMENT_TERMS_MISMATCH')
            ensure(payload.get('resource') == self._resource(mandate_id), 'PAYMENT_RESOURCE_MISMATCH')
            # Reservations survive timeout and cancellation; prevents double-settle.
            m['state'] = 'settling'
            self._fingerprints.add(fingerprint)

        try:
            result = await asyncio.wait_for(self.facilitator.settle(payload, required),
                                            timeout=self.config.settlement_timeout_seconds)
        except asyncio.CancelledError:
            async with self._lock:
                m['state'] = 'unresolved'
            raise
        except Exception:
            async with self._lock:
                m['state'] = 'unresolved'
            raise GateError('SETTLEMENT_UNRESOLVED') from None

        async with self._lock:
            # Delayed settlement may have charged after human mandate expiration
            # or a revocation. No call permit can be issued in that case.
            if not (isinstance(result, dict) and result.get('success') is True and
                    result.get('network') == self.config.network and
                    isinstance(result.get('transaction'), str) and
                    bool(TX.fullmatch(result['transaction'])) and
                    isinstance(result.get('payer'), str) and bool(ADDRESS.fullmatch(result['payer']))):
                m['state'] = 'unresolved'
                raise GateError('SETTLEMENT_UNRESOLVED')
            tx_key = (self.config.network, result['transaction'].lower())
            if tx_key in self._transactions:
                m['state'] = 'unresolved'
                raise GateError('TRANSACTION_REPLAY')
            self._transactions.add(tx_key)
            m['transaction'] = result['transaction']
            if m['state'] == 'revoked' or self.clock() >= m['expires_at']:
                m['state'] = 'paid_not_admitted'
                raise GateError('PAID_BUT_NOT_ADMITTED_RECONCILIATION_REQUIRED')
            permit = secrets.token_urlsafe(32)
            m['state'] = 'paid'
            m['permit'] = permit
            self._permits[permit] = mandate_id
            return {'state': 'paid', 'one_use_permit': permit,
                    'expires_at': m['expires_at'], 'network': result['network'],
                    'transaction': result['transaction'],
                    'price_model': 'fixed_upfront_no_automatic_refund',
                    'real_call_started': False}

    async def redeem(self, permit):
        """One-use permission to PROCEED TO independent SIP/policy checks, NOT dial.

        The authoritative caller must compare the bound number/limit with its
        PBX enforcement and recheck the live human mandate before dialling.
        """
        async with self._lock:
            ensure(isinstance(permit, str) and permit in self._permits, 'PERMIT_NOT_FOUND')
            mandate_id = self._permits[permit]
            m = self._mandates[mandate_id]
            ensure(self.clock() < m['expires_at'], 'MANDATE_EXPIRED')
            ensure(m['state'] == 'paid' and m['permit'] == permit, 'PERMIT_NOT_REDEEMABLE')
            m['state'] = 'admitted'
            self._permits.pop(permit, None)
            return {'mandate_id': mandate_id, 'destination': m['destination'],
                    'max_seconds': m['max_seconds'], 'approved': True,
                    'payment_settled': True, 'requires_independent_sip_readiness': True,
                    'network_call_authorised': False}

    async def operator_revoke(self, *, bearer, mandate_id):
        self._require_operator(bearer)
        async with self._lock:
            ensure(mandate_id in self._mandates, 'UNKNOWN_MANDATE')
            m = self._mandates[mandate_id]
            ensure(m['state'] != 'admitted', 'CALL_CONTROL_MUST_STOP_ACTIVE_CALL')
            # Settling cannot be safely cancelled or promised to be refunded.
            if m['state'] == 'settling':
                m['state'] = 'revoked'
                return {'revoked': True, 'settlement_may_still_commit': True}
            m['state'] = 'revoked'
            self._permits.pop(m['permit'], None)
            return {'revoked': True, 'settlement_may_still_commit': False}

    async def operator_status(self, *, bearer, mandate_id):
        self._require_operator(bearer)
        async with self._lock:
            ensure(mandate_id in self._mandates, 'UNKNOWN_MANDATE')
            m = self._mandates[mandate_id]
            return {'mandate_id': mandate_id, 'state': m['state'],
                    'transaction': m['transaction'], 'real_call_started': False,
                    'automatic_refund_supported': False}
