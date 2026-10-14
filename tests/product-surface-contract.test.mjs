import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const read=async path=>readFile(new URL('../'+path,import.meta.url),'utf8');

test('website describes one end-to-end product and developers without claiming a live service',async()=>{
 const home=await read('site/index.html');
 const agent=await read('site/agents.html');
 const dev=await read('site/developers.html');
 const ref=await read('site/docs/index.html');
 assert.match(home,/end-to-end, open-source calling platform/);
 assert.match(home,/<h1>Give your AI<br><em>Dial-Tone<\/em><\/h1>/);
 assert.match(agent,/one end-to-end service/i);
 assert.match(agent,/human authorisation/i);
 assert.match(agent,/telco independently approves admission/i);
 assert.match(agent,/provider-side release|authority to end the call|end the call/i);
 assert.match(agent,/the GitHub repository is the open-source implementation/i);
 assert.match(agent,/Version 0\.0\.1 is a technical preview, not a live calling service/);
 assert.match(dev,/end-to-end design spans discovery/i);
 assert.match(dev,/not a separate BYOT-only offering/i);
 assert.match(dev,/no live public calling API/i);
 assert.match(ref,/one end-to-end autonomous calling platform/i);
 assert.match(ref,/href="\/developers\.html"/);
});

test('machines see full product intent, developer capabilities, and honest live status',async()=>{
 const m=JSON.parse(await read('site/agents.json'));
 assert.equal(m.product_definition.scope,'end_to_end_autonomous_telephone_calling');
 assert.equal(m.product_definition.product_status,'designed_end_to_end_not_live');
 assert.deepEqual(m.product_definition.intended_agent_workflow,[
 'discover_calling_capability','obtain_server_verified_bounded_human_authorisation',
 'request_provider_call_admission_and_approved_route','satisfy_x402_if_managed_access_requires_it',
 'connect_and_exchange_bidirectional_audio','end_call_under_independent_telecoms_authority',
 'receive_network_events_cost_and_grounded_outcome']);
 assert.equal(m.product_definition.access_models.managed_calling.available_in_0_0_1,false);
 assert.equal(m.product_definition.access_models.bring_your_own_telecoms.real_PSTN_verified,false);
 assert.equal(m.available_now.public_live_calling,false);
 assert.equal(m.available_now.x402_payment,false);
 assert.ok(m.developer_paths.integrate_agent);
 assert.ok(m.developer_paths.bring_asterisk_freepbx);
 const agents=await read('site/agents.txt');
 const llms=await read('site/llms.txt');
 const full=await read('site/llms-full.txt');
 for(const doc of [agents,llms,full]){
  assert.match(doc,/end-to-end/i);
  assert.match(doc,/GitHub|repository/i);
  assert.match(doc,/0\.0\.1|technical preview/i);
 }
});
