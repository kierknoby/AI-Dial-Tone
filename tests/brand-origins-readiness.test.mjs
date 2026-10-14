import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const get=p=>readFile(new URL(p,root),'utf8');
const load=async p=>JSON.parse(await get(p));

test('only the six approved colours appear in public and laboratory presentation; one accent per page', async()=>{
 const permitted=new Set(['#000000','#ffffff','#dedede','#808080','#c29200','#30beff']);
 const files=['site/assets/style.css','site/assets/reference.css','site/assets/faq.css','site/assets/logo.svg','site/assets/social.svg','site/site.webmanifest','labs/web-softphone/src/style.css'];
 for(const path of files){
  const data=await get(path);
  const colours=data.match(/#[0-9a-fA-F]{3,8}\b/g)||[];
  for(const colour of colours)assert.ok(permitted.has(colour.toLowerCase()),`unapproved colour ${colour} in ${path}`);
 }
 const style=await get('site/assets/style.css');
 assert.match(style, /--grey-mid:\s*#808080/);
 assert.match(style, /\.section-cream \.feature-icon \{ color: #808080; \}/);
 assert.match(style,/body\[data-palette="gold"\]\{--accent:#c29200;--red:#c29200/);
 assert.match(style,/body\[data-palette="blue"\]\{--accent:#30beff;--red:#30beff/);
 const logo=await get('site/assets/logo.svg');
 const social=await get('site/assets/social.svg');
 for(const neutral of ['#000000','#dedede'])assert.ok(logo.includes(neutral),`neutral mark missing ${neutral}`);
 for(const accent of ['#c29200','#30beff'])assert.ok(!logo.includes(accent) && !social.includes(accent),`shared brand asset mixes accents: ${accent}`);
 for(const [file,expected] of [['site/index.html','gold'],['site/agents.html','blue'],['site/developers.html','blue'],['site/playground.html','blue'],['site/docs/index.html','blue'],['site/overview.html','gold']]){
  const data=await get(file);
  assert.ok(data.includes(`<body data-palette="${expected}">`),`incorrect page accent on ${file}`);
 }
});

test('homepage and dedicated public pages have attributable provenance and a meaningful readiness promise',async()=>{
 const home=await get('site/index.html');
 const about=await get('site/about.html');
 const readiness=await get('site/readiness.html');
 const readme=await get('README.md');
 for(const link of ['https://20tele.com/','https://freepbx.uk/','https://github.com/kierknoby','https://github.com/freepbxUK/registrationwatch','https://github.com/kierknoby/repeatcaller','https://github.com/kierknoby/concurrencycount']){
  assert.ok(about.includes(link),`source missing from about page: ${link}`);
 }
 assert.match(about,/Kieran Knowles-Byrne/);
 assert.match(readme,/Kieran Knowles-Byrne/);
 assert.match(readiness,/SIP OPTIONS/);
 assert.match(readiness,/never confuse a reachable PBX with a guaranteed completed call/i);
 assert.match(home,/<h1>Give your AI<br><em>Dial-Tone<\/em><\/h1>/);
 assert.match(home,/x402 for managed calling/);
 assert.doesNotMatch(home,/<section[^>]*readiness-home/);
 assert.doesNotMatch(home,/<h1>Know the route/);
 assert.doesNotMatch(home,/<nav class="nav-links"[^>]*>[\s\S]*?<a class="nav-link[^"]*" href="\/readiness\.html"/);
 assert.ok(home.includes('href="/readiness.html"'));
 assert.ok(home.includes('href="/about.html"'));
 assert.match(about,/independent.*(?:Sangoma|MicroSIP)|(?:Sangoma|MicroSIP).*independent/is);
});

test('agent discovery points to real origin and preflight documents while refusing live-call claims',async()=>{
 const agent=await load('site/agents.json');
 assert.equal(agent.links.pre_call_principle,'/readiness.html');
 assert.equal(agent.links.pre_call_engineering,'/docs/pre-call-principle.html');
 assert.equal(agent.links.author_and_origins,'/about.html');
 assert.equal(agent.links.open_source_community,'/docs/origins.html');
 assert.equal(agent.available_now.local_operator_only_byot_endpoint_readiness_probe,true);
 assert.equal(agent.available_now.public_live_calling,false);
 assert.equal(agent.available_now.real_asterisk_interoperability_verified,false);
});

test('read-only Asterisk preflight neither originates a call nor grants an operator mandate',async()=>{
 const src=await get('byot/server.py');
 const start=src.indexOf('async def endpoint_readiness(req):');
 const end=src.indexOf('\nasync def ',start+1);
 assert.ok(start>=0,'missing read-only endpoint');
 const body=src.slice(start,end<0?src.length:end);
 assert.match(body,/m\.auth\(req, 'operator'\)/);
 assert.match(body,/m\.settings\.trunk/);
 assert.match(body,/m\.ari\.request\('GET'/);
 assert.match(body,/'network_call_authorised':False/);
 assert.match(body,/'sip_options_2xx_verified':False/);
 assert.match(body,/'pbx_route_policy_verified':False/);
 assert.doesNotMatch(body,/\b(?:originate|create_mandate|issue_ticket)\(/);
});

test('documentation differentiates audible local dial tone from a verified live carrier route',async()=>{
 const d=await get('content/docs/24-pre-call-principle.md');
 assert.match(d,/local audible dial tone/i);
 assert.match(d,/not.*a guarantee/i);
 assert.match(d,/No fully non-dialling preflight can guarantee/i);
 assert.match(d,/network_call_authorised/);
 const faq=await load('content/faqs.json');
 const qs=JSON.stringify(faq);
 assert.match(qs,/can (?:it|the system) actually make a call|readiness|route/i);
});
