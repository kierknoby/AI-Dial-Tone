"""Small, auditable aiohttp ARI client; credentials never enter URLs."""
from __future__ import annotations

import asyncio
import json
from urllib.parse import urlsplit
from aiohttp import BasicAuth, ClientSession, ClientTimeout, WSMsgType


class AriFailure(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


class Ari:
    def __init__(self, *, url, user, password, application, event_handler, disconnect_handler):
        self.url = url.rstrip('/')
        self.application = application
        self.auth = BasicAuth(user, password)
        self.event_handler = event_handler
        self.disconnect_handler = disconnect_handler
        self.http = ClientSession(timeout=ClientTimeout(total=8), raise_for_status=False)
        self.ws = None
        self.task = None
        self.connected = False

    async def request(self, method, path, *, params=None, json_body=None, missing_ok=False):
        # Paths are assembled by our own code from server-created IDs only.
        async with self.http.request(method, self.url + '/ari' + path, auth=self.auth, params=params,
                                     json=json_body, allow_redirects=False) as response:
            data = await response.read()
            if response.status == 404 and missing_ok:
                return None
            if response.status >= 300:
                raise AriFailure('ARI_HTTP_' + str(response.status), response.status)
            if data:
                try:
                    return json.loads(data)
                except (UnicodeError, json.JSONDecodeError):
                    raise AriFailure('ARI_INVALID_JSON')
            return {}

    async def start(self):
        scheme = 'wss' if self.url.startswith('https://') else 'ws'
        host = self.url.split('://', 1)[1]
        try:
            self.ws = await self.http.ws_connect(f'{scheme}://{host}/ari/events',
                                                 params={'app': self.application, 'subscribeAll': 'false'},
                                                 auth=self.auth, heartbeat=10, max_msg_size=16384,
                                                 autoping=True)
        except Exception:
            await self.http.close()
            raise
        self.connected = True
        self.task = asyncio.create_task(self._events())

    async def _events(self):
        try:
            async for message in self.ws:
                if message.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(message.data)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        await self.event_handler(data)
                elif message.type in (WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSED):
                    break
        finally:
            self.connected = False
            await self.disconnect_handler()

    async def close(self):
        if self.ws:
            await self.ws.close()
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        await self.http.close()
