/** AI Dial-Tone peer contract LAB ONLY.
 * Pure, dependency-free decisions. NOT human authentication, SIP, PSTN, x402,
 * A2A, MCP hosting, payment verification, or a live reservation provider.
 */
export const CONTRACT_VERSION = 'dialtone.peer.task.v1';
export const LAB_ONLY = true;

export class PeerContractError extends Error {
  constructor(code) { super(code); this.name = 'PeerContractError'; this.code = code; }
}
function must(condition, code) { if (!condition) throw new PeerContractError(code); }
const isObject = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const limited = (v, min, max) => typeof v === 'string' && v.length >= min && v.length <= max && !/[\x00-\x1f\x7f]/.test(v);
const isoDate = d => {
  if(!/^\d{4}-\d{2}-\d{2}$/.test(d||''))return false;
  const stamp=new Date(`${d}T12:00:00Z`);
  return Number.isFinite(stamp.getTime()) && stamp.toISOString().startsWith(`${d}T`);
};
const hhmm = t => /^([01]\d|2[0-3]):[0-5]\d$/.test(t||'');
const strictUkGeo = n => /^\+44[12]\d{9}$/.test(n||'');
const allowedKeys=(o,allowed,code)=>must(Object.keys(o).every(k=>allowed.includes(k)),code);

/** Defensive shape check, NOT proof the human really approved a call. A live
 * service MUST issue and verify a server-side signed/recorded mandate. */
export function validateReservationMandate(input,{now=new Date()}={}) {
  must(isObject(input), 'MANDATE_OBJECT_REQUIRED');
  allowedKeys(input,['version','mandate_id','human_principal','agent_id','issued_at','expires_at','human_approved','task','limits'], 'MANDATE_UNEXPECTED_FIELD');
  must(input.version===CONTRACT_VERSION,'UNSUPPORTED_CONTRACT_VERSION');
  must(limited(input.mandate_id,16,128) && /^[A-Za-z0-9_-]+$/.test(input.mandate_id),'INVALID_MANDATE_ID');
  must(limited(input.human_principal,3,100) && /^[A-Za-z0-9_.:@-]+$/.test(input.human_principal),'INVALID_HUMAN_PRINCIPAL');
  must(limited(input.agent_id,3,100) && /^[A-Za-z0-9_.:@-]+$/.test(input.agent_id),'INVALID_AGENT_ID');
  must(input.human_approved===true,'HUMAN_APPROVAL_REQUIRED');
  const issued=Date.parse(input.issued_at), expires=Date.parse(input.expires_at), current=new Date(now).getTime();
  must(Number.isFinite(current)&&Number.isFinite(issued)&&Number.isFinite(expires),'INVALID_MANDATE_TIME');
  must(issued<=current+30_000 && current<expires && expires-issued<=86_400_000,'MANDATE_EXPIRED_OR_INVALID');
  must(isObject(input.task),'TASK_OBJECT_REQUIRED');
  const task=input.task;
  allowedKeys(task,['kind','restaurant_name','destination','party_size','date','earliest','latest','customer_name','instructions','book_authorised','deposit_authorised','recording_authorised'], 'TASK_UNEXPECTED_FIELD');
  must(task.kind==='restaurant_reservation','UNSUPPORTED_TASK_KIND');
  must(limited(task.restaurant_name,2,120),'INVALID_RESTAURANT');
  must(strictUkGeo(task.destination),'DESTINATION_NOT_ALLOWED');
  must(Number.isSafeInteger(task.party_size)&&task.party_size>=1&&task.party_size<=12,'INVALID_PARTY_SIZE');
  must(isoDate(task.date),'INVALID_RESERVATION_DATE');
  must(task.date>=new Date(current).toISOString().slice(0,10),'PAST_RESERVATION_DATE');
  must(hhmm(task.earliest)&&hhmm(task.latest)&&task.earliest<=task.latest,'INVALID_TIME_WINDOW');
  must(limited(task.customer_name,2,80),'INVALID_CUSTOMER_NAME');
  must(!task.instructions || limited(task.instructions,1,500),'INVALID_INSTRUCTIONS');
  must(task.book_authorised===true,'BOOKING_NOT_AUTHORISED');
  must(task.deposit_authorised===false,'DEPOSIT_NOT_ALLOWED');
  must(task.recording_authorised===false,'RECORDING_NOT_ALLOWED');
  must(isObject(input.limits),'LIMITS_OBJECT_REQUIRED');
  allowedKeys(input.limits,['max_call_seconds','max_total_gbp_pence','max_attempts'],'LIMITS_UNEXPECTED_FIELD');
  must(Number.isSafeInteger(input.limits.max_call_seconds)&&input.limits.max_call_seconds>=30&&input.limits.max_call_seconds<=300,'CALL_DEADLINE_INVALID');
  must(Number.isSafeInteger(input.limits.max_total_gbp_pence)&&input.limits.max_total_gbp_pence>=0&&input.limits.max_total_gbp_pence<=500,'SPEND_LIMIT_INVALID');
  must(input.limits.max_attempts===1,'RETRIES_REQUIRE_NEW_APPROVAL');
  return Object.freeze({shape_valid:true,network_call_authorised:false,requires_server_verified_human_mandate:true,version:CONTRACT_VERSION,mandate_id:input.mandate_id,agent_id:input.agent_id,destination:task.destination,call_seconds:input.limits.max_call_seconds,spend_pence:input.limits.max_total_gbp_pence,scope:'reservation_inquiry_and_booking',recording_allowed:false,deposit_allowed:false,verified_human_identity:false});
}

