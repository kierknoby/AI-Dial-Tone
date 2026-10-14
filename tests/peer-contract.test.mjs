import test from 'node:test';
import assert from 'node:assert/strict';
import {validateReservationMandate,evaluateDialTonePreflight,assessReservationEvidence,CONTRACT_VERSION} from '../lib/peer-contract.mjs';
const now=new Date('2026-10-10T19:00:00.000Z');
const fixture=()=>({version:CONTRACT_VERSION,mandate_id:'mandate_0123456789ab',human_principal:'human:123',agent_id:'bot.reservations',issued_at:'2026-10-10T18:59:00Z',expires_at:'2026-10-10T19:10:00Z',human_approved:true,task:{kind:'restaurant_reservation',restaurant_name:'Example restaurant',destination:'+442079460123',party_size:2,date:'2026-10-17',earliest:'19:00',latest:'20:30',customer_name:'Test Guest',book_authorised:true,deposit_authorised:false,recording_authorised:false},limits:{max_call_seconds:120,max_total_gbp_pence:99,max_attempts:1}});
const readiness=()=>({observed_at:'2026-10-10T18:59:55Z',registered:true,options_status:200,options_rtt_ms:55,audio_device_ready:true,codec_ready:true,sip_transport:'tls',peer_certificate_verified:true,srtp_policy:'mandatory',isolated_route_policy_verified:true});
const invalid=(data,code)=>assert.throws(()=>validateReservationMandate(data,{now}),{code});
test('bounded human reservation mandate accepted but identity explicitly remains unverified',()=>{
 const grant=validateReservationMandate(fixture(),{now});assert.equal(grant.shape_valid,true);assert.equal(grant.network_call_authorised,false);assert.equal(grant.requires_server_verified_human_mandate,true);assert.equal(grant.verified_human_identity,false);assert.equal(grant.scope,'reservation_inquiry_and_booking');assert.equal(grant.deposit_allowed,false);
});
test('missing human approval rejected',()=>{const x=fixture();x.human_approved=false;invalid(x,'HUMAN_APPROVAL_REQUIRED');});
test('expired, overlong and future-issued mandates rejected',()=>{
 for(const [field,val] of [['expires_at','2026-10-10T18:55:00Z'],['expires_at','2026-10-12T19:01:00Z'],['issued_at','2026-10-10T20:00:00Z']]){const x=fixture();x[field]=val;invalid(x,'MANDATE_EXPIRED_OR_INVALID');}
});
test('UK geographic only; no emergency, premium, international, mobile or SIP URI injection',()=>{
 for(const number of ['999','112','+449001234567','+448441234567','+33123456789','+447700900123','sip:1001@pbx.example','+442079460123;transport=udp','+442079460123\r\nINVITE']){const x=fixture();x.task.destination=number;invalid(x,'DESTINATION_NOT_ALLOWED');}
});
test('booking/deposit/recording boundaries fail closed',()=>{
 for(const [key,value,code] of [['book_authorised',false,'BOOKING_NOT_AUTHORISED'],['deposit_authorised',true,'DEPOSIT_NOT_ALLOWED'],['recording_authorised',true,'RECORDING_NOT_ALLOWED']]){const x=fixture();x.task[key]=value;invalid(x,code);}
});
test('constraints reject unsupported scope expansion or repeated unattended attempts',()=>{
 const cases=[['task.party_size',0,'INVALID_PARTY_SIZE'],['task.date','2026-02-30','INVALID_RESERVATION_DATE'],['task.earliest','25:00','INVALID_TIME_WINDOW'],['limits.max_call_seconds',100000,'CALL_DEADLINE_INVALID'],['limits.max_total_gbp_pence',9999,'SPEND_LIMIT_INVALID'],['limits.max_attempts',3,'RETRIES_REQUIRE_NEW_APPROVAL']];
 for(const [path,val,code] of cases){const x=fixture();const [section,key]=path.split('.');x[section][key]=val;invalid(x,code);}
 const x=fixture();x.task.credit_card='123';invalid(x,'TASK_UNEXPECTED_FIELD');
});
test('native-like SIP readiness is explicitly not a PSTN or booking assurance',()=>{
 const r=evaluateDialTonePreflight(readiness(),{now});assert.equal(r.lab_policy_input_acceptable,true);assert.equal(r.network_call_authorised,false);assert.equal(r.observation_authenticity_verified,false);assert.ok(r.not_proven.includes('PSTN_REACHABILITY'));assert.ok(r.not_proven.includes('RESERVATION_AVAILABILITY'));
});
test('SIP preflight rejects optional or disabled SRTP, clear SIP and missing certificate validation',()=>{
 const cases=[['srtp_policy','optional','MANDATORY_MEDIA_ENCRYPTION_REQUIRED'],['srtp_policy','disabled','MANDATORY_MEDIA_ENCRYPTION_REQUIRED'],['sip_transport','udp','SECURE_SIP_REQUIRED'],['peer_certificate_verified',false,'SECURE_SIP_REQUIRED']];
 for(const [field,val,error] of cases){const r=readiness();r[field]=val;const res=evaluateDialTonePreflight(r,{now});assert.equal(res.lab_policy_input_acceptable,false);assert.ok(res.failures.includes(error));}
});
test('SIP preflight rejects stale OPTIONS, failed auth, latency and unverified route isolation',()=>{
 for(const [field,val,error] of [['observed_at','2026-10-10T18:58:00Z','STALE_READINESS'],['options_status',401,'OPTIONS_NOT_SUCCESSFUL'],['options_rtt_ms',1200,'OPTIONS_DEGRADED'],['isolated_route_policy_verified',false,'PBX_ROUTE_POLICY_UNVERIFIED']]){const r=readiness();r[field]=val;assert.ok(evaluateDialTonePreflight(r,{now}).failures.includes(error));}
});
test('model claims never become independent booking confirmation',()=>{
 const a=assessReservationEvidence({call_state:'ended',provider_hangup_confirmed:true,agent_report:{status:'claimed_booked',summary:'Booked for two'}});
 assert.equal(a.booking_status,'agent_reported_unverified');assert.equal(a.network_release_claim_consistent,true);assert.equal(a.network_termination_verified,false);
});
test('hangup requested is not provider-confirmed termination',()=>{
 const a=assessReservationEvidence({call_state:'ending',agent_report:{status:'claimed_booked',summary:'I think yes'}});
 assert.equal(a.network_release_claim_consistent,false);assert.equal(a.network_termination_verified,false);assert.equal(a.requires_provider_verification,true);
});
test('untrusted independent-confirmation boolean never upgrades agent claims',()=>{
 const a=assessReservationEvidence({call_state:'ended',provider_hangup_confirmed:true,agent_report:{status:'claimed_booked',summary:'Reference 1234'},independent_booking_confirmation:true});
 assert.equal(a.booking_status,'agent_reported_unverified');assert.equal(a.client_claims_independent_confirmation,true);
 const b=assessReservationEvidence({call_state:'failed',provider_hangup_confirmed:false,agent_report:{status:'claimed_booked',summary:'Reference 1234'},independent_booking_confirmation:true});
 assert.notEqual(b.booking_status,'independently_verified');
});
test('malformed states or missing trust assertions rejected',()=>{
 assert.throws(()=>assessReservationEvidence({call_state:'success'}),{code:'INVALID_CALL_STATE'});
 const r=evaluateDialTonePreflight({...readiness(),registered:false},{now});assert.ok(r.failures.includes('REGISTRATION_NOT_READY'));
});
