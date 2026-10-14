"""Adversarial tests of the x402 *upfront* admission boundary.

No real payments are submitted; the fake facilitator is exclusively a protocol
fixture. Passing this suite does NOT establish blockchain integration.
"""
import asyncio
import base64
import json
import unittest

from payments.x402 import (
    BASE_SEPOLIA, USDC_SEPOLIA, GateConfig, GateError, X402Gate,
)

SECRET = 'local-dev-operator-example-secret-value-32-chars'
PAYEE = '0x' + '3a' * 20
PAYER = '0x' + '4b' * 20
TX1 = '0x' + '5c' * 32
DEST = '+442079460123'  # Valid-shaped example only; no real call is made.


class Clock:
    value = 1000.0
    def __call__(self):
        return self.value


class FakeFacilitator:
    def __init__(self):
        self.calls = []
        self.result = {'success': True, 'network': BASE_SEPOLIA,
                       'payer': PAYER, 'transaction': TX1}
        self.waiter = None

    async def settle(self, payload, terms):
        self.calls.append((payload, terms))
        if self.waiter:
            await self.waiter.wait()
        if isinstance(self.result, Exception):
            raise self.result
        return dict(self.result)


def encoded(obj):
    return base64.b64encode(json.dumps(obj, separators=(',', ':')).encode('utf8')).decode('ascii')


