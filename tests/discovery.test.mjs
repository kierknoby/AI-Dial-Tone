import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {scenarios,buildScenario} from '../site/assets/simulator.mjs';
const root=resolve(new URL('../site/',import.meta.url).pathname);
const json=async path=>JSON.parse(await readFile(resolve(root,path),'utf8'));

test('machine-readable catalogue accurately excludes live PSTN, payments, and hosted agent protocols',async()=>{
  const capabilities=await json('agents.json');
  assert.equal(capabilities.status,'technical_preview');
  assert.equal(capabilities.available_now.public_live_calling,false);
  assert.equal(capabilities.available_now.x402_payment,false);
  assert.equal(capabilities.available_now.hosted_mcp_server,false);
  assert.equal(capabilities.available_now.hosted_a2a_agent,false);
  assert.equal(capabilities.available_now.machine_readable_scenarios,true);
  assert.equal(capabilities.safety.network_verified_events_available,false);
});

test('agent challenge documents point only to safe generated synthetic fixtures',async()=>{
  const challenge=await json('api/challenges.json');
  assert.equal(challenge.execution,'static_only');
  assert.equal(challenge.calling_available,false);
  assert.equal(challenge.required_registration,false);
  assert.equal(challenge.cases.length,Object.keys(scenarios).length);
  for(const item of challenge.cases){
    assert.match(item.fixture,/^\/api\/scenarios\/[a-z_]+\.json$/);
    const fixture=await json(item.fixture.slice(1));
    assert.equal(fixture.scenario,item.id);
    assert.equal(fixture.evidence_is_live,false);
    assert.equal(fixture.telephone_call_placed,false);
    assert.ok(fixture.events.length>=3);
    assert.ok(fixture.events.every(e=>e.network_verified===false&&e.payment===null&&e.source==='browser_script'));
    const expected=buildScenario(item.id,{id:`fixture-${item.id}`,start:0});
    assert.deepEqual(fixture.events,expected);
    assert.equal(item.expected_terminal_state,expected.at(-1).state);
  }
});

test('agent guidance does not claim false A2A, MCP, or payment endpoint availability',async()=>{
  const guide=await readFile(resolve(root,'agents.txt'),'utf8');
  const llms=await readFile(resolve(root,'llms.txt'),'utf8');
  assert.match(guide,/DOES NOT offer a publicly callable API/i);
  assert.match(guide,/x402 payments at present/i);
  assert.match(llms,/Machine-readable preview capability catalogue/);
  assert.ok(!(await readdir(resolve(root,'.'))).includes('.well-known'));
});
