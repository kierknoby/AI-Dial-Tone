import {readFile,readdir,stat} from 'node:fs/promises';
import {join} from 'node:path';
const site=new URL('../site/',import.meta.url);
const root=site.pathname;
const files=[];
async function walk(path){for(const n of await readdir(path)){const p=join(path,n),s=await stat(p);if(s.isDirectory())await walk(p);else files.push(p);}}
await walk(root);
const htmlFiles=files.filter(x=>x.endsWith('.html'));
const violations=[];
for(const f of htmlFiles){
  const value=await readFile(f,'utf8');
  if(!value.includes('<main id="main">'))violations.push(`${f}: missing main landmark`);
  if(!value.includes('TECHNICAL PREVIEW'))violations.push(`${f}: missing preview warning`);
  if(/<script(?![^>]*src=)[^>]*>\s*[^<]/.test(value))violations.push(`${f}: inline script`);
  for(const m of value.matchAll(/(?:href|src)="(\/[^"#?]+)(?:#[^"]*)?"/g)){
    const path=m[1]==='/'?'/index.html':m[1];
    if(!files.includes(join(root,path)))violations.push(`${f}: broken link ${path}`);
  }
}
for(const f of files){
 const raw=await readFile(f,'utf8');
 if(/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(raw))violations.push(`${f}: private key`);
 if(/(?:sk-proj-|sk_live_|ghp_)[A-Za-z0-9]{12}/.test(raw))violations.push(`${f}: secret-shaped token`);
}
if(violations.length){console.error(violations.join('\n'));process.exit(1);}
console.log(`Publication audit passed: ${htmlFiles.length} HTML pages, ${files.length} assets and documents, no inline scripts or unresolvable site links.`);
