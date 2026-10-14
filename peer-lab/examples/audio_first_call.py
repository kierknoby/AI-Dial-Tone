#!/usr/bin/env python3
"""Offline audio-first AI Dial-Tone demonstration with genuine sampled speech.

Requires espeak, ffmpeg and libpocketsphinx with its English acoustic model.
The model server is a deterministic fixture, NOT a live LLM. Genuine offline ASR
may misrecognise words: see proof.json. Nothing is booked or dialled.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import wave
from pathlib import Path
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from client import PeerClient
from model_adapter import ChatModel
from peer_lab import make_app
from voice_peer import VoicePeer
from speech import EspeakTTS, PocketSphinxASR

SYSTEM = ('You work at a fictional restaurant in a test environment. '
          'Respond politely, never suggest an actual table was reserved, '
          'and never claim to have access to a booking system.')


def word_error_rate(reference, recognised):
    expected=reference.lower().replace('?', '').replace(',', '').split()
    heard=recognised.lower().split()
    grid=list(range(len(heard)+1))
    for i, token in enumerate(expected,1):
        next_row=[i]+[0]*len(heard)
        for j, word in enumerate(heard,1):
            next_row[j]=min(next_row[j-1]+1,grid[j]+1,grid[j-1]+int(token!=word))
        grid=next_row
    return round(grid[-1] / max(1,len(expected)),3)

def verify_chain(events, expected):
    digest='0'*64
    for ev in events:
        content={k:v for k,v in ev.items() if k!='chain_hash'}
        digest=hashlib.sha256((digest+json.dumps(content,sort_keys=True,
              ensure_ascii=False,separators=(',',':'))).encode()).hexdigest()
        if ev.get('chain_hash')!=digest:return False
    return digest==expected

def write_wav(path, raw):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(raw)


async def demonstrate(output):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    model_input=[]
    async def fake_completion(req):
        data=await req.json()
        model_input.append(data['messages'][-1]['content'])
        return web.json_response({'choices':[{'message':{'content':
            'This is the AI Dial Tone test restaurant. I cannot confirm a real booking.'}}]})
    app=web.Application();app.router.add_post('/v1/chat/completions',fake_completion)
    model_service=TestServer(app)
    await model_service.start_server()
    op='op-'+'o'*32;caller_token='ca-'+'c'*32;peer_token='pe-'+'p'*32
    lab_service=TestServer(make_app(operator_token=op,agent_tokens={'test-caller':caller_token},
                                     peer_tokens={'test-restaurant':peer_token}))
    await lab_service.start_server()
    recogniser = PocketSphinxASR()
    async with ClientSession() as http:
        base=str(lab_service.make_url('/')).rstrip('/')
        async with http.post(base+'/v1/mandates',headers={'Authorization':'Bearer '+op},json={
            'caller_id':'test-caller','peer_id':'test-restaurant',
            'task':'Audio-first fictional restaurant conversation; no real reservation',
            'max_seconds':60}) as r:
            mandate=(await r.json())['mandate_id']
        async with http.post(base+'/v1/sessions',headers={'Authorization':'Bearer '+caller_token,
                             'Idempotency-Key':'voice-first-call-00001'},json={'mandate_id':mandate}) as r:
            sid=(await r.json())['session']['session_id']
        agent=PeerClient(http,base,peer_token,sid)
        voice=VoicePeer(agent,recogniser,ChatModel(str(model_service.make_url('/v1/chat/completions')),
                                                  'fictional-model'),EspeakTTS(),SYSTEM,
                        max_turns=2,threshold=300,silence_frames=6)
        voice_task=asyncio.create_task(voice.run(http))
        caller=PeerClient(http,base,caller_token,sid)
        caller_heard=bytearray()
        try:
            await caller.connect()
            while (await caller.recv(3))['type'] != 'session.connected':pass
            spoken=await EspeakTTS().speak('Hello, could I book a table for two?')
            for n in range(0,len(spoken),640):
                await caller.pcm(spoken[n:n+640],timestamp_ms=caller.seq*20)
                await asyncio.sleep(.0205)
            await caller.audio_end()
            async def receive_reply():
                while True:
                    ev=await caller.recv(15)
                    if ev['type']=='pcm':caller_heard.extend(ev['data'][16:])
                    if ev['type'] in ('audio.end','session.ended'):return ev['type']
            response_status=await receive_reply()
            await caller.hangup()
            await asyncio.wait_for(voice_task,12)
            async with http.get(base+'/v1/sessions/'+sid,
                                headers={'Authorization':'Bearer '+caller_token}) as r:
                evidence=await r.json()
        finally:
            await caller.close()
            if not voice_task.done():voice_task.cancel();await asyncio.gather(voice_task,return_exceptions=True)
            recogniser.close()
            await lab_service.close();await model_service.close()
    write_wav(output/'caller_heard.wav',bytes(caller_heard))
    write_wav(output/'caller_spoke.wav',spoken)
    proof={
        'mode':'real_offline_speech_to_transcript_then_deterministic_chat_fixture_then_real_tts',
        'speech_asr':'pocketsphinx_offline_c_library',
        'model':'deterministic_local_http_fixture_not_real_llm',
        'speech_tts':'espeak',
        'recognised_text':voice.transcriptions,
        'reference_spoken_words':'Hello, could I book a table for two?',
        'offline_recognition_word_error_rate':word_error_rate(
            'Hello, could I book a table for two?', ' '.join(voice.transcriptions)),
        'model_received_text':model_input,
        'received_audio_sha256':hashlib.sha256(caller_heard).hexdigest(),
        'caller_heard_duration_seconds':round(len(caller_heard)/32000,2),
        'last_event':response_status,
        'session':evidence['session'],
        'hash_chain_valid':verify_chain(evidence['events'],evidence['session']['event_chain_sha256']),
        'voice_runtime':voice.metrics(),
        'limitations':['No SIP or PSTN','No external live AI model','Small offline ASR is not sufficiently accurate for booking',
                       'No independent verification of reservations','No payment settlement'],
    }
    if not caller_heard or not model_input or voice.turns!=1 or not proof['hash_chain_valid']:
        raise RuntimeError('AUDIO_FIRST_PROOF_INCOMPLETE')
    (output/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='audio-proof-0.0.1')
    opts=parser.parse_args()
    result=asyncio.run(demonstrate(opts.out))
    print(json.dumps(result,indent=2))
