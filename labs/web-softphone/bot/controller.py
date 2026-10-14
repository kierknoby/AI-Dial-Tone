#!/usr/bin/env python3
"""Development-only bot controller for dialtone.agent.v2.

Requires: Python >=3.11, websockets >=14 (tested with websockets 16).
WSS with a trusted local development certificate is mandatory.
Does not perform PSTN calls or transcription. A sound-file playback + receive WAV
proves that bytes cross the bot transport; only live SIP tests prove phone audio.
"""
import argparse
import asyncio
import hashlib
import hmac
import json
import secrets
import ssl
import struct
import sys
import wave
from pathlib import Path
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed
from vad import EnergyVAD

VERSION = 'dialtone.agent.v2'
FRAME_BYTES = 641


def proof(token, role, client, server):
    payload = '|'.join((VERSION, role, client, server)).encode()
    return hmac.new(token.encode(), payload, hashlib.sha256).hexdigest()


def check_nonce(s):
    return isinstance(s, str) and len(s) == 32 and all(c in '0123456789abcdef' for c in s)


class Controller:
    def __init__(self, token, out_path=None, echo=False, play_path=None, automated_target=None, barge_in=False):
        if len(token) < 32 or len(token) > 256:
            raise ValueError('Use a 32–256 character random pairing secret')
        self.token = token
        self.out_path = out_path
        self.echo = echo
        self.play_path = play_path
        self.automated_target = automated_target
        self.barge_in = barge_in
        self.vad = EnergyVAD()
        self.used_nonces = set()
        self.used_token = False
        self.active = False
        self.frames = bytearray()
        self.events = []
        self.results = {}
        self.ws = None
        self.audio_enabled = False
        self.sequence = 0
        self.pending = {}

    async def command(self, command, target=None):
        if not self.ws or not self.active:
            raise RuntimeError('No paired browser')
        self.sequence += 1
        ident = f'bot-{self.sequence}'
        payload = dict(version=VERSION, kind='command', id=ident, command=command)
        if target is not None: payload['target'] = target
        future = asyncio.get_running_loop().create_future()
        self.pending[ident] = future
        await self.ws.send(json.dumps(payload))
        try:
            return await asyncio.wait_for(future, timeout=10)
        finally:
            self.pending.pop(ident, None)

    async def play(self, path):
        with wave.open(str(path), 'rb') as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                raise ValueError('Audio input must be a 16-kHz mono 16-bit PCM WAV')
            while self.audio_enabled and self.active:
                chunk = wf.readframes(320)
                if not chunk: break
                if len(chunk) != 640: chunk = chunk.ljust(640, b'\x00')
                await self.ws.send(b'\x02' + chunk)
                await asyncio.sleep(.02)

    def write_output(self):
        if self.out_path and self.frames:
            with wave.open(str(self.out_path), 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(bytes(self.frames))

    async def handle(self, websocket):
        if self.active or self.used_token:
            await websocket.close(4003, 'Only one controller connection'); return
        self.active = True
        self.ws = websocket
        try:
            raw = await asyncio.wait_for(websocket.recv(), 10)
            hello = json.loads(raw)
            client = hello.get('nonce')
            if hello.get('version') != VERSION or hello.get('kind') != 'hello' or not check_nonce(client) or client in self.used_nonces:
                await websocket.close(4001, 'Invalid hello'); return
            self.used_nonces.add(client)
            # The token never goes over the wire. Verify the client HMAC before pairing.
            server = secrets.token_hex(16)
            await websocket.send(json.dumps(dict(version=VERSION, kind='challenge', nonce=server,
                                                  proof=proof(self.token, 'server', client, server))))
            incoming = json.loads(await asyncio.wait_for(websocket.recv(), 10))
            expected = proof(self.token, 'client', client, server)
            if incoming.get('kind') != 'proof' or incoming.get('version') != VERSION or not hmac.compare_digest(str(incoming.get('proof', '')), expected):
                await websocket.close(4001, 'Authentication failed'); return
            self.used_token = True
            await websocket.send(json.dumps(dict(version=VERSION, kind='paired', accepted=True)))
            print('Browser paired; commands: status, readiness, diagnostics, call 1002, hangup, audio on/off, flush, quit', flush=True)
            if self.automated_target:
                asyncio.create_task(self.demo_sequence(self.automated_target))
            async for message in websocket:
                if isinstance(message, bytes):
                    if self.audio_enabled and len(message) == FRAME_BYTES and message[0] == 1:
                        self.frames.extend(message[1:])
                        speech=self.vad.feed(message[1:])
                        if speech:
                            print('VOICE:',speech,flush=True)
                            self.events.append(dict(kind='voice',type=speech))
                            if speech=='speech.start' and self.barge_in:
                                asyncio.create_task(self.command('audio.flush'))
                        if self.echo and websocket.transport.get_write_buffer_size() < 262144:
                            await websocket.send(b'\x02' + message[1:])
                    continue
                try: msg = json.loads(message)
                except json.JSONDecodeError: continue
                if msg.get('version') != VERSION: continue
                if msg.get('kind') == 'event':
                    self.events.append(msg)
                    print('EVENT:', msg.get('type'), flush=True)
                    if msg.get('type') == 'call.ended': self.audio_enabled = False
                if msg.get('kind') == 'result':
                    self.results[msg.get('id')] = msg
                    pending = self.pending.get(msg.get('id'))
                    if pending and not pending.done(): pending.set_result(msg)
                if msg.get('kind') == 'ping':
                    await websocket.send(json.dumps(dict(version=VERSION, kind='pong', id=msg.get('id'))))
        except (ConnectionClosed, asyncio.TimeoutError, json.JSONDecodeError) as exc:
            print('Session ended:', type(exc).__name__, flush=True)
        finally:
            self.active = False
            self.audio_enabled = False
            self.ws = None
            for future in self.pending.values():
                if not future.done():future.set_exception(ConnectionError('Bot disconnected'))
            self.write_output()

    async def demo_sequence(self, target):
        await asyncio.sleep(.1)
        for cmd, tgt in [('status', None), ('readiness', None), ('call', target), ('audio.enable', None)]:
            try:
                result = await self.command(cmd, tgt)
                print('RESULT', cmd, result, flush=True)
                if cmd == 'audio.enable': self.audio_enabled = bool(result.get('ok'))
            except Exception as exc: print('DEMO STOPPED:', exc, flush=True);return

    async def cli(self):
        while True:
            line = await asyncio.to_thread(input, 'bot> ')
            parts = line.strip().split()
            if not parts: continue
            if parts[0] == 'quit':break
            try:
                if parts == ['audio','on']:
                    result = await self.command('audio.enable')
                    self.audio_enabled = bool(result.get('ok'))
                    if self.audio_enabled and self.play_path:
                        asyncio.create_task(self.play(self.play_path))
                elif parts == ['audio','off']:
                    result = await self.command('audio.disable');self.audio_enabled = False
                elif parts == ['flush']:result = await self.command('audio.flush')
                elif parts[0] == 'call' and len(parts) == 2:result = await self.command('call', parts[1])
                elif parts[0] in ('status','readiness','diagnostics','hangup') and len(parts) == 1: result = await self.command(parts[0])
                else: print('Unknown command');continue
                print(json.dumps(result, indent=2))
            except Exception as exc: print('ERROR:', exc)


async def main(args):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(args.cert, args.key)
    token=args.token
    if not token: raise SystemExit('Supply --token or DIALTONE_PAIRING_TOKEN')
    controller=Controller(token, args.out, args.echo, args.play, args.demo_target, args.barge_in)
    async with serve(controller.handle, args.host, args.port, ssl=ctx, max_size=4096, ping_interval=20):
        print(f'Controller listening on wss://{args.host}:{args.port}/; secret is never logged', flush=True)
        if args.noninteractive:
            await asyncio.Future()
        else: await controller.cli()

if __name__ == '__main__':
    p=argparse.ArgumentParser(description='Development WSS bot controller')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8766)
    p.add_argument('--cert', required=True)
    p.add_argument('--key', required=True)
    p.add_argument('--token', default=__import__('os').environ.get('DIALTONE_PAIRING_TOKEN'))
    p.add_argument('--out', type=Path, help='save bot-received telephone audio as PCM WAV')
    p.add_argument('--play', type=Path, help='send a 16-kHz mono PCM WAV to phone when audio enabled')
    p.add_argument('--barge-in', action='store_true', help='flush bot playback when voice energy starts')
    p.add_argument('--echo', action='store_true', help='echo remote call audio back to far end (testing only)')
    p.add_argument('--demo-target', help='optional automatically request a local test extension')
    p.add_argument('--noninteractive', action='store_true')
    a=p.parse_args()
    try: asyncio.run(main(a))
    except KeyboardInterrupt:pass
