export function validateConfig({wss,aor,user,password}) {
  if (!/^wss:\/\/[a-z0-9.-]+(?::\d+)?(?:\/[\w./-]*)?$/i.test(wss||'')) throw Error('Use a secure WSS SIP endpoint');
  if (!/^sip:[a-z0-9_.+-]+@[a-z0-9.-]+$/i.test(aor||'')) throw Error('Invalid SIP address');
  if (!user || !password) throw Error('SIP username and password are required');
  return {wss,aor,user,password};
}
export function destinationURI(value,domain) {
  if (!/^[a-z0-9.-]+$/i.test(domain||'')) throw Error('Invalid SIP domain');
  if (!/^[*#0-9]{1,32}$/.test(value||'')) throw Error('Dial digits or PBX feature codes only');
  return `sip:${value}@${domain}`;
}
export function readiness({registered, microphone, websocket, media, options}) {
  const checks={registered:!!registered,microphone:!!microphone,websocket:!!websocket,media:!!media};
  const ok=Object.values(checks).every(Boolean);
  return {status:ok?'LOCAL READY':'NOT READY',checks,options:options??'NOT TESTED',pstn:'NOT TESTED'};
}
