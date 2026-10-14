import test from 'node:test';import assert from 'node:assert/strict';
import {validateConfig,destinationURI,readiness} from '../src/policy.js';
test('validates WSS Asterisk account config',()=>{
 assert.equal(validateConfig({wss:'wss://pbx.example.com:8089/ws',aor:'sip:1001@example.com',user:'1001',password:'secret'}).user,'1001');
 assert.throws(()=>validateConfig({wss:'ws://pbx.example.com/ws',aor:'sip:1001@example.com',user:'1001',password:'secret'}));
});
test('builds a SIP URI without allowing injection',()=>{
 assert.equal(destinationURI('1002','example.com'),'sip:1002@example.com');
 assert.throws(()=>destinationURI('1002@evil','example.com'));
 assert.throws(()=>destinationURI('1002','a.com@evil.com'));
});
test('local readiness never means proven PSTN or OPTIONS connectivity',()=>{
 const report=readiness({registered:true,microphone:true,websocket:true,media:true});
 assert.equal(report.status,'LOCAL READY');assert.equal(report.options,'NOT TESTED');assert.equal(report.pstn,'NOT TESTED');
});
