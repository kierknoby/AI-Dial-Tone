import test from 'node:test';import assert from 'node:assert/strict';
import {BotSession} from '../src/bot-session.js';
function make(){let starts=[],finishes=[],calls=[],hangups=0;const p={call:async target=>{calls.push(target);},hangup:async()=>hangups++};const s=new BotSession({getPhone:()=>p,setTimer:fn=>{starts.push(fn);return 1;},clearTimer:()=>finishes.push(true)});s.configure({allowlist:['1002'],armed:true,audioAllowed:false});s.onRegistered(true);return {s,calls,starts,finishes,hangups:()=>hangups};}
test('only operator-approved extensions can be dialled',async()=>{const {s,calls}=make();await assert.rejects(s.callExtension('1003'),/TARGET_NOT_ALLOWLISTED/);assert.equal(calls.length,0);});
test('operator disarming blocks call',async()=>{const {s,calls}=make();s.configure({allowlist:['1002'],armed:false,audioAllowed:false});await assert.rejects(s.callExtension('1002'),/OPERATOR_NOT_ARMED/);assert.equal(calls.length,0);});
test('call runs with a 60-second deadline and resets on hangup',async()=>{const {s,calls,starts,finishes}=make();const r=await s.callExtension('1002');assert.equal(r.timeoutSeconds,60);assert.deepEqual(calls,['1002']);assert.equal(starts.length,1);await assert.rejects(s.callExtension('1002'),/NOT_AVAILABLE/);await s.hangup();assert.equal(s.call,'idle');assert.equal(finishes.length,1);});
test('call failure cancels deadline',async()=>{const s=new BotSession({getPhone:()=>({call:async()=>{throw Error('SIP_REJECTED')}})});s.configure({allowlist:['1002'],armed:true});s.onRegistered(true);await assert.rejects(s.callExtension('1002'),/SIP_REJECTED/);assert.equal(s.call,'idle');assert.equal(s.timer,null);});
test('allowlist rejects malicious and excessive entries',()=>{const {s}=make();assert.throws(()=>s.configure({allowlist:['sip:evil']}));assert.throws(()=>s.configure({allowlist:Array(21).fill('1002')}));});
test('tracks bot versus human call ownership for fail-closed disconnect',async()=>{
 const {s}=make();await s.callExtension('1002');assert.equal(s.origin,'bot');s.end();assert.equal(s.origin,null);
 await s.callExtension('1002','human');assert.equal(s.origin,'human');s.end();
});
test('incoming test call also has deadline instead of an unbounded session',()=>{
 const {s,starts,finishes}=make();s.incoming();assert.equal(s.call,'ringing');assert.equal(starts.length,1);
 s.answered();assert.equal(s.call,'connected');assert.equal(starts.length,1);s.end();assert.equal(finishes.length,1);
});
