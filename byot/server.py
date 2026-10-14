"""AI Dial-Tone Bring-Your-Own-Telecoms (BYOT) experimental ARI connector.

No real calling by default. Intentionally single-call, loopback HTTP, fixed
PJSIP trunk, human-bound E.164 mandate, verified agent before origination.
Not suitable for production deployment without a separate PBX-side watchdog,
credential management, TLS-protected ARI and real Asterisk interoperability tests.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import struct
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from aiohttp import web, WSMsgType, ClientError

from .ari import Ari, AriFailure
from .rtp import bind_rtp, AGENT_HEADER, PCM_BYTES

MAX_BODY = 2048
TRUNK_RE = re.compile(r'[A-Za-z0-9_\-]{1,48}\Z')
APP_RE = re.compile(r'[A-Za-z][A-Za-z0-9_\-]{0,48}\Z')
GEOGRAPHIC_RE = re.compile(r'\+44[12][0-9]{9}\Z')
CALL_ID_RE = re.compile(r'[a-f0-9]{24}\Z')


class ApiError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status
        super().__init__(code)


def require(cond, code, status=400):
    if not cond:
        raise ApiError(code, status)


def bearer_hash(token):
    return hashlib.sha256(token.encode('utf-8')).digest()


def token_value(req):
    v = req.headers.get('Authorization', '')
    if not v.startswith('Bearer ') or len(v) > 256:
        return ''
    return v[7:]


@dataclass(frozen=True)
class Settings:
    ari_url: str
    ari_user: str
    ari_password: str
    app: str
    trunk: str
    operator_token: str
    agent_token: str
    media_bind: str = '127.0.0.1'
    media_advertise: str = '127.0.0.1'
    asterisk_media_ip: str = '127.0.0.1'
    control_host: str = '127.0.0.1'
    allow_private_rtp: bool = False
    allow_origination: bool = False
    require_qualified_endpoint: bool = True
    ring_seconds: int = 25
    max_seconds: int = 90

    def __post_init__(self):
        p = urlsplit(self.ari_url)
        require(p.scheme in ('http', 'https') and p.hostname and not (p.username or p.password or
                p.query or p.fragment or p.path not in ('','/')), 'INVALID_ARI_URL')
        ip = None
        try: ip = ipaddress.ip_address(p.hostname)
        except ValueError: pass
        if p.scheme == 'http':
            require(ip is not None and ip.is_loopback, 'REMOTE_ARI_REQUIRES_HTTPS')
        require(bool(self.ari_user) and bool(self.ari_password), 'ARI_CREDENTIALS_REQUIRED')
        require(bool(APP_RE.fullmatch(self.app)), 'INVALID_STASIS_APP')
        require(bool(TRUNK_RE.fullmatch(self.trunk)), 'INVALID_PJSIP_TRUNK')
        require(len(self.operator_token) >= 32 and len(self.agent_token) >= 32 and
                self.operator_token != self.agent_token, 'STRONG_DISTINCT_TOKENS_REQUIRED')
        require(self.control_host in ('127.0.0.1','::1'), 'CONTROL_MUST_BIND_LOOPBACK')
        ips = [ipaddress.ip_address(n) for n in (self.media_bind,self.media_advertise,self.asterisk_media_ip)]
        require(all(x.version == 4 for x in ips), 'IPV4_MEDIA_ONLY')
        require(all(x.is_loopback for x in ips) or
                (self.allow_private_rtp and all(x.is_private for x in ips)), 'RTP_MUST_BE_ISOLATED')
        require(type(self.ring_seconds) is int and 5 <= self.ring_seconds <= 60, 'INVALID_RING_TIMEOUT')
        require(type(self.max_seconds) is int and 10 <= self.max_seconds <= 120, 'INVALID_MAX_DURATION')

    @classmethod
    def env(cls):
        def get(name):
            value = os.environ.get('AIDT_' + name, '')
            require(value, 'MISSING_' + name)
            return value
        return cls(ari_url=get('ARI_URL'), ari_user=get('ARI_USER'),
                   ari_password=get('ARI_PASSWORD'), app=os.getenv('AIDT_ARI_APP','ai-dial-tone'),
                   trunk=get('PJSIP_TRUNK'), operator_token=get('OPERATOR_TOKEN'),
                   agent_token=get('AGENT_TOKEN'),
                   media_bind=os.getenv('AIDT_MEDIA_BIND','127.0.0.1'),
                   media_advertise=os.getenv('AIDT_MEDIA_ADVERTISE','127.0.0.1'),
                   asterisk_media_ip=os.getenv('AIDT_ASTERISK_MEDIA_IP','127.0.0.1'),
                   allow_private_rtp=os.getenv('AIDT_ALLOW_PRIVATE_RTP','') == 'YES',
                   allow_origination=os.getenv('AIDT_ENABLE_LIVE_ORIGINATION','') == 'YES',
                   require_qualified_endpoint=os.getenv('AIDT_ALLOW_UNQUALIFIED_ENDPOINT','') != 'YES')


@dataclass
class Mandate:
    id: str
    number: str
    max_seconds: int
    created: float
    expires: float
    claimed: bool = False
    revoked: bool = False


@dataclass
class Call:
    id: str
    mandate: Mandate
    state: str = 'waiting_for_agent'
    created: float = field(default_factory=time.monotonic)
    ticket: str | None = None
    ticket_expires: float = 0
    ws: object = None
    outbound_id: str = ''
    external_id: str = ''
    bridge_id: str = ''
    rtp: object = None
    rtp_port: int = 0
    arrived: asyncio.Event = field(default_factory=asyncio.Event)
    ext_arrived: asyncio.Event = field(default_factory=asyncio.Event)
    flow_task: asyncio.Task | None = None
    deadline_task: asyncio.Task | None = None
    sender_task: asyncio.Task | None = None
    agent_sender_task: asyncio.Task | None = None
    join_task: asyncio.Task | None = None
    agent_out: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=25))
    ending: bool = False
    finished: asyncio.Event = field(default_factory=asyncio.Event)
    ended_reason: str = ''
    cleanup_confirmed: bool = False
    last_pcm_seq: int = -1
    ws_rate: list = field(default_factory=list)
    dtmf_rate: list = field(default_factory=list)
    media_ready: bool = False
    probe_task: asyncio.Task | None = None
    endpoint_state: str = 'not_checked'
    to_asterisk: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=25))
    agent_seq: int = 0
    recv_count: int = 0
    sent_count: int = 0

    def status(self):
        return {'call_id':self.id,'state':self.state,'reason':self.ended_reason or None,
                'destination':self.mandate.number,'media':'DT01 PCM16LE/16000/20ms',
                'frames_from_asterisk':self.recv_count,'frames_to_asterisk':self.sent_count,
                'ari_pjsip_endpoint_state':self.endpoint_state,
                'first_rtp_received':self.media_ready,
                'pbx_channel_absence_observed':self.cleanup_confirmed,
                'carrier_release_verified':False,'reservation_verified':False}


class Manager:
    def __init__(self, settings: Settings, *, ari=None):
        self.settings = settings
        self._operator = bearer_hash(settings.operator_token)
        self._agent = bearer_hash(settings.agent_token)
        self.mandates = {}
        self.calls = {}
        self.lock = asyncio.Lock()
        self.ari = ari or Ari(url=settings.ari_url, user=settings.ari_user,
                              password=settings.ari_password, application=settings.app,
                              event_handler=self.on_ari_event, disconnect_handler=self.on_ari_disconnect)

    def auth(self, req, role):
        candidate = bearer_hash(token_value(req))
        expected = self._operator if role == 'operator' else self._agent
        require(hmac.compare_digest(candidate, expected), 'UNAUTHORISED', 401)

    async def notify(self, call, event):
        if call.ws and not call.ws.closed:
            try: await call.ws.send_json(event)
            except (OSError, ConnectionError, RuntimeError): pass

    async def on_ari_event(self, event):
        ch = event.get('channel', {})
        cid = ch.get('id') if isinstance(ch, dict) else None
        if not cid: return
        for call in list(self.calls.values()):
            if call.ending: continue
            if event.get('type') == 'StasisStart':
                if cid == call.outbound_id:
                    call.arrived.set()
                elif cid == call.external_id:
                    call.ext_arrived.set()
            elif event.get('type') in ('StasisEnd','ChannelDestroyed'):
                if cid in (call.outbound_id, call.external_id) and cid:
                    asyncio.create_task(self.stop(call, 'PBX_CHANNEL_ENDED'))

    async def on_ari_disconnect(self):
        for call in list(self.calls.values()):
            if call.state not in ('waiting_for_agent','ended') and not call.ending:
                asyncio.create_task(self.stop(call, 'ARI_DISCONNECTED'))

    def on_rtp(self, call, pcm):
        if call.ending or call.state not in ('bridged','answered') or not call.ws or call.ws.closed:
            return
        if call.agent_out.full():
            if call.rtp: call.rtp.counters.dropped += 1
            return
        if not call.media_ready:
            call.media_ready=True
            asyncio.create_task(self.notify(call, {'type':'media.ready','call_id':call.id,
                                                   'evidence':'validated_first_rtp_packet',
                                                   'bidirectional_audio_verified':False}))
        call.recv_count += 1
        call.agent_seq += 1
        packet = AGENT_HEADER.pack(b'DT01',call.agent_seq,int(time.monotonic()*1000)) + pcm
        call.agent_out.put_nowait(packet)

    async def _agent_sender(self, call):
        while not call.ending:
            packet = await call.agent_out.get()
            if call.ending or not call.ws or call.ws.closed: return
            try:
                await asyncio.wait_for(call.ws.send_bytes(packet),timeout=2)
            except (OSError, ConnectionError, RuntimeError, asyncio.TimeoutError):
                asyncio.create_task(self.stop(call,'AGENT_MEDIA_BACKPRESSURE'))
                return

    async def _agent_join_timeout(self, call):
        await asyncio.sleep(20)
        if call.state in ('waiting_for_agent','admitted') and not call.flow_task:
            await self.stop(call,'AGENT_JOIN_TIMEOUT')

    async def _rtp_sender(self, call):
        """Independent 20ms RTP pacing. A bursty agent cannot flood Asterisk."""
        next_at = time.monotonic()
        while not call.ending:
            pcm = await call.to_asterisk.get()
            if not call.rtp or call.ending: return
            next_at = max(next_at + .02, time.monotonic())
            if call.rtp.send_pcm(pcm): call.sent_count += 1
            await asyncio.sleep(max(0,next_at-time.monotonic()))

    async def _media_probe(self, call):
        await asyncio.sleep(8)
        if not call.media_ready and not call.ending:
            await self.stop(call,'MEDIA_PROBE_TIMEOUT')

    async def _deadline(self, call):
        await asyncio.sleep(call.mandate.max_seconds)
        await self.stop(call, 'HARD_DEADLINE')

    async def begin(self, call):
        if call.ending or call.state != 'admitted': return
        if not self.settings.allow_origination:
            await self.stop(call,'LIVE_ORIGINATION_DISABLED')
            return
        if not self.ari.connected:
            await self.stop(call,'ARI_NOT_CONNECTED')
            return
        call.state = 'dialling'
        call.deadline_task = asyncio.create_task(self._deadline(call))
        try:
            loop = asyncio.get_running_loop()
            endpoint = await self.ari.request('GET', f'/endpoints/PJSIP/{self.settings.trunk}')
            state = endpoint.get('state') if isinstance(endpoint, dict) else None
            call.endpoint_state = state if isinstance(state,str) and len(state) < 48 else 'unknown'
            if self.settings.require_qualified_endpoint and state != 'online':
                await self.stop(call, 'PJSIP_ENDPOINT_NOT_QUALIFIED')
                return
            call.rtp, call.rtp_port = await bind_rtp(loop,host=self.settings.media_bind,
                                                    receiver=lambda pcm:self.on_rtp(call,pcm))
            call.outbound_id = 'aidt-' + secrets.token_hex(12)
            # Asterisk originates directly against the PRECONFIGURED PJSIP endpoint.
            # The agent cannot choose a trunk, dialplan context, or channel params.
            await self.ari.request('POST','/channels', params={
                'endpoint':f'PJSIP/{call.mandate.number}@{self.settings.trunk}',
                'app':self.settings.app, 'appArgs':'aidt-outbound',
                'channelId':call.outbound_id, 'timeout':self.settings.ring_seconds,
            })
            await asyncio.wait_for(call.arrived.wait(),self.settings.ring_seconds + 3)
            if call.ending: return
            call.state = 'answered'
            await self.notify(call, {'type':'call.answered','call_id':call.id})
            call.bridge_id = 'aidt-' + secrets.token_hex(12)
            await self.ari.request('POST','/bridges/'+call.bridge_id,
                                   params={'type':'mixing','name':'AI Dial-Tone lab'})
            call.external_id = 'aidt-' + secrets.token_hex(12)
            await self.ari.request('POST','/channels/externalMedia',params={
                'channelId':call.external_id,'app':self.settings.app,
                'external_host':f'{self.settings.media_advertise}:{call.rtp_port}',
                'format':'slin16','encapsulation':'rtp','transport':'udp','direction':'both',
            })
            await asyncio.wait_for(call.ext_arrived.wait(),5)
            port = None
            for attempt in range(8):
                try:
                    observed = await self.ari.request('GET','/channels/'+call.external_id+'/variable',
                                                       params={'variable':'UNICASTRTP_LOCAL_PORT'})
                    port = int(observed['value'])
                    if 1 <= port <= 65535: break
                except (AriFailure, ClientError, OSError, ValueError, TypeError, KeyError):
                    port = None
                await asyncio.sleep(.12)
            if port is None or not 1 <= port <= 65535:
                raise ValueError('ASTERISK_MEDIA_PEER_UNAVAILABLE')
            call.rtp.set_remote(self.settings.asterisk_media_ip, port)
            await self.ari.request('POST','/bridges/'+call.bridge_id+'/addChannel',
                                   params={'channel':call.outbound_id+','+call.external_id})
            if call.ending: return
            call.state = 'bridged'
            call.sender_task = asyncio.create_task(self._rtp_sender(call))
            call.probe_task = asyncio.create_task(self._media_probe(call))
            await self.notify(call, {'type':'media.bridged','call_id':call.id,
                                      'codec':'slin16','rtp_source_tuple_locked':True, 'rtp_integrity_verified':False,
                                      'real_sip_readiness_verified':False})
        except (AriFailure, ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError, OSError) as exc:
            if not call.ending:
                # Never send ARI response bodies or credential-containing exceptions.
                await self.stop(call, 'CALL_SETUP_FAILED')

    async def stop(self, call, reason):
        if call.ending:
            try: await asyncio.wait_for(call.finished.wait(),timeout=5)
            except asyncio.TimeoutError: pass
            return
        call.ending = True
        call.state = 'ending'
        call.ended_reason = reason
        # No await before setting ending: concurrent stop paths cannot start twice.
        for task in (call.flow_task,call.sender_task,call.agent_sender_task,call.join_task,call.probe_task,call.deadline_task):
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
        if call.rtp: call.rtp.close()
        confirmations = []
        for path in ([f'/channels/{call.external_id}' if call.external_id else None,
                      f'/channels/{call.outbound_id}' if call.outbound_id else None]):
            if not path: continue
            try: await self.ari.request('DELETE',path,missing_ok=True)
            except (AriFailure, ClientError, OSError, asyncio.TimeoutError): pass
            confirmed=False
            for _ in range(3):
                try:
                    observed = await self.ari.request('GET',path,missing_ok=True)
                    confirmed = observed is None
                except (AriFailure, ClientError, OSError, asyncio.TimeoutError):
                    confirmed=False
                if confirmed: break
                await asyncio.sleep(.1)
            confirmations.append(confirmed)
        if call.bridge_id:
            try: await self.ari.request('DELETE',f'/bridges/{call.bridge_id}',missing_ok=True)
            except (AriFailure, ClientError, OSError, asyncio.TimeoutError): pass
        call.cleanup_confirmed = bool(confirmations) and all(confirmations)
        call.state = 'ended'
        await self.notify(call,{'type':'call.ended','call_id':call.id,'reason':reason,
                                'pbx_channel_absence_observed':call.cleanup_confirmed,
                                'carrier_release_verified':False})
        call.finished.set()
        if call.ws and not call.ws.closed:
            await call.ws.close()

    async def shutdown(self):
        for call in list(self.calls.values()):
            if call.state != 'ended': await self.stop(call,'SERVER_SHUTDOWN')
        await self.ari.close()


KEY = web.AppKey('byot', Manager)


async def json_input(req):
    require(req.content_length is None or req.content_length <= MAX_BODY,'BODY_TOO_LARGE',413)
    raw = await req.content.read(MAX_BODY + 1)
    require(len(raw) <= MAX_BODY,'BODY_TOO_LARGE',413)
    try: data = json.loads(raw)
    except (UnicodeDecodeError, ValueError): raise ApiError('INVALID_JSON')
    require(isinstance(data,dict),'INVALID_JSON_OBJECT')
    return data


@web.middleware
async def error_middleware(req, handler):
    try: return await handler(req)
    except ApiError as exc:
        return web.json_response({'error':exc.code},status=exc.status)


def get_call(manager, req):
    cid = req.match_info['call_id']
    require(bool(CALL_ID_RE.fullmatch(cid)),'CALL_NOT_FOUND',404)
    call = manager.calls.get(cid)
    require(call is not None,'CALL_NOT_FOUND',404)
    return call


async def health(req):
    manager=req.app[KEY]
    return web.json_response({'version':'0.0.1','component':'byot-asterisk-experimental',
                              'real_call_enabled':manager.settings.allow_origination,
                              'ari_event_stream_connected':manager.ari.connected,
                              'carrier_readiness_verified':False})


async def endpoint_readiness(req):
    """Non-dialling PBX observation. Neither an origination permit nor SIP route proof.

    The fixed PJSIP endpoint is read from operator-owned settings. The agent
    cannot invoke this endpoint or supply a trunk/route, and this handler does
    not create mandates, originate, make audio channels or mutate ARI state.
    """
    m=req.app[KEY]
    m.auth(req, 'operator')
    result={
        'version':'0.0.1',
        'kind':'BYOT_READ_ONLY_ENDPOINT_OBSERVATION',
        'origin':'asterisk_ari',
        'pjsip_endpoint':m.settings.trunk,
        'ari_event_stream_connected':bool(m.ari.connected),
        'endpoint_state':'not_observed',
        'endpoint_observed':False,
        'observed_at_utc':None,
        'preflight_state':'BLOCKED',
        'endpoint_online_observed':False,
        'network_call_authorised':False,
        'sip_options_2xx_verified':False,
        'tls_certificate_verified':False,
        'media_encryption_verified':False,
        'pbx_route_policy_verified':False,
        'isolated_audio_test_verified':False,
        'not_proven':['SIP_OPTIONS_RESULT','TLS_CERTIFICATE','ENCRYPTED_MEDIA',
                      'DIALPLAN_ROUTE','CARRIER_PSTN_REACHABILITY','INVITE_SUCCESS',
                      'REMOTE_ANSWER','BIDIRECTIONAL_AUDIO','TASK_OUTCOME'],
    }
    if not m.ari.connected:
        result['reason']='ARI_NOT_CONNECTED'
        return web.json_response(result,status=503)
    try:
        value=await asyncio.wait_for(m.ari.request('GET',f'/endpoints/PJSIP/{m.settings.trunk}'),timeout=5)
        if not isinstance(value,dict):
            raise ValueError('invalid ARI endpoint result')
        state=value.get('state')
        if type(state) is not str or not re.fullmatch(r'[a-zA-Z_]{1,32}',state):
            raise ValueError('invalid ARI endpoint state')
    except (AriFailure, ClientError, ValueError, KeyError, OSError, asyncio.TimeoutError):
        result['reason']='ENDPOINT_OBSERVATION_UNAVAILABLE'
        return web.json_response(result,status=503)
    from datetime import datetime, timezone
    result['endpoint_observed']=True
    result['endpoint_state']=state.lower()
    result['observed_at_utc']=datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    result['endpoint_online_observed']=state.lower()=='online'
    result['preflight_state']='ENDPOINT_ONLINE_ROUTE_UNVERIFIED' if result['endpoint_online_observed'] else 'BLOCKED'
    result['reason']='ENDPOINT_ONLINE_SIP_AND_ROUTE_UNVERIFIED' if result['endpoint_online_observed'] else 'ENDPOINT_NOT_ONLINE'
    return web.json_response(result,status=200)


async def create_mandate(req):
    m=req.app[KEY]; m.auth(req,'operator')
    data=await json_input(req)
    require(set(data) == {'destination','max_seconds'},'INVALID_MANDATE_FIELDS')
    dest=data['destination']; limit=data['max_seconds']
    require(isinstance(dest,str) and bool(GEOGRAPHIC_RE.fullmatch(dest)),'DESTINATION_NOT_ALLOWED')
    require(type(limit) is int and 10 <= limit <= m.settings.max_seconds,'INVALID_DURATION')
    async with m.lock:
        require(len(m.mandates) < 100,'MANDATE_CAPACITY',429)
        mandate=Mandate(secrets.token_hex(12),dest,limit,time.monotonic(),time.monotonic()+120)
        m.mandates[mandate.id]=mandate
    return web.json_response({'mandate_id':mandate.id,'destination':dest,'max_seconds':limit,
                              'expires_in_seconds':120,'single_use':True,'human_approved':False,
                              'approval_provenance':'LOCAL_OPERATOR_BEARER_ONLY'},status=201)


async def create_call(req):
    m=req.app[KEY];m.auth(req,'agent')
    data=await json_input(req)
    require(set(data)=={'mandate_id'},'INVALID_CALL_FIELDS')
    mandate_id=data['mandate_id']
    require(isinstance(mandate_id,str) and bool(CALL_ID_RE.fullmatch(mandate_id)),'INVALID_MANDATE')
    async with m.lock:
        mandate=m.mandates.get(mandate_id)
        require(mandate is not None and not mandate.revoked and not mandate.claimed and
                time.monotonic() < mandate.expires,'MANDATE_UNAVAILABLE',403)
        require(not any(c.state != 'ended' for c in m.calls.values()),'CALL_CAPACITY',409)
        require(len(m.calls)<100,'CALL_HISTORY_CAPACITY',429)
        mandate.claimed=True
        call=Call(secrets.token_hex(12),mandate)
        m.calls[call.id]=call
        call.join_task=asyncio.create_task(m._agent_join_timeout(call))
    return web.json_response({'call_id':call.id,'state':'waiting_for_agent',
                              'destination':mandate.number,'can_originate':m.settings.allow_origination},status=201)


async def ticket(req):
    m=req.app[KEY];m.auth(req,'agent');call=get_call(m,req)
    require(call.state=='waiting_for_agent' and not call.ending,'CALL_NOT_JOINABLE',409)
    call.ticket=secrets.token_urlsafe(32)
    call.ticket_expires=time.monotonic()+20
    return web.json_response({'ticket':call.ticket,'expires_in_seconds':20})


async def call_info(req):
    m=req.app[KEY]
    value=token_value(req);dig=bearer_hash(value)
    require(hmac.compare_digest(dig,m._agent) or hmac.compare_digest(dig,m._operator),'UNAUTHORISED',401)
    return web.json_response(get_call(m,req).status())


async def stop_call(req):
    m=req.app[KEY];m.auth(req,'operator');call=get_call(m,req)
    # Shield cleanup so disconnecting the HTTP operator cannot cancel a PBX hangup.
    task=asyncio.create_task(m.stop(call,'OPERATOR_STOPPED'))
    await asyncio.shield(task)
    return web.json_response(call.status())


async def revoke(req):
    m=req.app[KEY];m.auth(req,'operator')
    mid=req.match_info['mandate_id']
    mandate=m.mandates.get(mid)
    require(mandate is not None,'MANDATE_NOT_FOUND',404)
    mandate.revoked=True
    for call in list(m.calls.values()):
        if call.mandate is mandate and call.state != 'ended':
            await asyncio.shield(asyncio.create_task(m.stop(call,'OPERATOR_REVOKED')))
    return web.json_response({'revoked':True})


async def media(req):
    m=req.app[KEY];call=get_call(m,req)
    # Tickets belong in the first WebSocket message, never in URL parameters.
    ws=web.WebSocketResponse(max_msg_size=2048, heartbeat=10, autoclose=True)
    await ws.prepare(req)
    try:
        first=await asyncio.wait_for(ws.receive(),4)
        if first.type != WSMsgType.TEXT:
            await ws.close(code=1008);return ws
        try: entry=json.loads(first.data)
        except ValueError: entry={}
        t=entry.get('ticket') if isinstance(entry,dict) else None
        if (not isinstance(t,str) or not call.ticket or call.ending or
            call.state!='waiting_for_agent' or time.monotonic()>call.ticket_expires or
            not hmac.compare_digest(t,call.ticket)):
            await ws.send_json({'type':'error','code':'ADMISSION_DENIED'})
            await ws.close(code=1008);return ws
        call.ticket=None
        call.ws=ws
        call.state='admitted'
        call.agent_sender_task=asyncio.create_task(m._agent_sender(call))
        await ws.send_json({'type':'admitted','call_id':call.id,'real_call_enabled':m.settings.allow_origination})
        async for msg in ws:
            if msg.type==WSMsgType.TEXT:
                try: data=json.loads(msg.data)
                except ValueError: data={}
                typ=data.get('type') if isinstance(data,dict) else ''
                if typ=='start':
                    if call.state=='admitted' and not call.flow_task and not call.ending:
                        if call.join_task: call.join_task.cancel()
                        call.flow_task=asyncio.create_task(m.begin(call))
                    else: await ws.send_json({'type':'error','code':'ALREADY_STARTED'})
                elif typ=='hangup':
                    await asyncio.shield(asyncio.create_task(m.stop(call,'AGENT_HANGUP')))
                    break
                elif typ in ('audio.end','audio.interrupt','ping'):
                    if typ=='ping': await ws.send_json({'type':'pong'})
                    if typ=='audio.interrupt':
                        # Remove already queued speech: do not play stale TTS after a barge-in.
                        while not call.to_asterisk.empty():
                            try: call.to_asterisk.get_nowait()
                            except asyncio.QueueEmpty: break
                    # This is local media control, NOT SIP interruption semantics.
                elif typ=='dtmf':
                    digits=data.get('digits')
                    if not (call.state=='bridged' and isinstance(digits,str) and
                            re.fullmatch(r'[0-9*#ABCD]{1,8}',digits)):
                        await ws.send_json({'type':'error','code':'DTMF_NOT_ALLOWED'})
                        continue
                    now=time.monotonic()
                    call.dtmf_rate=[x for x in call.dtmf_rate if now-x<3]
                    if len(call.dtmf_rate)>4:
                        await ws.send_json({'type':'error','code':'DTMF_RATE_LIMIT'})
                        continue
                    call.dtmf_rate.append(now)
                    try:
                        await m.ari.request('POST',f'/channels/{call.outbound_id}/dtmf',params={'dtmf':digits})
                        await ws.send_json({'type':'dtmf.sent','digits':len(digits)})
                    except (AriFailure, ClientError, OSError, asyncio.TimeoutError):
                        await ws.send_json({'type':'error','code':'DTMF_FAILED'})
                else:
                    await ws.send_json({'type':'error','code':'UNSUPPORTED_EVENT'})
            elif msg.type == WSMsgType.BINARY:
                b=msg.data
                if call.state!='bridged' or not call.rtp or not isinstance(b,bytes) or len(b)!=656:
                    await ws.send_json({'type':'error','code':'MEDIA_NOT_READY'}); continue
                magic, seq, stamp = AGENT_HEADER.unpack_from(b)
                if magic != b'DT01' or seq <= call.last_pcm_seq:
                    await ws.send_json({'type':'error','code':'BAD_FRAME_SEQUENCE'});continue
                now=time.monotonic()
                # Absolute media budget: 65 frames per second, no unbounded queued output.
                call.ws_rate=[t for t in call.ws_rate if now-t<1]
                if len(call.ws_rate)>=65 or call.to_asterisk.full():
                    await ws.send_json({'type':'error','code':'MEDIA_BACKPRESSURE'});continue
                call.ws_rate.append(now)
                call.last_pcm_seq=seq
                call.to_asterisk.put_nowait(b[16:])
            if call.ending: break
    except (asyncio.TimeoutError, ConnectionError): pass
    finally:
        if call.ws is ws and not call.ending:
            await asyncio.shield(asyncio.create_task(m.stop(call,'AGENT_DISCONNECTED')))
    return ws


async def startup(app):
    await app[KEY].ari.start()


async def cleanup(app):
    await app[KEY].shutdown()


def app_factory(settings,*,ari=None):
    manager=Manager(settings,ari=ari)
    app=web.Application(middlewares=[error_middleware],client_max_size=MAX_BODY)
    app[KEY]=manager
    app.router.add_get('/health',health)
    app.router.add_get('/v1/readiness',endpoint_readiness)
    app.router.add_post('/v1/mandates',create_mandate)
    app.router.add_post('/v1/mandates/{mandate_id}/revoke',revoke)
    app.router.add_post('/v1/calls',create_call)
    app.router.add_get('/v1/calls/{call_id}',call_info)
    app.router.add_post('/v1/calls/{call_id}/tickets',ticket)
    app.router.add_post('/v1/calls/{call_id}/stop',stop_call)
    app.router.add_get('/v1/calls/{call_id}/media',media)
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    return app


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8877)
    parser.add_argument('--check-config',action='store_true',help='Validate configuration without connecting or dialling')
    args=parser.parse_args()
    settings=Settings.env()
    if args.check_config:
        print(json.dumps({'valid': True, 'version':'0.0.1', 'origination_enabled': settings.allow_origination,
                          'loopback_control':True, 'trunk_configured':True}))
        raise SystemExit(0)
    web.run_app(app_factory(settings),host=settings.control_host,port=args.port,access_log=None)
