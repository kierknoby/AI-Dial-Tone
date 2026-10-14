/** Local-only, read-only static preview. Does not proxy tokens or connect to a PBX. */
import {createServer} from 'node:http';
import {readFile,stat,realpath} from 'node:fs/promises';
import {resolve,extname,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=resolve(fileURLToPath(new URL('../site/',import.meta.url)));
const port=Number(process.env.DIALTONE_WEB_PORT||4173);
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8',
  '.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8','.svg':'image/svg+xml',
  '.webmanifest':'application/manifest+json','.txt':'text/plain; charset=utf-8'};
const csp="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; manifest-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'";
function headers(res){
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Cross-Origin-Resource-Policy','same-origin');
  res.setHeader('X-Frame-Options','DENY');
  res.setHeader('Content-Security-Policy',csp);
  res.setHeader('Cache-Control','no-store');
}
function error(res,status,code){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify({error:code}));}
function trustedHost(host){return /^(?:localhost|127\.0\.0\.1|\[::1\])(?::\d{1,5})?$/.test(host||'');}
export const server=createServer(async(req,res)=>{
  headers(res);
  if(!trustedHost(req.headers.host))return error(res,403,'LOCALHOST_ONLY');
  if(req.method!=='GET'&&req.method!=='HEAD')return error(res,405,'METHOD_NOT_ALLOWED');
  let pathname;
  try{pathname=decodeURIComponent(new URL(req.url,`http://${req.headers.host}`).pathname);}
  catch{return error(res,400,'BAD_PATH');}
  if(pathname==='/' )pathname='/index.html';
  if(pathname.includes('\0')||pathname.includes('\\')||pathname.split('/').some(x=>x.startsWith('.')&&x.length>1))return error(res,404,'NOT_FOUND');
  const filename=resolve(root,'.'+pathname);
  if(filename!==root&&!filename.startsWith(root+sep))return error(res,404,'NOT_FOUND');
  let data,contentType;
  try{
    const actual=await realpath(filename);
    if(actual!==root&&!actual.startsWith(root+sep))return error(res,404,'NOT_FOUND');
    if(!(await stat(actual)).isFile())throw Error('NOT_A_FILE');
    data=await readFile(actual);
    contentType=mime[extname(actual)]||'application/octet-stream';
  }catch{
    if(pathname.endsWith('.html')||!extname(pathname)){
      data=await readFile(resolve(root,'404.html'));
      contentType=mime['.html'];
      res.writeHead(404,{'Content-Type':contentType});
      if(req.method==='HEAD')res.end();else res.end(data);
      return;
    }
    return error(res,404,'NOT_FOUND');
  }
  res.writeHead(200,{'Content-Type':contentType,'Content-Length':data.length});
  if(req.method==='HEAD')res.end();else res.end(data);
});
if(import.meta.url===`file://${process.argv[1]}`){
  if(!Number.isInteger(port)||port<1024||port>65535)throw Error('INVALID_LOCAL_PORT');
  server.listen(port,'127.0.0.1',()=>console.log(`AI Dial-Tone static preview http://127.0.0.1:${port}/`));
}
