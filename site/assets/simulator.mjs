/** Explicitly scripted illustrative events. Never evidence of a telephone call. */
export const scenarios=Object.freeze({
  answered:{label:'Answered',destination:'1002',steps:[
    ['call.created','dialling','Idempotent request accepted by the illustrative simulator'],
    ['call.ringing','ringing','Simulated remote ringing'],
    ['call.answered','answered','Synthetic answer event; no carrier observed'],
    ['media.ready','answered','Example full-duplex audio state; no sound transmitted'],
    ['agent.observation','answered','Scripted illustration only. The task was not executed by an AI.'],
    ['call.ending','ending','Simulated agent termination request'],
    ['call.ended','ended','Simulated terminal state, not network-confirmed'],
    ['agent.outcome','ended','Unverified illustrative outcome; no real-world task completed']
  ]},
  busy:{label:'Busy',destination:'1003',steps:[
    ['call.created','dialling','Illustrative call request'],
    ['call.ringing','ringing','Simulated ringing'],
    ['call.failed','failed','BUSY · synthetic failure']
  ]},
  no_answer:{label:'No answer',destination:'1004',steps:[
    ['call.created','dialling','Illustrative call request'],
    ['call.ringing','ringing','Simulated ringing'],
    ['call.failed','failed','NO_ANSWER · synthetic failure']
  ]},
  remote_hangup:{label:'Remote hangup',destination:'1005',steps:[
    ['call.created','dialling','Illustrative call request'],
    ['call.ringing','ringing','Simulated ringing'],
    ['call.answered','answered','Simulated answer'],
    ['agent.observation','answered','Illustrative conversation interrupted by remote party'],
    ['call.ended','ended','REMOTE_HANGUP · synthetic termination']
  ]},
  deadline:{label:'Deadline',destination:'1002',steps:[
    ['call.created','dialling','Illustrative call request'],
    ['call.ringing','ringing','Simulated ringing'],
    ['call.answered','answered','Simulated answer'],
    ['call.ending','ending','DEADLINE_EXCEEDED · synthetic watchdog'],
    ['call.ended','ended','Illustrative closure; a real carrier must independently confirm this']
  ]}
});
export const finalStates=new Set(['ended','failed']);
export function buildScenario(name,{id='demo-call',start=Date.now()}={}){
  if(!Object.hasOwn(scenarios,name))throw new Error('UNKNOWN_SCENARIO');
  return scenarios[name].steps.map(([type,state,detail],index)=>({
    id,seq:index+1,type,state,detail,source:'browser_script',network_verified:false,
    trust:type.startsWith('agent.')?'agent_reported_unverified':'illustrative_only',
    payment:null,at:new Date(start+index*550).toISOString()
  }));
}
export function classifyCall(call){
  if(!call || typeof call!=='object')return 'idle';
  if(call.state==='failed')return 'failed';
  if(finalStates.has(call.state))return 'done';
  return 'running';
}
export function safeEvent(event){
  return {
    seq:Number.isSafeInteger(event.seq)?event.seq:0,
    type:typeof event.type==='string'?event.type.slice(0,100):'unknown',
    detail:typeof event.detail==='string'?event.detail.slice(0,500):'',
    state:typeof event.state==='string'?event.state:'unknown',
    at:typeof event.at==='string'?event.at:new Date().toISOString(),
    source:event.source==='browser_script'?'browser_script':'local_lab',
    network_verified:false,
    trust:event.trust||'lab_only'
  };
}
