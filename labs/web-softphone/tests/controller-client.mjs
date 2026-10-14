// Child process launched by WSS integration test with trusted ephemeral local CA.
import {AgentBridge} from '../src/agent-bridge.js';
import {VERSION} from '../src/agent-protocol.js';
const port=process.argv[2],token=process.argv[3];
let callTarget=null, received=0, paired=false, enabled=false, framesSent=0;
const bridge=new AgentBridge({
 status:async()=>({test:true}),readiness:async()=>({local:'ready',pstn:'not tested'}),
 call:async target=>{callTarget=target;return {state:'dialling'};},
 'audio.enable':async()=>({format:'pcm16',rate:16000})
},v=>{if(v==='PAIRED')paired=true;});
bridge.setAudioSink(pcm=>{if(pcm.byteLength===640)received++;});
try{
 await bridge.connect(`wss://127.0.0.1:${port}/`,token);
 const start=Date.now();
 while(Date.now()-start<10000){
  if(bridge.audioEnabled){enabled=true;if(framesSent<15){bridge.sendAudio(new ArrayBuffer(640));framesSent++;}}
  if(paired&&callTarget==='1002'&&received>=5)break;
  await new Promise(r=>setTimeout(r,25));
 }
 const result={paired,callTarget,received,enabled,framesSent,invalid:bridge.metrics.invalid};
 console.log(JSON.stringify(result));bridge.close();
 if(!paired||callTarget!=='1002'||received<5||!enabled)process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;bridge.close();}
