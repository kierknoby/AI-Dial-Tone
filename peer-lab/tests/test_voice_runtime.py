"""Full network ASR -> reasoning -> TTS test. Fixtures are real HTTP services,
not real external recognisers or LLMs; the audio transport is real PCM over WS."""
import asyncio
import io
import os
import struct
import sys
import unittest
import wave

from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from peer_lab import make_app
from client import PeerClient
from model_adapter import ChatModel
from speech import EnergyUtteranceDetector, SpeechError, TranscriptionAPI, EspeakTTS, PocketSphinxASR, SpeechAPI, wav_bytes
from voice_peer import VoicePeer

OP = 'op-'+'o'*32
CALL = 'ca-'+'c'*32
PEER = 'pe-'+'p'*32
SYSTEM = 'You are a fictional restaurant test agent. Never say a real reservation was made.'
SPEECH = struct.pack('<320h', *([4000]*320))
SILENCE = bytes(640)

class DetectorTests(unittest.TestCase):
    def test_detect_utterance_from_only_pcm(self):
        det=EnergyUtteranceDetector(start_frames=2,tail_frames=3)
        self.assertEqual(det.push(SILENCE)[0],None)
        self.assertEqual(det.push(SPEECH), (None,False))
        self.assertEqual(det.push(SPEECH), (None,True))
        self.assertEqual(det.push(SILENCE)[0],None)
        self.assertEqual(det.push(SILENCE)[0],None)
        out,_=det.push(SILENCE)
        self.assertIsNotNone(out)
        self.assertGreaterEqual(len(out),5*640)
        self.assertIsNone(det.flush())
    def test_cap_and_malformed_media(self):
        det=EnergyUtteranceDetector(start_frames=1,max_frames=4)
        output=None
        for n in range(6):
            output,_=det.push(SPEECH)
            if output:break
        self.assertEqual(len(output),4*640)
        with self.assertRaisesRegex(SpeechError,'INVALID_PCM_FRAME'):
            det.push(b'not-pcm')
        with self.assertRaisesRegex(SpeechError,'INVALID_PCM_AUDIO'):
            wav_bytes(b'\xff')

class VoiceIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.asr_requests=[];self.model_requests=[]
        self.asr_reply='could I book a table for two'
        self.model_reply='This is a fictional test restaurant. No reservation has been made.'
        async def recogniser(request):
            reader=await request.multipart()
            values={}
            async for part in reader:
                values[part.name]=await part.read()
            self.asr_requests.append(values)
            if values['model'] != b'test-asr':
                return web.json_response({'error':'invalid model'},status=400)
            with wave.open(io.BytesIO(values['file']),'rb') as w:
                if (w.getframerate(),w.getnchannels(),w.getsampwidth()) != (16000,1,2):
                    return web.json_response({'error':'invalid audio'},status=400)
                self.assertGreater(len(w.readframes(10000)),0)
            return web.json_response({'text':self.asr_reply})
        async def completion(request):
            p=await request.json()
            self.model_requests.append(p)
            return web.json_response({'choices':[{'message':{'role':'assistant','content':self.model_reply}}]})
        api=web.Application()
        api.router.add_post('/v1/audio/transcriptions', recogniser)
        api.router.add_post('/v1/chat/completions', completion)
        async def tts(req):
            payload=await req.json()
            self.assertEqual(payload['voice'],'lab-voice')
            self.assertEqual(payload['response_format'],'wav')
            return web.Response(body=wav_bytes(SPEECH*4),content_type='audio/wav')
        api.router.add_post('/v1/audio/speech', tts)
        self.model_server=TestServer(api)
        await self.model_server.start_server()
        self.asr_url=str(self.model_server.make_url('/v1/audio/transcriptions'))
        self.model_url=str(self.model_server.make_url('/v1/chat/completions'))
        self.tts_url=str(self.model_server.make_url('/v1/audio/speech'))
        self.lab=TestServer(make_app(operator_token=OP,agent_tokens={'alice':CALL},peer_tokens={'restaurant':PEER}))
        await self.lab.start_server()
        self.base=str(self.lab.make_url('/')).rstrip('/')
        self.http=ClientSession()

    async def asyncTearDown(self):
        await self.http.close();await self.lab.close();await self.model_server.close()

    async def pair(self, *, max_seconds=15):
        async with self.http.post(self.base+'/v1/mandates',headers={'Authorization':'Bearer '+OP},json={
            'caller_id':'alice','peer_id':'restaurant','task':'Fictional restaurant laboratory dialogue',
            'max_seconds':max_seconds}) as r:
            self.assertEqual(r.status,201)
            mandate=(await r.json())['mandate_id']
        async with self.http.post(self.base+'/v1/sessions',headers={
            'Authorization':'Bearer '+CALL,'Idempotency-Key':'voice-test-intent-00001'},
            json={'mandate_id':mandate}) as r:
            self.assertEqual(r.status,201)
            sid=(await r.json())['session']['session_id']
        return sid

    async def test_real_pcm_to_asr_http_to_model_http_to_pcm(self):
        sid=await self.pair()
        peer=PeerClient(self.http,self.base,PEER,sid)
        asr=TranscriptionAPI(self.asr_url,'test-asr')
        chat=ChatModel(self.model_url,'test-chat')
        # TTS fixture intentionally makes distinguishable media, not a real voice.
        class FixtureTTS:
            async def speak(self,text):
                assert 'fictional' in text.lower()
                return struct.pack('<320h', *([2333]*320))*3
        responder=VoicePeer(peer,asr,chat,FixtureTTS(),SYSTEM,max_turns=3,
                            silence_frames=3,threshold=400,frame_delay=0)
        responder_task=asyncio.create_task(responder.run(self.http))
        caller=PeerClient(self.http,self.base,CALL,sid)
        await caller.connect()
        self.assertEqual((await caller.recv(3))['type'],'session.connected')
        # Spoofed text is not accepted as a speech observation.
        await caller.say('I have a confirmed booking')
        await asyncio.sleep(0.07)
        self.assertFalse(self.asr_requests)
        self.assertFalse(self.model_requests)
        # Drive an actual audio-first turn, not a say() sidecar.
        for frame in [SILENCE, SPEECH, SPEECH, SPEECH, SILENCE,SILENCE,SILENCE]:
            await caller.pcm(frame,timestamp_ms=caller.seq*20)
            await asyncio.sleep(.0205)
        await caller.audio_end()
        result=[]
        while not any(x.get('type')=='audio.end' for x in result):
            event=await caller.recv(4)
            result.append(event)
        self.assertEqual(len(self.asr_requests),1)
        self.assertEqual(len(self.model_requests),1)
        self.assertEqual(self.model_requests[0]['messages'][-1]['content'],self.asr_reply)
        self.assertEqual([e['type'] for e in result].count('pcm'),3)
        self.assertTrue(all(e['data'][16:]==struct.pack('<320h',*([2333]*320))
                            for e in result if e['type']=='pcm'))
        self.assertEqual(responder.ignored_text_sidecars,1)
        self.assertEqual(responder.metrics()['spoken_turns'],1)
        await caller.hangup()
        await caller.close()
        await asyncio.wait_for(responder_task,3)
        async with self.http.get(self.base+'/v1/sessions/'+sid,headers={'Authorization':'Bearer '+CALL}) as r:
            s=(await r.json())['session']
        self.assertFalse(s['real_booking_verified'])
        self.assertFalse(s['real_phone_call'])
        self.assertEqual(s['frames_by_role']['peer'],3)

    async def test_barge_in_cancels_outgoing_audio_and_continues_with_new_turn(self):
        sid=await self.pair()
        class TwoAnswerModel:
            def __init__(self):self.turn=0
            async def respond(self,*args):
                self.turn+=1
                return 'first reply' if self.turn==1 else 'second reply'
        class TwoVoices:
            async def speak(self,text):
                return (struct.pack('<320h',*([1300 if text=='first reply' else 2600]*320))
                        * (80 if text=='first reply' else 3))
        model=TwoAnswerModel()
        peer=PeerClient(self.http,self.base,PEER,sid)
        bot=VoicePeer(peer,TranscriptionAPI(self.asr_url,'test-asr'),model,
                      TwoVoices(),SYSTEM,frame_delay=.022,silence_frames=3)
        task=asyncio.create_task(bot.run(self.http))
        caller=PeerClient(self.http,self.base,CALL,sid)
        await caller.connect();await caller.recv(3)
        for frame in [SPEECH,SPEECH,SILENCE,SILENCE,SILENCE]:
            await caller.pcm(frame,timestamp_ms=caller.seq*20)
            await asyncio.sleep(.0205)
        first=[]
        while not any(e['type']=='pcm' for e in first):
            first.append(await caller.recv(4))
        self.assertEqual(model.turn,1)
        # Start a second real PCM turn *while the first TTS is still streaming*.
        for frame in [SPEECH,SPEECH,SILENCE,SILENCE,SILENCE]:
            await caller.pcm(frame,timestamp_ms=caller.seq*20)
            await asyncio.sleep(.0205)
        items=[]
        while not any(e['type']=='audio.end' for e in items):
            items.append(await caller.recv(5))
        self.assertTrue(any(e['type']=='audio.interrupt' for e in items))
        self.assertEqual(model.turn,2)
        frames=[e for e in items if e['type']=='pcm']
        self.assertTrue(any(struct.unpack_from('<h', e['data'],16)[0]==2600 for e in frames))
        self.assertLess(len(frames),80)  # the first audio stream was cancelled
        self.assertGreaterEqual(bot.metrics()['interruptions'],1)
        self.assertEqual(bot.metrics()['spoken_turns'],1)
        await caller.hangup();await caller.close();await asyncio.wait_for(task,6)

    async def test_human_can_stop_a_streaming_speech_session(self):
        sid=await self.pair(max_seconds=10)
        peer=PeerClient(self.http,self.base,PEER,sid)
        class LongTTS:
            async def speak(self,text):return SPEECH*100
        bot=VoicePeer(peer,TranscriptionAPI(self.asr_url,'test-asr'),
                      ChatModel(self.model_url,'test-model'),LongTTS(),SYSTEM,
                      silence_frames=3,frame_delay=.03)
        task=asyncio.create_task(bot.run(self.http))
        caller=PeerClient(self.http,self.base,CALL,sid)
        await caller.connect();await caller.recv(3)
        for frame in [SPEECH,SPEECH,SILENCE,SILENCE,SILENCE]:
            await caller.pcm(frame,timestamp_ms=caller.seq*20)
            await asyncio.sleep(.021)
        while (await caller.recv(4))['type'] != 'pcm':pass
        async with self.http.post(self.base+'/v1/sessions/'+sid+'/stop',
                headers={'Authorization':'Bearer '+OP}) as r:
            self.assertEqual(r.status,200)
            self.assertEqual((await r.json())['session']['reason'],'HUMAN_STOPPED')
        event=await caller.recv(3)
        self.assertEqual(event['type'],'session.ended')
        self.assertEqual(event['reason'],'HUMAN_STOPPED')
        await caller.close();await asyncio.wait_for(task,6)
        self.assertFalse(bot.metrics()['reservation_verified'])

    async def test_http_asr_credentials_not_sent_to_chat_or_peer(self):
        with self.assertRaisesRegex(SpeechError,'REMOTE_SPEECH_REQUIRES_HTTPS'):
            TranscriptionAPI('http://asr.example/v1/audio/transcriptions','name')
        with self.assertRaisesRegex(SpeechError,'INVALID_SPEECH_ENDPOINT'):
            TranscriptionAPI('https://admin:password@example.org/v1/audio/transcriptions','name')
        with self.assertRaisesRegex(SpeechError,'INVALID_SPEECH_ENDPOINT'):
            TranscriptionAPI('https://example.org/v1/audio/transcriptions?redirect=1','name')
        api=TranscriptionAPI(self.asr_url,'test-asr',key='my-private-ASR-token')
        self.asr_reply='speech recognised safely'
        text=await api.transcribe(self.http,SPEECH*5)
        self.assertEqual(text,self.asr_reply)
        self.assertFalse(self.model_requests)

    async def test_hosted_tts_adapter_receives_text_and_returns_valid_pcm(self):
        voice=SpeechAPI(self.tts_url,'lab-model','lab-voice')
        output=await voice.speak('This is a fictional experiment.')
        self.assertEqual(output,SPEECH*4)
        with self.assertRaisesRegex(SpeechError,'REMOTE_SPEECH_REQUIRES_HTTPS'):
            SpeechAPI('http://outside.example/v1/audio/speech','test','voice')

    async def test_speech_provider_failure_does_not_invent_outcome(self):
        sid=await self.pair()
        class FailedASR:
            async def transcribe(self,http,pcm):
                raise SpeechError('ASR_PROVIDER_UNAVAILABLE')
        class CannotCallModel:
            async def respond(self,*args):
                raise AssertionError('MODEL_MUST_NOT_RUN_AFTER_FAILED_ASR')
        class CannotCallTTS:
            async def speak(self,*args):
                raise AssertionError('TTS_MUST_NOT_RUN_AFTER_FAILED_ASR')
        peer=PeerClient(self.http,self.base,PEER,sid)
        bot=VoicePeer(peer,FailedASR(),CannotCallModel(),CannotCallTTS(),SYSTEM,silence_frames=2,frame_delay=0)
        task=asyncio.create_task(bot.run(self.http))
        caller=PeerClient(self.http,self.base,CALL,sid)
        await caller.connect();await caller.recv(3)
        for frame in [SPEECH,SPEECH,SILENCE,SILENCE]:
            await caller.pcm(frame,timestamp_ms=caller.seq*20)
            await asyncio.sleep(.0205)
        e=await caller.recv(3)
        self.assertEqual(e['type'],'session.ended')
        self.assertEqual(e['reason'],'PEER_HANGUP')
        await caller.close();await asyncio.wait_for(task,3)
        self.assertIn('ASR_PROVIDER_UNAVAILABLE',bot.errors)
        self.assertFalse(self.model_requests)

