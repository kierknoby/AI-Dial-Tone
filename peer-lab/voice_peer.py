"""Audio-native AI peer runtime: PCM -> VAD -> ASR -> model -> TTS -> PCM.

Voice turns are derived from *received media*, never a remote `say` claim.
This development runtime cannot originate phone calls, book reservations, or pay.
"""
from __future__ import annotations

import asyncio
import inspect
import time
from speech import PCM_BYTES, MAX_AUDIO, EnergyUtteranceDetector, SpeechError, validate_recognition
from model_adapter import ModelError


class VoicePeer:
    def __init__(self, client, asr, model, tts, system_prompt, *, max_turns=6,
                 silence_frames=8, threshold=400, frame_delay=0.0205):
        if type(max_turns) is not int or not 1 <= max_turns <= 12:
            raise ValueError('INVALID_TURN_LIMIT')
        if not isinstance(system_prompt, str) or not 30 <= len(system_prompt) <= 2000:
            raise ValueError('INVALID_SYSTEM_PROMPT')
        self.client, self.asr, self.model, self.tts = client, asr, model, tts
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.detector = EnergyUtteranceDetector(threshold=threshold, tail_frames=silence_frames)
        self.frame_delay = frame_delay
        self.turns = 0
        self.turns_received = 0
        self.interruptions = 0
        self.ignored_text_sidecars = 0
        self.errors = []
        self.history = []
        self.pending = None
        self.speaking = False
        self.audio_received = 0
        self.audio_transmitted = 0
        self.model_latency_ms = []
        self.transcriptions = []  # private in-process; only explicitly relayed text is journalled

    async def _abort_pending(self):
        if self.pending and not self.pending.done():
            was_speaking = self.speaking
            self.interruptions += 1
            self.pending.cancel()
            await asyncio.gather(self.pending, return_exceptions=True)
            self.pending = None
            if was_speaking:
                self.speaking = False
                try:
                    await self.client.interrupt()
                except Exception:
                    pass

    async def _conversation_turn(self, http, utterance):
        try:
            text = validate_recognition(await self.asr.transcribe(http, utterance))
            if not text:
                return  # noise, unknown words, or empty recognition: do not invent a turn
            self.turns_received += 1
            self.transcriptions.append(text)
            # An agent-originated claim, *not* an independently verified transcript.
            await self.client.say('[ASR, unverified] ' + text[:1160])
            self.history.append({'role':'user','content':text})
            start = time.monotonic()
            answer = await self.model.respond(http, self.history[-16:], self.system_prompt)
            self.model_latency_ms.append(round((time.monotonic() - start) * 1000, 1))
            # Answer remains an agent assertion; it cannot directly mutate bookings.
            if hasattr(self.tts, 'speak_with_session'):
                pcm = await self.tts.speak_with_session(http, answer)
            else:
                pcm = await self.tts.speak(answer)
            if not isinstance(pcm, bytes) or not pcm or len(pcm) > MAX_AUDIO or len(pcm) % PCM_BYTES:
                raise SpeechError('INVALID_SYNTHESISED_MEDIA')
            self.history.append({'role':'assistant','content':answer})
            await self.client.say(answer)
            self.speaking = True
            clock_start = time.monotonic()
            for index, pos in enumerate(range(0, len(pcm), PCM_BYTES)):
                # PeerClient increments its own monotonic sequence. Never reset
                # timestamps to zero at the start of a new response.
                await self.client.pcm(pcm[pos:pos+PCM_BYTES], timestamp_ms=self.client.seq * 20)
                self.audio_transmitted += 1
                # Pace from a fixed monotonic origin: avoid accumulating jitter.
                # Excessive lag is a media failure, not permission to flood the socket.
                target = clock_start + (index + 1) * self.frame_delay
                lag = time.monotonic() - target
                if self.frame_delay and lag > 0.25:
                    raise SpeechError('MEDIA_SEND_TOO_SLOW')
                await asyncio.sleep(max(0, -lag))
            self.speaking = False
            await self.client.audio_end()
            self.turns += 1
        except asyncio.CancelledError:
            raise
        except (SpeechError, ModelError, OSError, ValueError, TypeError, asyncio.TimeoutError) as exc:
            self.errors.append(getattr(exc, 'code', 'VOICE_PIPELINE_FAILURE'))
            # Fail closed: no invented booking confirmation or substituted text.
            try:
                await self.client.hangup()
            except Exception:
                pass
        finally:
            self.speaking = False

    async def _handle_audio(self, http, pcm):
        utterance, started = self.detector.push(pcm)
        self.audio_received += 1
        if started and self.pending and not self.pending.done():
            await self._abort_pending()
        if utterance:
            await self._finish_utterance(http, utterance)

    async def _finish_utterance(self, http, utterance):
        if self.pending and not self.pending.done():
            await self._abort_pending()
        if self.turns_received >= self.max_turns:
            await self.client.hangup()
            return
        self.pending = asyncio.create_task(self._conversation_turn(http, utterance))

    async def run(self, http):
        await self.client.connect()
        try:
            while True:
                message = await self.client.recv(timeout=90)
                typ = message.get('type')
                if typ in ('session.ended','socket.closed'):
                    return
                if typ == 'say':
                    # Bot assertions must NEVER be used as a stand-in for hearing audio.
                    self.ignored_text_sidecars += 1
                    continue
                if typ == 'audio.interrupt':
                    self.detector.reset()
                    await self._abort_pending()
                    continue
                if typ == 'pcm':
                    packet = message.get('data')
                    if not isinstance(packet, bytes) or len(packet) != 656 or packet[:4] != b'DT01':
                        self.errors.append('INVALID_RECEIVED_MEDIA')
                        continue
                    await self._handle_audio(http, packet[16:])
                if typ == 'audio.end':
                    utterance = self.detector.flush()
                    if utterance:
                        await self._finish_utterance(http, utterance)
        finally:
            await self._abort_pending()
            await self.client.close()

    def metrics(self):
        return {
            'audio_received_frames': self.audio_received,
            'audio_transmitted_frames': self.audio_transmitted,
            'asr_turns': self.turns_received,
            'spoken_turns': self.turns,
            'interruptions': self.interruptions,
            'text_sidecars_ignored': self.ignored_text_sidecars,
            'model_latency_ms': list(self.model_latency_ms),
            'errors': list(self.errors),
            'real_pstn': False,
            'reservation_verified': False,
        }
