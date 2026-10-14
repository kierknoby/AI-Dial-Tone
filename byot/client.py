"""BYOT adapter for the existing model-neutral VoicePeer runtime.

No phone-number, SIP-trunk or ARI credentials are available to this client.
The human operator issues the immutable mandate, and BYOT owns origination.
"""
from __future__ import annotations
import json
import struct
from urllib.parse import urlsplit
from aiohttp import WSMsgType


class CallClient:
    def __init__(self,http,base,agent_token,call_id):
        address=urlsplit(base)
        if (address.scheme!='http' or address.hostname not in ('localhost','127.0.0.1','::1') or
            address.username or address.password or address.query or address.fragment or
            address.path not in ('','/')):
            raise ValueError('BYOT_CONTROL_REQUIRES_LOOPBACK')
        if not agent_token or not call_id:
            raise ValueError('MISSING_CALL_OR_CREDENTIAL')
        self.http=http
        self.base=base.rstrip('/')
        self.token=agent_token
        self.call_id=call_id
        self.ws=None
        self.seq=0

    async def connect(self):
        path=f'/v1/calls/{self.call_id}'
        async with self.http.post(self.base+path+'/tickets',headers={'Authorization':'Bearer '+self.token}) as res:
            payload=await res.json()
            if res.status != 200:
                raise ValueError('BYOT_TICKET_DENIED')
        base=self.base.replace('http://','ws://',1)
        self.ws=await self.http.ws_connect(base+path+'/media',max_msg_size=2048)
        await self.ws.send_json({'type':'admit','ticket':payload['ticket']})
        message=await self.ws.receive_json(timeout=5)
        if message.get('type')!='admitted':
            raise ValueError('BYOT_ADMISSION_FAILED')
        await self.ws.send_json({'type':'start'})
        return message

    async def recv(self,timeout=10):
        message=await self.ws.receive(timeout=timeout)
        if message.type==WSMsgType.BINARY:
            return {'type':'pcm','data':message.data}
        if message.type==WSMsgType.TEXT:
            result=json.loads(message.data)
            if result.get('type')=='call.ended':
                # Compatibility with VoicePeer's non-telephone session abstraction.
                return {**result,'type':'session.ended','byot_event':'call.ended'}
            return result
        return {'type':'socket.closed','close_code':message.data}

    async def pcm(self,pcm,timestamp_ms=0):
        if len(pcm)!=640:raise ValueError('INVALID_PCM_LENGTH')
        self.seq+=1
        await self.ws.send_bytes(struct.pack('!4sIQ',b'DT01',self.seq,timestamp_ms)+pcm)

    async def say(self,text):
        # ASR/model-generated words never masquerade as PBX observations.
        # The BYOT control service deliberately does not accept asserted transcripts.
        return None

    async def audio_end(self):
        await self.ws.send_json({'type':'audio.end'})

    async def interrupt(self):
        await self.ws.send_json({'type':'audio.interrupt'})

    async def dtmf(self,digits):
        await self.ws.send_json({'type':'dtmf','digits':digits})

    async def hangup(self):
        if self.ws and not self.ws.closed:
            await self.ws.send_json({'type':'hangup'})

    async def close(self):
        if self.ws and not self.ws.closed:await self.ws.close()
