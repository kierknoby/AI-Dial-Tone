import struct
import unittest
from vad import EnergyVAD
class EnergyVADTest(unittest.TestCase):
    def test_speech_start_stop_hysteresis(self):
        vad=EnergyVAD()
        speaking=struct.pack('<320h',*[8000]*320)
        silent=bytes(640)
        self.assertIsNone(vad.feed(speaking));self.assertIsNone(vad.feed(speaking))
        self.assertEqual(vad.feed(speaking),'speech.start')
        self.assertTrue(vad.talking)
        for i in range(19):self.assertIsNone(vad.feed(silent))
        self.assertEqual(vad.feed(silent),'speech.end')
        self.assertFalse(vad.talking)
    def test_short_noise_does_not_trigger(self):
        vad=EnergyVAD()
        loud=struct.pack('<320h',*[16000]*320)
        self.assertIsNone(vad.feed(loud))
        self.assertIsNone(vad.feed(bytes(640)))
        self.assertIsNone(vad.feed(loud))
        self.assertFalse(vad.talking)
    def test_invalid_pcm_fails(self):
        with self.assertRaises(ValueError):EnergyVAD().feed(bytes(6400))
if __name__=='__main__':unittest.main()
