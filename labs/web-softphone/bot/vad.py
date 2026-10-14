"""Lightweight framing-level voice activity detector for lab interruption tests.
Not speech recognition, diarisation, or a substitute for an acoustic VAD model.
"""
import math
import struct

class EnergyVAD:
    def __init__(self, threshold=0.02, start_frames=3, end_frames=20):
        self.threshold=threshold
        self.start_frames=start_frames
        self.end_frames=end_frames
        self.talking=False
        self.voiced=0
        self.silent=0

    def feed(self, pcm):
        if not isinstance(pcm, bytes) or len(pcm)!=640:
            raise ValueError('Expected 20 ms of 16kHz mono PCM16')
        power=sum((sample/32768)**2 for (sample,) in struct.iter_unpack('<h',pcm))/320
        rms=math.sqrt(power)
        if rms>=self.threshold:
            self.voiced+=1;self.silent=0
            if not self.talking and self.voiced>=self.start_frames:
                self.talking=True;return 'speech.start'
        else:
            self.silent+=1;self.voiced=0
            if self.talking and self.silent>=self.end_frames:
                self.talking=False;return 'speech.end'
        return None
