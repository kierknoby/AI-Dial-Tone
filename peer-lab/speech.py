"""Audio-native voice adapters for the local AI Dial-Tone agent laboratory.

No SIP or PSTN. ASR transcripts are unverified machine interpretations of media,
not evidence of a reservation. Voice services are explicitly configured; neither
agent is given telephone credentials, a payment interface, or external tools.
"""
from __future__ import annotations

import asyncio
import ctypes
import ctypes.util
import io
import ipaddress
import json
import math
import os
import re
import struct
import wave
from collections import deque
from urllib.parse import urlsplit

PCM_BYTES = 640
HZ = 16000
MAX_AUDIO = PCM_BYTES * 600  # twelve seconds of incoming speech
MAX_TEXT = 1200


class SpeechError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_endpoint(url, suffix):
    p = urlsplit(url)
    if (p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or
            p.query or p.fragment or not p.path.endswith(suffix)):
        raise SpeechError('INVALID_SPEECH_ENDPOINT')
    try:
        loopback = ipaddress.ip_address(p.hostname).is_loopback
    except ValueError:
        loopback = p.hostname == 'localhost'
    if p.scheme == 'http' and not loopback:
        raise SpeechError('REMOTE_SPEECH_REQUIRES_HTTPS')
    return url


def validate_pcm(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_AUDIO or len(raw) % 2:
        raise SpeechError('INVALID_PCM_AUDIO')
    return raw


def wav_bytes(pcm):
    validate_pcm(pcm)
    out = io.BytesIO()
    with wave.open(out, 'wb') as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(HZ)
        writer.writeframes(pcm)
    return out.getvalue()


def validate_recognition(text):
    if not isinstance(text, str) or len(text) > MAX_TEXT or any(ord(c) < 32 for c in text):
        raise SpeechError('INVALID_TRANSCRIPT')
    return text.strip()


class TranscriptionAPI:
    """OpenAI-compatible /audio/transcriptions with bounded WAV uploads.

    Provider must accept WAV (16-bit 16 kHz mono) with model and file fields.
    Never follow redirects; never send the peer's bearer token to this endpoint.
    """
    def __init__(self, endpoint, model, *, key='', timeout=10):
        self.endpoint = validate_endpoint(endpoint, '/audio/transcriptions')
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][\w.:/-]{0,127}', model):
            raise SpeechError('INVALID_ASR_MODEL')
        if not isinstance(key, str) or len(key) > 500:
            raise SpeechError('INVALID_ASR_CREDENTIAL')
        self.model, self.key, self.timeout = model, key, timeout

    async def transcribe(self, http, pcm):
        from aiohttp import FormData, ClientError
        upload = FormData()
        upload.add_field('model', self.model)
        upload.add_field('file', wav_bytes(pcm), filename='utterance.wav', content_type='audio/wav')
        headers = {'Authorization': 'Bearer ' + self.key} if self.key else {}
        try:
            async with http.post(self.endpoint, data=upload, headers=headers,
                                 allow_redirects=False, timeout=self.timeout) as resp:
                if resp.status != 200:
                    raise SpeechError('ASR_HTTP_FAILURE')
                raw = await resp.content.read(16001)
                if len(raw) > 16000:
                    raise SpeechError('ASR_RESPONSE_TOO_LARGE')
                payload = json.loads(raw)
                return validate_recognition(payload['text'])
        except SpeechError:
            raise
        except (OSError, ValueError, TypeError, KeyError, asyncio.TimeoutError, ClientError) as exc:
            raise SpeechError('ASR_UNAVAILABLE') from exc


class EnergyUtteranceDetector:
    """Bounded deterministic 20 ms voice segmentation for the developer lab.

    Energy gating is *not* acoustic echo cancellation or production VAD. Senders
    may also explicitly signal audio.end to flush a speech turn immediately.
    """
    def __init__(self, *, threshold=400, start_frames=2, tail_frames=8, max_frames=600):
        if not 0 < threshold < 30000 or not 1 <= start_frames <= 10 or not 1 <= tail_frames <= 50 or not 4 <= max_frames <= 600:
            raise ValueError('INVALID_VAD_SETTINGS')
        self.threshold = threshold
        self.start_frames = start_frames
        self.tail_frames = tail_frames
        self.max_frames = max_frames
        self.reset()

    def reset(self):
        self.frames = []
        self.prefix = deque(maxlen=self.start_frames + 4)
        self.streak = 0
        self.trailing = 0
        self.active = False

    def voiced(self, pcm):
        if not isinstance(pcm, bytes) or len(pcm) != PCM_BYTES:
            raise SpeechError('INVALID_PCM_FRAME')
        # Evaluate every fourth sample; no third-party DSP dependency required.
        samples = struct.unpack('<320h', pcm)
        return math.sqrt(sum(n*n for n in samples[::4]) / 80) >= self.threshold

    def push(self, pcm):
        talking = self.voiced(pcm)
        started = False
        if not self.active:
            self.prefix.append(pcm)
            self.streak = self.streak + 1 if talking else 0
            if self.streak < self.start_frames:
                return None, False
            self.active = True
            started = True
            self.frames = list(self.prefix)
            self.prefix.clear()
        else:
            self.frames.append(pcm)
        self.trailing = 0 if talking else self.trailing + 1
        if self.trailing >= self.tail_frames or len(self.frames) >= self.max_frames:
            utterance = self.flush()
            return utterance, started
        return None, started

    def flush(self):
        if not self.active:
            self.reset()
            return None
        utterance = b''.join(self.frames)
        self.reset()
        return utterance if len(utterance) >= PCM_BYTES * self.start_frames else None


