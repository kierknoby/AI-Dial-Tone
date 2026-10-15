// Child process launched by WSS integration test with trusted ephemeral local CA.
import {AgentBridge} from '../src/agent-bridge.js';
const port=process.argv[2],token=process.argv[3];
let callTarget=null, received=0, echoed=0, paired=false, framesSent=0;
const expectedFrames=new Set(),commands=[];
const hex=buffer=>Array.from(new Uint8Array(buffer),value=>value.toString(16).padStart(2,'0')).join('');
const bridge=new AgentBridge({
 status:async()=>{commands.push('status');return {test:true};},
 readiness:async()=>{commands.push('readiness');return {local:'ready',pstn:'not tested'};},
 call:async target=>{commands.push('call');callTarget=target;return {state:'dialling'};},
 'audio.enable':async()=>{commands.push('audio.enable');return {format:'pcm16',rate:16000};}
},v=>{if(v==='PAIRED')paired=true;});
bridge.setAudioSink(pcm=>{
 if(pcm.byteLength!==640)return;
 received++;
 if(expectedFrames.delete(hex(pcm)))echoed++;
});
try{
 await bridge.connect(`wss://127.0.0.1:${port}/`,token);
 const start=Date.now();
 while(Date.now()-start<10000){
  if(bridge.audioEnabled&&framesSent<15){
   const pcm=new Uint8Array(640);
   for(let i=0;i<pcm.length;i++)pcm[i]=(framesSent*17+i)%256;
   expectedFrames.add(hex(pcm.buffer));
   if(!bridge.sendAudio(pcm.buffer))throw Error('PCM_UPLINK_REJECTED');
   framesSent++;
  }
  if(paired&&callTarget==='1002'&&echoed>=5)break;
  await new Promise(r=>setTimeout(r,25));
 }
 const result={paired,commands,callTarget,received,echoed,framesSent,invalid:bridge.metrics.invalid};
 console.log(JSON.stringify(result));bridge.close();
 if(!paired||commands.join(',')!=='status,readiness,call,audio.enable'||
    callTarget!=='1002'||framesSent<5||received<5||echoed<5)process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;bridge.close();}