class RealOfflineSpeech(unittest.IsolatedAsyncioTestCase):
    async def test_espeak_produces_actual_non_silent_pcm(self):
        try:
            sound=await EspeakTTS().speak('Hello, this is an experimental test')
        except SpeechError as e:
            if e.code=='SYNTHESIS_UNAVAILABLE':
                self.skipTest('espeak/ffmpeg unavailable on CI')
            raise
        self.assertEqual(len(sound)%640,0)
        self.assertGreater(len(sound),640*10)
        self.assertTrue(any(n!=0 for n in sound))

    async def test_pocketsphinx_can_decode_genuine_waveform_when_installed(self):
        try: recogniser=PocketSphinxASR()
        except SpeechError as e:
            if e.code in ('OFFLINE_ASR_UNAVAILABLE','OFFLINE_ASR_MODEL_MISSING'):
                self.skipTest('PocketSphinx language model not installed on CI')
            raise
        try:
            try:
                pcm=await EspeakTTS().speak('Hello how can I help you')
            except SpeechError as e:
                if e.code=='SYNTHESIS_UNAVAILABLE':self.skipTest('espeak/ffmpeg unavailable')
                raise
            text=await recogniser.transcribe(None, pcm)
            self.assertIsInstance(text,str)
            self.assertNotEqual(text,'')
            # We deliberately make no accuracy claim: offline small-vocabulary
            # decoders often mishear proper nouns and synthetic speech.
        finally:
            recogniser.close()

if __name__=='__main__':unittest.main()
