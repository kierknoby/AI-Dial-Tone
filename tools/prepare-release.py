#!/usr/bin/env python3
"""Prepare branded static publication for verified HTTPS origin."""
from pathlib import Path
from argparse import ArgumentParser
from urllib.parse import urlparse
from shutil import copytree
from xml.sax.saxutils import escape as xml_escape
import re
parser=ArgumentParser()
parser.add_argument('--origin',required=True)
parser.add_argument('--out',required=True)
a=parser.parse_args()
p=urlparse(a.origin)
if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
    parser.error('origin must be an HTTPS site origin')
if p.hostname!='ai.dial-tone.uk':
    parser.error('this release is scoped to https://ai.dial-tone.uk')
out=Path(a.out).resolve()
if out.exists():parser.error('output already exists')
copytree(Path(__file__).resolve().parents[1]/'site',out)
base=a.origin.rstrip('/')
urls=[]
for page in sorted(out.rglob('*.html')):
    if page.name=='404.html':continue
    path='/'+page.relative_to(out).as_posix()
    if path=='/index.html':path='/'
    canonical=base+path
    value=page.read_text(encoding='utf-8')
    value=re.sub(r'<link rel="canonical" href="[^"]+">',f'<link rel="canonical" href="{canonical}">',value,count=1)
    value=re.sub(r'<meta property="og:url" content="[^"]+">',f'<meta property="og:url" content="{canonical}">',value,count=1)
    value=re.sub(r'<meta property="og:image" content="[^"]+">',f'<meta property="og:image" content="{base}/assets/social.svg">',value,count=1)
    page.write_text(value,encoding='utf-8')
    urls.append(canonical)
(out/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{xml_escape(u)}</loc></url>\n' for u in urls)+'</urlset>\n',encoding='utf-8')
(out/'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n',encoding='utf-8')
print('Prepared',len(urls),'pages for',base)
