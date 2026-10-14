import test from 'node:test';
import assert from 'node:assert/strict';
import {AgentBridge} from '../src/agent-bridge.js';
import {VERSION,authKey,signProof,freshNonce,makeAudioPacket,AUDIO_DOWNLINK} from '../src/agent-protocol.js';
class FakeWebSocket {
 static OPEN=1;
 static last;
 constructor(url){this.url=url;this.readyState=0;this.bufferedAmount=0;this.sent=[];FakeWebSocket.last=this;}
 send(v){this.sent.push(v);}
 open(){this.readyState=1;this.onopen?.();}
 push(v){this.onmessage?.({data:typeof v==='string'||v instanceof ArrayBuffer?v:JSON.stringify(v)});}
 close(code,reason){this.readyState=3;this.closeInfo={code,reason};this.onclose?.();}
 messages(){return this.sent.filter(s=>typeof s==='string').map(JSON.parse);}
}
async function tick(){await new Promise(resolve=>setTimeout(resolve,5));}
async function waitFor(predicate, description, timeoutMs=1000){
 const deadline=Date.now()+timeoutMs;
 while(!predicate()){
  if(Date.now()>=deadline)assert.fail(`Timed out waiting for ${description}`);
  await tick();
 }
}
const TOKEN='testpairingtoken'.repeat(3);
async function pairedBridge(actions={}) {
 const bridge=new AgentBridge(actions);
 await bridge.connect('wss://localhost:8766/',TOKEN,{WebSocketClass:FakeWebSocket});
 const ws=FakeWebSocket.last;ws.open();
 const hello=ws.messages()[0],server=freshNonce(),key=await authKey(TOKEN);
 ws.push({version:VERSION,kind:'challenge',nonce:server,proof:await signProof(key,'server',hello.nonce,server)});
 await waitFor(()=>ws.messages()[1]?.kind==='proof','HMAC handshake proof');
 ws.push({version:VERSION,kind:'paired',accepted:true});
 await waitFor(()=>bridge.state==='PAIRED','pairing completion');return {bridge,ws};
}
test('handshake never transmits pairing token',async()=>{
 const {bridge,ws}=await pairedBridge();
 assert.equal(JSON.stringify(ws.sent).includes(TOKEN),false);
 assert.equal(ws.messages()[0].kind,'hello');bridge.close();
});
test('invalid server proof is rejected and never pairs',async()=>{
 const bridge=new AgentBridge({});await bridge.connect('wss://localhost/',TOKEN,{WebSocketClass:FakeWebSocket});
 const ws=FakeWebSocket.last;ws.open();ws.push({version:VERSION,kind:'challenge',nonce:freshNonce(),proof:'00'.repeat(32)});
 await waitFor(()=>bridge.state==='OFFLINE' && ws.closeInfo?.code===4001,'invalid server proof rejection');assert.equal(bridge.state,'OFFLINE');assert.equal(ws.closeInfo.code,4001);
});
test('commands execute with result correlation and dedupe',async()=>{
 let called=0;const {bridge,ws}=await pairedBridge({status:async()=>{called++;return {ok:true};}});
 const c={version:VERSION,kind:'command',id:'same',command:'status'};
 ws.push(c);await tick();ws.push(c);await tick();
 const replies=ws.messages().filter(m=>m.kind==='result');
 assert.equal(replies.length,2);assert.equal(called,1);assert.deepEqual(replies[0],replies[1]);bridge.close();
});
test('audio cannot transmit before enable, can after, halts on disable',async()=>{
 const {bridge,ws}=await pairedBridge({'audio.enable':async()=>({sampleRate:16000}),'audio.disable':async()=>({})});
 assert.equal(bridge.sendAudio(new ArrayBuffer(640)),false);
 ws.push({version:VERSION,kind:'command',id:'en',command:'audio.enable'});await tick();
 assert.equal(bridge.audioEnabled,true);assert.equal(bridge.sendAudio(new ArrayBuffer(640)),true);
 assert.equal(ws.sent.filter(s=>s instanceof ArrayBuffer).length,1);
 let recvd=0;bridge.setAudioSink(pcm=>{if(pcm.byteLength)recvd++;});
 ws.push(makeAudioPacket(AUDIO_DOWNLINK,new ArrayBuffer(640)));assert.equal(recvd,1);
 ws.push(new ArrayBuffer(40));assert.equal(bridge.metrics.invalid,1);
 ws.push({version:VERSION,kind:'command',id:'off',command:'audio.disable'});await tick();
 assert.equal(bridge.sendAudio(new ArrayBuffer(640)),false);bridge.close();
});
test('backpressure drops audio instead of queuing unbounded frames',async()=>{
 const {bridge,ws}=await pairedBridge({'audio.enable':async()=>({})});
 ws.push({version:VERSION,kind:'command',id:'en',command:'audio.enable'});await tick();
 ws.bufferedAmount=300000;assert.equal(bridge.sendAudio(new ArrayBuffer(640)),false);assert.equal(bridge.metrics.dropped,1);bridge.close();
});
test('forged command before pairing has no effect',async()=>{
 let called=0;const bridge=new AgentBridge({call:async()=>called++});
 await bridge.connect('wss://localhost/',TOKEN,{WebSocketClass:FakeWebSocket});
 const ws=FakeWebSocket.last;ws.open();ws.push({version:VERSION,kind:'command',id:'x',command:'call',target:'1002'});await tick();
 assert.equal(called,0);assert.equal(bridge.state,'OFFLINE');bridge.close();
});
test('same command id with changed arguments is rejected instead of replaying old success',async()=>{
 let called=0;const {bridge,ws}=await pairedBridge({call:async()=>{called++;return {state:'dialling'};}});
 ws.push({version:VERSION,kind:'command',id:'callid',command:'call',target:'1002'});
 await waitFor(()=>ws.messages().some(m=>m.kind==='result'&&m.id==='callid'),'first command result');
 ws.push({version:VERSION,kind:'command',id:'callid',command:'call',target:'1003'});
 await waitFor(()=>ws.messages().filter(m=>m.kind==='result'&&m.id==='callid').length===2,'duplicate-id rejection');
 const last=ws.messages().filter(m=>m.kind==='result').at(-1);
 assert.equal(last.error.code,'COMMAND_ID_REUSED');assert.equal(called,1);bridge.close();
});
