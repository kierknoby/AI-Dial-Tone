"""Initial release negative-path / adversarial regression tests, no network carriers."""
import os
import sys
import unittest
from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from peer_lab import make_app, ROLE_KEY, MAX_MANDATES, MAX_SESSIONS, MAX_TICKETS, Session, Mandate

OP = 'operator-' + 'o'*32
CALLER = 'caller-' + 'c'*32
PEER = 'peer-' + 'p'*32


class ReleaseNegativePaths(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = make_app(operator_token=OP, agent_tokens={'alice': CALLER}, peer_tokens={'restaurant': PEER})
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()
        self.lab = self.app[ROLE_KEY]

    async def asyncTearDown(self):
        await self.client.close()

    async def post(self, path, bearer, obj=None, headers=None):
        r = await self.client.post(path, headers={'Authorization': f'Bearer {bearer}', **(headers or {})}, json=obj or {})
        return r.status, await r.json()

    async def approval(self):
        return await self.post('/v1/mandates',OP,{'caller_id':'alice','peer_id':'restaurant',
                             'task':'Fictional table test only, no real booking', 'max_seconds':30})

    async def test_malformed_unicode_mandate_is_rejected_before_any_session(self):
        s,d=await self.post('/v1/mandates',OP,{'caller_id':'alice','peer_id':'restaurant',
          'task':'text\ud800bad', 'max_seconds':30})
        self.assertEqual((s,d['error']),(400,'INVALID_TASK'))
        self.assertEqual(self.lab.mandates,{})

    async def test_unhashable_mandate_id_does_not_raise_server_500(self):
        s,d=await self.post('/v1/sessions',CALLER,{'mandate_id':['bad']},
                             {'Idempotency-Key':'test-intent-1234567890'})
        self.assertEqual((s,d['error']),(400,'INVALID_MANDATE_ID'))

    async def test_invalid_unicode_ws_claim_does_not_end_valid_session(self):
        s,d=await self.approval();self.assertEqual(s,201)
        s,created=await self.post('/v1/sessions',CALLER,{'mandate_id':d['mandate_id']},
                                   {'Idempotency-Key':'intent-unicode-123456'})
        sid=created['session']['session_id']
        async def connect(token):
            s,t=await self.post(f'/v1/sessions/{sid}/tickets',token)
            self.assertEqual(s,200)
            ws=await self.client.ws_connect(f'/v1/sessions/{sid}/connect')
            await ws.send_json({'type':'admit','ticket':t['ticket']})
            self.assertEqual((await ws.receive_json(timeout=2))['type'],'admitted')
            return ws
        caller=await connect(CALLER)
        peer=await connect(PEER)
        self.assertEqual((await caller.receive_json(timeout=2))['type'],'session.connected')
        self.assertEqual((await peer.receive_json(timeout=2))['type'],'session.connected')
        await caller.send_json({'type':'say','text':'bad\ud800claim'})
        self.assertEqual((await caller.receive_json(timeout=2))['code'],'INVALID_UTTERANCE')
        await caller.send_json({'type':'say','text':'Hello, legitimate agent'})
        self.assertEqual((await peer.receive_json(timeout=2))['text'],'Hello, legitimate agent')
        await caller.send_json({'type':'hangup'})
        self.assertEqual((await peer.receive_json(timeout=2))['type'],'session.ended')
        await caller.close();await peer.close()

    async def test_mandate_resource_limit_is_explicit_and_fail_closed(self):
        for i in range(MAX_MANDATES):self.lab.mandates[str(i)]=object()
        s,d=await self.approval()
        self.assertEqual((s,d['error']),(429,'MANDATE_CAPACITY_EXCEEDED'))
        self.lab.mandates.clear()

    async def test_session_and_ticket_limits_are_explicit(self):
        s,d=await self.approval();self.assertEqual(s,201)
        mandate_id=d['mandate_id']
        for i in range(MAX_SESSIONS):
            m=Mandate(f'dummy-m-{i}','alice','restaurant','synthetic',999999999,30)
            self.lab.sessions[f'dummy-{i}']=Session(f'dummy-{i}',m,0,state='ended')
        s,d=await self.post('/v1/sessions',CALLER,{'mandate_id':mandate_id},
                             {'Idempotency-Key':'test-session-cap-1234'})
        self.assertEqual((s,d['error']),(429,'SESSION_CAPACITY_EXCEEDED'))
        self.lab.sessions.clear()
        s,d=await self.post('/v1/sessions',CALLER,{'mandate_id':mandate_id},
                             {'Idempotency-Key':'test-session-cap-1234'})
        self.assertEqual(s,201)
        sid=d['session']['session_id']
        for i in range(MAX_TICKETS):self.lab.tickets[str(i)]=(sid,'peer',self.lab.monotonic()+90)
        s,d=await self.post(f'/v1/sessions/{sid}/tickets',CALLER)
        self.assertEqual((s,d['error']),(429,'TICKET_CAPACITY_EXCEEDED'))
        self.lab.tickets.clear()
        s,d=await self.post(f'/v1/sessions/{sid}/tickets',CALLER)
        self.assertEqual(s,200)
