import test from 'node:test';import assert from 'node:assert/strict';
// AudioWorklet processing runs without DOM access. This harness exercises its
// 128-sample render quantum, frame assembly, jitter handling and playback.
test('AudioWorklet produces 20-ms PCM frames and accepts reverse direction audio',async()=>{
 const names={};const old={AudioWorkletProcessor:globalThis.AudioWorkletProcessor,registerProcessor:globalThis.registerProcessor,sampleRate:globalThis.sampleRate};
 globalThis.sampleRate=48000;
 globalThis.AudioWorkletProcessor=class{constructor(){this.port={out:[],onmessage:null,postMessage(data){this.out.push(data);}};}};
 globalThis.registerProcessor=(name,cls)=>names[name]=cls;
 try{
  await import('../src/audio-worklet.js');
  const capture=new names['dialtone-capture']();
  for(let q=0;q<150;q++){
    const inBlock=new Float32Array(128);
    for(let i=0;i<128;i++)inBlock[i]=0.5*Math.sin((i+q*128)*2*Math.PI*440/48000);
    capture.process([[inBlock]]);
  }
  assert.equal(capture.port.out.length,20);
  for(const frame of capture.port.out)assert.equal(frame.byteLength,640);
  const playback=new names['dialtone-playback']();
  const audio=capture.port.out.slice(0,4);
  for(const pcm of audio)playback.port.onmessage({data:pcm});
  let power=0;
  for(let q=0;q<15;q++){
    const o=new Float32Array(128);playback.process([],[[o]]);
    for(const v of o)power+=v*v;
  }
  assert(power>1,'Audio from bot should render');
  playback.port.onmessage({data:'flush'});
  assert.equal(playback.frames.length,0);
  capture.port.onmessage({data:'flush'});
  assert.equal(capture.total,0);
 }finally{
  for(const [k,v]of Object.entries(old)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
 }
});
