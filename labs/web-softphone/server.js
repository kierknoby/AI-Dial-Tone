import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'src');
const allowed=new Set(['/','/app.js','/policy.js','/agent-protocol.js','/agent-bridge.js','/bot-audio.js','/bot-session.js','/rtc-metrics.js','/audio-codec.js','/audio-worklet.js','/style.css','/vendor/sip.js']);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
export const server=createServer(async(req,res)=>{
 const path=new URL(req.url,'http://127.0.0.1').pathname;
 if(req.method!=='GET'||!allowed.has(path)){res.writeHead(404);res.end('Not found');return;}
 try{
  const body=await readFile(resolve(root,path==='/'?'index.html':path.slice(1)));
  res.writeHead(200,{'Content-Type':types[extname(path==='/'?'index.html':path)],'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Cross-Origin-Resource-Policy':'same-origin','Permissions-Policy':'camera=(), microphone=(self), geolocation=()','Content-Security-Policy':"default-src 'self'; script-src 'self'; connect-src 'self' wss:; style-src 'self'; media-src 'self' blob:; worker-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"});res.end(body);
 }catch{res.writeHead(500);res.end('File error');}
});
if(process.argv[1]&&import.meta.filename===resolve(process.argv[1])){
 const port=Number(process.env.PORT||8787);server.listen(port,'127.0.0.1',()=>console.log(`AI Dial-Tone Browser SIP Lab http://127.0.0.1:${port}`));
}
