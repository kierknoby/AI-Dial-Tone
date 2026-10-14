import os
import sys
import unittest
from aiohttp import ClientSession

sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from client import PeerClient
from peer_lab import Session, Mandate, MAX_EVENTS, ApiError


class SafetyContracts(unittest.TestCase):
    def test_no_credentials_sent_to_remote_unprotected_peer_lab(self):
        for address in ('http://attacker.example:8765','http://192.168.1.10:8765',
                        'https://api.dial-tone.uk','http://user:pass@localhost:8765'):
            with self.assertRaisesRegex(ValueError,'PEER_LAB_REQUIRES_LOOPBACK_HTTP'):
                PeerClient(None,address,'token','session')

    def test_terminal_event_is_still_possible_when_event_quota_exhausted(self):
        mandate=Mandate('m','c','p','test',9999,30)
        session=Session('s',mandate,0)
        session.event_log=[None]*MAX_EVENTS
        with self.assertRaisesRegex(ApiError,'EVENT_QUOTA_EXCEEDED'):
            session.emit('agent.utterance',text='another')
        result=session.emit('session.ended',reason='HARD_DEADLINE')
        self.assertEqual(result['type'],'session.ended')
