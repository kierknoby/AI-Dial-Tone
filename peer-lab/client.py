"""Model-neutral client for the local AI Dial-Tone peer laboratory.

No SIP operations or real-world booking are performed here. The client can be
used by any process that implements transcription and text/voice generation.
"""
import json
import struct
from urllib.parse import urlsplit
from aiohttp import ClientSession, WSMsgType


class PeerClient:
    def __init__(self, http, base, token, session_id):
        address=urlsplit(base)
        if (address.scheme != 'http' or address.hostname not in ('localhost','127.0.0.1','::1') or
                address.username or address.password or address.query or address.fragment or
                address.path not in ('','/')):
            raise ValueError('PEER_LAB_REQUIRES_LOOPBACK_HTTP')
        self.http = http
        self.base = base.rstrip('/')
        self.token = token
        self.session_id = session_id
        self.ws = None
        self.seq = 0

    async def connect(self):
        base_path = f'/v1/sessions/{self.session_id}'
        async with self.http.post(self.base + base_path + '/tickets',
                                  headers={'Authorization': 'Bearer ' + self.token}) as res:
            data = await res.json()
            if res.status != 200:
                raise ValueError('PEER_TICKET_REJECTED:' + data.get('error','UNKNOWN'))
        path = self.base.replace('http://', 'ws://').replace('https://', 'wss://')
        self.ws = await self.http.ws_connect(path + base_path + '/connect', max_msg_size=2048)
        await self.ws.send_json({'type':'admit','ticket': data['ticket']})
        msg=await self.ws.receive_json(timeout=5)
        if msg.get('type')!='admitted':
            raise ValueError('ADMISSION_REJECTED')
        return msg

    async def recv(self, timeout=10):
        msg=await self.ws.receive(timeout=timeout)
        if msg.type == WSMsgType.TEXT:
            return json.loads(msg.data)
        if msg.type == WSMsgType.BINARY:
            return {'type':'pcm','data':msg.data}
        return {'type':'socket.closed','close_code':msg.data}

    async def say(self, text):
        await self.ws.send_json({'type':'say','text':text})

    async def dtmf(self, digits):
        await self.ws.send_json({'type':'dtmf','digits':digits})

    async def pcm(self, samples, timestamp_ms=0):
        """Send one exactly-20-ms 16-kHz mono signed 16-bit PCM frame."""
        if len(samples)!=640:
            raise ValueError('EXPECTED_640_PCM_BYTES')
        self.seq += 1
        await self.ws.send_bytes(struct.pack('!4sIQ',b'DT01',self.seq,timestamp_ms)+samples)

    async def audio_end(self):
        await self.ws.send_json({'type':'audio.end'})

    async def interrupt(self):
        await self.ws.send_json({'type':'audio.interrupt'})

    async def hangup(self):
        await self.ws.send_json({'type':'hangup'})

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
