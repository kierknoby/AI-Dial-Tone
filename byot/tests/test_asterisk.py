"""Synthetic ARI integration tests. They do NOT establish live SIP interop."""
import asyncio
import json
import socket
import struct
import unittest
from unittest.mock import patch
from aiohttp import ClientSession, WSMsgType
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from byot.server import Settings, app_factory, KEY
from byot.rtp import RTP_HEADER, AGENT_HEADER, swap16, decode_rtp, RtpPort

OP = 'operator-'+'o'*48
AG = 'agent-'+'a'*48
TEST_PHONE = '+442079460000'  # UK drama-reserved range, NEVER dial in production

class FakeARI:
    def __init__(self):
        self.connected = False
        self.calls=[]
        self.channels=set()
        self.manager=None
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1',0))
        self.remote_port=self.sock.getsockname()[1]
        self.media_sink=None
        self.enabled=True
        self.hangup_fail=False

    async def start(self):
        self.connected=True

    async def close(self):
        self.connected=False
        self.sock.close()

    async def request(self,method,path,*,params=None,json_body=None,missing_ok=False):
        self.calls.append((method,path,params))
        if method=='POST' and path=='/channels':
            self.channels.add(params['channelId'])
            asyncio.get_running_loop().call_soon(lambda:asyncio.create_task(self.manager.on_ari_event({
                'type':'StasisStart','channel':{'id':params['channelId']}})))
            return {'id':params['channelId']}
        if method=='POST' and path=='/channels/externalMedia':
            self.channels.add(params['channelId'])
            self.media_sink=(params['external_host'].split(':')[0],int(params['external_host'].split(':')[1]))
            asyncio.get_running_loop().call_soon(lambda:asyncio.create_task(self.manager.on_ari_event({
                'type':'StasisStart','channel':{'id':params['channelId']}})))
            return {'id':params['channelId']}
        if method=='GET' and path.startswith('/endpoints/PJSIP/'):
            return {'state': 'online' if self.enabled else 'offline'}
        if method=='GET' and path.endswith('/variable'):
            return {'value':str(self.remote_port)}
        if method=='GET' and path.startswith('/channels/'):
            if path[10:] not in self.channels: return None
            return {'id':path[10:]}
        if method=='DELETE' and path.startswith('/channels/'):
            if not self.hangup_fail: self.channels.discard(path[10:])
            return {}
        return {}

    def inject(self,pcm=b'\x01\x02'*320,seq=12,ssrc=4242,pt=118):
        assert self.media_sink
        self.sock.sendto(RTP_HEADER.pack(0x80,pt,seq,seq*320,ssrc)+swap16(pcm),self.media_sink)

