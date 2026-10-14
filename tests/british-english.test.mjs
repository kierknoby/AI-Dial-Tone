import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const root=resolve(new URL('../',import.meta.url).pathname);
const read=async path=>readFile(resolve(root,path),'utf8');

test('all published HTML pages and the browser laboratory declare British English',async()=>{
  const {readdir}=await import('node:fs/promises');
  const pages=(await readdir(resolve(root,'site'))).filter(x=>x.endsWith('.html'));
  const docs=(await readdir(resolve(root,'site/docs'))).filter(x=>x.endsWith('.html')).map(x=>'docs/'+x);
  for(const page of [...pages,...docs]){
    assert.match(await read('site/'+page),/<html lang="en-GB">/i,page);
  }
  assert.match(await read('labs/web-softphone/src/index.html'),/<html lang="en-GB">/i);
});

test('British English spellings are used in published prose, not US forms',async()=>{
  const {readdir}=await import('node:fs/promises');
  const docs=(await readdir(resolve(root,'content/docs'))).filter(x=>x.endsWith('.md')).map(x=>'content/docs/'+x);
  for(const path of [...docs,'content/project-overview.md','site/agents.txt','site/llms.txt']){
    const text=await read(path);
    // Leave protocol headers (for example HTTP Authorization), CSS properties and code identifiers alone.
    const prose=text.replace(/```[\s\S]*?```/g,'');
    assert.doesNotMatch(prose,/\b(?:catalog|artifacts|behavior|behaviors|analyze|analyzed|organize|organization|color|center|dialing|signaling|canceled|canceling)\b/i,path);
  }
});
