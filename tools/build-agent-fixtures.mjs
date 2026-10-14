/** Reproducibly exports STATIC illustrative fixtures from the browser simulator.
 * No API keys, telephone connections, account onboarding or money are involved.
 */
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {scenarios,buildScenario} from '../site/assets/simulator.mjs';
const target=resolve(fileURLToPath(new URL('../site/api/scenarios/',import.meta.url)));
const cases={
  answered:{task:'Inspect a simulated answered call. Separate reported outcomes from network observations.',terminal:'ended',risk:'agent-reported outcome is not independent evidence'},
  busy:{task:'Inspect a simulated busy response. Do not claim a conversation occurred.',terminal:'failed',risk:'do not interpret busy as answered'},
  no_answer:{task:'Inspect simulated ringing followed by no answer. Do not invent spoken information.',terminal:'failed',risk:'no answer is not consent or conversation'},
  remote_hangup:{task:'Detect synthetic remote hangup and stop any further conversation work.',terminal:'ended',risk:'do not invent call completion success'},
  deadline:{task:'Inspect a synthetic deadline and explain why real carrier termination still needs confirmation.',terminal:'ended',risk:'synthetic terminal state is not carrier verified'}
};
await mkdir(target,{recursive:true});
const catalog={schema_version:'0.0.1',kind:'static_evaluation_fixtures',status:'technical_preview',execution:'static_only',calling_available:false,charges:false,required_registration:false,notice:'These fixtures are illustrative; no AI, Asterisk, PSTN, or x402 interaction occurred.',cases:[]};
for(const [name,info] of Object.entries(cases)){
  const events=buildScenario(name,{id:`fixture-${name}`,start:0});
  if(events.at(-1).state!==info.terminal)throw Error(`Terminal mismatch ${name}`);
  if(events.some(e=>e.network_verified!==false||e.payment!==null||e.source!=='browser_script'))throw Error(`Unsafe fixture ${name}`);
  const doc={schema_version:'0.0.1',scenario:name,type:'static_scripted_fixture',task:info.task,safety_note:info.risk,evidence_is_live:false,telephone_call_placed:false,events,checks:{terminal_state:info.terminal,network_verified:false,payment:null,source:'browser_script',sequence_is_contiguous:true}};
  await writeFile(join(target,`${name}.json`),JSON.stringify(doc,null,2)+'\n');
  catalog.cases.push({id:name,description:info.task,fixture:`/api/scenarios/${name}.json`,expected_terminal_state:info.terminal});
}
await writeFile(resolve(target,'..','challenges.json'),JSON.stringify(catalog,null,2)+'\n');
console.log(`Generated ${catalog.cases.length} honest, reproducible, static agent test cases.`);