class EspeakTTS:
    """Offline speech synthesis; requires espeak and ffmpeg installed locally."""
    def __init__(self, *, speed=155, max_seconds=15):
        if type(speed) is not int or not 90 <= speed <= 240:
            raise SpeechError('INVALID_SPEECH_SPEED')
        self.speed, self.max_seconds = speed, max_seconds

    async def speak(self, text):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_TEXT:
            raise SpeechError('INVALID_TTS_TEXT')
        if any(ord(c) < 32 and c not in '\n\t' for c in text):
            raise SpeechError('INVALID_TTS_TEXT')
        try:
            process = await asyncio.create_subprocess_exec(
                'espeak', '--stdout', '-s', str(self.speed), ' ' + text,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            try:
                wav, _ = await asyncio.wait_for(process.communicate(), timeout=self.max_seconds)
            except BaseException:
                if process.returncode is None: process.kill(); await process.wait()
                raise
            if process.returncode != 0 or len(wav) > 2_000_000:
                raise SpeechError('SYNTHESIS_FAILED')
            converter = await asyncio.create_subprocess_exec(
                'ffmpeg', '-nostdin', '-loglevel', 'error', '-i', 'pipe:0',
                '-f', 's16le', '-ac', '1', '-ar', str(HZ), 'pipe:1',
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
            try:
                pcm, _ = await asyncio.wait_for(converter.communicate(wav), timeout=self.max_seconds)
            except BaseException:
                if converter.returncode is None: converter.kill(); await converter.wait()
                raise
            if converter.returncode != 0 or not pcm or len(pcm) > MAX_AUDIO:
                raise SpeechError('SYNTHESIS_FAILED_OR_TOO_LONG')
            pcm += b'\0' * (-len(pcm) % PCM_BYTES)
            return pcm
        except (FileNotFoundError, OSError, asyncio.TimeoutError) as exc:
            raise SpeechError('SYNTHESIS_UNAVAILABLE') from exc


class PocketSphinxASR:
    """Optional, offline *experimental* actual speech recogniser using the system C library.

    Not required in CI. Accuracy is limited, particularly with accents, names and
    phone quality. A provider-grade transcription engine is required for deployment.
    """
    def __init__(self, model_root='/usr/share/pocketsphinx/model/en-us'):
        self._ps_lib = ctypes.util.find_library('pocketsphinx')
        self._base_lib = ctypes.util.find_library('sphinxbase')
        if not self._ps_lib or not self._base_lib:
            raise SpeechError('OFFLINE_ASR_UNAVAILABLE')
        self._p = ctypes.CDLL(self._ps_lib)
        self._b = ctypes.CDLL(self._base_lib)
        p, b = self._p, self._b
        p.ps_args.restype = ctypes.c_void_p
        b.cmd_ln_init.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
        b.cmd_ln_init.restype = ctypes.c_void_p
        b.cmd_ln_free_r.argtypes = [ctypes.c_void_p]
        p.ps_init.argtypes = [ctypes.c_void_p]
        p.ps_init.restype = ctypes.c_void_p
        p.ps_free.argtypes = [ctypes.c_void_p]
        p.ps_start_utt.argtypes = [ctypes.c_void_p]
        p.ps_start_utt.restype = ctypes.c_int
        p.ps_process_raw.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
        p.ps_process_raw.restype = ctypes.c_int
        p.ps_end_utt.argtypes = [ctypes.c_void_p]
        p.ps_end_utt.restype = ctypes.c_int
        p.ps_get_hyp.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        p.ps_get_hyp.restype = ctypes.c_char_p
        paths = [os.path.join(model_root, 'en-us'), os.path.join(model_root, 'cmudict-en-us.dict'),
                 os.path.join(model_root, 'en-us.lm.bin')]
        if not all(os.path.exists(n) for n in paths):
            raise SpeechError('OFFLINE_ASR_MODEL_MISSING')
        self._args = b.cmd_ln_init(None, p.ps_args(), 1, b'-hmm', os.fsencode(paths[0]),
                                   b'-dict', os.fsencode(paths[1]), b'-lm', os.fsencode(paths[2]),
                                   b'-samprate', b'16000', b'-logfn', b'/dev/null', None)
        if not self._args:
            raise SpeechError('OFFLINE_ASR_INIT_FAILED')
        self._decoder = p.ps_init(self._args)
        if not self._decoder:
            b.cmd_ln_free_r(self._args)
            raise SpeechError('OFFLINE_ASR_INIT_FAILED')
        self._lock = asyncio.Lock()

    def close(self):
        if getattr(self, '_decoder', None):
            self._p.ps_free(self._decoder)
            self._decoder = None
        if getattr(self, '_args', None):
            self._b.cmd_ln_free_r(self._args)
            self._args = None

    async def transcribe(self, http, pcm):
        validate_pcm(pcm)
        async with self._lock:
            return await asyncio.to_thread(self._recognise, pcm)

    def _recognise(self, pcm):
        if self._p.ps_start_utt(self._decoder) != 0:
            raise SpeechError('OFFLINE_ASR_FAILED')
        samples = (ctypes.c_int16 * (len(pcm) // 2)).from_buffer_copy(pcm)
        result = self._p.ps_process_raw(self._decoder, samples, len(samples), 0, 1)
        ended = self._p.ps_end_utt(self._decoder)
        if result < 0 or ended != 0:
            raise SpeechError('OFFLINE_ASR_FAILED')
        value = self._p.ps_get_hyp(self._decoder, None)
        return validate_recognition(value.decode('utf-8', errors='replace') if value else '')


class SpeechAPI:
    """OpenAI-compatible POST /audio/speech, with bounded WAV reply.

    The API must support the response_format='wav' request. The returned
    PCM stream is normalised to 16-kHz mono s16le with local ffmpeg if needed.
    Other, provider-specific TTS transports require their own adapters.
    """
    def __init__(self, endpoint, model, voice, *, key='', timeout=15):
        self.endpoint = validate_endpoint(endpoint, '/audio/speech')
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][\w.:/-]{0,127}', model):
            raise SpeechError('INVALID_TTS_MODEL')
        if not isinstance(voice, str) or not re.fullmatch(r'[A-Za-z0-9][\w_-]{0,63}', voice):
            raise SpeechError('INVALID_TTS_VOICE')
        if not isinstance(key, str) or len(key) > 500:
            raise SpeechError('INVALID_TTS_CREDENTIAL')
        self.model, self.voice, self.key, self.timeout = model, voice, key, timeout

    async def speak(self, text):
        """Use speak_with_session(http, text) for connection reuse."""
        from aiohttp import ClientSession
        async with ClientSession() as http:
            return await self.speak_with_session(http, text)

    async def speak_with_session(self, http, text):
        from aiohttp import ClientError
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_TEXT:
            raise SpeechError('INVALID_TTS_TEXT')
        if any(ord(c) < 32 and c not in '\n\t' for c in text):
            raise SpeechError('INVALID_TTS_TEXT')
        headers = {'Authorization': 'Bearer ' + self.key} if self.key else {}
        try:
            async with http.post(self.endpoint,
                    json={'model': self.model,'voice':self.voice,'input':text,'response_format':'wav'},
                    headers=headers, allow_redirects=False, timeout=self.timeout) as r:
                if r.status != 200:
                    raise SpeechError('TTS_HTTP_FAILURE')
                raw = await r.content.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise SpeechError('TTS_RESPONSE_TOO_LARGE')
            try:
                with wave.open(io.BytesIO(raw), 'rb') as recording:
                    if recording.getcomptype() != 'NONE':
                        raise SpeechError('TTS_WAV_CODEC_UNSUPPORTED')
                    settings = (recording.getframerate(),recording.getnchannels(),recording.getsampwidth())
                    pcm = recording.readframes(recording.getnframes())
            except (wave.Error, EOFError) as exc:
                raise SpeechError('TTS_MALFORMED_WAV') from exc
            if settings != (HZ,1,2):
                # A 24 kHz model output cannot be sent in a 16 kHz media frame.
                # Use a controlled local converter, never relabel its sample rate.
                try:
                    process = await asyncio.create_subprocess_exec(
                        'ffmpeg','-nostdin','-loglevel','error','-i','pipe:0',
                        '-f','s16le','-ar',str(HZ),'-ac','1','pipe:1',
                        stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL)
                    try:
                        pcm, _ = await asyncio.wait_for(process.communicate(raw),timeout=10)
                    except BaseException:
                        if process.returncode is None:process.kill();await process.wait()
                        raise
                    if process.returncode != 0:
                        raise SpeechError('TTS_TRANSCODE_FAILED')
                except FileNotFoundError as exc:
                    raise SpeechError('TTS_TRANSCODER_UNAVAILABLE') from exc
            if not pcm or len(pcm) > MAX_AUDIO or len(pcm)%2:
                raise SpeechError('TTS_AUDIO_REJECTED')
            return pcm + b'\0' * (-len(pcm) % PCM_BYTES)
        except SpeechError:
            raise
        except (OSError,ValueError,TypeError,asyncio.TimeoutError,ClientError) as exc:
            raise SpeechError('TTS_UNAVAILABLE') from exc
