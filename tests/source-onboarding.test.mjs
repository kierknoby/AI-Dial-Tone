import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir,stat} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const load=async path=>readFile(new URL(path,root),'utf8');

const sourceSlugs=['overview','quickstart','architecture','authentication','api','lifecycle','events','media','agents','provider','errors','challenge','readiness','peer-contract','human-journey','native-security','roadmap','peer-lab','audio-first-voice','byot-asterisk','x402-payment-admission','payment-telecom-handoff','faq','pre-call-principle','origins'];

test('all 25 Markdown source chapters have GitHub-valid relative links, with corresponding website links',async()=>{
  const files=(await readdir(new URL('content/docs/',root))).filter(f=>f.endsWith('.md')).sort();
  assert.equal(files.length,sourceSlugs.length);
  const full=await load('site/llms-full.txt');
  for(let i=0;i<files.length;i++){
    const content=await load('content/docs/'+files[i]);
    const web=await load('site/docs/'+sourceSlugs[i]+'.html');
    for(const match of content.matchAll(/\]\(([^)#]+)(#[^)]+)?\)/g)){
      const target=match[1];
      if(/^(https?:|mailto:|\/)/.test(target))continue;
      await stat(new URL('content/docs/'+target,root));
      assert.ok(target.endsWith('.md'),`${files[i]} has a website-only link: ${target}`);
      const slug=sourceSlugs[files.findIndex(name=>name===target)];
      assert.ok(slug,`${files[i]} links to an unrecognised chapter ${target}`);
      assert.ok(web.includes('href="/docs/'+slug+'.html'+(match[2]||'')+'"'),`${files[i]} generated page lost website link ${target}`);
      assert.ok(full.includes('](/docs/'+slug+'.html'+(match[2]||'')+')'),`agent guide lost website link ${target}`);
    }
  }
});

test('agent contributor entrypoint runs a real lab and explicitly refuses production claims',async()=>{
  const doc=await load('AGENTS.md');
  assert.match(doc,/python tools\/verify_first_call\.py --out demo-output/);
  assert.match(doc,/not hosted telephone endpoints/i);
  assert.match(doc,/origination \*\*OFF\*\*/);
  assert.match(doc,/payment fixture is not a settlement receipt/i);
  for(const name of ['peer-lab/README.md','byot/README.md','payments/README.md','integration/README.md','content/project-overview.md']){
    await stat(new URL(name,root));
  }
});

test('RTP media status never mistakes source-tuple pinning for authenticated/encrypted media',async()=>{
  const source=await load('byot/server.py');
  assert.ok(source.includes("'rtp_source_tuple_locked':True"));
  assert.ok(source.includes("'rtp_integrity_verified':False"));
  assert.ok(!source.includes('rtp_trusted_peer'));
});
