import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const load=(p)=>readFile(new URL(p,root),'utf8');
const data=async p=>JSON.parse(await load(p));

test('BYOT is a distinct self-hosted contract and is not served as the Peer Lab API',async()=>{
 const agent=await data('site/agents.json');
 const byot=await data('site/api/byot-openapi.json');
 const peer=await data('site/api/openapi.json');
 assert.equal(agent.available_now.public_live_calling,false);
 assert.equal(agent.available_now.experimental_self_hosted_asterisk_connector,true);
 assert.equal(agent.available_now.real_asterisk_interoperability_verified,false);
 assert.equal(byot.servers[0].url,'http://127.0.0.1:8877');
 assert.equal(byot.info.version,'0.0.1');
 assert.ok(byot.paths['/v1/readiness']);
 assert.ok(byot.paths['/v1/calls']);
 assert.ok(byot.paths['/v1/calls/{call_id}/media']);
 assert.ok(!peer.paths['/v1/calls']);
 assert.deepEqual(byot, await data('byot/openapi.json'));
});
test('BYOT never enables calls without explicit operator and configuration gates',async()=>{
 const server=await load('byot/server.py');
 const readme=await load('byot/README.md');
 assert.match(server,/allow_origination: bool = False/);
 assert.match(server,/AIDT_ENABLE_LIVE_ORIGINATION/);
 assert.match(server,/GEOGRAPHIC_RE/);
 assert.match(server,/call\.state='admitted'/);
 assert.match(server,/require_qualified_endpoint: bool = True/);
 assert.match(server,/carrier_release_verified':False/);
 assert.match(readme,/simulated-Asterisk HTTP|simulated ARI HTTP|simulated Asterisk/i);
 assert.match(readme,/NOT.*production|not.*production/i);
});
test('BYOT local media protocol uses the public DT01 frame but no native SIP source',async()=>{
 const rtp=await load('byot/rtp.py');
 const client=await load('byot/client.py');
 const readme=await load('README.md');
 assert.match(rtp,/AGENT_HEADER = struct\.Struct\('!4sIQ'\)/);
 assert.match(rtp,/swap16/);
 assert.match(client,/b'DT01'/);
 assert.match(readme,/Bring Your Own Telecoms/);
 assert.doesNotMatch(rtp,/MicroSIP-3\.22|#include "pjsip/);
});

test('BYOT is directly discoverable from homepage, developer pages and the reference hub',async()=>{
 const home=await load('site/index.html');
 const developers=await load('site/developers.html');
 const reference=await load('site/docs/index.html');
 for(const [name,html] of [['homepage',home],['developers',developers],['reference',reference]]){
  assert.match(html,/href="\/docs\/byot-asterisk\.html"/,name+' must link to BYOT');
 }
 assert.match(developers,/Your Asterisk\./);
 assert.match(developers,/python -m byot\.server --check-config/);
 assert.match(developers,/Calling is disabled by default/);
 assert.match(developers,/not a live Asterisk, SIP trunk, or PSTN interoperability test/);
 assert.match(developers,/An operator issues a one-use destination-and-duration mandate/);
 assert.match(home,/Bring your own telecoms: how it works/);
});

test('BYOT publication states independent telecoms routing and teardown authority',async()=>{
 const developers=await load('site/developers.html');
 const guide=await load('content/docs/20-byot-asterisk.md');
 const readme=await load('byot/README.md');
 assert.match(developers,/The human permits the task; the PBX or telco independently controls/);
 assert.match(developers,/does not create or remove PBX routes for individual calls/);
 assert.match(guide,/does not create, edit or remove PBX outbound routes/);
 assert.match(guide,/independent, PBX-side hard timeout/);
 assert.match(guide,/not a completed 0\.0\.1 feature/);
 assert.match(readme,/does not authorise PSTN egress on its own/);
 assert.match(readme,/carrier has released the call/);
});
