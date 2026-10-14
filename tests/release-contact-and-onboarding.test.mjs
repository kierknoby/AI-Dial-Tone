import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const load=async file=>readFile(new URL('../'+file,import.meta.url),'utf8');

test('public privacy and security notices offer a real consistent maintainer contact without guessing host retention',async()=>{
  const privacy=await load('site/privacy.html');
  const source=await load('tools/privacy-body.html');
  const security=await load('SECURITY.md');
  const readme=await load('README.md');
  for(const text of [privacy,source,security,readme])assert.match(text,/ai@dial-tone\.uk/);
  for(const text of [privacy,source,security,readme])assert.doesNotMatch(text,/kieran@freepbx\.uk/);
  assert.match(privacy,/ICO|Information Commissioner/);
  assert.match(privacy,/hosting provider|host.*retention/i);
  assert.doesNotMatch(privacy,/Operator contact and statutory company details must be verified/);
  assert.match(security,/before sending exploits, credentials, recordings or sensitive logs/);
  assert.match(security,/not yet confirmed to be enabled/);
});

test('one clear quickstart promises exactly local evidence',async()=>{
  const readme=await load('README.md');
  const first=await load('FIRST-CALL.md');
  const verifier=await load('tools/verify_first_call.py');
  for(const s of [readme,first]){
    assert.match(s,/python tools\/verify_first_call\.py --out demo-output/);
    assert.match(s,/aiohttp==3\.13\.3/);
    assert.match(s,/does not|not.*PSTN|not.*dial|no real/i);
  }
  assert.match(first,/'?"?real_pstn_call_verified"?: false/i);
  assert.match(verifier,/'real_pstn_call_verified':False/);
});

test('personal-development and Egyptian Eyes preparation are accurately attributed, with a separate abuse route',async()=>{
  const files=['README.md','SECURITY.md','PUBLISHING.md','PRODUCT-SCOPE.md','site/about.html','site/privacy.html','site/trust.html','site/faqs.html','site/docs/origins.html','site/api/faqs.json'];
  for (const path of files){
    const s=await load(path);
    assert.match(s,/Egyptian Eyes|Egyptian Eyes project/,path);
  }
  for(const path of files.filter(x=>x!=='site/about.html')){
    assert.match(await load(path),/dial-tone@egyptianeyes\.com/,path);
  }
  for(const path of ['site/privacy.html','SECURITY.md','README.md']){
    const s=await load(path);
    assert.match(s,/ai@dial-tone\.uk/,path);
    assert.match(s,/dial-tone@egyptianeyes\.com/,path);
    assert.doesNotMatch(s,/kieran@freepbx\.uk/,path);
  }
  const privacy=await load('site/privacy.html');
  const policy=await load('SECURITY.md');
  assert.match(privacy,/personal development space/);
  assert.match(privacy,/does not establish that Egyptian Eyes is already the operator/);
  assert.match(policy,/not an emergency response service/);
  assert.match(policy,/before sending exploits, credentials, recordings or sensitive logs/);
  const overview=await load('content/project-overview.md');
  const readme=await load('README.md');
  assert.ok(readme.includes(overview.trim()),'approved project overview must remain verbatim');
});
