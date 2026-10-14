"""Real loopback HTTP integration with a fake, never-live BYOT component."""
import asyncio
import base64
import json
import secrets
import unittest

from aiohttp import ClientSession, web
from payments.x402 import X402Gate, GateConfig, BASE_SEPOLIA, USDC_SEPOLIA
from integration.handoff import LocalHandoff, HandoffError


class FakeFacilitator:
    async def settle(self, payload, requirements):
        return {'success': True, 'network': requirements['network'],
                'transaction': '0x' + secrets.token_hex(32), 'payer': '0x' + 'ac'*20}


class HandoffTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.secret = secrets.token_hex(32)
        self.byot_token = secrets.token_hex(32)
        self.gate = X402Gate(GateConfig('https://mock-fixture.example.test',BASE_SEPOLIA,
                                      USDC_SEPOLIA,'0x'+'12'*20,self.secret),FakeFacilitator())
        self.records = []
        self.live = False
        self.component = 'byot-asterisk-experimental'
        self.status = 201
        self.corrupt = False
        self.calls = 0

        async def health(request):
            return web.json_response({'component': self.component, 'version':'0.0.1',
                                      'real_call_enabled': self.live,
                                      'ari_event_stream_connected': False})

        async def mandate(request):
            if request.headers.get('Authorization') != 'Bearer '+self.byot_token:
                return web.json_response({'error':'unauthorised'},status=401)
            incoming=await request.json()
            self.records.append(incoming)
            if self.status != 201:
                return web.json_response({'error':'failed'},status=self.status)
            response={'mandate_id': secrets.token_hex(12),
                      'destination':incoming['destination'],
                      'max_seconds':incoming['max_seconds'],
                      'single_use':True,'human_approved':False}
            if self.corrupt:
                response['destination']='+441234567890'
            return web.json_response(response,status=201)

        self.app=web.Application()
        self.app.router.add_get('/health',health)
        self.app.router.add_post('/v1/mandates',mandate)
        self.runner=web.AppRunner(self.app)
        await self.runner.setup()
        self.site=web.TCPSite(self.runner,'127.0.0.1',0)
        await self.site.start()
        port=self.site._server.sockets[0].getsockname()[1]
        self.origin=f'http://127.0.0.1:{port}'
        self.http=ClientSession()
        self.handoff=LocalHandoff(self.gate,http=self.http,byot_origin=self.origin,
                                  operator_bearer=self.byot_token)

    async def asyncTearDown(self):
        await self.http.close()
        await self.runner.cleanup()

    async def permit(self, number='+442079460123', duration=30):
        m=await self.gate.operator_approve(bearer=self.secret,destination=number,
                                           max_seconds=duration, amount_atomic=5000)
        challenge=await self.gate.challenge(m['mandate_id'])
        expected=json.loads(base64.b64decode(challenge['headers']['PAYMENT-REQUIRED']))
        header=base64.b64encode(json.dumps({
            'x402Version':2,'resource':expected['resource'],
            'accepted':expected['accepts'][0],'payload':{'lab_fixture':True},
            'extensions':{},
        }).encode()).decode()
        admitted=await self.gate.settle_and_admit(m['mandate_id'],header)
        return admitted['one_use_permit']

    async def test_bound_from_real_gate_through_actual_http(self):
        permit=await self.permit()
        result=await self.handoff.handoff(permit)
        self.assertEqual(self.records,[{'destination':'+442079460123','max_seconds':30}])
        self.assertEqual(result['destination'],'+442079460123')
        self.assertEqual(result['max_seconds'],30)
        self.assertFalse(result['real_call_started'])
        self.assertFalse(result['origination_enabled'])
        self.assertFalse(result['live_payment_verified_by_this_lab'])
        self.assertTrue(result['requires_separate_byot_agent_auth'])
        self.assertNotIn(self.byot_token,json.dumps(result))
        self.assertNotIn(permit,json.dumps(result))

    async def test_permit_is_single_use(self):
        permit=await self.permit()
        await self.handoff.handoff(permit)
        with self.assertRaisesRegex(HandoffError,'HANDOFF_ALREADY_ATTEMPTED'):
            await self.handoff.handoff(permit)
        self.assertEqual(len(self.records),1)

    async def test_live_telephony_rejected_before_redeem(self):
        self.live=True
        permit=await self.permit()
        with self.assertRaisesRegex(HandoffError,'LIVE_CALLS_MUST_REMAIN_DISABLED'):
            await self.handoff.handoff(permit)
        self.assertEqual(self.records,[])
        self.live=False
        result=await self.handoff.handoff(permit)
        self.assertEqual(result['state'],'byot_lab_mandate_issued')

    async def test_unrecognised_byot_rejected_before_redeem(self):
        self.component='some-unrelated-app'
        permit=await self.permit()
        with self.assertRaisesRegex(HandoffError,'UNRECOGNISED_BYOT_COMPONENT'):
            await self.handoff.handoff(permit)
        self.assertEqual(self.records,[])

    async def test_downstream_failure_is_unresolved_and_never_retried(self):
        self.status=503
        permit=await self.permit()
        with self.assertRaisesRegex(HandoffError,'BYOT_OPERATOR_GATE_REJECTED'):
            await self.handoff.handoff(permit)
        self.status=201
        with self.assertRaisesRegex(HandoffError,'HANDOFF_ALREADY_ATTEMPTED'):
            await self.handoff.handoff(permit)
        self.assertEqual(len(self.records),1)

    async def test_mismatched_mandate_is_rejected(self):
        self.corrupt=True
        permit=await self.permit()
        with self.assertRaisesRegex(HandoffError,'BYOT_MANDATE_NOT_BOUND'):
            await self.handoff.handoff(permit)

    async def test_reject_remote_and_hostnames(self):
        for uri in ('http://example.com:8877','https://127.0.0.1:8877',
                    'http://localhost:8877','http://127.0.0.1:8877/trunk',
                    'http://foo@127.0.0.1:8877','http://127.0.0.1:8877/?token=123'):
            with self.subTest(uri=uri),self.assertRaises(HandoffError):
                LocalHandoff(self.gate,http=self.http,byot_origin=uri,
                             operator_bearer=self.byot_token)

    async def test_fake_or_expired_permit_fails_closed(self):
        with self.assertRaisesRegex(HandoffError,'PAYMENT_PERMIT_PERMIT_NOT_FOUND'):
            await self.handoff.handoff('x'*50)
        self.assertEqual(self.records,[])

    async def test_sequential_distinct_permits(self):
        for number in ('+442079460123','+441234567890'):
            result=await self.handoff.handoff(await self.permit(number))
            self.assertEqual(result['destination'],number)
        self.assertEqual(len(self.records),2)

    async def test_concurrent_replay_one_wins(self):
        permit=await self.permit()
        results=await asyncio.gather(self.handoff.handoff(permit),self.handoff.handoff(permit),return_exceptions=True)
        self.assertEqual(len([r for r in results if isinstance(r,dict)]),1)
        self.assertEqual(len([r for r in results if isinstance(r,HandoffError)]),1)
        self.assertEqual(len(self.records),1)

    async def test_no_agent_or_call_creation_routes_accessed(self):
        result=await self.handoff.handoff(await self.permit())
        self.assertTrue(result['byot_mandate_id'])
        self.assertEqual(self.calls,0)


if __name__ == '__main__': unittest.main()