class SettingsTests(unittest.TestCase):
    def base(self,**kw):
        args=dict(ari_url='http://127.0.0.1:8088',ari_user='ariuser',ari_password='securePassword',
                  app='aidt',trunk='isolatedtrunk',operator_token=OP,agent_token=AG)
        args.update(kw)
        return args

    def test_defaults_fail_closed(self):
        s=Settings(**self.base())
        self.assertFalse(s.allow_origination)
        self.assertEqual(s.media_bind,'127.0.0.1')

    def test_remote_ari_requires_https(self):
        with self.assertRaisesRegex(Exception,'REMOTE_ARI_REQUIRES_HTTPS'):
            Settings(**self.base(ari_url='http://10.1.1.2:8088'))

    def test_remote_rtp_requires_private_opt_in(self):
        with self.assertRaisesRegex(Exception,'RTP_MUST_BE_ISOLATED'):
            Settings(**self.base(media_bind='10.0.0.2'))
        Settings(**self.base(media_bind='10.0.0.2',media_advertise='10.0.0.2',
                             asterisk_media_ip='10.0.0.3',allow_private_rtp=True))
        with self.assertRaisesRegex(Exception,'RTP_MUST_BE_ISOLATED'):
            Settings(**self.base(media_bind='8.8.8.8',media_advertise='8.8.8.8',
                                 asterisk_media_ip='8.8.8.8',allow_private_rtp=True))

    def test_bad_trunk_and_tokens_rejected(self):
        for trunk in ('mytrunk/context','sip:evil','x?foo=1'):
            with self.assertRaisesRegex(Exception,'INVALID_PJSIP_TRUNK'):
                Settings(**self.base(trunk=trunk))
        with self.assertRaisesRegex(Exception,'STRONG_DISTINCT_TOKENS_REQUIRED'):
            Settings(**self.base(agent_token=OP))

    def test_rtp_rejects_invalid_and_swaps_bytes(self):
        pcm=b'\x01\x02'*320
        payload=RTP_HEADER.pack(0x80,118,123,500,12)+swap16(pcm)
        _,seq,_,_,decoded=decode_rtp(payload)
        self.assertEqual(seq,123); self.assertEqual(decoded,pcm)
        for altered in (payload[:8], b'X'+payload[1:], payload[:-2]):
            with self.assertRaises(ValueError): decode_rtp(altered)

    def test_rtp_sender_requires_learned_payload_type(self):
        port=RtpPort(lambda pcm: None)
        port.set_remote('127.0.0.1',50000)
        self.assertFalse(port.send_pcm(b'\x00'*640))
        self.assertEqual(port.counters.dropped,1)


