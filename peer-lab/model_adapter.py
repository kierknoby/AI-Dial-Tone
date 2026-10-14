"""Generic AI chat adapter for the local AI Dial-Tone Peer Lab.

This is a TEXT-sidecar model bridge, not speech recognition or SIP. Only chat
completion results are accepted; model-requested tools/actions are ignored.
A separate TTS/ASR layer is needed for genuine audio-native conversations.
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import inspect
from urllib.parse import urlsplit
from aiohttp import ClientSession, ClientError
from client import PeerClient


class ModelError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ChatModel:
    def __init__(self, endpoint, model, *, token='', timeout=12, max_tokens=160):
        address = urlsplit(endpoint)
        if (address.scheme not in ('http','https') or not address.hostname or
                address.username or address.password or address.fragment or address.query or
                not address.path.endswith('/chat/completions')):
            raise ModelError('INVALID_MODEL_ENDPOINT')
        host=address.hostname
        try:
            is_loopback=ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback=host=='localhost'
        if address.scheme=='http' and not is_loopback:
            raise ModelError('REMOTE_MODEL_REQUIRES_HTTPS')
        if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}',model):
            raise ModelError('INVALID_MODEL_NAME')
        if not isinstance(token,str) or len(token)>500:
            raise ModelError('INVALID_API_CREDENTIAL')
        if type(max_tokens) is not int or not 32<=max_tokens<=512:
            raise ModelError('INVALID_TOKEN_BUDGET')
        self.endpoint=endpoint;self.model=model;self.token=token
        self.timeout=timeout;self.max_tokens=max_tokens

    async def respond(self,http: ClientSession,history,system_prompt):
        if (not isinstance(history,list) or not history or len(history)>16 or
                any(not isinstance(m,dict) or m.get('role') not in ('user','assistant') or
                    not isinstance(m.get('content'),str) or len(m['content'])>1200 for m in history)):
            raise ModelError('INVALID_MODEL_CONTEXT')
        if not isinstance(system_prompt,str) or not 30<=len(system_prompt)<=2000:
            raise ModelError('INVALID_SYSTEM_PROMPT')
        payload={'model':self.model,'messages':[{'role':'system','content':system_prompt},*history],
                 'max_tokens':self.max_tokens,'temperature':0.4,'stream':False}
        headers={'Content-Type':'application/json'}
        if self.token:headers['Authorization']='Bearer '+self.token
        try:
            async with http.post(self.endpoint,json=payload,headers=headers,allow_redirects=False,
                                 timeout=self.timeout) as r:
                if r.status!=200:
                    raise ModelError('MODEL_HTTP_FAILURE')
                if (r.content_length is not None and r.content_length>24_000):
                    raise ModelError('MODEL_RESPONSE_TOO_LARGE')
                raw=await r.content.read(24_001)
                if len(raw)>24_000:raise ModelError('MODEL_RESPONSE_TOO_LARGE')
                data=json.loads(raw)
        except ModelError:raise
        except (OSError,ValueError,asyncio.TimeoutError,TypeError,ClientError) as exc:
            raise ModelError('MODEL_UNAVAILABLE_OR_INVALID_RESPONSE') from exc
        try:
            answer=data['choices'][0]['message']
            if answer.get('tool_calls') or answer.get('function_call'):
                raise ModelError('MODEL_TOOL_CALL_REJECTED')
            text=answer['content']
            if (not isinstance(text,str) or not 1<=len(text.strip())<=1200 or
                    any(ord(c)<32 and c not in '\n\t' for c in text)):
                raise ModelError('MODEL_OUTPUT_REJECTED')
            return text.strip()
        except (KeyError,TypeError,IndexError) as exc:
            raise ModelError('MODEL_OUTPUT_REJECTED') from exc


class ModelPeer:
    """Connect a caller or destination agent through the local text-sidecar contract.

    The AI provider is solely a text-completion engine; it receives no API secrets,
    no actual SIP numbers and no privileged tool interface.
    """
    def __init__(self, client: PeerClient, model: ChatModel, system_prompt: str, *, max_turns=4, speech=None):
        if type(max_turns) is not int or not 1<=max_turns<=8:
            raise ModelError('INVALID_TURN_LIMIT')
        self.client=client;self.model=model
        self.system_prompt=system_prompt
        self.max_turns=max_turns
        self.speech=speech  # optional callable(text)->PCM bytes; not an ASR implementation
        self.history=[]
        self.turns=0
        self.pending=None
        self.errors=[]

    async def _reply(self,http: ClientSession):
        try:
            text=await self.model.respond(http,self.history[-16:],self.system_prompt)
            self.history.append({'role':'assistant','content':text})
            await self.client.say(text)
            if self.speech is not None:
                raw=self.speech(text)
                if inspect.isawaitable(raw):raw=await raw
                if not isinstance(raw,bytes) or len(raw)<640 or len(raw)%640 or len(raw)>640*300:
                    raise ModelError('INVALID_GENERATED_AUDIO')
                for n in range(0,len(raw),640):
                    await self.client.pcm(raw[n:n+640],timestamp_ms=n//640*20)
                    await asyncio.sleep(0.0205)
                await self.client.audio_end()
        except asyncio.CancelledError:
            raise
        except (ModelError,OSError) as exc:
            self.errors.append(exc.code if isinstance(exc,ModelError) else 'MODEL_SOCKET_FAILURE')
            # Fail safe: do not forward an invented model answer or report success.
            try:await self.client.hangup()
            except Exception:pass

    async def run(self,http: ClientSession):
        """Respond to independent peer text; cancel pending inference on interruption.

        TTS/ASR are intentionally not supplied by this class. The peer lab itself
        relays actual PCM frames; audio-generating models must supply a separate
        signed/consented transcription pipeline before production calling.
        """
        await self.client.connect()
        try:
            while True:
                message=await self.client.recv(timeout=90)
                typ=message.get('type')
                if typ in ('session.ended','socket.closed'):
                    return
                if typ=='audio.interrupt':
                    if self.pending and not self.pending.done():
                        self.pending.cancel()
                        await asyncio.gather(self.pending,return_exceptions=True)
                    continue
                if typ!='say':
                    continue
                prompt=message.get('text')
                if not isinstance(prompt,str) or not 1<=len(prompt)<=1200:
                    continue
                if self.pending and not self.pending.done():
                    self.pending.cancel()
                    await asyncio.gather(self.pending,return_exceptions=True)
                if self.turns>=self.max_turns:
                    await self.client.hangup()
                    return
                self.turns+=1
                self.history.append({'role':'user','content':prompt})
                self.pending=asyncio.create_task(self._reply(http))
        finally:
            if self.pending and not self.pending.done():
                self.pending.cancel()
                await asyncio.gather(self.pending,return_exceptions=True)
            await self.client.close()
