// A conscious, call-scoped WebRTC media bridge. NEVER starts at SIP registration.
// Remote receive track -> 16k PCM to authenticated bot; bot 16k PCM -> WebRTC send track.
// No remote audio is looped to the far end; no microphone is sent to the bot.
export class BotAudio {
 constructor({onFrame,onState=()=>{}}){this.onFrame=onFrame;this.onState=onState;this.active=false;this.ctx=null;this.sender=null;this.original=null;this.nodes=[];this.timer=null;}
 async start(remoteElement){
  if(this.active)throw Error('BOT_AUDIO_ALREADY_ACTIVE');
  const stream=remoteElement?.srcObject;
  if(!(stream instanceof MediaStream)||!stream.getAudioTracks().some(x=>x.readyState==='live'))throw Error('REMOTE_WEBRTC_AUDIO_NOT_AVAILABLE');
  const pc=this.peerConnection;
  if(!pc||pc.connectionState==='closed')throw Error('WEBRTC_PEER_NOT_AVAILABLE');
  const sender=pc.getSenders().find(s=>s.track?.kind==='audio');
  if(!sender)throw Error('WEBRTC_AUDIO_SENDER_NOT_AVAILABLE');
  const ctx=new AudioContext({latencyHint:'interactive'});this.ctx=ctx;this.sender=sender;this.original=sender.track;
  try{
    await ctx.audioWorklet.addModule('/audio-worklet.js');await ctx.resume();
    const source=ctx.createMediaStreamSource(stream);
    const capture=new AudioWorkletNode(ctx,'dialtone-capture');
    const silence=ctx.createGain();silence.gain.value=0;
    source.connect(capture);capture.connect(silence);silence.connect(ctx.destination);
    const play=new AudioWorkletNode(ctx,'dialtone-playback',{outputChannelCount:[1]});
    const outgoing=ctx.createMediaStreamDestination();play.connect(outgoing);
    capture.port.onmessage=({data})=>{if(this.active && data instanceof ArrayBuffer) this.onFrame(data);};
    const botTrack=outgoing.stream.getAudioTracks()[0];
    if(!botTrack)throw Error('NO_BOT_AUDIO_TRACK');
    await sender.replaceTrack(botTrack);
    this.nodes=[source,capture,silence,play,outgoing];this.play=play;this.active=true;this.onState('ACTIVE');
  }catch(e){await this.stop();throw e;}
 }
 push(pcm){if(this.active && pcm?.byteLength===640)this.play.port.postMessage(pcm,[pcm]);}
 flush(){if(this.active){this.play.port.postMessage('flush');this.nodes[1].port.postMessage('flush');}}
 async stop(){
   const sender=this.sender,original=this.original;this.active=false;
   if(sender&&sender.track?.readyState!=='ended')try{await sender.replaceTrack(original?.readyState==='live'?original:null);}catch{}
   for(const n of this.nodes)try{n.disconnect();}catch{}
   this.nodes=[];this.sender=null;this.original=null;
   if(this.ctx)try{await this.ctx.close();}catch{}
   this.ctx=null;this.play=null;this.onState('OFF');
 }
}
