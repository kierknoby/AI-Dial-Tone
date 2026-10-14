import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const load=async path=>readFile(new URL(path,root),'utf8');

test('canonical Project Overview appears verbatim in the root README',async()=>{
  const canonical=(await load('content/project-overview.md')).trim();
  const readme=await load('README.md');
  const exact='## Project Overview\n'+canonical.slice('# Project Overview\n'.length);
  assert.ok(readme.includes(exact),'README must reproduce the user-approved Overview without edits');
  assert.ok(readme.indexOf('## Project Overview')<readme.indexOf('## Release Status'));
});

test('website includes all canonical Project Overview paragraphs, in order',async()=>{
  const original=(await load('content/project-overview.md')).trim();
  const paragraphs=original.split(/\n\n+/).slice(1);
  assert.equal(paragraphs.length,11,'unexpected change to the approved 11-paragraph description');
  const page=await load('site/overview.html');
  const match=page.match(/<article class="overview-article"[^>]*>([\s\S]*?)<\/article>/);
  assert.ok(match,'missing Project Overview article');
  const actual=[...match[1].matchAll(/<p>([^<]*)<\/p>/g)].map(m=>m[1]);
  assert.deepEqual(actual,paragraphs,'website must preserve every word, punctuation mark and paragraph');
  assert.match(page,/TECHNICAL PREVIEW/);
  assert.match(page,/<link rel="canonical" href="https:\/\/ai\.dial-tone\.uk\/overview\.html">/);
});

test('Project Overview is prominent on the homepage, linked in navigation and discoverable to agents',async()=>{
 const home=await load('site/index.html');
 const overview=(await load('content/project-overview.md')).trim().split(/\n\n+/);
 assert.ok(home.includes(overview[1]));
 assert.ok(home.includes(overview.at(-1)));
 assert.match(home,/Read the complete Project Overview/);
 assert.match(home,/href="\/overview\.html"/);
 assert.match(await load('site/llms.txt'),/Canonical Project Overview: \/overview.html/);
 const agent=JSON.parse(await load('site/agents.json'));
 assert.equal(agent.links.project_overview,'/overview.html');
 assert.match(await load('site/sitemap.xml'),/https:\/\/ai\.dial-tone\.uk\/overview\.html/);
});
