import test from 'node:test';import assert from 'node:assert/strict';import {server} from '../server.js';
async function withServer(fn){await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));try{return await fn('http://127.0.0.1:'+server.address().port);}finally{await new Promise(resolve=>server.close(resolve));}}
test('HTTP server serves all browser modules and has a restrictive CSP',async()=>withServer(async base=>{
 for(const path of ['/','/app.js','/agent-bridge.js','/agent-protocol.js','/rtc-metrics.js','/audio-worklet.js','/audio-codec.js','/bot-audio.js','/bot-session.js','/style.css','/vendor/sip.js']){
  const r=await fetch(base+path);assert.equal(r.status,200,path);assert((await r.text()).length>30);
  const csp=r.headers.get('content-security-policy');
  assert.match(csp,/script-src 'self'/);
  assert.doesNotMatch(csp,/esm\.sh/);
  assert.match(csp,/frame-ancestors 'none'/);
  assert.equal(r.headers.get('cache-control'),'no-store');
 }
}));
test('server refuses unknown paths, sensitive files and POST requests',async()=>withServer(async base=>{
 for(const u of ['/README.md','/package.json','/tests/protocol.test.js','/.env','/bot/controller.py']){
  assert.equal((await fetch(base+u)).status,404,u);
 }
 assert.equal((await fetch(base+'/',{method:'POST'})).status,404);
}));
