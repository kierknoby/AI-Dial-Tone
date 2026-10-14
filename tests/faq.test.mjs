import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,stat} from 'node:fs/promises';
const source=async path=>readFile(new URL('../'+path,import.meta.url),'utf8');
const json=async path=>JSON.parse(await source(path));

test('FAQ is a substantive, single-source 0.0.1 reference with eight categories',async()=>{
  const data=await json('content/faqs.json');
  const published=await json('site/api/faqs.json');
  assert.equal(data.version,'0.0.1');
  assert.equal(published.total_questions,63);
  assert.equal(published.public_live_calling,false);
  assert.equal(published.real_x402_settlement,false);
  assert.equal(published.hosted_mcp,false);
  assert.equal(data.categories.length,8);
  assert.deepEqual(published.categories,data.categories);
  const ids=new Set();
  for(const category of data.categories){
    assert.ok(category.items.length>=6);
    for(const entry of category.items){
      assert.ok(entry.answer.length>70,entry.question);
      assert.ok(!ids.has(entry.id),entry.id);ids.add(entry.id);
      assert.match(entry.read_more,/^\/[a-z0-9/.-]+$/);
      await stat(new URL('../site/'+entry.read_more.slice(1),import.meta.url));
    }
  }
  assert.equal(ids.size,63);
});

test('FAQ web page has all questions, accessible search and native details fallbacks',async()=>{
  const html=await source('site/faqs.html');
  const md=await source('content/docs/23-faq.md');
  const manifest=await json('site/agents.json');
  assert.equal((html.match(/<details class="faq-item"/g)||[]).length,63);
  assert.equal((html.match(/<summary>/g)||[]).length,63);
  assert.match(html,/<input id="faq-search" type="search"/);
  assert.match(html,/id="faq-count" role="status" aria-live="polite"/);
  assert.match(html,/href="\/assets\/faq.css"/);
  assert.match(html,/src="\/assets\/faq.js"/);
  assert.match(md,/^# Frequently asked questions/m);
  assert.equal((md.match(/^### /gm)||[]).length,63);
  assert.equal(manifest.links.faq_page,'/faqs.html');
  assert.equal(manifest.links.faq_agent_json,'/api/faqs.json');
});

test('integrated handoff is never a hosted calling/payment route or a live-call unlock',async()=>{
  const code=await source('integration/handoff.py');
  const doc=await source('content/docs/22-payment-telecom-handoff.md');
  const ci=await source('.github/workflows/verify.yml');
  assert.match(code,/LIVE_CALLS_MUST_REMAIN_DISABLED/);
  assert.match(code,/self\.gate\.redeem\(permit\)/);
  assert.match(code,/BYOT_MANDATE_NOT_BOUND/);
  assert.match(code,/http.*request/);
  assert.match(doc,/NOT LIVE TELEPHONY OR SETTLEMENT/);
  assert.match(ci,/npm run test:handoff/);
  const manifest=await json('site/agents.json');
  assert.equal(manifest.available_now.public_live_calling,false);
  assert.equal(manifest.available_now.local_operator_side_x402_to_byot_handoff,true);
});
