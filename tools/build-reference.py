#!/usr/bin/env python3
"""Build publishable, static AI Dial-Tone developer reference from local Markdown.
Authoring dependency: markdown-it-py (only required for rebuilding source).
The resulting site requires no runtime libraries or server.
"""
import html
import json
import re
import runpy
from pathlib import Path

from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'content'/'docs'
SITE=ROOT/'site'
OUT=SITE/'docs'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=sorted(DOCS.glob('*.md'))
SLUGS=['overview','quickstart','architecture','authentication','api','lifecycle','events','media','agents','provider','errors','challenge','readiness','peer-contract','human-journey','native-security','roadmap','peer-lab','audio-first-voice','byot-asterisk','x402-payment-admission','payment-telecom-handoff','faq','pre-call-principle','origins']
assert len(SOURCES)==len(SLUGS)

# Correct references in MD sources use the public slug, not the numbered source name.
BROWSER_PAGES=[]
for source, slug in zip(SOURCES,SLUGS):
    raw=source.read_text(encoding='utf-8')
    title=re.search(r'^#\s+(.+)$',raw,re.M).group(1)
    paragraphs=[s.strip() for s in re.split(r'\n\n+',raw) if s.strip() and not s.startswith('#') and not s.startswith('>')]
    desc=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',paragraphs[0]) if paragraphs else title
    desc=re.sub(r'[`*]','',desc)
    BROWSER_PAGES.append({'slug':slug,'title':title,'description':desc[:250],'file':source,'raw':raw})

# Verify no unsupported reference relative HTML links have been authored.
valid={x['slug']+'.html' for x in BROWSER_PAGES}
valid.add('index.html')
# Source chapters must link to source chapters on GitHub. Rewrite those
# links only when generating the website, so neither reading context breaks.
SOURCE_TO_SITE = {item['file'].name: '/docs/' + item['slug'] + '.html' for item in BROWSER_PAGES}
def website_links(markdown):
    return re.sub(r'\]\(([^)#]+\.md)(#[^)]+)?\)',
                  lambda match: '](' + SOURCE_TO_SITE[match.group(1)] + (match.group(2) or '') + ')'
                  if match.group(1) in SOURCE_TO_SITE else match.group(0), markdown)
for item in BROWSER_PAGES:
    for dest in re.findall(r'\]\(([^)]+)\)',item['raw']):
        if dest.endswith('.md') and dest not in SOURCE_TO_SITE and not dest.startswith('/') and not dest.startswith(('http://','https://')):
            raise ValueError(f"{item['file'].name}: unknown relative Markdown source {dest}")
        if dest.endswith('.html') and dest not in valid and not dest.startswith('/') and not dest.startswith(('http://','https://')):
            raise ValueError(f"{item['file'].name}: unknown relative docs page {dest}")

md=MarkdownIt('commonmark',{'html':False,'linkify':False,'typographer':True}).enable('table')
body_shell=runpy.run_path(str(ROOT/'tools'/'build-site.py'))['shell']
NAV=[('Start here','overview'),('Local quickstart','quickstart'),('Architecture','architecture'),('Authentication','authentication'),('HTTP API','api'),('Call lifecycle','lifecycle'),('Events & evidence','events'),('Media & framing','media'),('SDKs and MCP','agents'),('Provider integration','provider'),('Errors & recovery','errors'),('First Call challenge','challenge'),('Release readiness','readiness'),('Bot peer contract','peer-contract'),('For humans','human-journey'),('Native security','native-security'),('Roadmap','roadmap'),('First Call Peer Lab','peer-lab'),('Audio-first voice','audio-first-voice'),('BYOT: Asterisk','byot-asterisk'),('x402 payment admission','x402-payment-admission'),('x402 to BYOT handoff','payment-telecom-handoff'),('Frequently asked questions','faq'),('Pre-call qualification','pre-call-principle'),('Origins & community engineering','origins')]

