import asyncio
import os
import sys
import unittest
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer, TestClient

sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from model_adapter import ChatModel, ModelError, ModelPeer
from client import PeerClient
from peer_lab import make_app

OP='op-'+'o'*32
CALL='ca-'+'c'*32
PEER='pe-'+'p'*32
SYSTEM='You are a fictional restaurant simulation bot. Never claim an actual booking was made.'


class ModelAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests=[]
        self.model_response={'choices':[{'message':{'role':'assistant','content':'Fictional restaurant: no real booking was made.'}}]}
        async def fake_chat(req):
            payload=await req.json()
            self.requests.append(payload)
            return web.json_response(self.model_response)
        model_app=web.Application()
        model_app.router.add_post('/v1/chat/completions',fake_chat)
        self.model_server=TestServer(model_app)
        await self.model_server.start_server()
        self.model_url=str(self.model_server.make_url('/v1/chat/completions'))
        lab=make_app(operator_token=OP,agent_tokens={'model-caller':CALL},peer_tokens={'model-restaurant':PEER})
        self.lab_server=TestServer(lab)
        await self.lab_server.start_server()
        self.base=str(self.lab_server.make_url('/')).rstrip('/')
        self.http=ClientSession()

    async def asyncTearDown(self):
        await self.http.close()
        await self.lab_server.close()
        await self.model_server.close()

    async def post(self,path,token,payload,idem=None):
        h={'Authorization':'Bearer '+token}
        if idem:h['Idempotency-Key']=idem
        async with self.http.post(self.base+path,headers=h,json=payload) as r:
            assert r.status in (200,201),await r.text()
            return await r.json()

    async def create(self):
        mandate=await self.post('/v1/mandates',OP,{'caller_id':'model-caller','peer_id':'model-restaurant',
                                     'task':'Fictional table availability enquiry', 'max_seconds':30})
        d=await self.post('/v1/sessions',CALL,{'mandate_id':mandate['mandate_id']},idem='test-model-0000000001')
        return d['session']['session_id']

    async def test_https_required_for_nonlocal_model_and_malformed_replies(self):
        with self.assertRaisesRegex(ModelError,'REMOTE_MODEL_REQUIRES_HTTPS'):
            ChatModel('http://model.example/v1/chat/completions','generic')
        with self.assertRaisesRegex(ModelError,'INVALID_MODEL_ENDPOINT'):
            ChatModel('https://user:pass@example.org/v1/chat/completions','generic')
        client=ChatModel(self.model_url,'local/mock')
        self.assertIn('no real booking', (await client.respond(self.http,[{'role':'user','content':'any table?'}],SYSTEM)).lower())
        self.model_response={'choices':[{'message':{'role':'assistant','content':'unsafe', 'tool_calls':[{'id':'exec'}]}}]}
        with self.assertRaisesRegex(ModelError,'MODEL_TOOL_CALL_REJECTED'):
            await client.respond(self.http,[{'role':'user','content':'dial 999'}],SYSTEM)

    async def test_real_model_protocol_request_through_peer_session(self):
        sid=await self.create()
        peer=PeerClient(self.http,self.base,PEER,sid)
        responder=ModelPeer(peer,ChatModel(self.model_url,'local-fake-model'),SYSTEM,max_turns=1,speech=lambda text:b'\x10\x03'*640)
        task=asyncio.create_task(responder.run(self.http))
        caller=PeerClient(self.http,self.base,CALL,sid)
        await caller.connect()
        while True:
            event=await caller.recv(3)
            if event['type']=='session.connected':break
        await caller.say('Please book a table for two tonight, thanks.')
        response=await caller.recv(3)
        self.assertEqual(response['type'],'say')
        self.assertIn('no real booking',response['text'].lower())
        a=await caller.recv(3)
        b=await caller.recv(3)
        end=await caller.recv(3)
        self.assertEqual([a['type'],b['type'],end['type']],['pcm','pcm','audio.end'])
        self.assertEqual(a['data'][16:],b'\x10\x03'*320)
        self.assertEqual(len(self.requests),1)
        self.assertEqual(self.requests[0]['model'],'local-fake-model')
        self.assertEqual(self.requests[0]['messages'][0]['role'],'system')
        self.assertEqual(self.requests[0]['messages'][-1]['role'],'user')
        self.assertNotIn('api_key',str(self.requests[0]).lower())
        await caller.hangup()
        await caller.close()
        await asyncio.wait_for(task,timeout=3)
        self.assertEqual(responder.turns,1)
        async with self.http.get(self.base+'/v1/sessions/'+sid,headers={'Authorization':'Bearer '+CALL}) as r:
            result=(await r.json())['session']
        self.assertFalse(result['real_booking_verified'])
        self.assertFalse(result['real_phone_call'])


if __name__=='__main__':unittest.main()
