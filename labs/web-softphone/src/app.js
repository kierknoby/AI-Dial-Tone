import {AgentBridge} from './agent-bridge.js';
import {publicSnapshot,checkExtension} from './agent-protocol.js';
import {BotSession} from './bot-session.js';
import {BotAudio} from './bot-audio.js';
import {summariseRTCStats} from './rtc-metrics.js';
import {validateConfig,destinationURI,readiness} from './policy.js';
const $=id=>document.getElementById(id);
let phone=null,registered=false,microphone=false,incoming=false,callState='idle',botAudioReady=false;
let statsTimer=null,latestRTC={available:false};
const log=(message)=>{
 const now=new Date().toISOString();const trace=$('trace');trace.textContent+=`${now} ${message}\n`;
 if(trace.textContent.length>30000)trace.textContent=trace.textContent.slice(-25000);
 trace.scrollTop=trace.scrollHeight;
};
const status=v=>$('status').textContent=v;
const domain=()=>$('aor').value.trim().split('@')[1];
const botAudio=new BotAudio({onFrame:pcm=>bridge.sendAudio(pcm),onState:v=>{botAudioReady=v==='ACTIVE';$('audiostate').textContent=v;}});
function pcFromSimpleUser(p){
 // SIP.js 0.21.2 SimpleUser's session is currently private in TS but exists at
 // runtime; this compatibility adapter MUST be regression-tested on upgrades.
 return p?.session?.sessionDescriptionHandler?.peerConnection || null;
}
async function stopBotAudio(){await botAudio.stop();botAudioReady=false;}
async function getDiagnostics(){
 const pc=pcFromSimpleUser(phone);
 if(!pc||typeof pc.getStats!=='function')return {available:false,reason:'No active WebRTC peer'};
 try{latestRTC=summariseRTCStats(await pc.getStats());return latestRTC;}catch{return {available:false,reason:'RTC stats unavailable'};}
}
function stopStats(){if(statsTimer!==null)clearInterval(statsTimer);statsTimer=null;}
function startStats(){stopStats();statsTimer=setInterval(async()=>{if(callState!=='connected')return;const metrics=await getDiagnostics();if(metrics.available)bridge.emit('media.stats',metrics);},2000);}
function publish(type,detail={}){bridge.emit(type,detail);log(type+(Object.keys(detail).length?' '+JSON.stringify(detail):''));}
const session=new BotSession({
 getPhone:()=>phone?{call:t=>phone.call(destinationURI(t,domain())),hangup:()=>phone.hangup()}:null,
 onEvent:publish,
 onState:s=>{callState=s;status(s.toUpperCase());},
 onTimeout:async()=>{stopStats();publish('call.deadline_exceeded');try{if(phone&&callState!=='idle')await phone.hangup();}catch(e){log('Deadline hangup error: '+e.message);}finally{session.end();await stopBotAudio();}}
});
const snapshot=()=>publicSnapshot({registered,call:callState,microphone,media:!!window.RTCPeerConnection,agentAudio:botAudioReady});
const bridge=new AgentBridge({
 status:async()=>({...snapshot(),audioMetrics:bridge.metrics,allowlistCount:session.allowlist.length,armed:session.armed}),
 readiness:async()=>readiness({registered,microphone,websocket:!!phone,media:!!window.RTCPeerConnection}),
 diagnostics:async()=>getDiagnostics(),
 call:async target=>session.callExtension(target),
 hangup:async()=>{const r=await session.hangup();await stopBotAudio();return r;},
 'audio.enable':async()=>{
  if(!session.audioAllowed||!botAudioReady||callState!=='connected')throw Error('OPERATOR_AUDIO_APPROVAL_REQUIRED');
  publish('audio.enabled');return {format:'pcm_s16le',rate:16000,channels:1,frameMs:20};
 },
 'audio.disable':async()=>{botAudio.flush();publish('audio.disabled');return {enabled:false};},
 'audio.flush':async()=>{if(!botAudioReady)throw Error('BOT_AUDIO_NOT_READY');botAudio.flush();publish('audio.flushed');return {flushed:true};}
},v=>{$('agentstate').textContent=v;log('Bot bridge: '+v);},()=>{
 void stopBotAudio();
 if(session.origin==='bot' && session.call!=='idle')void session.hangup().catch(e=>log('Bot disconnect hangup failed: '+e.message));
});
bridge.setAudioSink(pcm=>{if(pcm.byteLength===0){botAudio.flush();return;}botAudio.push(pcm);});
for(const digit of ['1','2','3','4','5','6','7','8','9','*','0','#']){
 const b=document.createElement('button');b.textContent=digit;b.type='button';b.addEventListener('click',()=>{$('number').value+=digit;});$('dialgrid').append(b);
}
function guard(fn){return async()=>{try{await fn();}catch(e){log('ERROR '+String(e?.message||e).slice(0,180));}};}
function refreshPermissions(){
 const list=$('allowlist').value.split(',').map(x=>x.trim()).filter(Boolean);
 session.configure({allowlist:list,armed:$('arm').checked,audioAllowed:$('approveaudio').checked});
 $('approved').textContent=`${session.allowlist.join(', ')||'(none)'} · call ${session.armed?'armed':'disarmed'} · audio ${session.audioAllowed?'approved':'blocked'}`;
 publish('operator.permissions_updated',{count:session.allowlist.length,armed:session.armed,audioApproved:session.audioAllowed});
}
$('apply').onclick=guard(async()=>{
 if(!$('arm').checked && callState!=='idle')await session.hangup();
 if(!$('approveaudio').checked)await stopBotAudio();
 refreshPermissions();
});
async function registerPhone(){
 if(phone)throw Error('DISCONNECT_FIRST');
 const c=validateConfig({wss:$('wss').value.trim(),aor:$('aor').value.trim(),user:$('user').value.trim(),password:$('password').value});
 // Experimental dependency must be bundled locally for any non-lab deployment.
 const {Web}=await import('https://esm.sh/sip.js@0.21.2');
 const client=new Web.SimpleUser(c.wss,{
  aor:c.aor,
  userAgentOptions:{authorizationUsername:c.user,authorizationPassword:c.password},
  media:{constraints:{audio:true,video:false},remote:{audio:$('remote')}},
  delegate:{
   onCallReceived:()=>{incoming=true;session.incoming();publish('call.incoming');},
   onCallAnswered:()=>{incoming=false;session.answered();publish('call.answered');startStats();},
   onCallHangup:()=>{incoming=false;stopStats();session.end();void stopBotAudio();publish('call.ended');},
   onRegistered:()=>{registered=true;session.onRegistered(true);status('REGISTERED');},
   onUnregistered:()=>{registered=false;session.onRegistered(false);status('DISCONNECTED');},
   onServerDisconnect:()=>{registered=false;session.onRegistered(false);log('SIP transport disconnected');}
  }
 });
 phone=client;
 try{await client.connect();await client.register();log('Registration request sent. Waiting for SIP confirmation.');}
 catch(e){try{await client.disconnect();}catch{}phone=null;throw e;}
}
$('connect').onclick=guard(registerPhone);
$('disconnect').onclick=guard(async()=>{
 bridge.close();stopStats();await stopBotAudio();if(phone){try{await phone.disconnect();}finally{phone=null;}}
 registered=false;incoming=false;microphone=false;session.onRegistered(false);session.end();status('DISCONNECTED');
 session.configure({allowlist:session.allowlist,armed:false,audioAllowed:false});$('arm').checked=false;$('approveaudio').checked=false;refreshPermissions();
});
$('call').onclick=guard(async()=>{
 const target=checkExtension($('number').value.trim(),session.allowlist);
 await session.callExtension(target,'human');
});
$('answer').onclick=guard(async()=>{if(!phone||!incoming)throw Error('NO_INCOMING_CALL');await phone.answer();});
$('hangup').onclick=guard(async()=>{await session.hangup();await stopBotAudio();});
$('check').onclick=guard(async()=>{
 const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
 microphone=stream.getAudioTracks().some(t=>t.readyState==='live');stream.getTracks().forEach(t=>t.stop());
 const report=readiness({registered,microphone,websocket:!!phone,media:!!window.RTCPeerConnection});
 $('ready').textContent=JSON.stringify({...report,botAudio:botAudioReady,transport:bridge.state,pstn:'NOT TESTED'},null,2);
 publish('readiness.checked',{status:report.status});
});
$('activateaudio').onclick=guard(async()=>{
 if(!session.audioAllowed||callState!=='connected'||bridge.state!=='PAIRED')throw Error('PAIR_BOT_AND_APPROVE_AUDIO_ON_CONNECTED_TEST_CALL_FIRST');
 botAudio.peerConnection=pcFromSimpleUser(phone);
 await botAudio.start($('remote'));
 publish('audio.operator_activated');
});
$('stopaudio').onclick=guard(async()=>{await stopBotAudio();publish('audio.operator_stopped');});
$('agentconnect').onclick=guard(async()=>{if(!session.armed)throw Error('APPLY_ALLOWLIST_AND_ARM_FIRST');await bridge.connect($('agenturl').value.trim(),$('agenttoken').value);$('agenttoken').value='';});
$('agentdisconnect').onclick=()=>{bridge.close();void stopBotAudio();};
$('copy').onclick=guard(async()=>navigator.clipboard.writeText($('trace').textContent));
$('clear').onclick=()=>{$('trace').textContent='';};
window.addEventListener('pagehide',()=>{bridge.close();void stopBotAudio();});
refreshPermissions();log('AI Dial-Tone Browser SIP Lab 0.0.1. No SIP or bot connection has been attempted.');