# Stable readable anchors for TOC and direct links.
def anchors(content):
    used=set(); headings=[]
    def replace(match):
        level,inner=match.group(1),match.group(2)
        plain=html.unescape(re.sub(r'<[^>]+>','',inner))
        slug=re.sub(r'[^a-z0-9]+','-',plain.lower()).strip('-') or 'section'
        start=slug; i=2
        while slug in used:
            slug=f'{start}-{i}';i+=1
        used.add(slug)
        if level in ('2','3'):headings.append((level,slug,plain))
        return f'<h{level} id="{slug}">{inner}</h{level}>'
    return re.sub(r'<h([123])>(.*?)</h\1>',replace,content,flags=re.S),headings

def doc_sidebar(active):
    links=''.join(f'<a href="/docs/{slug}.html" {"aria-current=\"page\"" if slug==active else ""} class="ref-nav-link {"ref-active" if slug==active else ""}">{html.escape(label)}</a>' for label,slug in NAV)
    return f'<aside class="ref-sidebar" aria-label="Documentation navigation"><div class="ref-sidebar-inner"><span class="ref-sidebar-eyebrow">DOCUMENTATION / LOCAL LAB</span><a class="ref-home" href="/docs/index.html">← Documentation home</a><nav class="ref-nav">{links}</nav><div class="ref-sidebar-note">Preview only. No live PSTN, x402 settlement, or hosted agent API.</div></div></aside>'

def document(item,i):
    body,headings=anchors(md.render(website_links(item['raw'])))
    toc_headings=[h for h in headings if h[0]=='2'] if item['slug']=='faq' else headings
    toc=''.join(f'<a class="ref-toc-link {"ref-toc-child" if lev=="3" else ""}" href="#{h}">{html.escape(t)}</a>' for lev,h,t in toc_headings)
    previous=BROWSER_PAGES[i-1] if i else None
    following=BROWSER_PAGES[i+1] if i+1<len(BROWSER_PAGES) else None
    pager=f'<nav class="ref-pager" aria-label="Documentation pages">'
    pager+=f'<a href="/docs/{previous["slug"]}.html">← {html.escape(previous["title"])}</a>' if previous else '<span></span>'
    pager+=f'<a href="/docs/{following["slug"]}.html">{html.escape(following["title"])} →</a>' if following else '<span></span>'
    pager+='</nav>'
    article=f'''<div class="ref-layout container">{doc_sidebar(item['slug'])}<article class="ref-article" id="reference-article"><div class="ref-page-meta"><a href="/docs/index.html">Reference</a><span> / </span><strong>{html.escape(item['title'])}</strong></div><div class="ref-label"><span class="ref-dot"></span> CONTRACT: LOCAL LAB · NOT LIVE TELEPHONY</div><div class="ref-markdown">{body}</div>{pager}</article><aside class="ref-aside" aria-label="On this page"><span class="ref-sidebar-eyebrow">ON THIS PAGE</span><nav>{toc}</nav><a class="ref-download" href="/llms-full.txt">Full agent-readable guide ↗</a></aside></div>'''
    return f'<section class="ref-section">{article}</section>'

for i,item in enumerate(BROWSER_PAGES):
    rendered=body_shell(item['title'],item['description'], '/docs/index.html',document(item,i),'/assets/reference.js')
    (OUT/(item['slug']+'.html')).write_text(rendered,encoding='utf-8')

