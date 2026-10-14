import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, stat, readdir} from 'node:fs/promises';
import {join, resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=fileURLToPath(new URL('../site/',import.meta.url));
const docs=join(root,'docs');
const load=async name=>readFile(join(root,name),'utf8');
const json=async name=>JSON.parse(await load(name));

const expected=['overview','quickstart','architecture','authentication','api','lifecycle','events','media','agents','provider','errors','challenge','readiness','peer-contract','human-journey','native-security','roadmap','peer-lab','audio-first-voice','byot-asterisk','x402-payment-admission','payment-telecom-handoff','faq','pre-call-principle','origins'];

test('all generated reference chapters have one H1, meaningful examples and preview notice',async()=>{
  for(const slug of expected){
    const h=await load(`docs/${slug}.html`);
    assert.equal((h.match(/<h1\b/g)||[]).length,1,slug);
    assert.match(h,/TECHNICAL PREVIEW/,slug);
    assert.match(h,/NOT LIVE TELEPHONY/,slug);
    assert.match(h,/href="\/llms-full\.txt"/,slug);
    assert.match(h,/href="\/docs\/index\.html"/,slug);
    assert.match(h,/\<main id="main"\>/,slug);
    assert.ok(h.length>6500,slug);
  }
  assert.equal((await readdir(docs)).filter(x=>x.endsWith('.html')).length,expected.length+1);
});

test('machine-readable docs cross-reference actual experimental OpenAPI paths',async()=>{
  const structured=await json('api/reference.json');
  const api=await json('api/openapi.json');
  assert.equal(structured.public_hosted_api,false);
  assert.equal(structured.live_pstn,false);
  assert.equal(structured.self_hosted_experimental_byot,true);
  assert.equal(structured.byot_interoperability_tested_on_real_asterisk,false);
  assert.equal(structured.byot_local_spec,'/api/byot-openapi.json');
  assert.equal(structured.x402_settlement,false);
  assert.equal(structured.x402_lab_local_only,true);
  assert.equal(structured.real_x402_facilitator,false);
  assert.equal(structured.hosted_mcp,false);
  assert.equal(structured.documented_backend,'public-local-peer-lab');
  assert.equal(structured.release_version,'0.0.1');
  assert.equal(structured.media.frame_magic,'DT01');
  assert.equal(structured.docs.length,expected.length);
  for(const {path,title} of structured.docs){
    assert.match(path,/^\/docs\/[a-z0-9-]+\.html$/);
    assert.ok(title.length>4);
    await stat(join(root,path.slice(1)));
  }
  const swagger=new Set(Object.keys(api.paths));
  for(const operation of structured.routes){
    const canonical=operation.path.split('?')[0];
    assert.ok(swagger.has(canonical),`Missing public lab route ${canonical}`);
  }
});

test('agent discovery points to full documentation and never offers a hosted calling service',async()=>{
  const manifest=await json('agents.json');
  assert.equal(manifest.links.complete_agent_reference,'/llms-full.txt');
  assert.equal(manifest.links.developer_reference,'/docs/index.html');
  assert.equal(manifest.links.json_api_reference,'/api/reference.json');
  assert.equal(manifest.available_now.public_live_calling,false);
  const full=await load('llms-full.txt');
  assert.ok(full.length>20000);
  for(const topic of ['HTTP API: runnable local Peer Lab','Session lifecycle','Real-time media','MCP','Authentication','Release readiness']){
    assert.ok(full.includes(topic),`Missing ${topic}`);
  }
  assert.match(full,/NOT A LIVE CALLING SERVICE/);
});

test('all internal documentation links resolve, including source Markdown relative navigation',async()=>{
  for(const slug of expected){
    const markup=await load(`docs/${slug}.html`);
    const source=join(docs,`${slug}.html`);
    for(const match of markup.matchAll(/href="([^"#?]+)(?:#[^"]*)?"/g)){
      const href=match[1];
      if(!href || /^(?:https?:|mailto:|data:)/.test(href))continue;
      if(href.startsWith('/'))await stat(join(root,href.slice(1)));
      else await stat(resolve(dirname(source),href));
    }
  }
});

test('API auth examples never embed usable tokens or remote agent endpoints',async()=>{
  const reference=await load('llms-full.txt');
  assert.ok(!/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(reference));
  assert.ok(!/sk-proj-[A-Za-z0-9]{12}/.test(reference));
  assert.match(reference,/127\.0\.0\.1:8765/);
  assert.ok(!reference.includes('POST https://ai.dial-tone.uk/v1/calls'));
  assert.ok(!reference.includes('dialtone-agent-lab-v0.7'));
  assert.ok(!reference.includes('source under ai/peer-lab'));
});
