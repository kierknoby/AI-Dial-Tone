// Call session and operator permissions shared between UI and agent actions.
import {checkExtension,ACTIVE_TIMEOUT_MS} from './agent-protocol.js';
export class BotSession {
 constructor({getPhone,onEvent=()=>{},onTimeout=()=>{},onState=()=>{}, clock=()=>Date.now(),setTimer=setTimeout,clearTimer=clearTimeout}){
   Object.assign(this,{getPhone,onEvent,onTimeout,onState,clock,setTimer,clearTimer});
   this.call='idle';this.origin=null;this.registered=false;this.allowlist=[];this.armed=false;this.timer=null;this.audioAllowed=false;
 }
 configure({allowlist,armed,audioAllowed}){
   if(!Array.isArray(allowlist)||allowlist.length>20||allowlist.some(x=>!/^\d{2,6}$/.test(x)))throw Error('INVALID_ALLOWLIST');
   this.allowlist=[...new Set(allowlist)];this.armed=!!armed;this.audioAllowed=!!audioAllowed;
 }
 onRegistered(yes){this.registered=!!yes;this.onEvent(yes?'registration.ready':'registration.lost');}
 transition(next){this.call=next;this.onState(next);this.onEvent('call.'+next);}
 startDeadline(){this.cancelDeadline();this.timer=this.setTimer(()=>{this.timer=null;this.onTimeout();},ACTIVE_TIMEOUT_MS);}
 cancelDeadline(){if(this.timer!==null){this.clearTimer(this.timer);this.timer=null;}}
 async callExtension(target,origin='bot'){
  if(!['bot','human'].includes(origin))throw Error('INVALID_CALL_ORIGIN');
  checkExtension(target,this.allowlist);
  if(!this.armed)throw Error('OPERATOR_NOT_ARMED');
  if(!this.registered||this.call!=='idle'||!this.getPhone())throw Error('NOT_AVAILABLE_FOR_CALL');
  const phone=this.getPhone();this.origin=origin;this.transition('dialling');this.startDeadline();
  try{await phone.call(target);return {state:this.call,timeoutSeconds:ACTIVE_TIMEOUT_MS/1000};}
  catch(e){this.cancelDeadline();this.origin=null;this.transition('idle');throw e;}
 }
 async hangup(){if(this.call==='idle')throw Error('NO_ACTIVE_CALL');const p=this.getPhone();if(!p)throw Error('SIP_DISCONNECTED');await p.hangup();this.end();return {state:'idle'};}
 answered(){if(this.call!=='idle'){if(this.timer===null)this.startDeadline();this.transition('connected');}}
 incoming(){if(this.call==='idle'){this.origin='human';this.transition('ringing');this.startDeadline();}}
 end(){this.cancelDeadline();this.origin=null;this.transition('idle');}
}
