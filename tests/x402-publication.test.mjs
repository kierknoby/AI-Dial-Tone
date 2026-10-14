import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,stat} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const read=async(path)=>readFile(new URL(path,root),'utf8');
const json=async(path)=>JSON.parse(await read(path));

test('x402 is a local admission fixture, never advertised as a public payment endpoint',async()=>{
  const a=await json('site/agents.json');
  const ref=await json('site/api/reference.json');
  assert.equal(a.available_now.x402_payment,false);
  assert.equal(a.available_now.local_x402_v2_payment_admission_fixture,true);
  assert.equal(a.available_now.real_x402_facilitator_or_settlement,false);
  assert.equal(ref.x402_settlement,false);
  assert.equal(ref.real_x402_facilitator,false);
  assert.equal(ref.public_hosted_api,false);
  assert.equal(a.links.local_x402_lab_reference,'/docs/x402-payment-admission.html');
  await stat(new URL('site/docs/x402-payment-admission.html',root));
});

test('x402 specification documentation discloses upfront-charge failure and refund risk',async()=>{
  const doc=await read('content/docs/21-x402-payment-admission.md');
  const lib=await read('payments/README.md');
  assert.match(doc,/No merchant endpoint, real facilitator, real USDC transfer/);
  assert.match(doc,/fixed-price/);
  assert.match(doc,/FreePBX\/PJSIP/);
  assert.match(doc,/BYOT/);
  assert.match(lib,/upfront payment can settle even when a subsequent call cannot connect/);
  assert.match(lib,/No actual USDC transfer/i);
  assert.match(lib,/one-use permit/);
});

test('public payment layer cannot originate phone calls or load commercial configuration',async()=>{
  const source=await read('payments/x402.py');
  const policy=await read('REPOSITORY-POLICY.md');
  assert.match(source,/network_call_authorised': False/);
  assert.match(source,/real_call_started': False/);
  assert.ok(!source.includes('ARI_PASSWORD'));
  assert.ok(!source.includes('PJSIP_TRUNK'));
  assert.match(policy,/private/i);
});
