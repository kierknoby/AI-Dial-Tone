#!/usr/bin/env python3
"""Reproducible two-agent local conversation with real bidirectional PCM transport.

The dialogue is scripted, NOT model-generated or speech-recognised. Audio is
optionally synthesised with eSpeak and converted with ffmpeg. No real phone calls,
PSTN, calendar reservation, x402 payment, or cloud model is used.
"""
import asyncio
import json
import secrets
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

from aiohttp import ClientSession, web

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from peer_lab import make_app
from client import PeerClient


async def api(http,method,url,token,data,idem=None):
    h={'Authorization':'Bearer '+token}
    if idem:h['Idempotency-Key']=idem
    async with http.request(method,url,headers=h,json=data) as response:
        payload=await response.json()
        if response.status not in (200,201):
            raise RuntimeError(f'{url} -> {response.status}: {payload}')
        return payload


def synth(text):
    """Returns local voice PCM or a 1.2s audible tone when eSpeak is unavailable.

    Explicitly does not perform recognition or transcribe an incoming audio frame.
    """
    if shutil.which('espeak') and shutil.which('ffmpeg'):
        wav=subprocess.run(['espeak','-v','en-gb','-s','160','--stdout',text],
                           capture_output=True,check=True,timeout=10).stdout
        pcm=subprocess.run(['ffmpeg','-loglevel','error','-i','pipe:0','-f','s16le',
                            '-ar','16000','-ac','1','pipe:1'],input=wav,capture_output=True,
                           check=True,timeout=15).stdout
    else:
        import math
        pcm=b''.join(int(3500*math.sin(i/16000*2*math.pi*440)).to_bytes(2,'little',signed=True)
                     for i in range(19200))
    n=((len(pcm)+639)//640)*640
    return pcm.ljust(n,b'\0')


async def play(client, speech, *, limit=350, pace=0.0205):
    """Deliver real PCM bytes, deliberately quicker than realtime for the lab demo."""
    raw=synth(speech)
    for i,at in enumerate(range(0,min(len(raw),limit*640),640)):
        await client.pcm(raw[at:at+640], timestamp_ms=i*20)
        await asyncio.sleep(pace)
    await client.audio_end()
    return min(len(raw)//640,limit)


def save_audio(folder,name,raw):
    path=folder/(name+'.wav')
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(raw)
    return str(path)


async def run_demo(output_dir):
    output_dir.mkdir(parents=True,exist_ok=True)
    operator='op_'+secrets.token_urlsafe(32)
    caller_token='caller_'+secrets.token_urlsafe(32)
    restaurant_token='restaurant_'+secrets.token_urlsafe(32)
    app=make_app(operator_token=operator,
                 agent_tokens={'assistant-model':caller_token},
                 peer_tokens={'restaurant-peer':restaurant_token})
    runner=web.AppRunner(app,access_log=None)
    await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',0)
    await site.start()
    port=site._server.sockets[0].getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    audio={'caller':bytearray(),'peer':bytearray()}
    dialogue=[]
    try:
        async with ClientSession() as http:
            grant=await api(http,'POST',base+'/v1/mandates',operator,{
                'caller_id':'assistant-model', 'peer_id':'restaurant-peer',
                'task':'Fictional reservation enquiry for demonstration only; no real business contacted.',
                'max_seconds':40})
            created=await api(http,'POST',base+'/v1/sessions',caller_token,
                              {'mandate_id':grant['mandate_id']},idem='demo-first-call-00000001')
            sid=created['session']['session_id']
            async def callee():
                c=PeerClient(http,base,restaurant_token,sid)
                await c.connect()
                try:
                    while True:
                        msg=await c.recv(timeout=10)
                        if msg['type']=='pcm': audio['peer'].extend(msg['data'][16:]); continue
                        if msg['type']=='say':
                            dialogue.append({'speaker':'caller','text':msg['text']})
                            answer='This is a test restaurant peer. No real table has been booked.'
                            await c.say(answer)
                            await play(c,answer)
                        if msg['type'] in ('session.ended','socket.closed'):return
                finally:
                    await c.close()
            worker=asyncio.create_task(callee())
            c=PeerClient(http,base,caller_token,sid)
            await c.connect()
            try:
                while True:
                    msg=await c.recv(timeout=10)
                    if msg['type']=='session.connected':break
                greeting='Hello. Could I book a table for two at seven thirty?'
                await c.say(greeting)
                await play(c,greeting)
                received=False
                end=time.monotonic()+15
                while time.monotonic()<end:
                    msg=await c.recv(timeout=10)
                    if msg['type']=='pcm':
                        audio['caller'].extend(msg['data'][16:])
                        continue
                    if msg['type']=='audio.end' and msg['speaker']=='peer':
                        break
                    if msg['type']=='say':
                        dialogue.append({'speaker':'peer','text':msg['text']})
                        received=True
                        continue
                    if msg['type']=='session.ended':break
                    if received and len(audio['caller'])>=6400:break
                await c.hangup()
                try:await c.recv(timeout=3)
                except Exception:pass
            finally:
                await c.close()
            await asyncio.wait_for(worker,timeout=6)
            async with http.get(base+'/v1/sessions/'+sid,
                                headers={'Authorization':'Bearer '+caller_token}) as res:
                data=await res.json()
        receipt=data['session']
        result={
            'experiment':'AI Dial-Tone First Call Peer Lab',
            'local_websocket_agents':2,
            'dialogue':dialogue,
            'receipt':receipt,
            'wav_files':{
                'caller_heard':save_audio(output_dir,'caller_heard',bytes(audio['caller'])),
                'peer_heard':save_audio(output_dir,'peer_heard',bytes(audio['peer'])),
            },
            'caution':'Scripted text side-channel, independently carried real PCM; no ASR, LLM, PSTN, calendar or booking.',
        }
        assert receipt['state']=='ended' and receipt['reason']=='CALLER_HANGUP',receipt
        assert receipt['frames_by_role']['caller']>1 and receipt['frames_by_role']['peer']>1, receipt
        assert len(dialogue)==2,dialogue
        assert len(audio['caller'])>6400 and len(audio['peer'])>6400
        path=output_dir/'proof.json'
        path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'proof_file':str(path),'receipt':receipt,'dialogue':dialogue},indent=2))
        return result
    finally:
        await runner.cleanup()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='demo-output')
    args=parser.parse_args()
    asyncio.run(run_demo(Path(args.out)))
