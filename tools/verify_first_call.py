#!/usr/bin/env python3
"""Run and independently check a locally simulated AI Dial-Tone first-call proof.

This verifies a two-peer, local audio transport experiment, never PSTN, payment,
ASR accuracy, a model-driven dialogue, or a real-world booking.
"""
import argparse
import asyncio
import hashlib
import json
import re
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'peer-lab' / 'examples'))


def validate(output: Path):
    proof_path = output / 'proof.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    receipt = proof['receipt']
    expected_identities = {'caller': 'assistant-model', 'peer': 'restaurant-peer'}
    if proof['local_websocket_agents'] != 2 or any(receipt[k + '_id'] != v for k, v in expected_identities.items()):
        raise ValueError('Independent local peer identities are missing or inconsistent')
    if receipt['state'] != 'ended' or receipt['reason'] != 'CALLER_HANGUP':
        raise ValueError('Local session did not end via caller hangup')
    if receipt['media'] != 'pcm16le_16khz_mono_20ms':
        raise ValueError('Unexpected audio contract')
    if receipt['evidence_scope'] != 'LAB_TRANSPORT_AND_AGENT_ASSERTIONS_ONLY':
        raise ValueError('Local evidence scope changed unexpectedly')
    for key in ('real_phone_call', 'real_booking_verified', 'payment_settled'):
        if receipt[key] is not False:
            raise ValueError(f'Receipt incorrectly asserts {key}')
    if not re.fullmatch('[a-f0-9]{64}', receipt['event_chain_sha256']):
        raise ValueError('Session event-chain hash is missing or malformed')
    if receipt['events'] < 3 or proof['dialogue'] != [
        {'speaker':'caller', 'text':'Hello. Could I book a table for two at seven thirty?'},
        {'speaker':'peer', 'text':'This is a test restaurant peer. No real table has been booked.'},
    ]:
        raise ValueError('Unexpected or incomplete scripted dialogue')
    if set(proof['wav_files']) != {'caller_heard', 'peer_heard'}:
        raise ValueError('Both received-audio files are required')
    audio_evidence = {}
    for name, sender in [('caller_heard', 'peer'), ('peer_heard', 'caller')]:
        path = (output / (name + '.wav')).resolve()
        # Validate the output directory, not arbitrary paths embedded in the proof file.
        if Path(proof['wav_files'][name]).resolve() != path or not path.is_file():
            raise ValueError(f'Audio file is missing or outside intended output: {name}')
        with wave.open(str(path), 'rb') as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                raise ValueError(f'Invalid PCM WAV format: {name}')
            frames = wav.getnframes()
            samples = wav.readframes(frames)
        if frames <= 16000 or not any(samples):
            raise ValueError(f'No meaningful received audio: {name}')
        if receipt['frames_by_role'][sender] < 50:
            raise ValueError(f'No meaningful transmitted frame evidence: {sender}')
        audio_evidence[name] = {
            'received_audio_frames':frames,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    result = {
        'status':'PASS', 'release':'0.0.1',
        'scope':'LOCAL_WEB_SOCKET_PCM_AND_SESSION_ONLY',
        'test_contains_two_independent_clients':True,
        'operator_bound_local_mandate_observed':True,
        'bidirectional_received_audio_verified':True,
        'local_session_ended':True,
        'real_pstn_call_verified':False,
        'real_payment_settlement_verified':False,
        'real_world_booking_verified':False,
        'real_model_or_asr_quality_verified':False,
        'carrier_release_verified':False,
        'receipt_event_hash_is_local_not_carrier_attestation':True,
        'audio':audio_evidence,
    }
    (output / 'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description='Run/verify a deliberately local and synthetic first-call proof')
    parser.add_argument('--out',default='demo-output',help='Output directory (default: demo-output)')
    parser.add_argument('--verify-only', action='store_true',help='Validate an existing proof without running the demo')
    args=parser.parse_args()
    output=Path(args.out).resolve()
    if not args.verify_only:
        try:
            from first_call import run_demo
        except ModuleNotFoundError as e:
            if e.name == 'aiohttp':
                parser.error("Missing dependency: run python -m pip install 'aiohttp==3.13.3'")
            raise
        asyncio.run(run_demo(output))
    try:
        result=validate(output)
    except (ValueError, KeyError, OSError, wave.Error, json.JSONDecodeError) as exc:
        print(f'FAIL: local demo proof rejected: {exc}',file=sys.stderr)
        raise SystemExit(1) from exc
    print('\nPASS: two received-audio WAV files and local session receipt verified.')
    print('Evidence: '+str(output/'verification.json'))
    print('NO PSTN CALL, PAYMENT, MODEL QUALITY OR BOOKING HAS BEEN VERIFIED.')
    return result


if __name__=='__main__':
    main()
