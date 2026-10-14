import os
import sys
import tempfile
import unittest
import wave
import json
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from first_call import run_demo
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from verify_first_call import validate


class EndToEndVoiceDemo(unittest.IsolatedAsyncioTestCase):
    async def test_two_independent_agents_have_audible_exchange_with_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result = await run_demo(Path(directory))
            verification=validate(Path(directory))
            self.assertEqual(verification['status'],'PASS')
            self.assertTrue(verification['bidirectional_received_audio_verified'])
            self.assertFalse(verification['real_pstn_call_verified'])
            receipt=result['receipt']
            self.assertEqual(receipt['state'],'ended')
            self.assertEqual(receipt['reason'],'CALLER_HANGUP')
            self.assertEqual(receipt['frames_by_role']['caller']>50,True)
            self.assertEqual(receipt['frames_by_role']['peer']>50,True)
            self.assertEqual(len(result['dialogue']),2)
            self.assertFalse(receipt['real_phone_call'])
            self.assertFalse(receipt['real_booking_verified'])
            for item in result['wav_files'].values():
                with wave.open(item,'rb') as handle:
                    self.assertEqual(handle.getframerate(),16000)
                    self.assertEqual(handle.getnchannels(),1)
                    self.assertGreater(handle.getnframes(),16000)
                    data=handle.readframes(handle.getnframes())
                    self.assertTrue(any(b!=0 for b in data),'audio unexpectedly silent')

    async def test_verifier_rejects_forged_network_success(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            await run_demo(output)
            path=output/'proof.json'
            source=json.loads(path.read_text())
            source['receipt']['real_phone_call']=True
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'real_phone_call'):
                validate(output)

    async def test_verifier_rejects_missing_received_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            await run_demo(output)
            (output/'peer_heard.wav').unlink()
            with self.assertRaisesRegex(ValueError, 'Audio file is missing'):
                validate(output)