search_terms={'events':'local event journal hash chain sequence assertions', 'media':'WebSocket PCM16 DT01 actual 656 byte binary framing', 'authentication':'bearer operator caller peer single-use tickets', 'api':'HTTP REST POST GET endpoints response JSON idempotency', 'provider':'future Asterisk TLS SRTP SIP SBC integration acceptance', 'agents':'Python client model-neutral chat protocol non-hosted MCP', 'errors':'fail closed quotas invalid token failed admission recover', 'readiness':'x402 payments settlement UK PSTN compliant launch', 'challenge':'first call honeypot static scenarios agent fixtures', 'peer-contract':'bot peer human mandate reservation trust A2A MCP', 'human-journey':'person reservation human approval call evidence', 'native-security':'PJSIP TLS SIP SRTP DTLS-SRTP MicroSIP OPTIONS', 'roadmap':'release phases R0 R1 R2 R3 R4 R5 R6 acceptance', 'peer-lab':'AI peer to peer websocket actual PCM audio demo model-neutral bot test', 'byot-asterisk':'self-hosted local Asterisk ARI experimental RTP externalMedia BYOT PJSIP operator mandate test', 'x402-payment-admission':'x402 v2 upfront exact USDC Base payment signature human approval settlement permit no live payment', 'payment-telecom-handoff':'operator side binding of x402 lab permit to Asterisk BYOT mandate real origination disabled', 'faq':'substantial questions pricing telecoms security BYOT FreePBX SIP ASR models human outcomes', 'pre-call-principle':'MicroSIP Dial-Tone readiness registration SIP OPTIONS audible local tone Call Trace verify path before calling route guarantee', 'origins':'Kieran Knowles-Byrne kierknoby 20tele FreePBX UK Registration Watch Repeat Caller Concurrency Count Heqet IN1CLICK developer'   }
cards=''.join(f'<a class="ref-card" data-search="{html.escape((item["title"]+" "+item["description"]+" "+search_terms.get(item["slug"],"")).lower(),quote=True)}" href="/docs/{item["slug"]}.html"><span class="ref-card-number">{i+1:02d} / REFERENCE</span><h2>{html.escape(item["title"])}</h2><p>{html.escape(item["description"][:160])}</p><span class="ref-card-arrow">Read chapter →</span></a>' for i,item in enumerate(BROWSER_PAGES))
hub=f'''<section class="page-hero compact-hero"><div class="container"><p class="eyebrow">DEVELOPER REFERENCE / {len(BROWSER_PAGES)} CHAPTERS</p><h1>Built to be<br><em>understood.</em></h1><p>The developer reference for one end-to-end autonomous calling platform: agent contracts, consent, media, managed x402 research, telecoms policy, Asterisk BYOT and evidence. The 0.0.1 implementation is local and experimental, not a hosted telephone service.</p><div class="hero-actions"><a class="button button-red" href="/developers.html">Explore developer capabilities →</a><a class="button button-ghost" href="/docs/quickstart.html">Local quickstart →</a><a class="button button-ghost" href="/docs/byot-asterisk.html">BYOT: use your own Asterisk →</a><a class="button button-ghost" href="/llms-full.txt">Agent-readable full reference ↗</a></div></div></section>
<section class="ref-hub section section-cream"><div class="container"><div class="ref-hub-top"><div><p class="eyebrow eyebrow-red">START WITH THE CONTRACT</p><h2>Choose your entry point.</h2></div><label class="ref-search-label">Search documentation<input id="ref-search" type="search" placeholder="Search topics, API methods, errors…" autocomplete="off" aria-describedby="ref-search-count"></label></div><p id="ref-search-count" class="ref-search-count" role="status" aria-live="polite">{len(BROWSER_PAGES)} chapters available</p><div class="ref-cards" id="ref-cards">{cards}</div><div class="ref-search-empty" id="ref-search-empty" hidden>No matching topics. Try “media”, “hangup”, “MCP”, or “error”.</div><div class="ref-file-strip"><div><strong>Need machine-readable context?</strong><p>Read our full versioned reference, project-specific capability manifest, and source-backed Peer Lab OpenAPI specification. All are static, publicly readable documents. They do not expose a callable cloud API.</p></div><div><a href="/llms-full.txt">LLM full reference ↗</a><a href="/api/reference.json">JSON reference ↗</a><a href="/api/openapi.json">OpenAPI 3.1 ↗</a></div></div></div></section>'''
(OUT/'index.html').write_text(body_shell('Developer reference',f'End-to-end AI Dial-Tone architecture and open-source developer reference across agent calling, BYOT, x402 and operator safety, {len(BROWSER_PAGES)} chapters. Preview.','/docs/index.html',hub,'/assets/reference.js'),encoding='utf-8')

