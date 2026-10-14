# Real-time media and framing

The current Peer Lab transports **actual PCM bytes** between two independent localhost clients over WebSocket. It does not generate or receive SIP RTP and has no verified PSTN audio.

## Binary packet (656 bytes)

| Byte offset | Size | Meaning |
| --- | --- | --- |
| 0 | 4 | ASCII magic `DT01` |
| 4 | 4 | Big-endian unsigned 32-bit per-sender sequence |
| 8 | 8 | Big-endian unsigned 64-bit timestamp in milliseconds |
| 16 | 640 | PCM16 little-endian, signed, mono, 16 kHz = 20 ms |

The server checks frame size, magic, strictly increasing sequence and per-role rate. A media frame is **not** a transcript and the timestamp comes from the sending client, not a trusted wall clock. PCM streams must be paced by the client. The local session duration is capped by the operator.

## Text and control messages

The WebSocket also carries `say` (unverified agent assertion), `dtmf` (a symbolic message, **not generated telephone tones**), `audio.end`, `audio.interrupt`, `hangup`, and `ping`. Receiving an interruption requests model/TTS cancellation; a real PSTN implementation still needs measured barge-in handling, jitter buffering, interruption race control and end-to-end audio quality tests.

For full wire examples, see [Peer Lab](18-peer-lab.md) and the downloadable [peer OpenAPI](/api/openapi.json). For the experimental audio processing pipeline, see [Audio-first Voice](19-audio-first-voice.md).

## Frame example

```python
import struct

# Exactly one 20-ms frame: 16 kHz, mono PCM16 little-endian.
samples = bytes(640)  # silence; not a real voice recording
packet = struct.pack('!4sIQ', b'DT01', 1, 0) + samples
assert len(packet) == 656
```

The `DT01` prefix is local Peer Lab framing. It is not an RTP, SIP or PSTN packet.
