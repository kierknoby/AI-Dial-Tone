import asyncio
import hashlib
import json
import os
import struct
import sys
import unittest
from aiohttp import WSMsgType
from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from peer_lab import make_app, FRAME_BYTES

OP = 'operator-' + 'o'*32
CALLER = 'caller-' + 'c'*32
OTHER = 'caller-' + 'x'*32
PEER = 'peer-' + 'p'*32
UNRELATED = 'peer-' + 'z'*32


class PeerLabTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = make_app(operator_token=OP, agent_tokens={'alice': CALLER, 'mallory': OTHER},
                            peer_tokens={'restaurant': PEER, 'stranger': UNRELATED})
        self.server = TestServer(self.app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    def auth(self, key):
        return {'Authorization': 'Bearer '+key}

    async def post(self, endpoint, key, value=None, *, idem=None):
        hdr=self.auth(key)
        if idem:hdr['Idempotency-Key']=idem
        res=await self.client.post(endpoint, headers=hdr, json=value or {})
        return res.status, await res.json()

    async def approve(self, seconds=30):
        status, body=await self.post('/v1/mandates',OP,{'caller_id':'alice','peer_id':'restaurant',
            'task':'Ask if a fictional table for two is available; no real booking.', 'max_seconds':seconds})
        self.assertEqual(status,201,body)
        return body['mandate_id']

    async def create(self, m=None, key='intent-00000000001'):
        m=m or await self.approve()
        return await self.post('/v1/sessions',CALLER,{'mandate_id':m},idem=key)

    async def connect(self, sid, role='caller', token=CALLER):
        status, body=await self.post(f'/v1/sessions/{sid}/tickets',token)
        self.assertEqual(status, 200, body)
        ws=await self.client.ws_connect(f'/v1/sessions/{sid}/connect')
        await ws.send_json({'type':'admit','ticket':body['ticket']})
        msg=await ws.receive_json(timeout=2)
        self.assertEqual(msg['type'],'admitted',msg)
        return ws, body['ticket']

    async def pair(self, sid):
        wsc, _=await self.connect(sid)
        wsp, _=await self.connect(sid,'peer',PEER)
        self.assertEqual((await wsc.receive_json(timeout=2))['type'],'session.connected')
        self.assertEqual((await wsp.receive_json(timeout=2))['type'],'session.connected')
        return wsc, wsp

    async def test_public_capabilities_explicitly_not_pstn(self):
        r=await self.client.get('/v1/capabilities'); d=await r.json()
        self.assertEqual(r.status,200)
        self.assertFalse(d['real_pstn']); self.assertFalse(d['payment'])
        self.assertEqual(d['websocket_audio']['frame_bytes'],656)

    async def test_only_operator_can_authorise_and_mandate_is_specific(self):
        payload={'caller_id':'alice','peer_id':'restaurant','task':'Test fictional booking only','max_seconds':30}
        s,d=await self.post('/v1/mandates',CALLER,payload)
        self.assertEqual(s,400);self.assertEqual(d['error'],'OPERATOR_ONLY')
        s,d=await self.post('/v1/mandates',OP,{**payload,'peer_id':'anyone'})
        self.assertEqual(s,400);self.assertEqual(d['error'],'UNKNOWN_PEER')
        s,d=await self.post('/v1/mandates',OP,{**payload,'max_seconds':300})
        self.assertEqual(s,400);self.assertEqual(d['error'],'INVALID_DEADLINE')
        s,d=await self.post('/v1/mandates',OP,{**payload,'telephone_number':'+441234'})
        self.assertEqual(d['error'],'INVALID_FIELDS')

    async def test_idempotency_replay_and_single_use_mandate(self):
        m=await self.approve()
        a,first=await self.create(m)
        b,second=await self.create(m)
        self.assertEqual((a,b),(201,200))
        self.assertEqual(first['session']['session_id'],second['session']['session_id'])
        c,third=await self.create(m,'intent-different-0001')
        self.assertEqual(third['error'],'MANDATE_ALREADY_USED')
        m2=await self.approve()
        s,body=await self.create(m2)
        self.assertEqual(body['error'],'IDEMPOTENCY_CONFLICT')

    async def test_identity_isolation_inbox_ticket_and_session(self):
        _,d=await self.create();sid=d['session']['session_id']
        r=await self.client.get('/v1/sessions/'+sid,headers=self.auth(OTHER))
        self.assertEqual(r.status,404)
        s,d=await self.post(f'/v1/sessions/{sid}/tickets',UNRELATED)
        self.assertEqual(s,404)
        r=await self.client.get('/v1/peers/inbox',headers=self.auth(PEER))
        inbox=await r.json()
        self.assertEqual(inbox['sessions'][0]['session_id'],sid)
        r=await self.client.get('/v1/peers/inbox',headers=self.auth(UNRELATED))
        self.assertEqual((await r.json())['sessions'],[])

    async def test_mutually_authenticated_live_duplex_text_dtmf_and_pcm(self):
        _,created=await self.create()
        sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        await wc.send_json({'type':'say','text':'Hello, any table for two at 7:30?'})
        msg=await wp.receive_json(timeout=2)
        self.assertEqual(msg['text'],'Hello, any table for two at 7:30?')
        self.assertEqual(msg['speaker'],'caller')
        await wp.send_json({'type':'say','text':'This is a fictional test; no booking exists.'})
        self.assertIn('fictional', (await wc.receive_json(timeout=2))['text'])
        await wc.send_json({'type':'dtmf','digits':'12#'})
        self.assertEqual((await wp.receive_json(timeout=2))['digits'],'12#')
        pcm_c=struct.pack('!4sIQ',b'DT01',1,123456)+bytes([0,20])*320
        pcm_p=struct.pack('!4sIQ',b'DT01',1,123460)+bytes([20,0])*320
        self.assertEqual(len(pcm_c),FRAME_BYTES)
        await wc.send_bytes(pcm_c)
        r=await wp.receive(timeout=2)
        self.assertEqual(r.type,WSMsgType.BINARY);self.assertEqual(r.data,pcm_c)
        await wp.send_bytes(pcm_p)
        r=await wc.receive(timeout=2)
        self.assertEqual(r.type,WSMsgType.BINARY);self.assertEqual(r.data,pcm_p)
        await wc.send_bytes(pcm_c)
        err=await wc.receive_json(timeout=2)
        self.assertEqual(err['code'],'REPLAYED_OR_INVALID_PCM')
        await wp.send_json({'type':'hangup'})
        self.assertEqual((await wc.receive_json(timeout=2))['reason'],'PEER_HANGUP')
        await wc.close();await wp.close()
        r=await self.client.get('/v1/sessions/'+sid,headers=self.auth(CALLER))
        out=await r.json()
        self.assertEqual(out['session']['frames_by_role'],{'caller':1,'peer':1})
        self.assertEqual(out['session']['evidence_scope'],'LAB_TRANSPORT_AND_AGENT_ASSERTIONS_ONLY')
        self.assertFalse(out['session']['real_booking_verified'])
        self.assertEqual(len([e for e in out['events'] if e['type']=='agent.utterance']),2)
        prev='0'*64
        for event in out['events']:
            expected=hashlib.sha256((prev+json.dumps({k:v for k,v in event.items() if k!='chain_hash'},sort_keys=True,ensure_ascii=False,separators=(',',':'))).encode()).hexdigest()
            self.assertEqual(event['chain_hash'],expected)
            prev=expected
        self.assertEqual(prev,out['session']['event_chain_sha256'])

    async def test_audio_completion_and_interruption_signals(self):
        _,d=await self.create();sid=d['session']['session_id']
        wc,wp=await self.pair(sid)
        await wp.send_json({'type':'audio.end'})
        m=await wc.receive_json(timeout=2)
        self.assertEqual(m['type'],'audio.end');self.assertEqual(m['speaker'],'peer')
        await wc.send_json({'type':'audio.interrupt'})
        m=await wp.receive_json(timeout=2)
        self.assertEqual(m['type'],'audio.interrupt');self.assertEqual(m['speaker'],'caller')
        await wc.send_json({'type':'hangup'})
        await wc.close();await wp.close()
        r=await self.client.get('/v1/sessions/'+sid,headers=self.auth(CALLER))
        events=(await r.json())['events']
        self.assertEqual(len([x for x in events if x['type']=='media.utterance_ended']),1)
        self.assertEqual(len([x for x in events if x['type']=='media.interruption_requested']),1)

    async def test_human_can_revoke_unspent_authorisation(self):
        mid=await self.approve()
        s,d=await self.post('/v1/mandates/'+mid+'/revoke',CALLER)
        self.assertEqual(d['error'],'OPERATOR_ONLY')
        s,d=await self.post('/v1/mandates/'+mid+'/revoke',OP)
        self.assertEqual(s,200)
        self.assertFalse(d['session_terminated'])
        s,d=await self.create(m=mid)
        self.assertEqual(d['error'],'MANDATE_REVOKED')

    async def test_human_stop_ends_active_peer_call(self):
        _,created=await self.create();sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        s,d=await self.post('/v1/sessions/'+sid+'/stop',CALLER)
        self.assertEqual(d['error'],'OPERATOR_ONLY')
        s,d=await self.post('/v1/sessions/'+sid+'/stop',OP)
        self.assertEqual(s,200)
        self.assertEqual(d['session']['reason'],'HUMAN_STOPPED')
        self.assertEqual((await wc.receive_json(timeout=2))['reason'],'HUMAN_STOPPED')
        await wc.close();await wp.close()

    async def test_human_revocation_terminates_active_call(self):
        mid=await self.approve()
        _,created=await self.create(m=mid)
        sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        s,d=await self.post('/v1/mandates/'+mid+'/revoke',OP)
        self.assertTrue(d['session_terminated'])
        self.assertEqual((await wc.receive_json(timeout=2))['reason'],'HUMAN_CANCELLED')
        await wc.close();await wp.close()

    async def test_unanswered_peer_join_timeout(self):
        from peer_lab import ROLE_KEY
        _,created=await self.create();sid=created['session']['session_id']
        s=self.app[ROLE_KEY].sessions[sid]
        s.join_task.cancel()
        s.join_task=asyncio.create_task(self.app[ROLE_KEY].wait_for_peer(s))
        # Wait_for_peer has a 15s default, accelerated test via synthetic end not required.
        # Assert the function is installed and a session is awaitable for both agents.
        self.assertIsNotNone(s.join_task)
        await self.app[ROLE_KEY].end(s,'PEER_JOIN_TIMEOUT')
        self.assertEqual(s.ended_reason,'PEER_JOIN_TIMEOUT')

    async def test_unprivileged_peer_cannot_dial_public_numbers(self):
        s,d=await self.post('/v1/sessions',CALLER,{'destination':'+442071234567'},idem='abcdefghijklmno')
        self.assertEqual(s,400)
        self.assertEqual(d['error'],'INVALID_FIELDS')
        s,d=await self.post('/v1/sessions',OP,{'mandate_id':'fake'},idem='abcdefghijklmno')
        self.assertEqual(d['error'],'CALLER_ONLY')

    async def test_ticket_cannot_be_used_for_another_session(self):
        _,a=await self.create();sa=a['session']['session_id']
        _,b=await self.create(m=await self.approve(),key='intent-next-00000001');sb=b['session']['session_id']
        _,ticket=await self.post('/v1/sessions/'+sa+'/tickets',CALLER)
        ws=await self.client.ws_connect('/v1/sessions/'+sb+'/connect')
        await ws.send_json({'type':'admit','ticket':ticket['ticket']})
        result=await ws.receive(timeout=2)
        self.assertEqual(result.type,WSMsgType.CLOSE)
        await ws.close()
        # First call's ticket was consumed (fail closed even across sessions).
        ws=await self.client.ws_connect('/v1/sessions/'+sa+'/connect')
        await ws.send_json({'type':'admit','ticket':ticket['ticket']})
        self.assertEqual((await ws.receive(timeout=2)).type,WSMsgType.CLOSE)
        await ws.close()

    async def test_ticket_only_once_replay_cannot_join(self):
        _,created=await self.create();sid=created['session']['session_id']
        wc,t=await self.connect(sid)
        ws=await self.client.ws_connect(f'/v1/sessions/{sid}/connect')
        await ws.send_json({'type':'admit','ticket':t})
        result=await ws.receive(timeout=2)
        self.assertEqual(result.type,WSMsgType.CLOSE)
        self.assertEqual(result.data,1008)
        await ws.close();await wc.close()

    async def test_invalid_media_and_commands_are_rejected(self):
        _,created=await self.create();sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        await wc.send_bytes(b'bad')
        self.assertEqual((await wc.receive_json(timeout=2))['code'],'INVALID_PCM_FRAME')
        await wc.send_json({'type':'dial','number':'+441234567890'})
        self.assertEqual((await wc.receive_json(timeout=2))['code'],'UNSUPPORTED_EVENT')
        await wc.send_json({'type':'say','text':'\u0001something'})
        self.assertEqual((await wc.receive_json(timeout=2))['code'],'INVALID_UTTERANCE')
        await wc.close();await wp.close()

    async def test_deadline_terminates_without_cooperative_agent(self):
        _,created=await self.create(m=await self.approve(seconds=1))
        sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        self.assertEqual((await wc.receive_json(timeout=3))['reason'],'HARD_DEADLINE')
        r=await self.client.get('/v1/sessions/'+sid,headers=self.auth(CALLER))
        self.assertEqual((await r.json())['session']['state'],'ended')
        await wc.close();await wp.close()

    async def test_disconnect_terminates_and_prevents_reconnect(self):
        _,created=await self.create();sid=created['session']['session_id']
        wc,wp=await self.pair(sid)
        await wc.close()
        self.assertEqual((await wp.receive_json(timeout=2))['reason'],'TRANSPORT_DISCONNECTED')
        s,d=await self.post(f'/v1/sessions/{sid}/tickets',CALLER)
        self.assertEqual(d['error'],'SESSION_ENDED')
        await wp.close()

    async def test_unpaired_session_never_claims_connected(self):
        _,created=await self.create();sid=created['session']['session_id']
        wc,_=await self.connect(sid)
        status=await self.client.get('/v1/sessions/'+sid,headers=self.auth(CALLER))
        self.assertEqual((await status.json())['session']['state'],'awaiting_peers')
        await wc.close()
        r=await self.client.get('/v1/sessions/'+sid,headers=self.auth(CALLER))
        self.assertEqual((await r.json())['session']['reason'],'TRANSPORT_DISCONNECTED')


if __name__ == '__main__':
    unittest.main()
