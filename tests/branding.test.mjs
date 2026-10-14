import test from 'node:test';
import assert from 'node:assert/strict';
import {readdir,readFile} from 'node:fs/promises';
import {join,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../site/',import.meta.url));
async function htmlFiles(path=root){let out=[];for(const name of await readdir(path,{withFileTypes:true})){const entry=join(path,name.name);if(name.isDirectory())out.push(...await htmlFiles(entry));else if(entry.endsWith('.html')&&name.name!=='404.html')out.push(entry);}return out;}
test('all public pages have distinct canonical and OpenGraph URLs at ai.dial-tone.uk',async()=>{
 let seen=new Set();const html=await htmlFiles();assert.ok(html.length>=30);
 for(const file of html){const urlPath=relative(root,file).split('\\').join('/');const canonical='https://ai.dial-tone.uk'+(urlPath==='index.html'?'/':'/'+urlPath);const content=await readFile(file,'utf8');
  assert.ok(content.includes(`<link rel="canonical" href="${canonical}">`),file);
  assert.ok(content.includes(`<meta property="og:url" content="${canonical}">`),file);
  assert.equal((content.match(/<link rel="canonical" /g)||[]).length,1,`${file}: canonical must appear exactly once`);
  assert.equal((content.match(/<meta property="og:url" /g)||[]).length,1,`${file}: og:url must appear exactly once`);
  assert.ok(!seen.has(canonical));seen.add(canonical);
 }
});
test('agent discovery identifies the intended site and the simulated release accurately',async()=>{
 const m=JSON.parse(await readFile(join(root,'agents.json'),'utf8'));
 assert.equal(m.name,'AI Dial-Tone');assert.equal(m.origin,'https://ai.dial-tone.uk');
 assert.equal(m.available_now.public_live_calling,false);
 const sitemap=await readFile(join(root,'sitemap.xml'),'utf8');assert.equal((sitemap.match(/<loc>/g)||[]).length,(await htmlFiles()).length);
 assert.match(await readFile(join(root,'robots.txt'),'utf8'),/Sitemap: https:\/\/ai\.dial-tone\.uk\/sitemap\.xml/);
});
