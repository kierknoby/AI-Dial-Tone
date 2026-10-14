// Portable helpers, used by the worklet and deterministic tests.
export const PCM_RATE=16000;
export const FRAME_SAMPLES=320;
export function pcm16ToFloat(buffer){
 if(!(buffer instanceof ArrayBuffer)||buffer.byteLength%2)throw Error('Bad PCM16 buffer');
 const v=new DataView(buffer),out=new Float32Array(buffer.byteLength/2);
 for(let i=0;i<out.length;i++)out[i]=v.getInt16(i*2,true)/32768;
 return out;
}
export function floatToPcm16(input){
 const out=new ArrayBuffer(input.length*2),v=new DataView(out);
 for(let i=0;i<input.length;i++){const n=Math.max(-1,Math.min(1,Number.isFinite(input[i])?input[i]:0));v.setInt16(i*2,n<0?Math.round(n*32768):Math.round(n*32767),true);}return out;
}
// Stateful output-timed linear resampler; `feed` can receive arbitrary chunks.
export class Resampler {
 constructor(inputRate,outputRate){if(inputRate<8000||outputRate<8000)throw Error('Unsupported audio sample rate');this.step=inputRate/outputRate;this.buffer=[];this.position=0;}
 feed(samples){this.buffer.push(...samples);const out=[];while(this.position+1<this.buffer.length){const i=Math.floor(this.position),f=this.position-i;out.push(this.buffer[i]*(1-f)+this.buffer[i+1]*f);this.position+=this.step;}
 const consumed=Math.min(Math.floor(this.position),this.buffer.length-1);if(consumed){this.buffer.splice(0,consumed);this.position-=consumed;}return new Float32Array(out);}
 reset(){this.buffer=[];this.position=0;}
}
