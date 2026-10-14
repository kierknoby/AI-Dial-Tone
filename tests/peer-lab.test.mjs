import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const at = rel => new URL(rel, import.meta.url);

test('AI Peer Lab is explicitly local, separated from static deployment and non-telephony', async () => {
  const src = await readFile(at('../peer-lab/peer_lab.py'),'utf8');
  const readme = await readFile(at('../peer-lab/README.md'),'utf8');
  const discovery = JSON.parse(await readFile(at('../site/agents.json'),'utf8'));
  assert.match(src,/NON_LOOPBACK_BINDING_FORBIDDEN/);
  assert.match(readme,/NOT a SIP telephone/);
  assert.equal(discovery.available_now.local_peer_voice_transport_demo,true);
  assert.equal(discovery.available_now.public_live_calling,false);
  assert.equal(discovery.available_now.public_bidirectional_audio,false);
  assert.equal(discovery.available_now.x402_payment,false);
  assert.equal(discovery.links.peer_lab_reference,'/docs/peer-lab.html');
});

test('documentation and CI ship runnable peer exchange rather than a promise', async () => {
  const doc=await readFile(at('../site/docs/peer-lab.html'),'utf8');
  const workflow=await readFile(at('../.github/workflows/verify.yml'),'utf8');
  const demo=await readFile(at('../peer-lab/examples/first_call.py'),'utf8');
  assert.match(doc,/eSpeak/);
  assert.match(doc,/Two independent/);
  assert.match(workflow,/npm run test:peer/);
  assert.match(workflow,/branches: \[main\]/);
  assert.match(demo,/client\.pcm/);
  assert.match(demo,/No real table has been booked/);
});

test('machine-readable Peer Lab spec exactly distinguishes localhost and separate agent simulator', async () => {
  const peer = JSON.parse(await readFile(at('../site/api/peer-lab-openapi.json'),'utf8'));
  const backend = JSON.parse(await readFile(at('../site/api/openapi.json'),'utf8'));
  assert.equal(peer.openapi,'3.1.0');
  assert.equal(peer.servers[0].url,'http://127.0.0.1:8765');
  assert.equal(peer['x-operational-boundaries'].public_hosted,false);
  assert.equal(peer['x-operational-boundaries'].telephone_routing,false);
  assert.ok(peer.paths['/v1/mandates/{mid}/revoke']);
  assert.ok(peer.paths['/v1/sessions/{sid}/stop']);
  assert.ok(peer.paths['/v1/sessions/{sid}/connect']);
  assert.equal(peer.paths['/v1/sessions/{sid}/connect'].get['x-websocket-admission'].frame_size,656);
  assert.ok(!peer.paths['/v1/calls']);
  assert.deepEqual(backend,peer);
  assert.equal(peer.info.version,'0.0.1');
});