# Aggregated, self-contained Markdown for agents. Explicit source/version scope.
full=['# AI Dial-Tone — Full agent-readable documentation',
      '\n**Documentation edition 0.0.1 (11 October 2026). Public-source Peer Lab; local only.**',
      '\n**NOT A LIVE CALLING SERVICE.** This is a static preview with synthetic scenarios and a local-only, public-source peer lab. No public MCP, A2A, PSTN, x402 settlement or hosted model calling API is available. A self-hosted, disabled-by-default experimental Asterisk ARI connector exists in byot/. The payments/ folder has an isolated x402 header/settlement-decision lab with a fake facilitator, not a deployed payment gateway. Do not infer otherwise from examples.',
      '\nTARGET PRODUCT: One end-to-end agent calling capability: discovery, human authorisation, independent provider route admission, optional managed x402 payment, conversation, provider-controlled hangup and verifiable outcome. Managed calling and self-hosted BYOT are two paths to the same product. WEBSITE = public product/discovery entry; GITHUB = open-source development and runnable local labs. Version 0.0.1 does not deliver a live end-to-end service.',
      '\nIndex: /docs/index.html | Canonical Project Overview: /overview.html | Capability manifest: /agents.json | OpenAPI (local-only): /api/openapi.json | Scope: /api/product-scope.json (planned is not available)']
for item in BROWSER_PAGES:
    full.extend(['\n---\n',f'<!-- /docs/{item["slug"]}.html -->',website_links(item['raw'])])
(SITE/'llms-full.txt').write_text('\n'.join(full).rstrip('\n')+'\n',encoding='utf-8')

