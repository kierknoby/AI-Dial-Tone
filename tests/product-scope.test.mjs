import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const read = file => readFile(new URL(file, import.meta.url),'utf8');
const json = async file => JSON.parse(await read(file));

test('one source of truth for public product scope and explicit not-live boundary',async()=>{
 const source=await json('../content/product-scope.json');
 const publicScope=await json('../site/api/product-scope.json');
 assert.deepEqual(publicScope,source);
 assert.equal(source.release_version,'0.0.1');
 for(const [k,v] of Object.entries(source.availability))assert.equal(v,false,k);
 for(const category of ['included_in_0_0_1','target_capabilities_not_yet_available','excluded_from_product_direction','deferred_or_not_decided']){
  assert.ok(source.decisions[category].length>=5,category);
  for(const item of source.decisions[category])assert.ok(item.name && item.boundary);
 }
 assert.equal(source.open_product_questions.length,15);
 const human=await read('../PRODUCT-SCOPE.md');
 for(const group of Object.values(source.decisions))for(const item of group)assert.ok(human.includes(`**${item.name}:**`),item.name);
});

test('site, agent discovery and repository link to same product decisions',async()=>{
 const scope=await read('../site/scope.html');
 const status=await read('../site/status.html');
 const readme=await read('../README.md');
 const roadmap=await read('../ROADMAP.md');
 const agents=await json('../site/agents.json');
 assert.match(scope,/TECHNICAL PREVIEW/);
 assert.match(scope,/None of the planned capabilities is a live service today/);
 assert.match(scope,/href="\/api\/product-scope.json"/);
 assert.match(status,/href="\/scope.html"/);
 assert.match(readme,/PRODUCT-SCOPE.md/);
 assert.match(roadmap,/PRODUCT-SCOPE.md/);
 assert.equal(agents.links.product_scope,'/scope.html');
 assert.equal(agents.links.product_scope_json,'/api/product-scope.json');
 assert.equal(agents.available_now.public_live_calling,false);
 assert.equal(agents.available_now.real_x402_facilitator_or_settlement,false);
});
