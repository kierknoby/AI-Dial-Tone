#!/usr/bin/env python3
"""Agent-operated isolated PBX media diagnostic: 425 Hz 1s test tone.

NOT a real conversation, booking or a test involving an unconsenting recipient.
"""
from __future__ import annotations
import asyncio
import json
import math
import os
import struct
from aiohttp import ClientSession
from byot.client import CallClient


def need(name):
    value=os.getenv(name,'')
    if not value: raise SystemExit('Missing '+name)
    return value


async def main():
    base=os.getenv('AIDT_BYOT_URL','http://127.0.0.1:8877')
    token=need('AIDT_AGENT_TOKEN')
    mandate=need('AIDT_MANDATE_ID')
    async with ClientSession() as http:
        async with http.post(base+'/v1/calls',json={'mandate_id':mandate},
                             headers={'Authorization':'Bearer '+token},allow_redirects=False) as resp:
            data=await resp.json()
            if resp.status!=201:raise SystemExit('Call refused: '+data.get('error','UNKNOWN'))
        client=CallClient(http,base,token,data['call_id'])
        print('Call ID for operator stop:',data['call_id'])
        await client.connect()  # Separate from HTTP creation: only now may Asterisk dial.
        received=0
        sent=0
        try:
            while True:
                evt=await client.recv(timeout=45)
                kind=evt.get('type')
                if kind=='media.ready':
                    print('First validated RTP received; sending one second 425 Hz diagnostic')
                    for frame in range(50):
                        samples=[int(1400*math.sin(2*math.pi*425*(frame*320+i)/16000)) for i in range(320)]
                        await client.pcm(struct.pack('<320h',*samples),timestamp_ms=frame*20)
                        sent+=1
                        await asyncio.sleep(.02)
                    await client.audio_end()
                    await asyncio.sleep(1)
                    await client.hangup()
                elif kind=='pcm':received+=1
                elif kind in ('session.ended','socket.closed'):
                    print(json.dumps({'frames_received':received,'frames_sent':sent,
                                      'reason':evt.get('reason'),'carrier_release_verified':False}))
                    break
        finally:await client.close()

if __name__=='__main__':asyncio.run(main())
