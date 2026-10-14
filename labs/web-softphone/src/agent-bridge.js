import {VERSION,MAX_BUFFERED,MAX_COMMAND_BYTES,AUTH_TIMEOUT_MS,validateAgentCommand,makeResult,eventMessage,validateBridgeUrl,freshNonce,authKey,signProof,verifyProof,makeAudioPacket,decodeAudioPacket,AUDIO_UPLINK,AUDIO_DOWNLINK} from './agent-protocol.js';

// An outbound, operator-authorised, mutually HMAC-authenticated WSS connection.
// The pairing secret never crosses the WebSocket. Controller proves knowledge first.
// Audio only flows after an explicit operator action AND audio.enable command.
export class AgentBridge {
  constructor(actions,onState=()=>{},onEvent=()=>{}) {
    this.actions=actions;this.onState=onState;this.onEvent=onEvent;
    this.ws=null;this.state='OFFLINE';this.seq=0;this.seen=new Map();this.commandBusy=false;this.audioEnabled=false;this.inboundAudio=()=>{};
    this.metrics={sent:0,dropped:0,received:0,invalid:0};
  }
  status(state){this.state=state;this.onState(state);}
  async connect(endpoint,token,{WebSocketClass=WebSocket}={}){
    if(this.ws)throw Error('ALREADY_CONNECTED');
    const url=validateBridgeUrl(endpoint),key=await authKey(token),nonce=freshNonce();
    const ws=new WebSocketClass(url);ws.binaryType='arraybuffer';this.ws=ws;this.status('CONNECTING');
    let paired=false,serverNonce=null;
    let timer=setTimeout(()=>{if(!paired&&this.ws===ws)ws.close(4000,'Pairing timed out');},AUTH_TIMEOUT_MS);
    const transmit=(obj)=>{if(ws.readyState===1 && ws.bufferedAmount<MAX_BUFFERED)ws.send(JSON.stringify(obj));};
    ws.onopen=()=>{transmit({version:VERSION,kind:'hello',nonce,capabilities:['status','readiness','call:test-extension','hangup','audio:pcm16-16000-mono']});this.status('AUTHENTICATING');};
    ws.onmessage=async({data})=>{
      if(this.ws!==ws)return;
      if(data instanceof ArrayBuffer){
        if(!paired||!this.audioEnabled)return;
        try{const pcm=decodeAudioPacket(data,AUDIO_DOWNLINK);this.metrics.received++;this.inboundAudio(pcm);}catch{this.metrics.invalid++;}return;
      }
      if(typeof data!=='string'||data.length>MAX_COMMAND_BYTES){this.metrics.invalid++;return;}
      let msg;try{msg=JSON.parse(data);}catch{this.metrics.invalid++;return;}
      if(!paired){
        if(msg.kind==='challenge' && msg.version===VERSION && !serverNonce){
          serverNonce=msg.nonce;
          if(!await verifyProof(key,'server',nonce,serverNonce,msg.proof)){ws.close(4001,'Controller authentication failed');return;}
          transmit({version:VERSION,kind:'proof',proof:await signProof(key,'client',nonce,serverNonce)});
        }else if(msg.kind==='paired' && msg.version===VERSION && msg.accepted===true && serverNonce){
          clearTimeout(timer);paired=true;this.status('PAIRED');this.emit('bridge.paired');
        }else{ws.close(4001,'Invalid authentication flow');}
        return;
      }
      if(msg.version!==VERSION)return;
      if(msg.kind==='ping'){transmit({version:VERSION,kind:'pong',id:msg.id});return;}
      if(msg.kind!=='command')return;
      let cmd;try{cmd=validateAgentCommand(msg);}catch(e){transmit(makeResult(typeof msg.id==='string'?msg.id.slice(0,64):null,null,{code:e.message}));return;}
      if(this.seen.has(cmd.id)){const prior=this.seen.get(cmd.id);transmit(prior.fingerprint===JSON.stringify(cmd)?prior.reply:makeResult(cmd.id,null,{code:'COMMAND_ID_REUSED'}));return;}
      if(this.commandBusy){transmit(makeResult(cmd.id,null,{code:'BUSY'}));return;}
      this.commandBusy=true;
      try{
        const action=this.actions[cmd.command];if(typeof action!=='function')throw Error('COMMAND_UNAVAILABLE');
        const result=await action(cmd.target);
        if(cmd.command==='audio.enable')this.audioEnabled=true;
        if(cmd.command==='audio.disable'){this.audioEnabled=false;this.inboundAudio(new ArrayBuffer(0));}
        if(cmd.command==='hangup'){this.audioEnabled=false;this.inboundAudio(new ArrayBuffer(0));}
        const reply=makeResult(cmd.id,result);
        this.seen.set(cmd.id,{fingerprint:JSON.stringify(cmd),reply});if(this.seen.size>128)this.seen.delete(this.seen.keys().next().value);
        transmit(reply);
      }catch(e){const reply=makeResult(cmd.id,null,{code:e.message});this.seen.set(cmd.id,{fingerprint:JSON.stringify(cmd),reply});transmit(reply);}
      finally{this.commandBusy=false;}
    };
    ws.onclose=()=>{clearTimeout(timer);if(this.ws===ws){this.ws=null;this.audioEnabled=false;this.seen.clear();this.inboundAudio(new ArrayBuffer(0));this.onEvent('closed');this.status('OFFLINE');}};
    ws.onerror=()=>{if(this.ws===ws)this.status('ERROR');};
  }
  emit(type,detail={}) {if(this.state==='PAIRED'&&this.ws?.readyState===1&&this.ws.bufferedAmount<MAX_BUFFERED)this.ws.send(JSON.stringify(eventMessage(type,detail)));}
  sendAudio(pcm){
    if(this.state!=='PAIRED'||!this.audioEnabled||this.ws?.readyState!==1)return false;
    if(this.ws.bufferedAmount>MAX_BUFFERED){this.metrics.dropped++;return false;}
    try{this.ws.send(makeAudioPacket(AUDIO_UPLINK,pcm));this.metrics.sent++;return true;}catch{this.metrics.invalid++;return false;}
  }
  setAudioSink(fn){this.inboundAudio=fn;}
  close(){const ws=this.ws;this.ws=null;this.audioEnabled=false;this.seen.clear();this.inboundAudio(new ArrayBuffer(0));if(ws)ws.close(1000,'Operator disconnected');this.status('OFFLINE');}
}
