"""Real ARI REST + event WebSocket *wire protocol* with local fake PBX.

This is not an Asterisk instance, carrier, SIP trace, or interoperability test.
"""
import asyncio
import json
import socket
import unittest
from aiohttp import web, ClientSession, WSMsgType
from aiohttp.test_utils import unused_port
from byot.server import Settings, app_factory
from byot.client import CallClient
from byot.rtp import RTP_HEADER, swap16, decode_rtp, AGENT_HEADER

OP = 'operator-'+'o'*48
AG = 'agent-'+'a'*48
DRAMA_NUMBER = '+442079460000'

class WireTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.audit=[]
        self.channels=set()
        self.media_dest=None
        self.ari_ws=None
        self.rtp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.rtp.bind(('127.0.0.1',0))
        self.rtp.setblocking(False)
        async def verify(req):
            self.assertEqual(req.headers.get('Authorization'), 'Basic YXJpdXNlcjpBcmlQYXNzMTIzIQ==')
        async def events(req):
            await verify(req)
            self.assertEqual(req.query.get('app'),'aidt')
            ws=web.WebSocketResponse()
            await ws.prepare(req)
            self.ari_ws=ws
            async for msg in ws:
                pass
            return ws
        async def request(req):
            await verify(req)
            p=req.path
            method=req.method
            self.audit.append((method,p,dict(req.query)))
            if method=='GET' and p=='/ari/endpoints/PJSIP/labtrunk':
                return web.json_response({'state':'online','technology':'PJSIP','resource':'labtrunk'})
            if method=='POST' and p=='/ari/channels':
                cid=req.query['channelId']
                self.channels.add(cid)
                await self.ari_ws.send_json({'type':'StasisStart','channel':{'id':cid}})
                return web.json_response({'id':cid})
            if method=='POST' and p=='/ari/channels/externalMedia':
                cid=req.query['channelId']
                self.channels.add(cid)
                self.assertEqual(req.query['format'],'slin16')
                self.assertEqual(req.query['transport'],'udp')
                self.media_dest=('127.0.0.1',int(req.query['external_host'].split(':')[1]))
                await self.ari_ws.send_json({'type':'StasisStart','channel':{'id':cid}})
                return web.json_response({'id':cid})
            if method=='GET' and p.endswith('/variable'):
                self.assertEqual(req.query['variable'],'UNICASTRTP_LOCAL_PORT')
                return web.json_response({'value':str(self.rtp.getsockname()[1])})
            if method=='POST' and p.endswith('/addChannel'):
                self.assertEqual(len(req.query['channel'].split(',')),2)
                return web.Response(status=204)
            if method=='POST' and p.startswith('/ari/bridges/'):
                return web.Response(status=204)
            if method=='DELETE' and p.startswith('/ari/channels/'):
                self.channels.discard(p.split('/')[-1])
                return web.Response(status=204)
            if method=='GET' and p.startswith('/ari/channels/'):
                if p.split('/')[-1] in self.channels:return web.json_response({'id':p.split('/')[-1]})
                return web.Response(status=404)
            if method=='DELETE' and p.startswith('/ari/bridges/'):
                return web.Response(status=204)
            return web.Response(status=404)
        ari_app=web.Application()
        ari_app.router.add_get('/ari/events',events)
        ari_app.router.add_route('*','/ari/{tail:.*}',request)
        self.ari_runner=web.AppRunner(ari_app,access_log=None)
        await self.ari_runner.setup()
        self.ari_site=web.TCPSite(self.ari_runner,'127.0.0.1',0)
        await self.ari_site.start()
        self.ari_port=self.ari_site._server.sockets[0].getsockname()[1]
        settings=Settings(ari_url=f'http://127.0.0.1:{self.ari_port}',ari_user='ariuser',
                          ari_password='AriPass123!',app='aidt',trunk='labtrunk',
                          operator_token=OP,agent_token=AG,allow_origination=True)
        self.runner=web.AppRunner(app_factory(settings),access_log=None)
        await self.runner.setup()
        self.site=web.TCPSite(self.runner,'127.0.0.1',0)
        await self.site.start()
        self.port=self.site._server.sockets[0].getsockname()[1]
        self.session=ClientSession()

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.cleanup()
        await self.ari_runner.cleanup()
        self.rtp.close()

    async def api(self, method, path, token, body=None):
        async with self.session.request(method,f'http://127.0.0.1:{self.port}'+path,
                                        json=body,headers={'Authorization':'Bearer '+token}) as res:
            return res.status,await res.json()

    async def test_complete_real_rest_and_websocket_ari_wire_with_udp(self):
        status,m=await self.api('POST','/v1/mandates',OP,{'destination':DRAMA_NUMBER,'max_seconds':20})
        self.assertEqual(status,201)
        status,c=await self.api('POST','/v1/calls',AG,{'mandate_id':m['mandate_id']})
        self.assertEqual(status,201)
        path=f"/v1/calls/{c['call_id']}"
        status,t=await self.api('POST',path+'/tickets',AG,{})
        ws=await self.session.ws_connect(f'http://127.0.0.1:{self.port}'+path+'/media')
        await ws.send_json({'type':'admit','ticket':t['ticket']})
        self.assertEqual((await ws.receive_json())['type'],'admitted')
        await ws.send_json({'type':'start'})
        seen=[]
        for _ in range(5):
            evt=await ws.receive_json(timeout=5)
            seen.append(evt['type'])
            if evt['type']=='media.bridged':break
        self.assertIn('call.answered',seen)
        self.assertIn('media.bridged',seen)
        self.assertEqual(len(self.channels),2)
        pcm=b'\x00\x07'*320
        self.rtp.sendto(RTP_HEADER.pack(0x80,118,70,1000,444)+swap16(pcm),self.media_dest)
        msg=await ws.receive(timeout=3)
        if msg.type==WSMsgType.TEXT:
            self.assertEqual(json.loads(msg.data)['type'],'media.ready')
            msg=await ws.receive(timeout=3)
        self.assertEqual(msg.type,WSMsgType.BINARY)
        self.assertEqual(msg.data[16:],pcm)
        await ws.send_bytes(AGENT_HEADER.pack(b'DT01',1,20)+b'\x08\x09'*320)
        data,_=await asyncio.wait_for(asyncio.get_running_loop().sock_recvfrom(self.rtp,2000),2)
        self.assertEqual(decode_rtp(data)[4],b'\x08\x09'*320)
        status,summary=await self.api('POST',path+'/stop',OP,{})
        self.assertEqual(status,200)
        self.assertEqual(summary['reason'],'OPERATOR_STOPPED')
        self.assertTrue(summary['pbx_channel_absence_observed'])
        self.assertFalse(summary['carrier_release_verified'])
        self.assertEqual(self.channels,set())
        self.assertEqual(next(q['endpoint'] for method,path,q in self.audit if path=='/ari/channels'),
                         'PJSIP/'+DRAMA_NUMBER+'@labtrunk')
        await ws.close()

    async def test_model_neutral_agent_sdk_protocol(self):
        status,m=await self.api('POST','/v1/mandates',OP,
                                {'destination':DRAMA_NUMBER,'max_seconds':20})
        status,c=await self.api('POST','/v1/calls',AG,{'mandate_id':m['mandate_id']})
        client=CallClient(self.session,f'http://127.0.0.1:{self.port}',AG,c['call_id'])
        await client.connect()
        types=[]
        for _ in range(5):
            evt=await client.recv(timeout=3)
            types.append(evt['type'])
            if evt['type']=='media.bridged':break
        self.assertIn('call.answered',types)
        self.assertIn('media.bridged',types)
        pcm=b'\x10\x20'*320
        self.rtp.sendto(RTP_HEADER.pack(0x80,118,79,1600,444)+swap16(pcm),self.media_dest)
        messages=[]
        for _ in range(4):
            evt=await client.recv(timeout=3)
            messages.append(evt)
            if evt['type']=='pcm':break
        self.assertEqual(messages[-1]['type'],'pcm')
        self.assertEqual(messages[-1]['data'][16:],pcm)
        await client.pcm(b'\x11\x22'*320,timestamp_ms=20)
        out,_=await asyncio.wait_for(asyncio.get_running_loop().sock_recvfrom(self.rtp,2000),2)
        self.assertEqual(decode_rtp(out)[4],b'\x11\x22'*320)
        await self.api('POST',f"/v1/calls/{c['call_id']}/stop",OP,{})
        ended=await client.recv(timeout=2)
        self.assertEqual(ended['type'],'session.ended')
        self.assertEqual(ended['byot_event'],'call.ended')
        self.assertEqual(ended['reason'],'OPERATOR_STOPPED')
        await client.close()

if __name__=='__main__':unittest.main()
