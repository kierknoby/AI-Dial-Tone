import {Resampler,floatToPcm16,pcm16ToFloat} from './audio-codec.js';
// AudioWorklet owns frame timing. The main thread does not schedule each RTP packet.
class CaptureProcessor extends AudioWorkletProcessor {
 constructor(){super();this.resampler=new Resampler(sampleRate,16000);this.queue=[];this.total=0;this.port.onmessage=e=>{if(e.data==='flush'){this.queue=[];this.total=0;this.resampler.reset();}};}
 process(inputs){const channel=inputs[0]?.[0];if(!channel)return true;
 const samples=this.resampler.feed(channel);this.queue.push(...samples);this.total+=samples.length;
 while(this.total>=320){const out=this.queue.splice(0,320);this.total-=320;const pcm=floatToPcm16(out);this.port.postMessage(pcm,[pcm]);}return true;}
}
class PlaybackProcessor extends AudioWorkletProcessor {
 constructor(){super();this.frames=[];this.position=0;this.playing=false;this.port.onmessage=({data})=>{
 if(data==='flush'){this.frames=[];this.position=0;this.playing=false;return;}
 if(!(data instanceof ArrayBuffer) || data.byteLength!==640)return;
 if(this.frames.length>28)this.frames.splice(0,10); // drop excess jitter/latency, bounded buffer
 this.frames.push(pcm16ToFloat(data));
 };}
 process(inputs,outputs){const output=outputs[0]?.[0];if(!output)return true;
 const step=16000/sampleRate;
 for(let i=0;i<output.length;i++){
   if(!this.playing){if(this.frames.length>=3)this.playing=true;else{output[i]=0;continue;}}
   while(this.position>=320){this.position-=320;this.frames.shift();if(!this.frames.length){this.playing=false;break;}}
   if(!this.playing){output[i]=0;continue;}
   const f=this.frames[0],a=Math.floor(this.position),b=Math.min(a+1,319),t=this.position-a;
   output[i]=f[a]*(1-t)+f[b]*t;this.position+=step;
 }return true;}
}
registerProcessor('dialtone-capture',CaptureProcessor);
registerProcessor('dialtone-playback',PlaybackProcessor);
