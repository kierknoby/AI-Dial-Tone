import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
const at = path => new URL(path,import.meta.url);

test('standalone CI targets main and tests labs', async()=>{
 const workflow=await readFile(at('../.github/workflows/verify.yml'),'utf8');
 assert.match(workflow,/branches: \[main\]/);
 assert.match(workflow,/permissions:\s*\n\s*contents: read/);
 assert.match(workflow,/npm run check/);
 assert.match(workflow,/test:peer/);
 assert.match(workflow,/labs\/web-softphone/);
 assert.doesNotMatch(workflow,/branches: \['AI'\]/);
});

test('AI Dial-Tone has its own root README, policy, licence, and no Windows sources',async()=>{
 const readme=await readFile(at('../README.md'),'utf8');
 const policy=await readFile(at('../REPOSITORY-POLICY.md'),'utf8');
 assert.match(readme,/# AI Dial-Tone/);
 assert.match(readme,/kierknoby\/AI-Dial-Tone/);
 assert.match(policy,/standalone public research repository/);
 await access(at('../LICENSE'));
 await assert.rejects(access(at('../NATIVE-README.md')));
 await assert.rejects(access(at('../INSTALL-AI-BRANCH.sh')));
 await assert.rejects(access(at('../extracted/MicroSIP-3.22.3-src/mainDlg.cpp')));
});

test('agent and human journeys distinct; no live calling promises',async()=>{
 const humans=await readFile(at('../site/humans.html'),'utf8');
 const agents=await readFile(at('../site/agents.html'),'utf8');
 const roadmap=await readFile(at('../ROADMAP.md'),'utf8');
 assert.match(humans,/FOR HUMANS/);
 assert.match(agents,/FOR AUTONOMOUS AGENTS \/ END-TO-END CALLING/);
 assert.match(humans,/not a live booking system/i);
 assert.match(agents,/not a live calling service/);
 assert.match(roadmap,/Asterisk|PSTN/);
});
