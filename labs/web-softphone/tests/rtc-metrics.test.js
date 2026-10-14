import test from 'node:test';import assert from 'node:assert/strict';
import {summariseRTCStats} from '../src/rtc-metrics.js';
test('summarises packet loss, jitter and RTT but redacts IP and candidates',()=>{
 const report=new Map([
 ['in',{type:'inbound-rtp',kind:'audio',packetsReceived:400,packetsLost:10,bytesReceived:120000,jitter:.013457,localCandidateId:'a'}],
 ['out',{type:'outbound-rtp',kind:'audio',packetsSent:410,bytesSent:123456}],
 ['remote',{type:'remote-inbound-rtp',kind:'audio',roundTripTime:.035}],
 ['candidate',{type:'local-candidate',address:'192.168.1.1',port:1234}],
 ['pair',{type:'candidate-pair',nominated:true,state:'succeeded',currentRoundTripTime:.042}]
 ]);
 const r=summariseRTCStats(report);
 assert.deepEqual(r,{available:true,inbound:{packets:400,lost:10,jitterMs:13.46,bytes:120000},outbound:{packets:410,bytes:123456},rttMs:35});
 assert(!JSON.stringify(r).includes('192.168.1.1'));
});
test('missing or malformed stats are reported as unavailable',()=>assert.deepEqual(summariseRTCStats(null),{available:false}));
