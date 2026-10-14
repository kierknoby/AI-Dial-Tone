#!/usr/bin/env python3
"""Local human-operator CLI: issue one-use mandate, revoke, or stop a call.

Never gives its operator credential to an AI agent. No automatic dialling.
"""
import argparse
import asyncio
import json
import os
from urllib.parse import urlsplit
from aiohttp import ClientSession


def required(name):
    value=os.getenv(name,'')
    if not value: raise SystemExit('Missing '+name)
    return value


async def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--destination',help='UK geographic E.164 destination, for your own test endpoint only')
    group.add_argument('--stop',metavar='CALL_ID',help='Operator emergency stop')
    group.add_argument('--revoke',metavar='MANDATE_ID',help='Revoke one mandate')
    parser.add_argument('--max-seconds',type=int,default=35)
    args=parser.parse_args()
    base=os.getenv('AIDT_BYOT_URL','http://127.0.0.1:8877').rstrip('/')
    p=urlsplit(base)
    if p.scheme!='http' or p.hostname not in ('127.0.0.1','localhost','::1') or p.path not in ('','/'):
        raise SystemExit('BYOT operator URL must be loopback HTTP')
    token=required('AIDT_OPERATOR_TOKEN')
    if args.destination:
        print('You are granting one agent one attempt to call:',args.destination)
        print('Maximum session seconds:',args.max_seconds)
        print('Use only a number/endpoint you own or have consent to call.')
        if input('Type AUTHORISE to issue this one-time mandate: ').strip()!='AUTHORISE':
            raise SystemExit('Cancelled: no mandate issued')
        method,path,body='POST','/v1/mandates',{'destination':args.destination,'max_seconds':args.max_seconds}
    elif args.stop:
        method,path,body='POST','/v1/calls/'+args.stop+'/stop',{}
    else:
        method,path,body='POST','/v1/mandates/'+args.revoke+'/revoke',{}
    async with ClientSession() as http:
        async with http.request(method,base+path,json=body,
                                headers={'Authorization':'Bearer '+token},allow_redirects=False) as resp:
            data=await resp.json()
            if resp.status>=300:
                raise SystemExit('Operation refused: '+data.get('error','HTTP '+str(resp.status)))
            print(json.dumps(data,indent=2))

if __name__=='__main__':asyncio.run(main())
