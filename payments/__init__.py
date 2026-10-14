"""Local, non-custodial x402 v2 call-admission research component.

No blockchain wallet, facilitator credentials, SIP or telecom implementation.
"""
from .x402 import X402Gate, GateConfig, GateError

__all__ = ['X402Gate', 'GateConfig', 'GateError']
