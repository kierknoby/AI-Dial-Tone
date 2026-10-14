#!/usr/bin/env node
// Completely synthetic control-policy exercise. No telephone or booking service is contacted.
import {validateReservationMandate,evaluateDialTonePreflight,assessReservationEvidence,CONTRACT_VERSION} from '../lib/peer-contract.mjs';
const now=new Date('2026-10-10T19:00:00.000Z');
const mandate={version:CONTRACT_VERSION,mandate_id:'demo_human_grant_000001',human_principal:'demo-user',agent_id:'demo-reservation-agent',issued_at:'2026-10-10T18:59:00Z',expires_at:'2026-10-10T19:20:00Z',human_approved:true,
 task:{kind:'restaurant_reservation',restaurant_name:'Example Restaurant (fictional)',destination:'+442079460123',party_size:2,date:'2026-10-17',earliest:'19:00',latest:'20:30',customer_name:'Example Guest',instructions:'Ask for a quiet table.',book_authorised:true,deposit_authorised:false,recording_authorised:false},limits:{max_call_seconds:120,max_total_gbp_pence:100,max_attempts:1}};
const mandate_shape=validateReservationMandate(mandate,{now});
const preflight=evaluateDialTonePreflight({observed_at:'2026-10-10T18:59:30Z',registered:true,options_status:200,options_rtt_ms:54,audio_device_ready:true,codec_ready:true,sip_transport:'tls',peer_certificate_verified:true,srtp_policy:'mandatory',isolated_route_policy_verified:true},{now});
const after=assessReservationEvidence({call_state:'ended',provider_hangup_confirmed:true,agent_report:{status:'claimed_booked',summary:'Example restaurant apparently agreed to 19:30.'},independent_booking_confirmation:false});
console.log(JSON.stringify({simulation:true,telephone_call_placed:false,real_reservation_made:false,mandate:mandate_shape,preflight,illustrative_post_call_evidence:after},null,2));