class ConnectorTests(AioHTTPTestCase):
    async def get_application(self):
        self.fake=FakeARI()
        s=Settings(**SettingsTests().base(allow_origination=True))
        app=app_factory(s,ari=self.fake)
        self.fake.manager=app[KEY]
        return app

    async def api(self,method,path,token=AG,body=None):
        response=await self.client.request(method,path,json=body,
                                           headers={'Authorization':'Bearer '+token})
        return response.status,await response.json()

    async def test_read_only_preflight_requires_operator_and_never_dials(self):
        stat,_=await self.api('GET','/v1/readiness',AG)
        self.assertEqual(stat,401)
        self.assertEqual(self.fake.calls,[])
        stat,report=await self.api('GET','/v1/readiness',OP)
        self.assertEqual(stat,200)
        self.assertEqual(report['kind'],'BYOT_READ_ONLY_ENDPOINT_OBSERVATION')
        self.assertEqual(report['endpoint_state'],'online')
        self.assertEqual(report['preflight_state'],'ENDPOINT_ONLINE_ROUTE_UNVERIFIED')
        self.assertFalse(report['network_call_authorised'])
        self.assertFalse(report['sip_options_2xx_verified'])
        self.assertFalse(report['pbx_route_policy_verified'])
        self.assertFalse(report['media_encryption_verified'])
        self.assertIn('CARRIER_PSTN_REACHABILITY',report['not_proven'])
        self.assertEqual(self.fake.calls,[('GET','/endpoints/PJSIP/isolatedtrunk',None)])
        self.assertEqual(self.fake.channels,set())
        self.fake.calls.clear()
        self.fake.enabled=False
        stat,report=await self.api('GET','/v1/readiness',OP)
        self.assertEqual(stat,200)
        self.assertEqual(report['preflight_state'],'BLOCKED')
        self.assertEqual(report['reason'],'ENDPOINT_NOT_ONLINE')
        self.assertFalse(report['endpoint_online_observed'])
        self.assertFalse(report['network_call_authorised'])
        self.assertEqual(self.fake.channels,set())

    async def test_readiness_fails_closed_when_ari_unavailable(self):
        self.fake.connected=False
        stat,report=await self.api('GET','/v1/readiness',OP)
        self.assertEqual(stat,503)
        self.assertEqual(report['reason'],'ARI_NOT_CONNECTED')
        self.assertFalse(report['network_call_authorised'])
        self.assertFalse(report['endpoint_observed'])
        self.assertEqual(self.fake.calls,[])

    async def mandate_and_call(self):
        stat,m=await self.api('POST','/v1/mandates',OP,
                              {'destination':TEST_PHONE,'max_seconds':20})
        self.assertEqual(stat,201)
        stat,c=await self.api('POST','/v1/calls',AG,{'mandate_id':m['mandate_id']})
        self.assertEqual(stat,201)
        return m,c

    async def admit(self,call):
        stat,t=await self.api('POST',f"/v1/calls/{call['call_id']}/tickets")
        self.assertEqual(stat,200)
        ws=await self.client.ws_connect(f"/v1/calls/{call['call_id']}/media")
        await ws.send_json({'type':'admit','ticket':t['ticket']})
        self.assertEqual((await ws.receive_json())['type'],'admitted')
        return ws,t

    async def wait_state(self,cid,state,timeout=3):
        for _ in range(int(timeout/.01)):
            stat,c=await self.api('GET',f'/v1/calls/{cid}')
            if c['state']==state: return c
            await asyncio.sleep(.01)
        self.fail(f'call did not reach state {state}')

    async def test_real_ari_contract_full_duplex_and_stop(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        await ws.send_json({'type':'start'})
        await self.wait_state(call['call_id'],'bridged')
        # Actual network UDP packet, trusted peer port and L16 bytes.
        self.fake.inject(b'\x01\x02'*320)
        inbound=None
        for _ in range(6):
            message=await ws.receive(timeout=1)
            if message.type == WSMsgType.BINARY:
                inbound=message.data;break
        self.assertIsNotNone(inbound)
        self.assertEqual(inbound[:4],b'DT01')
        self.assertEqual(inbound[16:],b'\x01\x02'*320)
        # Send through agent WebSocket; receive a genuine UDP packet at fake PBX.
        await ws.send_bytes(AGENT_HEADER.pack(b'DT01',1,20)+b'\x03\x04'*320)
        self.fake.sock.setblocking(False)
        data,source=await asyncio.wait_for(asyncio.get_running_loop().sock_recvfrom(self.fake.sock,2000),1)
        self.assertEqual(decode_rtp(data)[4],b'\x03\x04'*320)
        stat,stopped=await self.api('POST',f"/v1/calls/{call['call_id']}/stop",OP,{})
        self.assertEqual(stat,200)
        self.assertEqual(stopped['state'],'ended')
        self.assertTrue(stopped['pbx_channel_absence_observed'])
        self.assertFalse(stopped['carrier_release_verified'])
        self.assertEqual(len(self.fake.channels),0)
        originate=[p for method,path,p in self.fake.calls if method=='POST' and path=='/channels']
        self.assertEqual(originate[0]['endpoint'],'PJSIP/'+TEST_PHONE+'@isolatedtrunk')
        self.assertTrue(any(path.endswith('/addChannel') for _,path,_ in self.fake.calls))

    async def test_live_dialling_default_is_disabled_and_no_ari_originate(self):
        self.app[KEY].settings = Settings(**SettingsTests().base())
        _,call=await self.mandate_and_call()
        ws,_=await self.admit(call)
        await ws.send_json({'type':'start'})
        final=await self.wait_state(call['call_id'],'ended')
        self.assertEqual(final['reason'],'LIVE_ORIGINATION_DISABLED')
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))

    async def test_destination_whitelist_and_cannot_choose_trunk(self):
        for number in ['999','+447911123456','+448001231234','+12125551234','PJSIP/123@evil','+44207946;rm -rf /']:
            status,_=await self.api('POST','/v1/mandates',OP,{'destination':number,'max_seconds':20})
            self.assertEqual(status,400)
        status,_=await self.api('POST','/v1/mandates',AG,{'destination':TEST_PHONE,'max_seconds':20})
        self.assertEqual(status,401)
        status,_=await self.api('POST','/v1/mandates',OP,{'destination':TEST_PHONE,'max_seconds':20,'trunk':'evil'})
        self.assertEqual(status,400)

    async def test_one_use_mandate_and_call_capacity(self):
        mandate,call=await self.mandate_and_call()
        status,c=await self.api('POST','/v1/calls',AG,{'mandate_id':mandate['mandate_id']})
        self.assertEqual(status,403)
        status,m=await self.api('POST','/v1/mandates',OP,{'destination':TEST_PHONE,'max_seconds':20})
        status,c=await self.api('POST','/v1/calls',AG,{'mandate_id':m['mandate_id']})
        self.assertEqual(status,409)
        await self.api('POST',f"/v1/calls/{call['call_id']}/stop",OP,{})

    async def test_offline_endpoint_fails_before_origination(self):
        self.fake.enabled=False
        _,call=await self.mandate_and_call()
        ws,_=await self.admit(call)
        await ws.send_json({'type':'start'})
        info=await self.wait_state(call['call_id'],'ended')
        self.assertEqual(info['reason'],'PJSIP_ENDPOINT_NOT_QUALIFIED')
        self.assertEqual(info['ari_pjsip_endpoint_state'],'offline')
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))

    async def test_no_origination_before_agent_connected(self):
        mandate,call=await self.mandate_and_call()
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))
        ws,t=await self.admit(call)
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))
        await ws.close()
        await self.wait_state(call['call_id'],'ended')
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))

    async def test_replayed_ticket_refused(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        other=await self.client.ws_connect(f"/v1/calls/{call['call_id']}/media")
        await other.send_json({'type':'admit','ticket':t['ticket']})
        self.assertEqual((await other.receive_json())['code'],'ADMISSION_DENIED')
        await ws.close()

    async def test_revoked_before_start_never_dials(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        status,_=await self.api('POST',f"/v1/mandates/{mandate['mandate_id']}/revoke",OP,{})
        self.assertEqual(status,200)
        await self.wait_state(call['call_id'],'ended')
        self.assertFalse(any(path=='/channels' for _,path,_ in self.fake.calls))

    async def test_agent_cannot_read_others_credentials(self):
        status,data=await self.api('GET','/health',AG)
        self.assertNotIn('ari_user',str(data));self.assertNotIn('token',str(data))
        status,data=await self.api('POST','/v1/mandates','not authorised',{'destination':TEST_PHONE,'max_seconds':20})
        self.assertEqual(status,401)

    async def test_ari_hangup_failure_never_claims_confirmed(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        await ws.send_json({'type':'start'})
        await self.wait_state(call['call_id'],'bridged')
        self.fake.hangup_fail=True
        status,stopped=await self.api('POST',f"/v1/calls/{call['call_id']}/stop",OP,{})
        self.assertEqual(status,200)
        self.assertFalse(stopped['pbx_channel_absence_observed'])
        self.assertFalse(stopped['carrier_release_verified'])

    async def test_external_media_rejects_spoofed_rtp(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        await ws.send_json({'type':'start'})
        await self.wait_state(call['call_id'],'bridged')
        obj=self.app[KEY].calls[call['call_id']]
        pkt=RTP_HEADER.pack(0x80,118,50,100,80)+swap16(b'\x01\x02'*320)
        # Directly feed a packet from the wrong port. No media should be forwarded.
        obj.rtp.datagram_received(pkt,('127.0.0.1',self.fake.remote_port+1))
        self.assertEqual(obj.rtp.counters.rejected,1)
        await self.api('POST',f"/v1/calls/{call['call_id']}/stop",OP,{})

    async def test_unexpected_pbx_release_ends_session(self):
        mandate,call=await self.mandate_and_call()
        ws,t=await self.admit(call)
        await ws.send_json({'type':'start'})
        await self.wait_state(call['call_id'],'bridged')
        obj=self.app[KEY].calls[call['call_id']]
        self.fake.channels.discard(obj.outbound_id)
        await self.app[KEY].on_ari_event({'type':'StasisEnd','channel':{'id':obj.outbound_id}})
        state=await self.wait_state(call['call_id'],'ended')
        self.assertEqual(state['reason'],'PBX_CHANNEL_ENDED')

if __name__=='__main__': unittest.main()
