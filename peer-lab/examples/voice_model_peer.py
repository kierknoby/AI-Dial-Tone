#!/usr/bin/env python3
"""A configurable, audio-native peer for the LOCAL AI Dial-Tone laboratory.

Real speech recognition, reasoning and synthesis are provided by user-selected
compatible APIs. Real-world calling, payment, booking and SIP remain unavailable.

WARNING: media is uploaded to the ASR provider and transcripts to the model.
Operator must approve external processing separately from local lab authorisation.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from aiohttp import ClientSession
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from client import PeerClient
from model_adapter import ChatModel
from speech import TranscriptionAPI, SpeechAPI, EspeakTTS
from voice_peer import VoicePeer

SYSTEM = (
    'You are participating in a fictional, strictly local restaurant voice laboratory. '
    'Discuss fictional availability only. Never state that a real reservation has '
    'been created or accept payment. You have no calendar or telephone tools. '
    'Reply naturally and briefly, in a maximum of two sentences. '
    'If unclear, ask for clarification instead of inventing details.'
)


def required(name):
    value=os.getenv(name,'').strip()
    if not value:
        raise SystemExit(f'Missing required configuration: {name}')
    return value


def is_external(endpoint):
    return urlsplit(endpoint).hostname not in ('127.0.0.1','::1','localhost')


async def main():
    base=os.getenv('AIDT_PEER_URL','http://127.0.0.1:8765')
    session=required('AIDT_PEER_SESSION')
    token=required('AIDT_PEER_TOKEN')
    model_url=required('AIDT_MODEL_URL')
    asr_url=required('AIDT_ASR_URL')
    tts_url=os.getenv('AIDT_TTS_URL')
    if any(is_external(u) for u in (model_url,asr_url) if u) or (tts_url and is_external(tts_url)):
        if os.getenv('AIDT_EXTERNAL_AUDIO_PROCESSING_APPROVED') != 'YES':
            raise SystemExit('External AI processing requires explicit AIDT_EXTERNAL_AUDIO_PROCESSING_APPROVED=YES')
    asr=TranscriptionAPI(asr_url,required('AIDT_ASR_MODEL'),key=os.getenv('AIDT_ASR_KEY',''))
    chat=ChatModel(model_url,required('AIDT_MODEL_NAME'),token=os.getenv('AIDT_MODEL_KEY',''))
    voice=(SpeechAPI(tts_url,required('AIDT_TTS_MODEL'),required('AIDT_TTS_VOICE'),
                      key=os.getenv('AIDT_TTS_KEY','')) if tts_url else EspeakTTS())
    async with ClientSession() as http:
        peer=VoicePeer(PeerClient(http,base,token,session),asr,chat,voice,SYSTEM,max_turns=6)
        try:
            await peer.run(http)
        finally:
            # Metrics only. Never print credentials or private conversation text.
            print(json.dumps(peer.metrics(),indent=2))

if __name__=='__main__': asyncio.run(main())
