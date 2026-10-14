// Versioned, transport-neutral contract. No SIP credentials or PSTN permissions.
export const VERSION = 'dialtone.agent.v2';
export const COMMANDS = Object.freeze(['status','readiness','diagnostics','call','hangup','audio.enable','audio.disable','audio.flush']);
export const AUDIO_RATE = 16000;
export const AUDIO_SAMPLES = 320; // 20 ms, 16-bit mono LE
export const AUDIO_BYTES = AUDIO_SAMPLES * 2;
export const AUDIO_UPLINK = 1; // telephone remote -> agent
export const AUDIO_DOWNLINK = 2; // agent -> telephone sender
export const MAX_BUFFERED = 256 * 1024;
export const MAX_COMMAND_BYTES = 4096;
export const AUTH_TIMEOUT_MS = 10000;
export const ACTIVE_TIMEOUT_MS = 60000;
const idPattern = /^[A-Za-z0-9_-]{1,64}$/;
const hexPattern = /^[a-f0-9]{32}$/;
export function validateAgentCommand(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw Error('INVALID_MESSAGE');
  if(input.version !== VERSION || input.kind !== 'command' || typeof input.id !== 'string' || !idPattern.test(input.id)) throw Error('INVALID_COMMAND_ID');
  if(!COMMANDS.includes(input.command)) throw Error('COMMAND_NOT_ALLOWED');
  const expected = input.command === 'call' ? ['version','kind','id','command','target'] : ['version','kind','id','command'];
  if(Object.keys(input).some(k=>!expected.includes(k))) throw Error('UNEXPECTED_FIELD');
  if(input.command === 'call' && (typeof input.target !== 'string' || !/^\d{2,6}$/.test(input.target))) throw Error('INVALID_TEST_EXTENSION');
  return input;
}
export function checkExtension(target, allowed) {
  if(!/^\d{2,6}$/.test(target) || !Array.isArray(allowed) || !allowed.includes(target)) throw Error('TARGET_NOT_ALLOWLISTED');
  return target;
}
export function publicSnapshot(state) {
  return {version:VERSION,kind:'status',registration:state.registered?'registered':'disconnected',call:state.call||'idle', microphone:!!state.microphone,rtc:!!state.media,agentAudio:!!state.agentAudio,pstn:'not enabled',payment:'not connected'};
}
export function eventMessage(type,detail={}) {
  if(!/^[a-z][a-z0-9_.-]{0,48}$/.test(type))throw Error('INVALID_EVENT');
  return {version:VERSION,kind:'event',type,at:new Date().toISOString(),...detail};
}
export function makeResult(id,result,error) {
  return {version:VERSION,kind:'result',id,ok:!error,...(error ? {error:{code:(/^[A-Z][A-Z0-9_]{1,47}$/.test(String(error.code))?String(error.code):'ACTION_FAILED')}} : {result:result??null})};
}
export function validateBridgeUrl(input) {
  const u=new URL(input);
  if(u.protocol!=='wss:' || u.username || u.password || u.hash || u.search || !u.hostname)throw Error('BRIDGE_REQUIRES_CLEAN_WSS_URL');
  return u.toString();
}
export function isHexNonce(n) {return typeof n==='string' && hexPattern.test(n);}
export function freshNonce() {return Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,'0')).join('');}
export async function authKey(token) {
  if(typeof token!=='string'||token.length<32||token.length>256)throw Error('PAIRING_TOKEN_TOO_SHORT');
  return crypto.subtle.importKey('raw',new TextEncoder().encode(token),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
}
export async function signProof(key,role,clientNonce,serverNonce){
  if(!['server','client'].includes(role)||!isHexNonce(clientNonce)||!isHexNonce(serverNonce))throw Error('INVALID_NONCE');
  const data=new TextEncoder().encode([VERSION,role,clientNonce,serverNonce].join('|'));
  return Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,data)),b=>b.toString(16).padStart(2,'0')).join('');
}
export async function verifyProof(key,role,clientNonce,serverNonce,proof){
  if(typeof proof!=='string'|| !/^[a-f0-9]{64}$/.test(proof))return false;
  const data=new TextEncoder().encode([VERSION,role,clientNonce,serverNonce].join('|'));
  const sig=new Uint8Array(proof.match(/../g).map(x=>parseInt(x,16)));
  return crypto.subtle.verify('HMAC',key,sig,data);
}
export function makeAudioPacket(direction,payload) {
  if(![AUDIO_UPLINK,AUDIO_DOWNLINK].includes(direction) || !(payload instanceof ArrayBuffer) || payload.byteLength!==AUDIO_BYTES)throw Error('INVALID_AUDIO_PACKET');
  const out=new Uint8Array(1+AUDIO_BYTES);out[0]=direction;out.set(new Uint8Array(payload),1);return out.buffer;
}
export function decodeAudioPacket(buffer,expectedDirection) {
  if(!(buffer instanceof ArrayBuffer)||buffer.byteLength!==1+AUDIO_BYTES)throw Error('INVALID_AUDIO_FRAME');
  const view=new Uint8Array(buffer);
  if(view[0]!==expectedDirection)throw Error('INVALID_AUDIO_DIRECTION');
  return buffer.slice(1);
}
