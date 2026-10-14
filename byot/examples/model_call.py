#!/usr/bin/env python3
"""Bring your own ASR, LLM and TTS to a user-authorised Asterisk session.

ASR/model/TTS traffic can leave your network: explicit separate approval required.
The model has no destination, payment, dialplan, ARI or SIP credentials.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from aiohttp import ClientSession

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'peer-lab'))
from model_adapter import ChatModel
from speech import TranscriptionAPI, SpeechAPI, EspeakTTS
from voice_peer import VoicePeer
from byot.client import CallClient

SYSTEM = (
    'You are on an authorised experimental telephone call to a consenting test party. '
    'Speak briefly and naturally, one or two sentences at a time. '
    'Ask clarifying questions rather than assuming anything. '
    'Do not claim to have made a reservation or completed a transaction. '
    'A spoken assertion is not independent booking or payment evidence. '
    'If you are unsure whether the call has ended or an outcome is final, say so.'
)


def need(name):
    v=os.getenv(name,'').strip()
    if not v:raise SystemExit('Missing '+name)
    return v


def remote(url):
    return urlsplit(url).hostname not in ('127.0.0.1','::1','localhost')


async def main():
    base=os.getenv('AIDT_BYOT_URL','http://127.0.0.1:8877')
    token=need('AIDT_AGENT_TOKEN')
    mandate=need('AIDT_MANDATE_ID')
    model_url=need('AIDT_MODEL_URL')
    asr_url=need('AIDT_ASR_URL')
    tts_url=os.getenv('AIDT_TTS_URL','')
    if any(remote(endpoint) for endpoint in (model_url,asr_url,tts_url) if endpoint):
        if os.getenv('AIDT_EXTERNAL_AUDIO_PROCESSING_APPROVED')!='YES':
            raise SystemExit('Explicit approval is required before external audio/transcript processing')
    asr=TranscriptionAPI(asr_url,need('AIDT_ASR_MODEL'),key=os.getenv('AIDT_ASR_KEY',''))
    model=ChatModel(model_url,need('AIDT_MODEL_NAME'),token=os.getenv('AIDT_MODEL_KEY',''))
    tts=(SpeechAPI(tts_url,need('AIDT_TTS_MODEL'),need('AIDT_TTS_VOICE'),
                   key=os.getenv('AIDT_TTS_KEY','')) if tts_url else EspeakTTS())
    async with ClientSession() as http:
        async with http.post(base+'/v1/calls',json={'mandate_id':mandate},
                             headers={'Authorization':'Bearer '+token},allow_redirects=False) as resp:
            data=await resp.json()
            if resp.status!=201:raise SystemExit('Call refused: '+data.get('error','UNKNOWN'))
        client=CallClient(http,base,token,data['call_id'])
        print('Call ID for operator stop:',data['call_id'])
        bot=VoicePeer(client,asr,model,tts,SYSTEM,max_turns=6)
        try:await bot.run(http)
        finally:
            # Metrics are not verified booking, call settlement or delivery evidence.
            print(json.dumps(bot.metrics(),indent=2))

if __name__=='__main__':asyncio.run(main())
