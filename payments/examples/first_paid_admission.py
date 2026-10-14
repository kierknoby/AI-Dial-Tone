"""Print a REAL x402 v2 wire-shaped 402 challenge without transferring funds."""
import asyncio
import base64
import json
import os

from payments.x402 import GateConfig, X402Gate, BASE_SEPOLIA, USDC_SEPOLIA


class FakeFacilitator:
    """TEST FIXTURE. DO NOT USE WITH REAL CALLS OR TOKENS."""
    async def settle(self, payment_payload, requirements):
        if payment_payload['payload'].get('lab_only') is not True:
            return {'success': False, 'errorReason': 'not_lab_fixture'}
        return {'success': True, 'transaction': '0x' + 'ab'*32,
                'network': requirements['network'], 'payer': '0x'+'cd'*20}


async def main():
    secret = os.urandom(32).hex()
    gate = X402Gate(GateConfig(
        resource_origin='https://local-fixture.example.test',
        network=BASE_SEPOLIA, asset=USDC_SEPOLIA,
        pay_to='0x'+'12'*20, operator_secret=secret), FakeFacilitator())
    approved = await gate.operator_approve(
        bearer=secret, destination='+442079460123', max_seconds=30,
        amount_atomic=5000)
    challenged = await gate.challenge(approved['mandate_id'])
    requirement = json.loads(base64.b64decode(challenged['headers']['PAYMENT-REQUIRED']))
    print('HTTP', challenged['status'])
    print('PAYMENT-REQUIRED:', challenged['headers']['PAYMENT-REQUIRED'])
    print('Decoded x402 v2 terms:', json.dumps(requirement['accepts'][0], indent=2))
    print('WARNING: all addresses and facilitator responses are fictional lab fixtures; no funds move.')
    payload = {'x402Version': 2, 'resource': requirement['resource'],
               'accepted': requirement['accepts'][0],
               'payload': {'lab_only': True}, 'extensions': {}}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    result = await gate.settle_and_admit(approved['mandate_id'], encoded)
    admission = await gate.redeem(result['one_use_permit'])
    print('Lab admission:', json.dumps(admission, indent=2))
    assert admission['network_call_authorised'] is False
    print('No telephone call was attempted. No real x402 payment occurred.')


if __name__ == '__main__':
    asyncio.run(main())
