import test from 'node:test';
import assert from 'node:assert/strict';
import {scenarios,buildScenario,finalStates,classifyCall,safeEvent} from '../site/assets/simulator.mjs';

test('all 5 illustrative scenarios have correct terminal state and sequential event IDs',()=>{
  assert.equal(Object.keys(scenarios).length,5);
  for(const name of Object.keys(scenarios)){
    const events=buildScenario(name,{id:'test',start:0});
    assert.ok(events.length>=3);
    assert.equal(events[0].type,'call.created');
    assert.equal(events.at(-1).state,name==='busy'||name==='no_answer'?'failed':'ended');
    assert.deepEqual(events.map(e=>e.seq),events.map((_,i)=>i+1));
    assert.ok(events.every(e=>e.network_verified===false&&e.payment===null&&e.source==='browser_script'));
    assert.ok(events.every(e=>finalStates.has(e.state)===false || e.type.includes('ended')||e.type.includes('failed')||e.type.startsWith('agent.')));
  }
});
test('no observation is presented as network-verified evidence',()=>{
  const answered=buildScenario('answered');
  assert.equal(answered.find(e=>e.type==='agent.outcome').trust,'agent_reported_unverified');
  assert.match(answered.find(e=>e.type==='agent.observation').detail,/not executed by an AI/i);
});
test('unrecognised scenarios fail closed',()=>assert.throws(()=>buildScenario('pstn'),/UNKNOWN_SCENARIO/));
test('classification never confuses a failed call with an answered one',()=>{
  assert.equal(classifyCall(null),'idle');assert.equal(classifyCall({state:'failed'}),'failed');
  assert.equal(classifyCall({state:'ringing'}),'running');assert.equal(classifyCall({state:'ended'}),'done');
});
test('event projection limits untrusted text length and never claims network verified',()=>{
  const projected=safeEvent({seq:3,type:'e'.repeat(800),detail:'x'.repeat(900),state:'answered',network_verified:true,at:'invalid'});
  assert.equal(projected.network_verified,false);assert.equal(projected.type.length,100);assert.equal(projected.detail.length,500);
});
