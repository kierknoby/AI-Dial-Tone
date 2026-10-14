import test,{after,before} from 'node:test';
import assert from 'node:assert/strict';
import {request as httpRequest} from 'node:http';
import {server} from '../tools/serve.mjs';
let origin;
before(async()=>{await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin=`http://127.0.0.1:${server.address().port}`;});
after(async()=>{await new Promise(resolve=>server.close(resolve));});
test('home and four secondary pages return static HTML with safe headers',async()=>{
  for(const path of ['/', '/playground.html','/developers.html','/agents.html','/humans.html','/roadmap.html','/trust.html','/status.html']){
    const r=await fetch(origin+path);assert.equal(r.status,200,path);
    assert.match(r.headers.get('content-security-policy'),/default-src 'none'/);
    assert.equal(r.headers.get('x-frame-options'),'DENY');
    assert.match(await r.text(),/<main id="main">/);
  }
});
test('machine-readable OpenAPI is valid and clearly local-only',async()=>{
  const r=await fetch(origin+'/api/openapi.json');assert.equal(r.status,200);
  const obj=await r.json();assert.equal(obj.openapi,'3.1.0');assert.match(obj.servers[0].url,/127\.0\.0\.1/);
  assert.ok(obj.paths['/v1/sessions']);assert.ok(!obj.paths['/v1/calls']);assert.equal(obj.info.version,'0.0.1');
});
test('static server exposes no private lab proxy, dotfiles or caller credentials',async()=>{
  assert.equal((await fetch(origin+'/lab-api/meta')).status,404);
  assert.equal((await fetch(origin+'/lab-api/calls',{method:'POST',headers:{'Origin':'https://untrusted.example'}})).status,405);
  assert.equal((await fetch(origin+'/.env')).status,404);
  assert.equal((await fetch(origin+'/tools/serve.mjs')).status,404);
  assert.equal((await fetch(origin+'/api/peer-lab-openapi.json')).status,200);
  const head=await fetch(origin+'/agents.json',{method:'HEAD'});assert.equal(head.status,200);assert.equal(await head.text(),'');
});
test('host-header spoofing forbidden, static response cannot originate calls',async()=>{
  const spoof=await new Promise(resolve=>{const req=httpRequest(origin+'/',{headers:{Host:'attacker.invalid'}},res=>{res.resume();resolve(res.statusCode);});req.end();});
  assert.equal(spoof,403);
  assert.equal((await fetch(origin+'/v1/sessions',{method:'POST',body:'{}'})).status,405);
});
test('missing pages use a designed 404',async()=>{
  const r=await fetch(origin+'/not-an-endpoint');assert.equal(r.status,404);assert.match(await r.text(),/doesn.t connect/);
});

test('static agent discovery is fetchable without login or payment',async()=>{
  for(const path of ['/agents.json','/agents.txt','/llms.txt','/api/challenges.json','/api/scenarios/busy.json','/contracts/mandate.schema.json','/contracts/peer-event.schema.json']){
    const result=await fetch(origin+path);
    assert.equal(result.status,200,path);
    assert.equal(result.headers.get('x-content-type-options'),'nosniff');
    if(path.endsWith('.json')) await result.json();
  }
});

test('all real HTTP documentation pages and agent-facing assets load with correct MIME and security headers',async()=>{
  const {readdir}=await import('node:fs/promises');
  const {join}=await import('node:path');
  const {fileURLToPath}=await import('node:url');
  const root=fileURLToPath(new URL('../site/',import.meta.url));
  const items=[];
  async function collect(dir,rel=''){
    for(const e of await readdir(dir,{withFileTypes:true})){
      const relative=rel ? rel+'/'+e.name : e.name;
      if(e.isDirectory())await collect(join(dir,e.name),relative);
      else if(/\.(?:html|css|js|mjs|json|webmanifest|txt|svg)$/.test(e.name))items.push(relative);
    }
  }
  await collect(root);
  let tested=0;
  for(const pathname of items){
    const r=await fetch(origin+'/'+pathname);
    assert.equal(r.status,200,pathname);
    const expected=pathname.endsWith('.html')?'text/html':pathname.endsWith('.css')?'text/css':
      pathname.endsWith('.json')?'application/json':pathname.endsWith('.svg')?'image/svg+xml':
      pathname.endsWith('.txt')?'text/plain':pathname.endsWith('.webmanifest')?'application/manifest+json':'text/javascript';
    assert.ok(r.headers.get('content-type').startsWith(expected),`${pathname} MIME ${r.headers.get('content-type')}`);
    assert.match(r.headers.get('content-security-policy'),/script-src 'self'/,pathname);
    assert.equal(r.headers.get('x-content-type-options'),'nosniff');
    await r.arrayBuffer();
    tested++;
  }
  assert.ok(tested>=60,`Insufficient real HTTP coverage (${tested} files)`);
});
