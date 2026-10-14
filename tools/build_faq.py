"""Single source of truth for the public FAQ, reference chapter and agent JSON.

The supplied shell and styling are owned by the static website builder.
Answers are authored as plain text; never interpolate user-supplied HTML.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(shell):
    catalog = json.loads((ROOT / 'content/faqs.json').read_text(encoding='utf-8'))
    categories = catalog['categories']
    slugs, questions = set(), set()
    for category in categories:
        assert re.fullmatch(r'[a-z][a-z0-9-]+', category['slug'])
        assert category['slug'] not in slugs
        slugs.add(category['slug'])
        assert 4 <= len(category['items']) <= 15
        for entry in category['items']:
            assert re.fullmatch(r'[a-z][a-z0-9-]+', entry['id'])
            assert entry['id'] not in questions
            questions.add(entry['id'])
            assert len(entry['question']) > 12 and len(entry['answer']) > 35
            assert entry['read_more'].startswith('/') and not entry['read_more'].startswith('//')
            assert not any(x in entry['answer'].lower() for x in ('<script', 'javascript:', 'onerror='))
    assert len(questions) >= 50

    parts = ['''<section class="page-hero compact-hero"><div class="container"><p class="eyebrow">QUESTIONS AND ANSWERS / 0.0.1</p><h1>Every question<br><em>worth asking.</em></h1><p>For people, autonomous agents and PBX developers. Clear answers about how AI Dial-Tone works, how x402 and FreePBX fit, what is experimental, and what must be proven before live calling.</p><div class="hero-actions"><a class="button button-red" href="#faq-find">Find your answer ↓</a><a class="button button-ghost" href="/docs/index.html">Developer documentation ↗</a></div></div></section>
<section class="section section-cream"><div class="container"><div class="faq-status"><strong>Technical preview · 0.0.1</strong><span>No public telephone calling, no real x402 settlement and no hosted MCP service are available.</span><a href="/status.html">View evidence ↗</a></div>
<div class="faq-tools" id="faq-find"><div><p class="eyebrow eyebrow-red">DIRECT ANSWERS</p><h2>Frequently asked questions.</h2></div><div class="faq-filter"><label for="faq-search">Search all questions</label><input id="faq-search" type="search" placeholder="Try: FreePBX, x402, SIP, agent, privacy…" autocomplete="off" aria-describedby="faq-count"><button type="button" id="faq-clear">Clear search</button></div></div>
<div class="faq-category-nav" aria-label="Question categories">''']
    for cat in categories:
        parts.append(f'<a href="#faq-{cat["slug"]}">{html.escape(cat["category"])} <span>{len(cat["items"])}</span></a>')
    parts.append('</div><div class="faq-toolbar"><p id="faq-count" role="status" aria-live="polite">'+str(len(questions))+' questions in '+str(len(categories))+' categories</p><div><button type="button" id="faq-expand">Expand all visible</button><button type="button" id="faq-collapse">Collapse all</button></div></div>')
    for cat in categories:
        parts.append(f'<section class="faq-category" id="faq-{cat["slug"]}" data-category="{cat["slug"]}"><div class="faq-category-heading"><h3>{html.escape(cat["category"])}</h3><p>{html.escape(cat["description"])}</p></div><div class="faq-questions">')
        for item in cat['items']:
            q = html.escape(item['question'])
            a = html.escape(item['answer'])
            path = html.escape(item['read_more'],quote=True)
            parts.append(f'<details class="faq-item" id="{item["id"]}" data-search="{html.escape((item["question"]+" "+item["answer"]+" "+cat["category"]).lower(),quote=True)}"><summary>{q}<span class="faq-chevron" aria-hidden="true">+</span></summary><div class="faq-answer"><p>{a}</p><a href="{path}">Further reading →</a></div></details>')
        parts.append('</div></section>')
    parts.append('''<p class="faq-empty" id="faq-empty" hidden>No matches. Try another term, or <a href="/docs/index.html">browse the complete documentation</a>.</p><div class="faq-contact"><h2>Something we haven't covered?</h2><p>Ask a focused question or raise an issue in the source repository. Please don't include telephone credentials, payment secrets, call recordings or customer details.</p><a class="button button-dark" href="https://github.com/kierknoby/AI-Dial-Tone/issues">Project issues ↗</a><a class="button button-light" href="/trust.html">Security and privacy →</a></div></div></section>''')
    page = shell('Frequently asked questions', f'{len(questions)} substantial questions about autonomous AI calling, x402, FreePBX, Asterisk, security and project status.', '/faqs.html', ''.join(parts), '/assets/faq.js')
    page = page.replace('</head>', '<link rel="stylesheet" href="/assets/faq.css"></head>', 1)
    (ROOT / 'site/faqs.html').write_text(page, encoding='utf-8')
    (ROOT / 'site/api/faqs.json').write_text(json.dumps({
        'version': '0.0.1', 'status': 'technical_preview',
        'public_live_calling': False, 'real_x402_settlement': False,
        'hosted_mcp': False, 'total_questions': len(questions),
        'categories': categories,
    }, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    md = ['# Frequently asked questions', '',
          'AI Dial-Tone 0.0.1 is an open-source technical preview. **No public PSTN calling, real x402 settlement or hosted MCP service is available.**',
          '', 'These answers are generated from the same question catalogue as the website and machine-readable `/api/faqs.json`.', '']
    for cat in categories:
        md.extend(['## ' + cat['category'], '', cat['description'], ''])
        for item in cat['items']:
            md.extend(['### ' + item['question'], '', item['answer'], '', f'Further reading: [{item["read_more"]}]({item["read_more"]})', ''])
    (ROOT / 'content/docs/23-faq.md').write_text('\n'.join(md).rstrip()+'\n', encoding='utf-8')
    return len(questions)