/** A real SIP 2xx OPTIONS means that the responding SIP endpoint is reachable;
 * it does not test PSTN routing, remote media or the destination business. */
export function evaluateDialTonePreflight(input,{now=new Date()}={}){
  must(isObject(input),'PREFLIGHT_OBJECT_REQUIRED');
  const failures=[];
  const fresh = typeof input.observed_at==='string' && Number.isFinite(Date.parse(input.observed_at)) &&
    new Date(now).getTime() - Date.parse(input.observed_at) >= 0 &&
    new Date(now).getTime() - Date.parse(input.observed_at) <= 60_000;
  if(!fresh)failures.push('STALE_READINESS');
  if(input.registered!==true)failures.push('REGISTRATION_NOT_READY');
  if(!Number.isInteger(input.options_status)||input.options_status<200||input.options_status>=300)failures.push('OPTIONS_NOT_SUCCESSFUL');
  if(!Number.isFinite(input.options_rtt_ms)||input.options_rtt_ms<0||input.options_rtt_ms>1000)failures.push('OPTIONS_DEGRADED');
  if(input.audio_device_ready!==true)failures.push('AUDIO_NOT_READY');
  if(input.codec_ready!==true)failures.push('CODEC_NOT_READY');
  if(input.sip_transport!=='tls' || input.peer_certificate_verified!==true)failures.push('SECURE_SIP_REQUIRED');
  if(!['mandatory','dtls'].includes(input.srtp_policy))failures.push('MANDATORY_MEDIA_ENCRYPTION_REQUIRED');
  if(input.isolated_route_policy_verified!==true)failures.push('PBX_ROUTE_POLICY_UNVERIFIED');
  return Object.freeze({
    lab_policy_input_acceptable: failures.length===0,
    network_call_authorised:false,
    observation_authenticity_verified:false,
    state:failures.length?'PREFLIGHT_BLOCKED':'SIP_PREFLIGHT_INPUT_ACCEPTABLE_NOT_VERIFIED',
    not_proven:['PSTN_REACHABILITY','INVITE_SUCCESS','REMOTE_ANSWER','BIDIRECTIONAL_AUDIO','RESERVATION_AVAILABILITY'],
    failures
  });
}

/** Keep provider signalling, agent interpretation and independently verified
 * business results in separate evidence categories. */
export function assessReservationEvidence({call_state,provider_hangup_confirmed=false,agent_report,independent_booking_confirmation=false}={}){
  must(['dialling','ringing','answered','ending','ended','failed','needs_reconciliation'].includes(call_state),'INVALID_CALL_STATE');
  const terminal=['ended','failed'].includes(call_state);
  const release_claim_consistent=terminal && provider_hangup_confirmed===true;
  // This utility cannot authenticate a provider event. The private backend
  // must verify a provider signature/channel binding before declaring release.
  const reported=Boolean(isObject(agent_report)&&agent_report.status==='claimed_booked'&&limited(agent_report.summary,1,1000));
  // Caller-supplied boolean is NOT independent evidence. This pure library has
  // no trusted reservation-system integration or signature verification.
  return Object.freeze({network_release_claim_consistent:release_claim_consistent,network_termination_verified:false,agent_claim_recorded:reported,
    booking_status:reported?'agent_reported_unverified':'not_reported',
    client_claims_independent_confirmation:independent_booking_confirmation===true,
    requires_provider_verification:true,
    human_message:reported?'Agent reported a booking; independently verify the reservation':'No verified reservation result'});
}
