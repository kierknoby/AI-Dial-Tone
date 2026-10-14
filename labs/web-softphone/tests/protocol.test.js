import test from 'node:test';
import assert from 'node:assert/strict';
import {VERSION,validateAgentCommand,checkExtension,publicSnapshot,validateBridgeUrl,authKey,signProof,verifyProof,freshNonce,makeAudioPacket,decodeAudioPacket,AUDIO_UPLINK,AUDIO_DOWNLINK} from '../src/agent-protocol.js';
import {pcm16ToFloat,floatToPcm16,Resampler} from '../src/audio-codec.js';

const command=(name,target)=>({version:VERSION,kind:'command',id:'1',command:name,...(target?{target}:{})});
test('v2 command accepts only supported actions',()=>{
 for(const name of ['status','readiness','diagnostics','call','hangup','audio.enable','audio.disable','audio.flush']){
  assert.equal(validateAgentCommand(command(name,name==='call'?'1002':null)).command,name);
 }
 assert.throws(()=>validateAgentCommand(command('shell')));
});
test('rejects malformed ids, extra fields and target injection',()=>{
 for(const v of [{...command('call','100@evil')},{...command('hangup'),target:'1002'},{...command('status'),secret:'hijack'},{...command('status'),id:'<bad>'},{...command('call','+447700900123')}])assert.throws(()=>validateAgentCommand(v));
});
test('operator explicit allowlist enforced',()=>{assert.equal(checkExtension('1002',['1002']),'1002');for(const t of ['1003','999','+441234567890','*43','1002@evil'])assert.throws(()=>checkExtension(t,['1002']));});
test('public snapshot excludes secrets and PSTN capability',()=>{const result=publicSnapshot({registered:true,password:'no-show',media:true});assert.equal(JSON.stringify(result).includes('no-show'),false);assert.equal(result.pstn,'not enabled');});
test('WSS only, without URL credentials, fragments or query tokens',()=>{
 assert.equal(validateBridgeUrl('wss://controller.example:8766/'),'wss://controller.example:8766/');
 for(const u of ['ws://localhost/','http://host','wss://user:pass@host/','wss://host/?token=x','wss://host/#secret'])assert.throws(()=>validateBridgeUrl(u));
});
test('HMAC challenge uses two nonces and role binding',async()=>{
 const k=await authKey('a'.repeat(48)),c=freshNonce(),s=freshNonce();
 const server=await signProof(k,'server',c,s),client=await signProof(k,'client',c,s);
 assert.notEqual(server,client);
 assert.equal(await verifyProof(k,'server',c,s,server),true);
 assert.equal(await verifyProof(k,'client',c,s,server),false);
 assert.equal(await verifyProof(k,'server',c,freshNonce(),server),false);
 assert.equal(await verifyProof(k,'server',c,s,'00'.repeat(32)),false);
 await assert.rejects(()=>authKey('short'));
});
test('binary audio frames have exact size and direction',()=>{
 const original=new ArrayBuffer(640);new Uint8Array(original).fill(125);
 const data=makeAudioPacket(AUDIO_UPLINK,original);
 assert.equal(data.byteLength,641);
 assert.deepEqual(new Uint8Array(decodeAudioPacket(data,AUDIO_UPLINK)),new Uint8Array(original));
 assert.throws(()=>decodeAudioPacket(data,AUDIO_DOWNLINK));
 assert.throws(()=>makeAudioPacket(AUDIO_UPLINK,new ArrayBuffer(40)));
});
test('PCM16 roundtrip preserves sign and clipping',()=>{
 const arr=new Float32Array([-1,-0.25,0,0.25,1,3,NaN]);
 const restored=pcm16ToFloat(floatToPcm16(arr));
 assert.equal(restored.length,arr.length);assert(restored[0]<-.999);assert(restored[4]>.999);assert.equal(restored[5],restored[4]);assert.equal(restored[6],0);
});
test('resampler continuous 48 kHz chunks -> 16 kHz with bounded shape',()=>{
 const r=new Resampler(48000,16000),chunks=[];
 for(let c=0;c<150;c++){
  const part=new Float32Array(128);
  for(let j=0;j<128;j++)part[j]=Math.sin((c*128+j)*2*Math.PI*1000/48000);
  chunks.push(r.feed(part));
 }
 const out=Float32Array.from(chunks.flatMap(a=>Array.from(a)));
 assert(out.length>=6398 && out.length<=6400);
 let sum=0;for(const p of out)sum+=p*p;
 const rms=Math.sqrt(sum/out.length);
 assert(rms>.6 && rms<.73);
});
test('errors redact arbitrary exception messages before returning to bot',async()=>{
 const {makeResult}=await import('../src/agent-protocol.js');
 assert.equal(makeResult('x',null,{code:'username:secret@sip.example'}).error.code,'ACTION_FAILED');
 assert.equal(makeResult('x',null,{code:'TARGET_NOT_ALLOWLISTED'}).error.code,'TARGET_NOT_ALLOWLISTED');
});
