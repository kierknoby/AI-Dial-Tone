import {announce,copyText} from './app.js';
import {scenarios,buildScenario,finalStates,classifyCall,safeEvent} from './simulator.mjs';
const $=id=>document.getElementById(id);
const ui={form:$('play-form'),scenario:$('scenario'),destination:$('destination'),task:$('task'),duration:$('max-seconds'),agent:$('agent-id'),run:$('run-button'),reset:$('reset-button'),hangup:$('hangup-button'),copy:$('copy-events'),list:$('event-list'),state:$('call-state'),id:$('call-id'),indicator:$('run-indicator'),ring:document.querySelector('.live-ring'),note:$('source-note'),outcome:$('outcome-label'),explain:$('outcome-explainer')};
let active=false,generation=0,call=null,events=[],cursor=0;
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function setNote(text,isWarning=false){ui.note.className='notice '+(isWarning?'notice-warn':'notice-neutral');ui.note.textContent='ⓘ '+text;}
function changeIndicator(status){
  ui.indicator.className='mini-badge '+({'idle':'badge-idle','running':'badge-running','done':'badge-done','failed':'badge-failed'}[status]||'badge-idle');
  ui.indicator.textContent=status.toUpperCase();
  ui.ring.classList.toggle('on',status==='running');
}
function changeState(state){
  ui.state.textContent=state==='idle'?'Not started':state.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
  changeIndicator(state==='idle'?'idle':classifyCall({state}));
}
function updateOutcome(){
  if(!call){ui.outcome.textContent='Awaiting simulation';ui.explain.textContent='Agent-reported outcomes are not independently verified facts.';return;}
  if(call.state==='failed'){
    ui.outcome.textContent='No conversation completed';ui.explain.textContent='The reported failure is synthetic and has no carrier evidence.';
  } else if(call.state==='ended'){
    ui.outcome.textContent='Simulation ended · not verified';ui.explain.textContent='No telephone or speech-model exchange occurred. Example observations are scripted.';
  } else {
    ui.outcome.textContent='In progress · unverified';ui.explain.textContent='This is a developer simulation. Do not treat it as evidence of a real-world outcome.';
  }
}
function displayEvent(e){
  const li=document.createElement('li');
  const time=document.createElement('span');time.className='event-time';
  let date=new Date(e.at);time.textContent=Number.isNaN(date.valueOf())?'--:--:--':date.toLocaleTimeString('en-GB',{hour12:false});
  const body=document.createElement('div');const title=document.createElement('span');title.className='event-title';title.textContent=e.type;
  const detail=document.createElement('span');detail.className='event-detail';detail.textContent=e.detail||e.reason||'State event · no verified external network evidence';
  body.append(title,detail);li.append(time,body);ui.list.append(li);ui.list.scrollTop=ui.list.scrollHeight;
}
function appendEvents(items){
  if(items.length&&ui.list.querySelector('.empty-state'))ui.list.textContent='';
  for(const item of items){const normalized=safeEvent(item);events.push(normalized);displayEvent(normalized);cursor=Math.max(cursor,normalized.seq);}
}
function setActive(value){
  active=value;ui.run.disabled=value;ui.reset.disabled=value;ui.hangup.disabled=!value;
}
function resetView(){
  generation++;active=false;call=null;events=[];cursor=0;
  ui.run.disabled=false;ui.reset.disabled=false;ui.hangup.disabled=true;
  ui.list.replaceChildren();const el=document.createElement('li');el.className='empty-state';el.innerHTML='<span>⌁</span>Run a scenario to inspect its lifecycle.';ui.list.append(el);
  ui.id.textContent='No call ID';changeState('idle');updateOutcome();
}
async function runScripted(runId){
  const kind=ui.scenario.value;
  const id=`illustrative-${crypto.randomUUID()}`;
  call={id,state:'dialling'};ui.id.textContent=id;
  const timeline=buildScenario(kind,{id});
  for(let index=0;index<timeline.length;index++){
    if(runId!==generation)return;
    const item=timeline[index];call.state=item.state;changeState(item.state);appendEvents([item]);updateOutcome();
    if(!finalStates.has(item.state)||index<timeline.length-1)await sleep(480);
  }
  if(runId!==generation)return;
  setActive(false);ui.hangup.disabled=true;
}
async function begin(event){
  event.preventDefault();
  if(active)return;
  if(!ui.form.reportValidity())return;
  if(!ui.task.value.trim()){setNote('Please enter a non-empty task.',true);ui.task.focus();return;}
  resetView();setActive(true);const runId=generation;
  changeState('dialling');
  try{await runScripted(runId);}
  catch(err){if(runId!==generation)return;setActive(false);ui.hangup.disabled=true;changeIndicator('failed');ui.state.textContent='Request failed';setNote('Local playground error: '+(err?.message||'Unknown error'),true);}
}
async function hangup(){
  if(!active||!call)return;
  generation++;call.state='ended';const now=Date.now();appendEvents([
    {seq:cursor+1,type:'call.ending',state:'ending',detail:'User requested illustrative hangup',at:new Date(now).toISOString(),source:'browser_script'},
    {seq:cursor+2,type:'call.ended',state:'ended',detail:'Scripted closure, not carrier-confirmed',at:new Date(now+1).toISOString(),source:'browser_script'}
  ]);changeState('ended');updateOutcome();setActive(false);return;
}
ui.form?.addEventListener('submit',begin);
ui.reset?.addEventListener('click',resetView);
ui.hangup?.addEventListener('click',hangup);
ui.copy?.addEventListener('click',()=>copyText(JSON.stringify({mode:'SCRIPTED BROWSER SIMULATION',call,events,real_pstn_calls:0,settled_payments:0},null,2)));
ui.scenario?.addEventListener('change',()=>{if(!active)ui.destination.value=scenarios[ui.scenario.value].destination;});

resetView();
