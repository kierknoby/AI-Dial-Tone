"""Research-only x402 -> BYOT mandate handoff, intentionally NOT a dial endpoint.

Only an operator-side process possesses the BYOT operator bearer. The x402
lab permit is redeemed once, never sent to BYOT or to a call agent, and its
immutable destination and maximum duration are copied to the BYOT mandate.

This coordinator REQUIRES the BYOT service to have live origination disabled;
it is for validating the contracts together, not for accepting payment for
real calls. A future commercial coordinator needs genuine facilitator,
persisted reconciliation, independently verified human consent, and PBX-side
safety before enabling live routes.
"""
from __future__ import annotations

import asyncio
import ipaddress
from urllib.parse import urlsplit

from payments.x402 import GateError, X402Gate


class HandoffError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class LocalHandoff:
    """One operator-controlled lab transition. No dial, agent token, or wallet.

    ``http`` is an aiohttp ClientSession or a compatible injected test client.
    ``gate`` is a development X402Gate; using a fake facilitator is never
    evidence of on-chain settlement.
    """
    def __init__(self, gate: X402Gate, *, http, byot_origin: str, operator_bearer: str):
        parsed = urlsplit(byot_origin)
        try:
            address = ipaddress.ip_address(parsed.hostname or '')
            port = parsed.port
        except ValueError:
            raise HandoffError('LOOPBACK_BYOT_REQUIRED') from None
        if (parsed.scheme != 'http' or not address.is_loopback or parsed.username or
                parsed.password or parsed.query or parsed.fragment or
                parsed.path not in ('', '/') or not port):
            raise HandoffError('LOOPBACK_BYOT_REQUIRED')
        if not isinstance(operator_bearer, str) or len(operator_bearer) < 32:
            raise HandoffError('OPERATOR_CREDENTIAL_REQUIRED')
        if not isinstance(gate, X402Gate):
            raise HandoffError('X402_GATE_REQUIRED')
        self.gate = gate
        self.http = http
        self.origin = byot_origin.rstrip('/')
        self._operator_bearer = operator_bearer
        self._lock = asyncio.Lock()
        self._outcomes = {}

    async def _request(self, method, path, *, body=None):
        try:
            async with self.http.request(method, self.origin + path,
                                         json=body,
                                         headers={'Authorization': 'Bearer ' + self._operator_bearer},
                                         timeout=3) as response:
                if response.status not in (200, 201):
                    raise HandoffError('BYOT_OPERATOR_GATE_REJECTED')
                value = await response.json()
                if not isinstance(value, dict):
                    raise HandoffError('BYOT_INVALID_RESPONSE')
                return value
        except (HandoffError, asyncio.CancelledError):
            raise
        except Exception:
            # Never return HTTP bodies; they might reveal server credentials.
            raise HandoffError('BYOT_UNREACHABLE_OR_UNRESOLVED') from None

    async def handoff(self, permit: str):
        """Local lab handoff only; consumes the paid permit before BYOT mandate.

        An uncertain BYOT response after redemption requires operator
        reconciliation; never retry automatically or repeat a settlement.
        """
        if not isinstance(permit, str) or not (20 <= len(permit) <= 256):
            raise HandoffError('INVALID_PERMIT')
        async with self._lock:
            if permit in self._outcomes:
                raise HandoffError('HANDOFF_ALREADY_ATTEMPTED')
            status = await self._request('GET', '/health')
            if (status.get('component') != 'byot-asterisk-experimental' or
                    status.get('version') != '0.0.1'):
                raise HandoffError('UNRECOGNISED_BYOT_COMPONENT')
            if status.get('real_call_enabled') is not False:
                raise HandoffError('LIVE_CALLS_MUST_REMAIN_DISABLED')
            # Record an in-process reservation before redeem. No duplicate
            # local attempt is allowed, even when the request is cancelled.
            self._outcomes[permit] = 'in_progress'
            try:
                admission = await self.gate.redeem(permit)
            except GateError as exc:
                self._outcomes[permit] = 'permit_rejected'
                raise HandoffError('PAYMENT_PERMIT_' + exc.code) from None
            except BaseException:
                self._outcomes[permit] = 'unresolved'
                raise
            if (admission.get('network_call_authorised') is not False or
                    admission.get('payment_settled') is not True or
                    admission.get('approved') is not True):
                self._outcomes[permit] = 'unresolved'
                raise HandoffError('INVALID_REDEEMED_ADMISSION')
            try:
                result = await self._request('POST', '/v1/mandates', body={
                    'destination': admission['destination'],
                    'max_seconds': admission['max_seconds'],
                })
                if (result.get('destination') != admission['destination'] or
                        result.get('max_seconds') != admission['max_seconds'] or
                        result.get('single_use') is not True or
                        result.get('human_approved') is not False or
                        not isinstance(result.get('mandate_id'), str)):
                    raise HandoffError('BYOT_MANDATE_NOT_BOUND')
            except BaseException:
                self._outcomes[permit] = 'unresolved'
                raise
            self._outcomes[permit] = 'issued'
            return {
                'state': 'byot_lab_mandate_issued',
                'byot_mandate_id': result['mandate_id'],
                'destination': admission['destination'],
                'max_seconds': admission['max_seconds'],
                'payment_mandate_id': admission['mandate_id'],
                'real_call_started': False,
                'origination_enabled': False,
                'live_payment_verified_by_this_lab': False,
                'human_identity_verified_by_this_lab': False,
                'requires_separate_byot_agent_auth': True,
                'automatic_retry_safe': False,
            }
