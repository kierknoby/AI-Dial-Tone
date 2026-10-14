#!/usr/bin/env python3
"""Connect a REAL configurable text model to a local AI Dial-Tone peer session.

Requires an independently running Peer Lab, an operator-issued session, and
an already configured second peer. This script never dials the PSTN and does
not receive/transcribe the other peer's PCM: it consumes asserted text turns.
"""
import asyncio
import os
import sys
from pathlib import Path
from aiohttp import ClientSession

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from client import PeerClient
from model_adapter import ChatModel, ModelPeer


async def main():
    required=['AIDT_PEER_SESSION','AIDT_PEER_TOKEN','AIDT_MODEL_URL','AIDT_MODEL_NAME']
    missing=[k for k in required if not os.getenv(k)]
    if missing:
        raise SystemExit('Missing environment variable(s): '+', '.join(missing))
    url=os.getenv('AIDT_PEER_URL','http://127.0.0.1:8765')
    if not url.startswith(('http://127.0.0.1:', 'http://localhost:','http://[::1]:')):
        raise SystemExit('Peer Lab must be on loopback: public deployment is unsupported')
    async with ClientSession() as http:
        agent=PeerClient(http,url,os.environ['AIDT_PEER_TOKEN'],os.environ['AIDT_PEER_SESSION'])
        model=ChatModel(os.environ['AIDT_MODEL_URL'],os.environ['AIDT_MODEL_NAME'],
                        token=os.getenv('AIDT_MODEL_KEY',''))
        prompt='You are a fictional restaurant representative in a local AI communications experiment. '
        prompt+='Do not claim a real reservation exists, accept a deposit, or imply a real telephone call. '
        prompt+='Respond courteously and briefly. Never use tools or perform real-world actions.'
        peer=ModelPeer(agent,model,prompt,max_turns=5)
        print('Joining local peer session; no PSTN calls can be placed.',flush=True)
        await peer.run(http)
        print('Session finished. Model errors:',peer.errors,flush=True)


if __name__=='__main__':
    asyncio.run(main())
