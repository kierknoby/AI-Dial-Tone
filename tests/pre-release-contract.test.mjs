import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, stat} from 'node:fs/promises';
const read=async p=>readFile(new URL('../'+p,import.meta.url),'utf8');
const get=async p=>JSON.parse(await read(p));
const exists=async p=>stat(new URL('../site/'+p.slice(1),import.meta.url));

test('published interfaces are real static files, with local-only OpenAPI hosts',async()=>{
  const manifest=await get('site/agents.json');
  const reference=await get('site/api/reference.json');
  assert.equal(manifest.status,'technical_preview');
  assert.equal(manifest.origin,'https://ai.dial-tone.uk');
  assert.equal(manifest.product_definition.site_vs_source.repository_url,'https://github.com/kierknoby/AI-Dial-Tone');
  const interfaces=manifest.interface_availability;
  assert.equal(interfaces.length,5);
  for(const entry of interfaces){
    if(entry.url) await exists(entry.url);
    if(entry.spec) await exists(entry.spec);
    assert.equal(entry.callable_as_telephone_api??false,false);
    assert.notEqual(entry.server,'https://ai.dial-tone.uk');
  }
  const peer=await get('peer-lab/openapi.json');
  const byot=await get('byot/openapi.json');
  assert.deepEqual(await get('site/api/openapi.json'),peer);
  assert.deepEqual(await get('site/api/peer-lab-openapi.json'),peer);
  assert.deepEqual(await get('site/api/byot-openapi.json'),byot);
  assert.deepEqual(peer.servers.map(s=>s.url),['http://127.0.0.1:8765']);
  assert.deepEqual(byot.servers.map(s=>s.url),['http://127.0.0.1:8877']);
  assert.equal(reference.public_hosted_api,false);
  assert.equal(reference.live_pstn,false);
  assert.equal(reference.real_x402_facilitator,false);
  for(const path of Object.values(manifest.links)){
    if(path.startsWith('/'))await exists(path);
  }
  for(const path of Object.values(manifest.developer_paths)){
    if(path.startsWith('/'))await exists(path);
  }
});

test('agent-facing manifest refuses to promote design goals to deployed services',async()=>{
  const a=await get('site/agents.json');
  const safety=a.safety;
  assert.equal(safety.network_verified_events_available,false);
  assert.equal(safety.agent_claims_are_verified,false);
  assert.equal(safety.real_world_action_allowed,false);
  for(const name of ['public_live_calling','public_bidirectional_audio','hosted_mcp_server','hosted_a2a_agent','x402_payment','real_asterisk_interoperability_verified','real_x402_facilitator_or_settlement','experimental_byot_live_origination_default_enabled']){
    assert.equal(a.available_now[name],false,name);
  }
  assert.equal(a.product_definition.access_models.managed_calling.available_in_0_0_1,false);
  assert.equal(a.product_definition.access_models.bring_your_own_telecoms.real_PSTN_verified,false);
  assert.equal(a.product_definition.access_models.bring_your_own_telecoms.provider_controls_routing_and_termination,true);
  assert.equal(a.developer_demo.actual_pstn_call,false);
  assert.equal(a.developer_demo.actual_payment,false);
  assert.equal(a.developer_demo.real_world_booking,false);
  assert.equal(a.developer_demo.proof_scope,'local_bidirectional_pcm_and_session_termination_only');
  assert.equal(a.developer_demo.source_command,'python tools/verify_first_call.py --out demo-output');
  for(const name of ['site/agents.txt','site/llms.txt','AGENTS.md','content/docs/02-quickstart.md']) {
    assert.ok((await read(name)).includes('python tools/verify_first_call.py --out demo-output'),name);
  }
});

test('source, agent FAQ and release-evidence question counts cannot drift',async()=>{
  const data=await get('content/faqs.json');
  const published=await get('site/api/faqs.json');
  const evidence=await get('RELEASE-EVIDENCE.json');
  const actual=data.categories.reduce((n,c)=>n+c.items.length,0);
  assert.equal(published.total_questions,actual);
  assert.equal(evidence.faq_questions,actual);
  assert.equal(data.categories.length,evidence.faq_categories);
  assert.ok((await read('site/llms.txt')).includes(`(${actual} answers)`));
  assert.ok((await read('AGENTS.md')).includes(`${actual} questions`));
  assert.equal(published.public_live_calling,false);
});

test('release evidence separates the historical local snapshot from later public verification',async()=>{
  const evidence=await get('RELEASE-EVIDENCE.json');
  const beforePublication=evidence.initial_prepublication_state;
  assert.equal(beforePublication.captured_at,'2026-10-11');
  assert.equal(beforePublication.public_site_deployed,false);
  assert.equal(beforePublication.repository_created_remotely,false);
  const current=evidence.current_verification;
  assert.equal(current.repository.public,true);
  assert.equal(current.website.https_reachable,true);
  assert.equal(current.website.production_calling_available,false);
  assert.equal(current.website.real_payment_available,false);
  assert.equal(current.github_actions.conclusion,'success');
  assert.equal(current.github_actions.commit,'35348ad0d34bfb5e89b5f1db1a9b7d3eaca19536');
  assert.match(current.github_actions.scope_note,/predates the WSS hardening changes/);
  const baseline=current.baseline_test_counts;
  assert.equal(baseline.discovered,baseline.executed+baseline.skipped);
  assert.equal(baseline.passed,baseline.executed);
  assert.equal(baseline.failed,0);
  assert.equal(baseline.skipped,3);
});

test('website claims distinguish experimental Asterisk connector from live carrier acceptance',async()=>{
  const site=await read('site/status.html');
  const agent=await read('site/agents.html');
  const brief=await read('site/llms.txt');
  const source=await read('tools/build-site.py');
  const byot=await read('byot/README.md');
  const handoff=await read('integration/README.md');
  for(const status of [site,source]){
    assert.match(status,/Real Asterisk origination, two-way SIP media and network release<\/span><b class="status-wait">NOT VERIFIED/);
    assert.match(status,/Encrypted SIP\/SRTP and independent PBX-side call supervision<\/span><b class="status-wait">NOT IMPLEMENTED/);
  }
  assert.match(agent,/technical preview, not a live calling service/);
  assert.match(brief,/No verified real SIP\/PSTN origination/);
  assert.match(byot,/DISABLED BY DEFAULT/);
  assert.match(byot,/No real Asterisk, SIP trunk, PSTN call/);
  assert.match(handoff,/origination disabled|origination is disabled|disabled origination|disabled-origination|live origination is enabled/i);
});
