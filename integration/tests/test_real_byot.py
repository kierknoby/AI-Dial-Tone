"""Actual local BYOT HTTP/WebSocket service + genuine x402 lab gate integration.

ARI is injected and disabled: any attempt to originate is a test failure.
No real payment, SIP network, or external telephone call is performed.
"""
import base64
import json
import secrets
import unittest

from aiohttp import ClientSession, web
from byot.server import Settings, app_factory
from integration.handoff import LocalHandoff
from payments.x402 import X402Gate, GateConfig, BASE_SEPOLIA, USDC_SEPOLIA

OPERATOR='operator-'+secrets.token_hex(32)
AGENT='agent-'+secrets.token_hex(32)
DRAMA_NUMBER='+442079460000'


class FakeARI:
    def __init__(self):
        self.connected=False
        self.originate_requests=[]

    async def start(self):
        self.connected=True

    async def close(self):
        self.connected=False

    async def request(self, method, path, **kwargs):
        if method == 'POST' and path in ('/channels', '/channels/externalMedia'):
            self.originate_requests.append((method,path))
            raise AssertionError('NO_LIVE_ORIGINATION_PERMITTED')
        return {}


class FakeFacilitator:
    async def settle(self,payload,requirements):
        return {'success':True,'network':requirements['network'],
                'payer':'0x'+'ab'*20,'transaction':'0x'+secrets.token_hex(32)}


class RealBYOTHandoffTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ari=FakeARI()
        settings=Settings(ari_url='http://127.0.0.1:8088',ari_user='testuser',
                          ari_password='testpassword',app='aidt',trunk='testtrunk',
                          operator_token=OPERATOR,agent_token=AGENT)
        self.runner=web.AppRunner(app_factory(settings,ari=self.ari),access_log=None)
        await self.runner.setup()
        self.site=web.TCPSite(self.runner,'127.0.0.1',0)
        await self.site.start()
        port=self.site._server.sockets[0].getsockname()[1]
        self.origin=f'http://127.0.0.1:{port}'
        self.http=ClientSession()
        self.secret=secrets.token_hex(32)
        self.gate=X402Gate(GateConfig('https://mock-fixture.example.test',BASE_SEPOLIA,
                                     USDC_SEPOLIA,'0x'+'12'*20,self.secret),FakeFacilitator())
        self.handoff=LocalHandoff(self.gate,http=self.http,
                                  byot_origin=self.origin,operator_bearer=OPERATOR)

    async def asyncTearDown(self):
        await self.http.close()
        await self.runner.cleanup()

    async def paid_fixture_permit(self):
        mandate=await self.gate.operator_approve(bearer=self.secret,destination=DRAMA_NUMBER,
                                                 max_seconds=30,amount_atomic=5000)
        challenge=await self.gate.challenge(mandate['mandate_id'])
        parsed=json.loads(base64.b64decode(challenge['headers']['PAYMENT-REQUIRED']))
        signature=base64.b64encode(json.dumps({
            'x402Version':2,'resource':parsed['resource'],
            'accepted':parsed['accepts'][0],'payload':{'lab_only':True}
        }).encode()).decode()
        payment=await self.gate.settle_and_admit(mandate['mandate_id'],signature)
        return payment['one_use_permit']

    async def api(self,method,path,token,body=None):
        async with self.http.request(method,self.origin+path,json=body,
                                     headers={'Authorization':'Bearer '+token}) as res:
            return res.status,await res.json()

    async def test_paid_lab_handoff_real_byot_agent_join_and_no_origination(self):
        result=await self.handoff.handoff(await self.paid_fixture_permit())
        self.assertEqual(result['destination'],DRAMA_NUMBER)
        self.assertFalse(result['real_call_started'])
        self.assertFalse(result['origination_enabled'])
        status,forbidden=await self.api('POST','/v1/mandates',AGENT,
                                    {'destination':DRAMA_NUMBER,'max_seconds':30})
        self.assertEqual(status,401)
        status,created=await self.api('POST','/v1/calls',AGENT,
                                   {'mandate_id':result['byot_mandate_id']})
        self.assertEqual(status,201)
        self.assertFalse(created['can_originate'])
        path='/v1/calls/'+created['call_id']
        status,ticket=await self.api('POST',path+'/tickets',AGENT,{})
        self.assertEqual(status,200)
        ws=await self.http.ws_connect(self.origin+path+'/media')
        await ws.send_json({'type':'admit','ticket':ticket['ticket']})
        self.assertEqual((await ws.receive_json(timeout=3))['type'],'admitted')
        await ws.send_json({'type':'start'})
        ended=await ws.receive_json(timeout=3)
        self.assertEqual(ended['type'],'call.ended')
        self.assertEqual(ended['reason'],'LIVE_ORIGINATION_DISABLED')
        status,call=await self.api('GET',path,AGENT)
        self.assertEqual(call['state'],'ended')
        self.assertFalse(call['carrier_release_verified'])
        self.assertEqual(self.ari.originate_requests,[])
        await ws.close()


if __name__=='__main__':unittest.main()
