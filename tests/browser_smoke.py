"""Chromium smoke test without network navigation (restricted build containers).
Injects the exact static HTML/CSS/JS from site/ into an about:blank document.
Run: python tests/browser_smoke.py. Requires optional Playwright + Chromium.
"""
from pathlib import Path
import re, base64
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
css=(SITE/'assets/style.css').read_text() + '\n' + (SITE/'assets/reference.css').read_text()
logo_data='data:image/svg+xml;base64,'+base64.b64encode((SITE/'assets/logo.svg').read_bytes()).decode()
simulator=(SITE/'assets/simulator.mjs').read_text().replace('export const','const').replace('export function','function')
app=(SITE/'assets/app.js').read_text().replace('export function','function').replace('export async function','async function')
playground='\n'.join((SITE/'assets/playground.js').read_text().splitlines()[2:])


def load(page,file,interactive=''):
    html=(SITE/file).read_text()
    html=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',html)
    html=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>','',html)
    html=html.replace('/assets/logo.svg',logo_data)
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=css)
    if interactive=='playground':
        page.evaluate("Object.defineProperty(crypto, 'randomUUID', {value: ()=> '00000000-0000-4000-8000-000000000001', configurable:true})")
        page.add_script_tag(content='(function(){'+simulator+'\n'+app+'\n'+playground+'})();')

    elif interactive=='reference':page.add_script_tag(content='(function(){'+app+'\n'+(SITE/'assets/reference.js').read_text()+'})();')
    elif interactive=='faq':
        page.add_style_tag(content=(SITE/'assets/faq.css').read_text())
        page.add_script_tag(content='(function(){'+app+'\n'+(SITE/'assets/faq.js').read_text()+'})();')
    else:page.add_script_tag(content='(function(){'+app+'})();')

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    failures=[]
    page.on('pageerror',lambda error:failures.append(str(error)))
    load(page,'index.html')
    assert page.get_by_role('heading',name='Give your AI Dial-Tone').is_visible()
    assert page.get_by_role('link',name='Read the complete Project Overview →').is_visible()
    page.screenshot(path=str(ROOT/'tests/desktop.png'),full_page=True)
    load(page,'overview.html')
    assert page.locator('.overview-article p').count()==11
    assert 'The objective is to change that.' in page.locator('.overview-article').inner_text()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Desktop Project Overview overflow'
    page.screenshot(path=str(ROOT/'tests/overview-desktop.png'),full_page=True)
    load(page,'developers.html')
    assert page.get_by_role('heading',name='Build the calling capability.').is_visible()
    assert page.get_by_role('link',name='Run the local quickstart →').is_visible()
    load(page,'docs/index.html','reference')
    assert page.get_by_role('heading',name='Built to be understood.').is_visible()
    chapters=len(list((SITE/'docs').glob('*.html')))-1
    assert page.locator('.ref-card').count()==chapters
    page.locator('#ref-search').fill('audio')
    assert page.locator('.ref-card:visible').count()>=1
    assert page.locator('.ref-card:visible').count()<chapters
    page.screenshot(path=str(ROOT/'tests/reference-desktop.png'),full_page=True)
    load(page,'docs/media.html','reference')
    assert page.get_by_role('heading',name='Real-time media and framing').is_visible()
    assert page.locator('.ref-markdown table').count()>=1
    assert page.locator('.ref-code-copy').count()>=1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Desktop doc overflow'
    load(page,'playground.html','playground')
    page.get_by_role('button',name='Run scenario').click()
    page.wait_for_function("document.querySelector('#call-state').textContent === 'Ended'",timeout=10000)
    page.wait_for_function("document.querySelectorAll('#event-list li').length===8",timeout=4000)
    assert 'not verified' in page.locator('#outcome-label').inner_text()
    page.screenshot(path=str(ROOT/'tests/playground.png'),full_page=True)
    page.get_by_role('button',name='Reset').click()
    page.select_option('#scenario','busy')
    page.get_by_role('button',name='Run scenario').click()
    page.wait_for_function("document.querySelector('#call-state').textContent === 'Failed'",timeout=10000)
    assert page.locator('#event-list li').count()==3
    load(page,'agents.html')
    assert page.get_by_role('heading',name='One instruction. A complete call.').is_visible()
    assert page.get_by_role('link',name='Discover the capability ↗').is_visible()
    assert page.get_by_role('link',name='Busy Call failure, not conversation ↗').is_visible()
    assert page.get_by_role('heading',name='Use the platform. Build on the source.').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Desktop agent page overflow'
    page.screenshot(path=str(ROOT/'tests/agents-desktop.png'),full_page=True)
    load(page,'humans.html')
    assert page.get_by_role('heading',name='You ask. Your agent calls.').is_visible()
    assert page.get_by_role('link',name='Human experience in detail →').is_visible()
    page.screenshot(path=str(ROOT/'tests/humans-desktop.png'),full_page=True)
    load(page,'faqs.html','faq')
    assert page.get_by_role('heading',name='Every question worth asking.').is_visible()
    assert page.locator('.faq-item').count()==63
    page.locator('#faq-search').fill('x402')
    filtered=page.locator('.faq-item:visible').count()
    assert 4<filtered<63,filtered
    page.get_by_role('button',name='Expand all visible').click()
    assert page.locator('.faq-item:visible[open]').count()==filtered
    page.get_by_role('button',name='Collapse all').click()
    assert page.locator('.faq-item[open]').count()==0
    page.get_by_role('button',name='Clear search').click()
    assert page.locator('.faq-item:visible').count()==63
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'FAQ desktop overflow'
    page.screenshot(path=str(ROOT/'tests/faq-desktop.png'),full_page=True)
    load(page,'readiness.html')
    assert page.get_by_role('heading',name='Can it actually make the call?').is_visible()
    assert 'ENDPOINT' in page.locator('body').inner_text().upper()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Desktop readiness overflow'
    page.screenshot(path=str(ROOT/'tests/readiness-desktop.png'),full_page=True)
    load(page,'about.html')
    assert page.get_by_role('heading',name='Built by people who build FreePBX.').is_visible()
    assert page.get_by_text('Registration Watch').count()>=1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Desktop about overflow'
    page.screenshot(path=str(ROOT/'tests/about-desktop.png'),full_page=True)
    load(page,'roadmap.html')
    assert page.get_by_role('heading',name='Build the network. Prove every claim.').is_visible()
    load(page,'docs/native-security.html','reference')
    assert page.get_by_role('heading',name='MicroSIP and Dial-Tone security: source inventory and limitations').is_visible()
    load(page,'status.html')
    assert page.get_by_text('Not live for calling.').is_visible()
    assert page.get_by_role('link',name='See what is included, planned and excluded.').is_visible()
    load(page,'scope.html')
    assert page.get_by_role('heading',name='Clear boundaries. Credible progress.').is_visible()
    assert page.get_by_role('heading',name='Not part of the intended product').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Desktop product scope overflow'
    page.screenshot(path=str(ROOT/'tests/scope-desktop.png'),full_page=True)
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    mobile.on('pageerror',lambda error:failures.append(str(error)))
    load(mobile,'index.html')
    assert mobile.get_by_role('heading',name='Give your AI Dial-Tone').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile page overflow'
    load(mobile,'scope.html')
    assert mobile.get_by_role('heading',name='Clear boundaries. Credible progress.').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile product scope overflow'
    mobile.screenshot(path=str(ROOT/'tests/scope-mobile.png'),full_page=True)
    load(mobile,'overview.html')
    assert mobile.locator('.overview-article p').count()==11
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile Project Overview overflow'
    mobile.screenshot(path=str(ROOT/'tests/overview-mobile.png'),full_page=True)
    load(mobile,'index.html')
    mobile.locator('.menu-button').click()
    assert mobile.locator('#primary-nav').is_visible()
    mobile.screenshot(path=str(ROOT/'tests/mobile.png'),full_page=True)
    load(mobile,'docs/index.html','reference')
    assert mobile.get_by_role('heading',name='Built to be understood.').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile docs hub overflow'
    mobile.screenshot(path=str(ROOT/'tests/reference-mobile.png'),full_page=True)
    load(mobile,'docs/api.html','reference')
    assert mobile.get_by_role('heading',name='HTTP API: runnable local Peer Lab').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile reference overflow'
    load(mobile,'humans.html')
    assert mobile.get_by_role('heading',name='You ask. Your agent calls.').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile human page overflow'
    mobile.screenshot(path=str(ROOT/'tests/humans-mobile.png'),full_page=True)
    load(mobile,'faqs.html','faq')
    assert mobile.get_by_role('heading',name='Every question worth asking.').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile FAQ overflow'
    mobile.locator('#faq-search').fill('privacy')
    assert 0<mobile.locator('.faq-item:visible').count()<63
    mobile.screenshot(path=str(ROOT/'tests/faq-mobile.png'),full_page=True)
    load(mobile,'readiness.html')
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Mobile readiness overflow'
    mobile.screenshot(path=str(ROOT/'tests/readiness-mobile.png'),full_page=True)
    load(mobile,'about.html')
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'Mobile about overflow'
    mobile.screenshot(path=str(ROOT/'tests/about-mobile.png'),full_page=True)
    load(mobile,'agents.html')
    assert mobile.get_by_role('heading',name='One instruction. A complete call.').is_visible()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Mobile agent page overflow'
    mobile.screenshot(path=str(ROOT/'tests/agents-mobile.png'),full_page=True)
    assert not failures,failures
    browser.close()
print('Chromium browser smoke passed: landing, agent entry desktop/mobile, source-backed developer docs, call cases, status, and navigation.')
