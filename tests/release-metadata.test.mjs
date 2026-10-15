import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
const read = async path => readFile(new URL(path,import.meta.url),'utf8');

test('root README follows practical house style for standalone development', async()=>{
 const s=await read('../README.md');
 for(const h of ['Overview','Release Status','Compatibility','Requirements','Installing','Running the Public Project','Updating AI Dial-Tone','Communication Architecture','Security Model','User Interface','Deployment','Validation','Current Limitations','Roadmap','Release History','Support and Feedback','Licence','AI-Assisted Contributions and Disclosure','Author']){
   assert.ok(s.includes(`## ${h}`),`Missing ${h}`);
 }
 assert.match(s,/not yet a publicly available telephone service/i);
 assert.match(s,/Assisted-by: AGENT_NAME:MODEL_VERSION/);
 assert.match(s,/npm run test:peer/);
 assert.doesNotMatch(s,/NATIVE-README\.md|INSTALL-AI-BRANCH/);
});

test('complete GPLv3 and accurate standalone licensing scope',async()=>{
 const license=await read('../LICENSE');
 const note=await read('../LICENSING-NOTE.md');
 assert.match(license,/GNU GENERAL PUBLIC LICENSE\s+Version 3, 29 June 2007/);
 assert.match(license,/TERMS AND CONDITIONS/);
 assert.match(license,/END OF TERMS AND CONDITIONS/);
 assert.match(note,/GPL-3\.0-or-later/);
 assert.match(note,/No native Windows\/PJSIP source or assets are shipped/);
 assert.match(note,/private/i);
});

test('publish instructions do not touch the native Windows repo',async()=>{
 const p=await read('../PUBLISHING.md');
 assert.match(p,/kierknoby\/AI-Dial-Tone/);
 assert.match(p,/No publishing, commit, or push is performed by this guide/);
 assert.doesNotMatch(p,/git push -u origin main/);
 assert.doesNotMatch(p,/git checkout AI|EgyptianEyes\/Dial-Tone\.git/);
});

test('first public release has one consistent 0.0.1 version and no old private lab docs',async()=>{
 const pkg=JSON.parse(await read('../package.json'));
 const webPkg=JSON.parse(await read('../labs/web-softphone/package.json'));
 const peer=JSON.parse(await read('../peer-lab/openapi.json'));
 const manifest=JSON.parse(await read('../site/agents.json'));
 const evidence=JSON.parse(await read('../RELEASE-EVIDENCE.json'));
 const readme=await read('../README.md');
 const changelog=await read('../CHANGELOG.md');
 assert.equal(pkg.version,'0.0.1');assert.equal(webPkg.version,'0.0.1');
 assert.equal(pkg.engines.node,'>=22');assert.equal(webPkg.engines.node,'>=22');
 assert.equal(peer.info.version,'0.0.1');assert.equal(manifest.release_version,'0.0.1');assert.equal(manifest.schema_version,'0.0.1');
 assert.equal(evidence.version,'0.0.1');
 const siteHtml=(await readdir(new URL('../site/',import.meta.url))).filter(x=>x.endsWith('.html') && x!=='404.html');
 const docsHtml=(await readdir(new URL('../site/docs/',import.meta.url))).filter(x=>x.endsWith('.html'));
 assert.equal(evidence.public_web_pages_total_excluding_404,siteHtml.length+docsHtml.length);
 assert.equal(evidence.public_suite_tests_passed,80);
 assert.equal(evidence.peer_lab_network_tests_discovered,39);
 assert.equal(evidence.web_softphone_tests_discovered,33);
 assert.equal(evidence.research_suite_tests_discovered,80+39+22+20+12+33+3);
 assert.equal(evidence.current_verification.baseline_test_counts.passed,206);
 assert.equal(evidence.current_verification.baseline_test_counts.skipped,3);
 assert.equal(evidence.current_verification.baseline_test_counts.discovered,209);
 const baseline=evidence.current_verification.baseline_test_counts;
 assert.equal(baseline.discovered,baseline.executed+baseline.skipped);
 assert.equal(baseline.executed,baseline.passed+baseline.failed);
 const current=evidence.current_worktree_validation.test_counts;
 assert.deepEqual(current,{discovered:210,executed:208,passed:208,skipped:2,failed:0});
 assert.equal(current.discovered,current.executed+current.skipped);
 assert.equal(current.executed,current.passed+current.failed);
 assert.equal(evidence.current_worktree_validation.suites.web_softphone.passed,33);
 assert.equal(evidence.current_worktree_validation.suites.web_softphone.skipped,0);
 assert.equal(evidence.first_call_verified_real_pstn,false);
 assert.equal(evidence.first_call_verified_real_payment,false);
 assert.match(readme,/^# AI Dial-Tone 0\.0\.1/m);
 assert.match(changelog,/## 0\.0\.1/);
 for (const item of [readme,changelog,await read('../PUBLISHING.md'),await read('../site/llms.txt'),await read('../tools/build-reference.py')]) {
   assert.doesNotMatch(item,/dialtone-agent-lab-v0\.7|v1\.4|1\.4\.2|source under ai\/peer-lab/i);
 }
 const publicSpec=JSON.parse(await read('../site/api/openapi.json'));
 assert.deepEqual(publicSpec,peer);
 assert.ok(!publicSpec.paths['/v1/calls']);
 assert.ok(publicSpec.paths['/v1/sessions']);
});
