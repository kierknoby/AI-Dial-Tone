#!/usr/bin/env python3
"""Read-only HTTP checks against a deployed AI Dial-Tone static website.

Run after actual DNS, HTTPS and hosting are configured; does not deploy anything.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from xml.etree import ElementTree

REQUIRED_PAGES = ('/', '/privacy.html', '/scope.html', '/status.html', '/docs/quickstart.html', '/agents.json', '/api/product-scope.json', '/sitemap.xml', '/robots.txt', '/assets/style.css', '/assets/app.js')
SITE = Path(__file__).resolve().parents[1] / 'site'

def fetch(url):
    req = Request(url, headers={'User-Agent': 'AI-Dial-Tone-release-verifier/0.0.1'})
    with urlopen(req, timeout=12) as response:
        return response.status, response.url, dict(response.headers.items()), response.read(2_000_000)

def validate(origin):
    p=urlparse(origin)
    if p.scheme!='https' or p.hostname!='ai.dial-tone.uk' or p.path not in ('','/') or p.query or p.fragment or p.username or p.password:
        raise ValueError('Only https://ai.dial-tone.uk is supported for this release')
    base=origin.rstrip('/')
    failures=[]
    for path in REQUIRED_PAGES:
        try:
            status, final, headers, body=fetch(base+path)
            if status!=200 or urlparse(final).scheme!='https':
                failures.append(f'{path}: expected HTTPS 200, got {status} {final}')
            if not body:
                failures.append(f'{path}: empty body')
            lower={k.lower():v for k,v in headers.items()}
            mime=lower.get('content-type','').split(';')[0].strip().lower()
            required_mime='application/json' if path.endswith('.json') else ('text/html' if path=='/' or path.endswith('.html') else ('text/css' if path.endswith('.css') else ('text/javascript' if path.endswith('.js') else ('application/xml' if path.endswith('.xml') else 'text/plain'))))
            allowed={'application/javascript','text/javascript'} if required_mime=='text/javascript' else ({'application/xml','text/xml'} if required_mime=='application/xml' else {required_mime})
            if mime not in allowed:failures.append(f'{path}: unexpected content type {mime}, expected {required_mime}')
            if path == '/robots.txt' and body != (SITE / 'robots.txt').read_bytes():
                failures.append('/robots.txt: published content does not match the repository source')
            # A short cache TTL is useful for changing pages and machine data.
            # robots.txt is low-churn static metadata and may safely use the
            # host's longer TTL when its published bytes match the source.
            if (path=='/' or (path!='/robots.txt' and path.endswith(('.html','.json','.txt','.xml')))) and 'no-cache' not in lower.get('cache-control','') and 'max-age=0' not in lower.get('cache-control',''):
                failures.append(f'{path}: missing short/revalidation cache policy')
            if path.endswith('.json'):
                json.loads(body)
            elif path=='/sitemap.xml':
                ElementTree.fromstring(body)
            elif path.endswith('.html') or path=='/':
                if b'TECHNICAL PREVIEW' not in body: failures.append(f'{path}: preview label missing')
                if b'<link rel="canonical" href="'+(base+('/' if path=='/' else path)).encode()+b'"' not in body:
                    failures.append(f'{path}: canonical missing or wrong')
            print(f'{status} {path}')
            if path=='/':
                for k in ('content-security-policy','strict-transport-security','x-content-type-options'):
                    if not lower.get(k):failures.append(f'/ missing HTTP security header: {k}')
        except (URLError,HTTPError,TimeoutError,OSError,ValueError,json.JSONDecodeError,ElementTree.ParseError) as e:
            failures.append(f'{path}: {type(e).__name__}: {e}')
    # The cPanel .htaccess must redirect HTTP to HTTPS before the site is accepted.
    try:
        _,url,_,_=fetch('http://ai.dial-tone.uk/')
        if not url.startswith(base+'/'):failures.append('HTTP does not redirect to the HTTPS homepage')
    except (URLError,HTTPError,TimeoutError,OSError) as e:
        failures.append(f'HTTP redirect: {e}')
    if failures:
        print('LIVE PUBLICATION VERIFICATION FAILED',file=sys.stderr)
        for f in failures:print(' - '+f,file=sys.stderr)
        return 1
    print('PASS: live HTTPS, static documents, security headers and HTTP redirect verified.')
    print('This does not verify hosting log-retention, legal review, GitHub Actions, or real calling.')
    return 0

if __name__=='__main__':
    arg=argparse.ArgumentParser()
    arg.add_argument('--origin',default='https://ai.dial-tone.uk')
    a=arg.parse_args()
    try:sys.exit(validate(a.origin))
    except ValueError as e:arg.error(str(e))