# Build the documented route catalog from the ACTUAL public Peer Lab specification.
peer_spec=json.loads((ROOT/'peer-lab'/'openapi.json').read_text(encoding='utf-8'))
assert peer_spec['servers'][0]['url']=='http://127.0.0.1:8765'
(SITE/'api'/'openapi.json').write_text(json.dumps(peer_spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
byot_spec=json.loads((ROOT/'byot'/'openapi.json').read_text(encoding='utf-8'))
assert byot_spec['servers'][0]['url']=='http://127.0.0.1:8877'
(SITE/'api'/'byot-openapi.json').write_text(json.dumps(byot_spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(SITE/'api'/'peer-lab-openapi.json').write_text(json.dumps(peer_spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
route_details={
 '/v1/capabilities':('none','Local capability discovery; real_pstn=false'),
 '/v1/mandates':('operator','Issue local, bounded test mandate'),
 '/v1/mandates/{mid}/revoke':('operator','Revoke mandate and end its session'),
 '/v1/sessions':('caller + Idempotency-Key','Create lab session exactly once'),
 '/v1/peers/inbox':('peer','Assigned pending sessions only'),
 '/v1/sessions/{sid}':('caller or peer','Read own session journal'),
 '/v1/sessions/{sid}/stop':('operator','Independent local operator stop'),
 '/v1/sessions/{sid}/tickets':('assigned caller or peer','Issue single-use WebSocket admission'),
 '/v1/sessions/{sid}/connect':('single-use ticket','WebSocket audio and control; ticket in first message')
}
routes=[]
for path, methods in peer_spec['paths'].items():
 for method, entry in methods.items():
  if method not in ('get','post'):continue
  auth,meaning=route_details[path]
  routes.append({'method':method.upper()+(' WebSocket' if path.endswith('/connect') else ''),
                 'path':path,'auth':auth,'meaning':meaning})
reference={
 'schema_version':'0.0.1','release_version':'0.0.1',
 'title':'AI Dial-Tone 0.0.1 public-source developer reference',
 'documented_backend':'public-local-peer-lab',
 'public_hosted_api':False,'environment':'localhost Peer Lab; separate experimental BYOT Asterisk ARI adapter',
 'base_url':'http://127.0.0.1:8765',
 'live_pstn':False,'self_hosted_experimental_byot':True,
 'byot_local_spec':'/api/byot-openapi.json',
 'x402_lab_local_only':True,'real_x402_facilitator':False,
 'operator_side_payment_to_byot_lab_handoff':True, 'handoff_requires_origination_disabled':True,
 'byot_interoperability_tested_on_real_asterisk':False,
 'local_handoff_never_enables_live_origination':True, 'local_handoff_is_not_a_hosted_api':True,
 'x402_settlement':False,'hosted_mcp':False,
 'documentation_root':'/docs/index.html','llm_full_reference':'/llms-full.txt',
 'routes':routes,
 'call_states':[], 'session_states':['awaiting_peers','running','ended'],
 'agent_trust_label':'MODEL_ASSERTION_NOT_ASR_VERIFIED',
 'media':{'frame_magic':'DT01','bytes_per_frame':656,'header_bytes':16,'sample_bytes':640,
          'sample_rate_hz':16000,'channels':1,'duration_ms':20,'ticket_ttl_seconds':20,
          'browser_header_gateway_implemented':False},
 'docs':[{'path':'/docs/'+p['slug']+'.html','title':p['title'],'summary':p['description']} for p in BROWSER_PAGES],
 'limitations':['local_development_only','no_public_runtime','no_verified_real_pstn','no_live_x402_settlement',
                'no_real_llm_quality_verification','no_verified_asterisk_originations','byot_default_no_live_origination']
}
(SITE/'api'/'reference.json').write_text(json.dumps(reference,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(SITE/'api'/'docs-index.json').write_text(json.dumps({'status':'technical_preview','chapters':reference['docs']},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Rendered {len(BROWSER_PAGES)} reference chapters, documentation hub, llms-full.txt, and JSON reference')

# Publication metadata is deterministic for the intended deployment hostname.
# Never canonicalise 13 distinct documentation pages to the same nav active URL.
for page in sorted(SITE.rglob('*.html')):
    pathname='/' + page.relative_to(SITE).as_posix()
    if pathname=='/index.html': pathname='/'
    origin='https://ai.dial-tone.uk'
    canonical=origin+pathname
    html_text=page.read_text(encoding='utf-8')
    # The site generator can already emit canonical and og:url metadata. Strip
    # existing values before writing the final per-page URL. This makes the
    # documented build-site -> build-reference sequence safe to repeat and
    # prevents duplicate canonical tags from reaching the published site.
    html_text=re.sub(r'<link rel="canonical" href="[^"]*">', '', html_text)
    html_text=re.sub(r'<meta property="og:url" content="[^"]*">', '', html_text)
    if page.name != '404.html':
        html_text=html_text.replace('<meta property="og:type" content="website">',
            f'<link rel="canonical" href="{canonical}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="website">',1)
    html_text=html_text.replace('content="/assets/social.svg"',f'content="{origin}/assets/social.svg"',1)
    page.write_text(html_text,encoding='utf-8')
from xml.sax.saxutils import escape as xml_escape
urlpaths=['/' + f.relative_to(SITE).as_posix() for f in sorted(SITE.rglob('*.html')) if f.name!='404.html']
urlpaths=['/' if url=='/index.html' else url for url in urlpaths]
(SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{xml_escape("https://ai.dial-tone.uk"+url)}</loc></url>\n' for url in urlpaths)+'</urlset>\n',encoding='utf-8')
(SITE/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: https://ai.dial-tone.uk/sitemap.xml\n',encoding='utf-8')
