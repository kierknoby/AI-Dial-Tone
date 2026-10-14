"""AI Dial-Tone Peer Lab: real local WebSocket agent-to-agent signalling and PCM.

This is deliberately NOT SIP, PSTN, ASR, a booking service, or a money service.
No credentials are embedded in this source. Default CLI binding is loopback only.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import struct
import time
from dataclasses import dataclass, field
from typing import Callable
from aiohttp import web, WSMsgType

MAX_BODY = 4096
MAX_EVENTS = 1200
FRAME_BYTES = 656
FRAME_HEADER = struct.Struct('!4sIQ')
MAX_UTTERANCE = 1200
MAX_MANDATES = 256
MAX_SESSIONS = 128
MAX_TICKETS = 256


def safe_text(value, minimum, maximum, *, allow_newlines=False):
    """Reject invalid Unicode scalars before event hashing or JSON broadcast."""
    return (isinstance(value, str) and minimum <= len(value) <= maximum and
            not any(0xD800 <= ord(ch) <= 0xDFFF or
                    (ord(ch) < 32 and not (allow_newlines and ch in '\n\t'))
                    for ch in value))

ROLE_KEY = web.AppKey('peer_lab', object)


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def require(value, message='INVALID_INPUT'):
    if not value:
        raise ApiError(message)


class ApiError(Exception):
    def __init__(self, code, status=400):
        self.code = code
        self.status = status
        super().__init__(code)


@dataclass
class Mandate:
    id: str
    caller: str
    peer: str
    task: str
    expires_at: float
    max_seconds: int
    used_by: str | None = None
    revoked: bool = False


@dataclass
class Session:
    id: str
    mandate: Mandate
    created_at: float
    state: str = 'awaiting_peers'
    ended_reason: str | None = None
    finished_at: float | None = None
    connected: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)
    event_hash: str = '0' * 64
    seq: int = 0
    frames: dict = field(default_factory=lambda: {'caller': 0, 'peer': 0})
    last_pcm_seq: dict = field(default_factory=lambda: {'caller': -1, 'peer': -1})
    rate: dict = field(default_factory=lambda: {'caller': [], 'peer': []})
    deadline_task: asyncio.Task | None = None
    join_task: asyncio.Task | None = None

    def emit(self, name, *, speaker='system', **data):
        # Always reserve termination evidence so hard cutoff cannot fail at quota.
        if len(self.event_log) >= MAX_EVENTS and name != 'session.ended':
            raise ApiError('EVENT_QUOTA_EXCEEDED', 429)
        self.seq += 1
        item = {'seq': self.seq, 'type': name, 'speaker': speaker, **data}
        self.event_hash = digest((self.event_hash + canonical(item)).encode())
        item['chain_hash'] = self.event_hash
        self.event_log.append(item)
        return item

    def summary(self):
        return {
            'session_id': self.id,
            'state': self.state,
            'reason': self.ended_reason,
            'peer_id': self.mandate.peer,
            'caller_id': self.mandate.caller,
            'real_phone_call': False,
            'real_booking_verified': False,
            'payment_settled': False,
            'media': 'pcm16le_16khz_mono_20ms',
            'frames_by_role': dict(self.frames),
            'events': self.seq,
            'event_chain_sha256': self.event_hash,
            'evidence_scope': 'LAB_TRANSPORT_AND_AGENT_ASSERTIONS_ONLY',
        }


class PeerLab:
    def __init__(self, *, operator_token, agent_tokens, peer_tokens, clock=None, monotonic=None):
        require(len(operator_token) >= 24, 'WEAK_OPERATOR_TOKEN')
        self._operator_hash = digest(operator_token)
        self._tokens = {}
        for role, token_map in (('caller', agent_tokens), ('peer', peer_tokens)):
            for identity, token in token_map.items():
                require(isinstance(identity, str) and 1 <= len(identity) <= 64 and identity.isascii(), 'INVALID_IDENTITY')
                require(isinstance(token, str) and len(token) >= 24, 'WEAK_AGENT_TOKEN')
                key = digest(token)
                require(key != self._operator_hash and key not in self._tokens, 'DUPLICATE_TOKEN')
                self._tokens[key] = (role, identity)
        require(self._tokens, 'NO_AGENT_CREDENTIALS')
        self.mandates = {}
        self.sessions = {}
        self.idempotency = {}
        self.tickets = {}
        self.clock = clock or time.time
        self.monotonic = monotonic or time.monotonic
        self.lock = asyncio.Lock()

    def principal(self, req):
        raw = req.headers.get('Authorization', '')
        if not raw.startswith('Bearer ') or len(raw) > 256:
            raise ApiError('UNAUTHORISED', 401)
        token_hash = digest(raw[7:])
        if hmac.compare_digest(token_hash, self._operator_hash):
            return 'operator', 'human-lab-operator'
        for key, principal in self._tokens.items():
            if hmac.compare_digest(token_hash, key):
                return principal
        raise ApiError('UNAUTHORISED', 401)

    def member(self, req, session, *, wanted=None):
        role, identity = self.principal(req)
        require(role != 'operator', 'OPERATOR_CANNOT_ACT_AS_AGENT')
        allowed = (role == 'caller' and identity == session.mandate.caller) or (role == 'peer' and identity == session.mandate.peer)
        if not allowed or (wanted and wanted != role):
            raise ApiError('SESSION_NOT_FOUND', 404)
        return role, identity

    async def end(self, session, reason, *, departed=None):
        async with self.lock:
            if session.state == 'ended':
                return
            session.state = 'ended'
            session.ended_reason = reason
            session.finished_at = self.clock()
            session.emit('session.ended', reason=reason)
            # A departing socket must not block notifying the surviving participant.
            sockets = [ws for ws in session.connected.values() if ws is not departed]
        async def notify(ws):
            try:
                await asyncio.wait_for(ws.send_json({'type': 'session.ended', 'reason': reason}), timeout=.5)
            except Exception:
                pass
        await asyncio.gather(*(notify(ws) for ws in sockets))
        await asyncio.gather(*(asyncio.wait_for(
            ws.close(code=1000, message=b'session ended'), timeout=.75)
            for ws in sockets), return_exceptions=True)
        if session.deadline_task and session.deadline_task != asyncio.current_task():
            session.deadline_task.cancel()
        if session.join_task and session.join_task != asyncio.current_task():
            session.join_task.cancel()

    async def wait_for_peer(self, session):
        try:
            await asyncio.sleep(15)
            if session.state == 'awaiting_peers':
                await self.end(session, 'PEER_JOIN_TIMEOUT')
        except asyncio.CancelledError:
            pass

    async def expiry(self, session):
        try:
            await asyncio.sleep(session.mandate.max_seconds)
            await self.end(session, 'HARD_DEADLINE')
        except asyncio.CancelledError:
            pass


def make_app(*, operator_token, agent_tokens, peer_tokens, clock=None, monotonic=None):
    lab = PeerLab(operator_token=operator_token, agent_tokens=agent_tokens,
                  peer_tokens=peer_tokens, clock=clock, monotonic=monotonic)
    app = web.Application(client_max_size=MAX_BODY)
    app[ROLE_KEY] = lab

    @web.middleware
    async def error_handler(req, handler):
        try:
            result = await handler(req)
            result.headers['Cache-Control'] = 'no-store'
            result.headers['X-Content-Type-Options'] = 'nosniff'
            return result
        except ApiError as exc:
            return web.json_response({'error': exc.code}, status=exc.status,
                                     headers={'Cache-Control': 'no-store'})
    app.middlewares.append(error_handler)

    async def body(req, fields):
        try:
            raw = await req.read()
            require(len(raw) <= MAX_BODY, 'BODY_TOO_LARGE')
            value = json.loads(raw)
            require(isinstance(value, dict) and set(value) == set(fields), 'INVALID_FIELDS')
            return value
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError('INVALID_JSON')

    def session_for(req):
        session = lab.sessions.get(req.match_info['sid'])
        if not session:
            raise ApiError('SESSION_NOT_FOUND', 404)
        return session

    async def capabilities(req):
        return web.json_response({
            'name': 'AI Dial-Tone Peer Lab', 'protocol': 'aidt.peer.v1',
            'environment': 'loopback_development',
            'real_pstn': False, 'booking_provider': False, 'payment': False,
            'websocket_audio': {'codec': 'pcm16le', 'sample_rate_hz': 16000,
                                'channels': 1, 'frame_bytes': FRAME_BYTES,
                                'magic': 'DT01', 'frame_duration_ms': 20},
            'roles': ['operator', 'caller', 'peer'],
            'features': ['operator_issued_mandates', 'mutual_agent_admission',
                         'real_duplex_media_transport', 'text_turns', 'dtmf_events',
                         'hard_deadlines', 'disconnect_cleanup', 'attributed_event_chain']})

    async def mandate(req):
        require(lab.principal(req)[0] == 'operator', 'OPERATOR_ONLY')
        v = await body(req, ['caller_id', 'peer_id', 'task', 'max_seconds'])
        require(v['caller_id'] in [identity for role, identity in lab._tokens.values() if role == 'caller'], 'UNKNOWN_CALLER')
        require(v['peer_id'] in [identity for role, identity in lab._tokens.values() if role == 'peer'], 'UNKNOWN_PEER')
        require(safe_text(v['task'], 4, 500), 'INVALID_TASK')
        require(type(v['max_seconds']) is int and 1 <= v['max_seconds'] <= 120, 'INVALID_DEADLINE')
        m = Mandate(secrets.token_urlsafe(24), v['caller_id'], v['peer_id'],
                    v['task'], lab.clock() + 300, v['max_seconds'])
        async with lab.lock:
            if len(lab.mandates) >= MAX_MANDATES:
                raise ApiError('MANDATE_CAPACITY_EXCEEDED', 429)
            lab.mandates[m.id] = m
        return web.json_response({'mandate_id': m.id, 'expires_at': m.expires_at,
                                  'max_seconds': m.max_seconds, 'caller_id': m.caller,
                                  'peer_id': m.peer, 'authorisation': 'operator_issued_lab_mandate',
                                  'real_world_actions_authorised': False}, status=201)

    async def revoke(req):
        require(lab.principal(req)[0] == 'operator', 'OPERATOR_ONLY')
        mandate_id = req.match_info['mid']
        async with lab.lock:
            m = lab.mandates.get(mandate_id)
            require(m is not None, 'MANDATE_NOT_FOUND')
            m.revoked = True
            target = lab.sessions.get(m.used_by) if m.used_by else None
        if target:
            await asyncio.shield(lab.end(target, 'HUMAN_CANCELLED'))
        return web.json_response({'mandate_id': mandate_id, 'revoked': True,
                                  'session_terminated': bool(target)})

    async def operator_stop(req):
        require(lab.principal(req)[0] == 'operator', 'OPERATOR_ONLY')
        s = session_for(req)
        await asyncio.shield(lab.end(s, 'HUMAN_STOPPED'))
        return web.json_response({'session': s.summary()})

    async def create(req):
        role, identity = lab.principal(req)
        require(role == 'caller', 'CALLER_ONLY')
        v = await body(req, ['mandate_id'])
        require(isinstance(v['mandate_id'], str) and 1 <= len(v['mandate_id']) <= 128, 'INVALID_MANDATE_ID')
        idem = req.headers.get('Idempotency-Key', '')
        require(isinstance(idem, str) and 12 <= len(idem) <= 128 and idem.isascii() and idem.isprintable(), 'IDEMPOTENCY_KEY_REQUIRED')
        async with lab.lock:
            prev = lab.idempotency.get((identity, idem))
            if prev:
                require(prev[0] == v['mandate_id'], 'IDEMPOTENCY_CONFLICT', )
                s = lab.sessions[prev[1]]
                return web.json_response({'session': s.summary(), 'new': False}, status=200)
            m = lab.mandates.get(v['mandate_id'])
            require(m is not None and m.caller == identity, 'MANDATE_NOT_FOUND')
            require(m.expires_at > lab.clock(), 'MANDATE_EXPIRED')
            require(not m.revoked, 'MANDATE_REVOKED')
            require(not m.used_by, 'MANDATE_ALREADY_USED')
            if len(lab.sessions) >= MAX_SESSIONS:
                raise ApiError('SESSION_CAPACITY_EXCEEDED', 429)
            s = Session(id=secrets.token_urlsafe(20), mandate=m, created_at=lab.clock())
            s.emit('session.created', caller=m.caller, peer=m.peer, source='operator_mandate')
            s.join_task = asyncio.create_task(lab.wait_for_peer(s))
            lab.sessions[s.id] = s
            lab.idempotency[(identity, idem)] = (m.id, s.id)
            m.used_by = s.id
        return web.json_response({'session': s.summary(), 'new': True}, status=201)

    async def inbox(req):
        role, identity = lab.principal(req)
        require(role == 'peer', 'PEER_ONLY')
        result = [{'session_id': s.id, 'task': s.mandate.task, 'caller_id': s.mandate.caller,
                   'state': s.state} for s in lab.sessions.values()
                  if s.mandate.peer == identity and s.state == 'awaiting_peers']
        return web.json_response({'sessions': result})

    async def get_session(req):
        s = session_for(req)
        lab.member(req, s)
        return web.json_response({'session': s.summary(), 'events': s.event_log})

    async def ticket(req):
        s = session_for(req)
        role, identity = lab.member(req, s)
        require(s.state != 'ended', 'SESSION_ENDED', )
        require(role not in s.connected, 'ROLE_ALREADY_CONNECTED')
        t = secrets.token_urlsafe(32)
        async with lab.lock:
            # Expired one-time admissions need not stay in memory.
            lab.tickets = {key: info for key, info in lab.tickets.items() if info[2] > lab.monotonic()}
            if len(lab.tickets) >= MAX_TICKETS:
                raise ApiError('TICKET_CAPACITY_EXCEEDED', 429)
            lab.tickets[digest(t)] = (s.id, role, lab.monotonic() + 20)
        return web.json_response({'ticket': t, 'expires_in_seconds': 20,
                                  'websocket_path': f'/v1/sessions/{s.id}/connect',
                                  'admission': 'single_use_first_message'})

    async def socket(req):
        s = session_for(req)
        ws = web.WebSocketResponse(max_msg_size=2048, heartbeat=20)
        await ws.prepare(req)
        role = None
        try:
            first = await ws.receive(timeout=4)
            if first.type != WSMsgType.TEXT:
                await ws.close(code=1008, message=b'ADMISSION_REQUIRED')
                return ws
            try:
                msg = json.loads(first.data)
                require(set(msg) == {'type', 'ticket'} and msg['type'] == 'admit', 'ADMISSION_REQUIRED')
                thash = digest(msg['ticket'])
                async with lab.lock:
                    entry = lab.tickets.pop(thash, None)
                    require(entry and entry[0] == s.id and entry[2] > lab.monotonic(), 'INVALID_OR_REPLAYED_TICKET')
                    role = entry[1]
                    require(role not in s.connected and s.state == 'awaiting_peers', 'SESSION_NOT_JOINABLE')
                    s.connected[role] = ws
                    s.emit('peer.joined', speaker=role)
                    now_ready = len(s.connected) == 2
                    if now_ready:
                        if s.join_task:
                            s.join_task.cancel()
                        s.state = 'running'
                        s.emit('session.connected', peer=s.mandate.peer, caller=s.mandate.caller)
                        s.deadline_task = asyncio.create_task(lab.expiry(s))
            except (ApiError, ValueError, TypeError, KeyError):
                await ws.close(code=1008, message=b'ADMISSION_REJECTED')
                return ws
            await ws.send_json({'type': 'admitted', 'role': role, 'session_id': s.id,
                                'state': s.state, 'real_pstn': False})
            if now_ready:
                for peer_ws in list(s.connected.values()):
                    await peer_ws.send_json({'type': 'session.connected', 'session_id': s.id})
            async for frame in ws:
                if s.state != 'running':
                    await ws.send_json({'type':'error','code':'SESSION_NOT_RUNNING'})
                    continue
                other = s.connected.get('peer' if role == 'caller' else 'caller')
                if not other or other.closed:
                    await asyncio.shield(lab.end(s, 'TRANSPORT_DISCONNECTED'))
                    break
                if frame.type == WSMsgType.TEXT:
                    try:
                        v = json.loads(frame.data)
                        require(isinstance(v, dict) and isinstance(v.get('type'), str), 'INVALID_EVENT')
                        typ = v['type']
                        if typ == 'say':
                            require(set(v)=={'type','text'} and
                                    safe_text(v['text'], 1, MAX_UTTERANCE, allow_newlines=True), 'INVALID_UTTERANCE')
                            item = s.emit('agent.utterance', speaker=role, text=v['text'],
                                          claim='MODEL_ASSERTION_NOT_ASR_VERIFIED')
                            await other.send_json({'type':'say','speaker':role,'text':v['text'],'seq':item['seq']})
                        elif typ == 'dtmf':
                            require(set(v)=={'type','digits'} and isinstance(v['digits'],str) and
                                    1 <= len(v['digits']) <= 16 and all(c in '0123456789*#' for c in v['digits']), 'INVALID_DTMF')
                            item=s.emit('agent.dtmf', speaker=role, digits=v['digits'])
                            await other.send_json({'type':'dtmf','speaker':role,'digits':v['digits'],'seq':item['seq']})
                        elif typ == 'audio.end':
                            require(set(v)=={'type'}, 'INVALID_EVENT')
                            item=s.emit('media.utterance_ended', speaker=role,
                                        last_pcm_sequence=s.last_pcm_seq[role])
                            await other.send_json({'type':'audio.end','speaker':role,'seq':item['seq']})
                        elif typ == 'audio.interrupt':
                            require(set(v)=={'type'}, 'INVALID_EVENT')
                            item=s.emit('media.interruption_requested', speaker=role)
                            await other.send_json({'type':'audio.interrupt','speaker':role,'seq':item['seq']})
                        elif typ == 'hangup':
                            require(set(v)=={'type'}, 'INVALID_EVENT')
                            await asyncio.shield(lab.end(s, f'{role.upper()}_HANGUP'))
                            break
                        elif typ == 'ping':
                            require(set(v)=={'type'}, 'INVALID_EVENT')
                            await ws.send_json({'type':'pong'})
                        else:
                            raise ApiError('UNSUPPORTED_EVENT')
                    except (ValueError, TypeError, ApiError) as exc:
                        code = exc.code if isinstance(exc, ApiError) else 'INVALID_JSON'
                        await ws.send_json({'type':'error','code':code})
                elif frame.type == WSMsgType.BINARY:
                    packet=frame.data
                    if len(packet)!=FRAME_BYTES:
                        await ws.send_json({'type':'error','code':'INVALID_PCM_FRAME'})
                        continue
                    magic, seq, stamp=FRAME_HEADER.unpack_from(packet)
                    if magic != b'DT01' or seq <= s.last_pcm_seq[role]:
                        await ws.send_json({'type':'error','code':'REPLAYED_OR_INVALID_PCM'})
                        continue
                    now = lab.monotonic()
                    s.rate[role] = [x for x in s.rate[role] if now - x < 1]
                    if len(s.rate[role]) >= 60:
                        await ws.send_json({'type':'error','code':'MEDIA_RATE_LIMIT'})
                        continue
                    s.rate[role].append(now)
                    s.last_pcm_seq[role] = seq
                    s.frames[role] += 1
                    if s.frames[role] % 50 == 1:
                        s.emit('media.frame_batch', speaker=role, frames_so_far=s.frames[role],
                               media='pcm16le', content_recorded=False)
                    await other.send_bytes(packet)
                elif frame.type == WSMsgType.ERROR:
                    break
        except (TimeoutError, asyncio.TimeoutError):
            await ws.close(code=1008, message=b'ADMISSION_TIMEOUT')
        finally:
            if role and s.connected.get(role) is ws:
                if s.state != 'ended':
                    await asyncio.shield(lab.end(s, 'TRANSPORT_DISCONNECTED', departed=ws))
                s.connected.pop(role, None)
        return ws

    async def shutdown(app):
        for s in list(lab.sessions.values()):
            if s.state != 'ended':
                await lab.end(s, 'LAB_SHUTDOWN')

    app.router.add_get('/v1/capabilities', capabilities)
    app.router.add_post('/v1/mandates', mandate)
    app.router.add_post('/v1/mandates/{mid}/revoke', revoke)
    app.router.add_post('/v1/sessions', create)
    app.router.add_get('/v1/peers/inbox', inbox)
    app.router.add_get('/v1/sessions/{sid}', get_session)
    app.router.add_post('/v1/sessions/{sid}/stop', operator_stop)
    app.router.add_post('/v1/sessions/{sid}/tickets', ticket)
    app.router.add_get('/v1/sessions/{sid}/connect', socket)
    app.on_shutdown.append(shutdown)
    return app


def cli():
    import argparse
    parser = argparse.ArgumentParser(description='Local-only AI Dial-Tone agent peer development server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='127.0.0.1')
    opt = parser.parse_args()
    if opt.host not in ('127.0.0.1','::1','localhost'):
        parser.error('NON_LOOPBACK_BINDING_FORBIDDEN: development service has no production security hardening')
    keys = {
        'operator': secrets.token_urlsafe(32),
        'caller': secrets.token_urlsafe(32),
        'peer': secrets.token_urlsafe(32),
    }
    print('LOCAL LAB TOKENS, KEEP PRIVATE (restart invalidates them):',flush=True)
    for name, value in keys.items():print(f'  {name.upper()}={value}',flush=True)
    print('Use only fictional data. No actual telephone calls or restaurant bookings.',flush=True)
    web.run_app(make_app(operator_token=keys['operator'],
                         agent_tokens={'demo-caller':keys['caller']},
                         peer_tokens={'demo-restaurant':keys['peer']}), host=opt.host,port=opt.port,access_log=None)


if __name__=='__main__':
    cli()
