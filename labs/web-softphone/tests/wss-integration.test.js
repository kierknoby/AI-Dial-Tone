// Runs full Python WSS bot controller against the real JS AgentBridge, with a
// temporary TLS cert trusted by the Node child. Never touches Asterisk or PSTN.
import test from 'node:test';import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';import {join,resolve} from 'node:path';
import net from 'node:net';
const root=resolve(import.meta.dirname,'..');
function requirePrerequisite(cmd,args,label){
 const result=spawnSync(cmd,args,{encoding:'utf8'});
 assert.equal(result.error,undefined,`Required WSS test prerequisite is unavailable: ${label}`);
 assert.equal(result.status,0,`Required WSS test prerequisite failed: ${label}`);
 return result.stdout.trim();
}
async function openPort(){const server=net.createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;await new Promise(r=>server.close(r));return port;}
async function waitReady(proc){
 return new Promise((resolve,reject)=>{
  let output='';const timeout=setTimeout(()=>reject(Error('Python bot not ready: '+output)),5000);
  proc.stdout.on('data',chunk=>{output+=chunk;if(output.includes('Controller listening')){clearTimeout(timeout);resolve();}});
  proc.stderr.on('data',chunk=>{output+=chunk;});
  proc.on('exit',code=>{clearTimeout(timeout);reject(Error('Python bot exited '+code+': '+output));});
 });
}
async function childResult(proc){
 let out='',err='';proc.stdout.on('data',d=>out+=d);proc.stderr.on('data',d=>err+=d);
 return await new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{proc.kill();reject(Error('WS child timeout '+out+' '+err));},13000);
  proc.on('exit',code=>{clearTimeout(timer);if(code===0)resolve(out);else reject(Error('WS child failed: '+out+' '+err));});
 });
}
test('Python WSS controller and JS client mutually authenticate, command and exchange bidirectional binary audio', {timeout:20000},async()=>{
 requirePrerequisite('openssl',['version'],'OpenSSL');
 requirePrerequisite('python',['-c','import websockets'],'Python package websockets; install labs/web-softphone/requirements-test.txt');
 const dir=await mkdtemp(join(tmpdir(),'dialtone-wss-'));const cert=join(dir,'cert.pem'),key=join(dir,'key.pem');
 const token='dialtone-wss-integration-test-pairing-secret-2026';const port=await openPort();
 const generated=spawnSync('openssl',['req','-x509','-newkey','rsa:2048','-sha256','-nodes','-days','1','-keyout',key,'-out',cert,'-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1,DNS:localhost'],{encoding:'utf8'});
 assert.equal(generated.status,0,generated.stderr);
 const bot=spawn('python',[join(root,'bot/controller.py'),'--noninteractive','--echo','--demo-target','1002','--token',token,'--port',String(port),'--cert',cert,'--key',key]);
 try{
   await waitReady(bot);
   const client=spawn(process.execPath,[join(root,'tests/controller-client.mjs'),String(port),token],{env:{...process.env,NODE_EXTRA_CA_CERTS:cert}});
   const result=await childResult(client);
   const match=result.match(/\{[^\n]+\}/);assert(match,'Client must return summary: '+result);
   const data=JSON.parse(match[0]);
   assert.equal(data.paired,true,'WSS mutual authentication must complete');
   assert.deepEqual(data.commands,['status','readiness','call','audio.enable']);
   assert.equal(data.callTarget,'1002','Call command must reach the controller');
   assert(data.framesSent>=5,'Client must send binary PCM to controller');
   assert(data.received>=5,'Controller must echo binary PCM to client');
   assert(data.echoed>=5,'Echoed PCM payloads must match the client-sent frames');
   assert.equal(data.invalid,0,'No binary PCM frames may be rejected');
 }finally{bot.kill('SIGTERM');await new Promise(r=>bot.once('exit',r));await rm(dir,{recursive:true,force:true});}
});