class TestX402(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.clock = Clock()
        self.fac = FakeFacilitator()
        self.gate = X402Gate(GateConfig(resource_origin='https://api.example.test',
                                      network=BASE_SEPOLIA, asset=USDC_SEPOLIA,
                                      pay_to=PAYEE, operator_secret=SECRET,
                                      settlement_timeout_seconds=.04), self.fac,
                             clock=self.clock)
        self.approval = await self.gate.operator_approve(
            bearer=SECRET, destination=DEST, max_seconds=60, amount_atomic=10000)
        self.mid = self.approval['mandate_id']
        self.challenge = await self.gate.challenge(self.mid)
        self.demand = json.loads(base64.b64decode(self.challenge['headers']['PAYMENT-REQUIRED']))
        self.message = {
            'x402Version': 2,
            'resource': self.demand['resource'],
            'accepted': self.demand['accepts'][0],
            'payload': {'signature': 'sample-auth-ONLY', 'authorization': {'from': PAYER}},
            'extensions': {},
        }

    async def rejects(self, code, coro):
        with self.assertRaises(GateError) as cm:
            await coro
        self.assertEqual(cm.exception.code, code)

    async def test_v2_http_402_signalling_and_fixed_upfront_terms(self):
        self.assertEqual(self.challenge['status'], 402)
        self.assertEqual(self.demand['x402Version'], 2)
        self.assertEqual(self.demand['accepts'][0]['scheme'], 'exact')
        self.assertEqual(self.demand['accepts'][0]['network'], BASE_SEPOLIA)
        self.assertEqual(self.demand['accepts'][0]['amount'], '10000')
        self.assertEqual(self.demand['accepts'][0]['extra']['paymentFlow'], 'upfront')
        self.assertEqual(self.demand['accepts'][0]['payTo'], PAYEE)
        self.assertNotIn(DEST, self.challenge['headers']['PAYMENT-REQUIRED'])
        self.assertTrue(self.demand['resource']['url'].endswith('/'+self.mid))

    async def test_duplicate_json_members_rejected(self):
        raw = b'{"x402Version":2,"x402Version":1,"accepted":{},"payload":{}}'
        await self.rejects('INVALID_PAYMENT_SIGNATURE_HEADER',
                           self.gate.settle_and_admit(self.mid, base64.b64encode(raw).decode()))

    async def test_no_payment_means_no_admission(self):
        await self.rejects('PERMIT_NOT_FOUND', self.gate.redeem('unauthorised'))
        self.assertEqual(len(self.fac.calls), 0)

    async def test_settled_payment_produces_one_use_sip_preflight_permission(self):
        result = await self.gate.settle_and_admit(self.mid, encoded(self.message))
        self.assertEqual(result['state'], 'paid')
        self.assertFalse(result['real_call_started'])
        permit = await self.gate.redeem(result['one_use_permit'])
        self.assertEqual(permit['destination'], DEST)
        self.assertEqual(permit['max_seconds'], 60)
        self.assertTrue(permit['payment_settled'])
        self.assertFalse(permit['network_call_authorised'])
        await self.rejects('PERMIT_NOT_FOUND', self.gate.redeem(result['one_use_permit']))
        self.assertEqual(len(self.fac.calls), 1)

    async def test_no_unauthed_operator_approvals(self):
        await self.rejects('OPERATOR_UNAUTHORISED', self.gate.operator_approve(
            bearer='bot-token', destination=DEST, max_seconds=30, amount_atomic=100))

    async def test_no_phone_redirection_premium_or_emergency(self):
        for destination in ('+448712345678', '+447700900111', '999', '112',
                            '+12025550123', '00442079460123', DEST+'\n'):
            await self.rejects('DESTINATION_NOT_PERMITTED', self.gate.operator_approve(
                bearer=SECRET, destination=destination, max_seconds=30, amount_atomic=100))

    async def test_no_overlong_or_overpriced_call(self):
        await self.rejects('INVALID_CALL_DURATION', self.gate.operator_approve(
            bearer=SECRET, destination=DEST, max_seconds=3600, amount_atomic=100))
        await self.rejects('INVALID_FIXED_PRICE', self.gate.operator_approve(
            bearer=SECRET, destination=DEST, max_seconds=30, amount_atomic=10_000_001))

    async def test_changed_network_asset_receiver_amount_timeout_extra_or_resource_rejected(self):
        for path, value in [('network', 'eip155:1'), ('asset', '0x'+'2a'*20),
                            ('payTo', '0x'+'9f'*20), ('amount', '1'),
                            ('maxTimeoutSeconds', 600),
                            ('extra', {'name':'USDC','version':'2'})]:
            original = self.message['accepted']
            self.message['accepted'] = {**original, path: value}
            await self.rejects('PAYMENT_TERMS_MISMATCH', self.gate.settle_and_admit(self.mid, encoded(self.message)))
            self.message['accepted'] = original
        self.message['resource'] = {**self.message['resource'], 'url': 'https://elsewhere.test/call'}
        await self.rejects('PAYMENT_RESOURCE_MISMATCH', self.gate.settle_and_admit(self.mid, encoded(self.message)))
        self.assertEqual(self.fac.calls, [])

    async def test_malformed_headers_never_reach_facilitator(self):
        for header in ('', 'not base64!', '!', encoded([1,2,3]), encoded({}),
                       encoded({'x402Version':1,'accepted':{},'payload':{}}),
                       encoded({'x402Version':2,'accepted':{},'payload':{}}),
                       'A'*15000):
            try: await self.gate.settle_and_admit(self.mid, header)
            except GateError: pass
            else: self.fail('bad header accepted')
        self.assertEqual(self.fac.calls, [])

    async def test_settlement_failure_never_creates_permit_and_is_not_retried(self):
        self.fac.result = {'success':False, 'errorReason':'insufficient_funds'}
        await self.rejects('SETTLEMENT_UNRESOLVED', self.gate.settle_and_admit(self.mid,encoded(self.message)))
        await self.rejects('MANDATE_ALREADY_USED', self.gate.settle_and_admit(self.mid,encoded(self.message)))
        s = await self.gate.operator_status(bearer=SECRET, mandate_id=self.mid)
        self.assertEqual(s['state'],'unresolved')
        self.assertFalse(s['automatic_refund_supported'])

    async def test_cancel_during_settlement_is_not_reported_as_success(self):
        self.fac.waiter = asyncio.Event()
        running = asyncio.create_task(self.gate.settle_and_admit(self.mid, encoded(self.message)))
        for _ in range(100):
            if self.fac.calls: break
            await asyncio.sleep(.001)
        running.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await running
        await self.rejects('MANDATE_ALREADY_USED',
                           self.gate.settle_and_admit(self.mid, encoded(self.message)))

    async def test_settlement_timeout_is_ambiguous_and_fail_closed(self):
        self.fac.waiter = asyncio.Event()
        await self.rejects('SETTLEMENT_UNRESOLVED', self.gate.settle_and_admit(self.mid, encoded(self.message)))
        await self.rejects('MANDATE_ALREADY_USED', self.gate.settle_and_admit(self.mid, encoded(self.message)))

    async def test_parallel_replay_cannot_settle_twice(self):
        self.fac.waiter = asyncio.Event()
        first = asyncio.create_task(self.gate.settle_and_admit(self.mid, encoded(self.message)))
        for _ in range(100):
            if self.fac.calls: break
            await asyncio.sleep(.001)
        await self.rejects('MANDATE_ALREADY_USED', self.gate.settle_and_admit(self.mid, encoded(self.message)))
        self.fac.waiter.set()
        await first
        self.assertEqual(len(self.fac.calls), 1)

    async def test_operator_revoke_during_settlement_bars_call_permit(self):
        self.fac.waiter = asyncio.Event()
        active = asyncio.create_task(self.gate.settle_and_admit(self.mid, encoded(self.message)))
        for _ in range(100):
            if self.fac.calls: break
            await asyncio.sleep(.001)
        x = await self.gate.operator_revoke(bearer=SECRET, mandate_id=self.mid)
        self.assertTrue(x['settlement_may_still_commit'])
        self.fac.waiter.set()
        await self.rejects('PAID_BUT_NOT_ADMITTED_RECONCILIATION_REQUIRED', active)

    async def test_mandate_expires_before_challenge(self):
        self.clock.value += 1000
        await self.rejects('MANDATE_EXPIRED', self.gate.challenge(self.mid))

    async def test_settlement_ends_after_mandate_expiry(self):
        self.fac.waiter = asyncio.Event()
        active = asyncio.create_task(self.gate.settle_and_admit(self.mid, encoded(self.message)))
        for _ in range(100):
            if self.fac.calls: break
            await asyncio.sleep(.001)
        self.clock.value += 1000
        self.fac.waiter.set()
        await self.rejects('PAID_BUT_NOT_ADMITTED_RECONCILIATION_REQUIRED', active)

    async def test_tx_replay_across_distinct_mandates_rejected(self):
        await self.gate.settle_and_admit(self.mid, encoded(self.message))
        b = await self.gate.operator_approve(bearer=SECRET, destination=DEST,
                                             max_seconds=60, amount_atomic=10000)
        new = await self.gate.challenge(b['mandate_id'])
        new_req = json.loads(base64.b64decode(new['headers']['PAYMENT-REQUIRED']))
        msg = dict(self.message, resource=new_req['resource'])
        await self.rejects('TRANSACTION_REPLAY', self.gate.settle_and_admit(b['mandate_id'], encoded(msg)))

    async def test_revoke_before_payment_and_after_settlement(self):
        await self.gate.operator_revoke(bearer=SECRET, mandate_id=self.mid)
        await self.rejects('MANDATE_NOT_PAYABLE', self.gate.challenge(self.mid))
        b = await self.gate.operator_approve(bearer=SECRET, destination=DEST,
                                             max_seconds=60, amount_atomic=10000)
        new = await self.gate.challenge(b['mandate_id'])
        new_req = json.loads(base64.b64decode(new['headers']['PAYMENT-REQUIRED']))
        msg = dict(self.message, resource=new_req['resource'])
        res = await self.gate.settle_and_admit(b['mandate_id'], encoded(msg))
        await self.gate.operator_revoke(bearer=SECRET, mandate_id=b['mandate_id'])
        await self.rejects('PERMIT_NOT_FOUND', self.gate.redeem(res['one_use_permit']))

    async def test_config_rejects_non_https_wrong_asset_and_weak_secrets(self):
        cfg = dict(resource_origin='https://api.example.test', network=BASE_SEPOLIA,
                   asset=USDC_SEPOLIA, pay_to=PAYEE, operator_secret=SECRET)
        for key, v, reason in [('resource_origin','http://api.example.test','INVALID_RESOURCE_ORIGIN'),
                               ('asset','0x'+'7a'*20,'ASSET_MUST_BE_NATIVE_BASE_USDC'),
                               ('operator_secret','short','OPERATOR_SECRET_TOO_SHORT'),
                               ('network','eip155:1','UNSUPPORTED_NETWORK'),
                               ('pay_to','0x'+'0'*40,'INVALID_PAYEE_ADDRESS')]:
            with self.assertRaises(GateError) as cm:
                GateConfig(**{**cfg,key:v})
            self.assertEqual(cm.exception.code, reason)

    async def test_status_does_not_expose_permit_or_payment_signature(self):
        res = await self.gate.settle_and_admit(self.mid, encoded(self.message))
        status = await self.gate.operator_status(bearer=SECRET, mandate_id=self.mid)
        self.assertNotIn(res['one_use_permit'],json.dumps(status))
        self.assertNotIn('sample-auth',json.dumps(status))


if __name__ == '__main__':
    unittest.main()
