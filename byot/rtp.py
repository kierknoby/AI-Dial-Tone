"""RTP/L16 16-kHz mono adapter for Asterisk externalMedia (experimental).

The public agent wire format uses signed PCM16 *little* endian. RFC 3551
L16 RTP samples are network byte order. This adapter swaps sample bytes in
both directions and refuses unknown/inconsistent RTP streams.
"""
from __future__ import annotations

import asyncio
import secrets
import struct
import time
from dataclasses import dataclass

PCM_SAMPLES = 320
PCM_BYTES = 640
AGENT_HEADER = struct.Struct('!4sIQ')
RTP_HEADER = struct.Struct('!BBHII')


def swap16(buf: bytes) -> bytes:
    if len(buf) % 2:
        raise ValueError('ODD_SAMPLE_LENGTH')
    out = bytearray(len(buf))
    out[::2], out[1::2] = buf[1::2], buf[::2]
    return bytes(out)


def decode_rtp(packet: bytes):
    if len(packet) < 12:
        raise ValueError('SHORT_RTP')
    first, second, seq, stamp, ssrc = RTP_HEADER.unpack_from(packet)
    if first >> 6 != 2:
        raise ValueError('INVALID_RTP_VERSION')
    if 64 <= (second & 127) <= 95:  # 64-95 are dynamic/reserved depending on profile; not a hard codec rule.
        pass
    offset = 12 + (first & 15) * 4
    if offset > len(packet):
        raise ValueError('INVALID_RTP_CSRC')
    if first & 0x10:
        if len(packet) < offset + 4:
            raise ValueError('INVALID_RTP_EXTENSION')
        ext_words = struct.unpack_from('!H', packet, offset + 2)[0]
        offset += 4 + ext_words * 4
    if offset > len(packet):
        raise ValueError('INVALID_RTP_EXTENSION')
    data = packet[offset:]
    if first & 0x20:
        if not data or not 0 < data[-1] <= len(data):
            raise ValueError('INVALID_RTP_PADDING')
        data = data[:-data[-1]]
    if len(data) != PCM_BYTES:
        raise ValueError('UNEXPECTED_L16_FRAME')
    return second & 127, seq, stamp, ssrc, swap16(data)


@dataclass
class MediaCounters:
    inbound: int = 0
    outbound: int = 0
    rejected: int = 0
    dropped: int = 0


class RtpPort(asyncio.DatagramProtocol):
    """One-call UDP port; only the ARI-reported peer IP:port can send media.

    Asterisk must be on the same trusted host or a separately secured private
    network; RTP here has NO built-in encryption or integrity protection.
    """
    def __init__(self, receiver):
        self.receiver = receiver
        self.transport = None
        self.remote = None
        self.payload_type = None
        self.in_ssrc = None
        self.last_in_seq = None
        self.out_seq = secrets.randbelow(65536)
        self.out_stamp = secrets.randbelow(2**32)
        self.out_ssrc = secrets.randbelow(2**32)
        self.counters = MediaCounters()

    def connection_made(self, transport):
        self.transport = transport

    def set_remote(self, ip: str, port: int):
        if self.remote is not None:
            raise ValueError('RTP_PEER_ALREADY_LOCKED')
        if not (1 <= port <= 65535):
            raise ValueError('INVALID_RTP_PEER_PORT')
        self.remote = (ip, port)

    def datagram_received(self, data: bytes, addr):
        if self.remote is None or addr != self.remote:
            self.counters.rejected += 1
            return
        try:
            pt, seq, _stamp, ssrc, pcm = decode_rtp(data)
            if self.in_ssrc is None:
                self.in_ssrc = ssrc
                self.payload_type = pt
            if self.in_ssrc != ssrc or self.payload_type != pt:
                raise ValueError('RTP_STREAM_CHANGED')
            if self.last_in_seq is not None:
                diff = (seq - self.last_in_seq) & 0xffff
                if not (0 < diff < 32768):
                    raise ValueError('STALE_OR_REPLAYED_RTP')
            self.last_in_seq = seq
            self.counters.inbound += 1
            self.receiver(pcm)
        except (ValueError, IndexError, struct.error):
            self.counters.rejected += 1

    def send_pcm(self, pcm: bytes):
        if len(pcm) != PCM_BYTES:
            raise ValueError('INVALID_PCM_FRAME')
        if not self.transport or self.remote is None or self.payload_type is None:
            self.counters.dropped += 1
            return False
        pkt = RTP_HEADER.pack(0x80, self.payload_type, self.out_seq, self.out_stamp, self.out_ssrc) + swap16(pcm)
        self.transport.sendto(pkt, self.remote)
        self.out_seq = (self.out_seq + 1) & 0xffff
        self.out_stamp = (self.out_stamp + PCM_SAMPLES) & 0xffffffff
        self.counters.outbound += 1
        return True

    def close(self):
        if self.transport:
            self.transport.close()
            self.transport = None


async def bind_rtp(loop, *, host: str, receiver):
    port = RtpPort(receiver)
    transport, _ = await loop.create_datagram_endpoint(lambda: port, local_addr=(host, 0))
    return port, transport.get_extra_info('sockname')[1]
