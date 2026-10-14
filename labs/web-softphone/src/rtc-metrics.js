// Public, privacy-minimised WebRTC audio metrics. Never export ICE candidate IPs,
// device identities, or raw RTCStats (which can contain local network addresses).
function number(v){return typeof v==='number'&&Number.isFinite(v)?v:null;}
function round(v,digits=2){return v===null?null:Number(v.toFixed(digits));}
export function summariseRTCStats(report){
 if(!report||typeof report.values!=='function')return {available:false};
 let inbound=null,outbound=null,remoteOutbound=null,remoteInbound=null,pair=null;
 for(const row of report.values()){
  if(row.type==='inbound-rtp' && !row.isRemote && (row.kind==='audio'||row.mediaType==='audio'))inbound=row;
  if(row.type==='outbound-rtp' && !row.isRemote && (row.kind==='audio'||row.mediaType==='audio'))outbound=row;
  if(row.type==='remote-inbound-rtp' && (row.kind==='audio'||row.mediaType==='audio'))remoteInbound=row;
  if(row.type==='candidate-pair' && (row.selected===true || (row.nominated===true && row.state==='succeeded')))pair=row;
 }
 if(!inbound&&!outbound)return {available:false};
 return {available:true,
  inbound:inbound?{packets:number(inbound.packetsReceived),lost:number(inbound.packetsLost),jitterMs:round(number(inbound.jitter)===null?null:inbound.jitter*1000),bytes:number(inbound.bytesReceived)}:null,
  outbound:outbound?{packets:number(outbound.packetsSent),bytes:number(outbound.bytesSent)}:null,
  rttMs:round((number(remoteInbound?.roundTripTime)??number(pair?.currentRoundTripTime))===null?null:(number(remoteInbound?.roundTripTime)??number(pair?.currentRoundTripTime))*1000)};
}
