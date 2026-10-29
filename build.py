#!/usr/bin/env python3
"""Build the site. No dependencies.

  posts/YYYY-MM-DD-slug.md -> posts/<slug>/index.html   (first line '# Title', then '*Subtitle: ...*')
  Optional post lines, same shape as Subtitle: *Title:*, *Description:*, *Image:* (share-image URL or site path; default /og.png)
  pages/*.md               -> <name>/index.html
  archive/<slug>/index.html are re-wrapped in the current layout (content untouched).
  An archive page can set data-image="..." (kept, like data-date) to override its share image.
  index.html, posts/index.html, archive/index.html, sitemap.xml, feed.xml, robots.txt are generated.
  The default share card is og.png (regenerate with scripts/render_og_image.py).
"""
import re, html, glob, os, datetime, json, subprocess, urllib.parse
import xml.etree.ElementTree as ET

BASE = 'https://omerlh.github.io'
NAME = 'Omer Levi Hevroni'
# X account linked from the footer and the About page (https://x.com/omerlh).
TWITTER = '@omerlh'
DEFAULT_IMAGE = f'{BASE}/og.png'
ATOM = 'http://www.w3.org/2005/Atom'
# GoatCounter site code (cookie-free, privacy-friendly stats). Leave empty until the code is registered:
# an unregistered code could be claimed by someone else, who would then receive visitor data.
GOATCOUNTER = 'omerlh'
NAV = [('posts/', 'Writing'), ('talks/', 'Talks'), ('about/', 'About'), ('archive/', 'Archive')]
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23b8431b'/%3E"
           "%3Ctext x='32' y='43' font-size='30' font-family='Georgia,serif' font-weight='700' text-anchor='middle' fill='white'%3EOL%3C/text%3E%3C/svg%3E")

def page_url(path):
    cleaned = path.strip('/')
    return f'{BASE}/{cleaned}/' if cleaned else f'{BASE}/'

def image_url(src):
    src = (src or '').strip()
    if not src:
        return DEFAULT_IMAGE
    if src.startswith(('http://', 'https://')):
        return src
    return f'{BASE}/{urllib.parse.quote(src.lstrip("/"), safe="/")}'

def atom_time(date):
    return f'{date}T00:00:00Z'

def git_date(path):
    """Commit date (YYYY-MM-DD) of a source file. Used for sitemap lastmod on pages
    that have no publication date. Stable across rebuilds; CI fetches full history."""
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], capture_output=True, text=True)
    except OSError:
        return ''
    d = (r.stdout or '').strip()
    return d if re.fullmatch(r'\d{4}-\d\d-\d\d', d) else ''

def absolutize(fragment, page):
    def repl(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        if url.startswith(('http://', 'https://', '//', 'mailto:', 'data:', '#')):
            return m.group(0)
        return f'{attr}={q}{urllib.parse.urljoin(page, url)}{q}'
    return re.sub(r'(href|src)=([\'"])(.*?)\2', repl, fragment)

def plain_summary(fragment, fallback, limit=300):
    for m in re.finditer(r'<p[^>]*>(.*?)</p>', fragment, re.S):
        text = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            continue
        if len(text) > limit:
            text = text[:limit].rsplit(' ', 1)[0].rstrip('.,;:') + '…'
        return text
    return fallback

def write_feed(items):
    ET.register_namespace('', ATOM)
    def el(parent, tag, text=None, **attrs):
        node = ET.SubElement(parent, f'{{{ATOM}}}{tag}', attrs)
        if text is not None:
            node.text = text
        return node
    items = sorted(items, key=lambda i: (i['date'], i['path']), reverse=True)
    feed = ET.Element(f'{{{ATOM}}}feed')
    feed.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
    el(feed, 'title', NAME)
    el(feed, 'subtitle', 'Writing on application security, finance, and AI agents.')
    el(feed, 'link', href=f'{BASE}/', rel='alternate', type='text/html')
    el(feed, 'link', href=f'{BASE}/feed.xml', rel='self', type='application/atom+xml')
    el(feed, 'id', f'{BASE}/')
    newest = items[0]['date'] if items else datetime.date.today().isoformat()
    el(feed, 'updated', atom_time(newest))
    author = el(feed, 'author')
    el(author, 'name', NAME)
    el(author, 'uri', f'{BASE}/about/')
    for item in items:
        entry = el(feed, 'entry')
        el(entry, 'title', item['title'])
        link = page_url(item['path'])
        el(entry, 'link', href=link, rel='alternate', type='text/html')
        el(entry, 'id', link)
        when = atom_time(item['date'])
        el(entry, 'published', when)
        el(entry, 'updated', when)
        who = el(entry, 'author')
        el(who, 'name', NAME)
        el(entry, 'summary', item['summary'])
        el(entry, 'content', item['content'], type='html')
    ET.indent(feed, space='  ')
    ET.ElementTree(feed).write('feed.xml', encoding='utf-8', xml_declaration=True)
    with open('feed.xml', 'ab') as fh:
        fh.write(b'\n')

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    return t

def blocks(lines):
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        if l.startswith('>'):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(re.sub(r'^> ?', '', lines[i])); i += 1
            out.append('<blockquote>' + blocks(q) + '</blockquote>'); continue
        m = re.match(r'(#{1,3}) (.*)', l)
        if m:
            n = len(m.group(1)); out.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); i += 1; continue
        if l.strip() == '---': out.append('<hr>'); i += 1; continue
        if l.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'): code.append(lines[i]); i += 1
            i += 1
            out.append('<pre><code>' + html.escape('\n'.join(code), quote=False) + '</code></pre>'); continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                if not re.match(r'^\|[\s|:-]+\|?$', lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            head, body_rows = rows[0], rows[1:]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body_rows) + '</tbody></table>'); continue
        if re.match(r'\s*([-*]|\d+\.) ', l):
            tag = 'ol' if re.match(r'\s*\d+\.', l) else 'ul'
            items = []
            while i < len(lines) and re.match(r'\s*([-*]|\d+\.) ', lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+\.) ', '', lines[i])); i += 1
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'(#{1,3} |>|---|```|\||\s*([-*]|\d+\.) )', lines[i]):
            p.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(p)) + '</p>')
    return '\n'.join(out)

def layout(title, desc, body, path, active='', wide=False, kind='website', ld=None, published=None, image=None):
    """path is the page's URL path relative to the site root, e.g. 'posts/x/'."""
    up = '../' * path.strip('/').count('/') + ('../' if path.strip('/') else '') if False else '../' * (len([p for p in path.split('/') if p]))
    root = up or './'
    nav = ''.join(f'<a href="{up}{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    url = page_url(path)
    img = image_url(image)
    e = html.escape
    analytics = (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>' if GOATCOUNTER else '')
    ldjson = ('<script type="application/ld+json">' + json.dumps(ld).replace('</', '<\\/') + '</script>') if ld else ''
    published_meta = f'<meta property="article:published_time" content="{atom_time(published)}">' if published else ''
    dims = '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if img == DEFAULT_IMAGE else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="{FAVICON}"><link rel="stylesheet" href="{up}style.css">
<link rel="alternate" type="application/atom+xml" title="{e(NAME)}" href="{BASE}/feed.xml">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="{kind}"><meta property="og:url" content="{url}">
<meta property="og:site_name" content="{e(NAME)}"><meta property="og:image" content="{e(img)}">{dims}<meta property="og:image:alt" content="{e(title)}">{published_meta}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(img)}"><meta name="twitter:site" content="{TWITTER}"><meta name="twitter:creator" content="{TWITTER}">
<meta name="color-scheme" content="light">{analytics}{ldjson}</head><body>
<header class="site"><div class="wrap{" wide" if wide else ""}"><a class="brand" href="{root}">Omer <span>Levi</span> Hevroni</a><nav>{nav}</nav></div></header>
<main>{body}</main>
<footer><div class="wrap"><span>© {datetime.date.today().year} {NAME}</span><span><a href="https://medium.com/@omerlh">Medium</a> · <a href="https://github.com/omerlh">GitHub</a> · <a href="https://www.linkedin.com/in/omerlh">LinkedIn</a> · <a href="https://x.com/omerlh">X</a> · <a href="{root}feed.xml">Subscribe</a></span></div></footer>
</body></html>'''

def write(path, content):
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)
    open(path, 'w').write(content)

def words(t): return len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', t)))

# ---- posts
posts = []
for f in sorted(glob.glob('posts/*.md'), reverse=True):
    name = os.path.basename(f)[:-3]; date, slug = name[:10], name[11:]
    lines = open(f).read().splitlines()
    title = re.sub(r'^# ', '', next(l for l in lines if l.startswith('# ')))
    sub = next((re.sub(r'^\*Subtitle: (.*)\*$', r'\1', l) for l in lines if l.startswith('*Subtitle:')), '')
    meta_title = next((re.sub(r'^\*Title: (.*)\*$', r'\1', l) for l in lines if l.startswith('*Title:')), title)
    meta_desc = next((re.sub(r'^\*Description: (.*)\*$', r'\1', l) for l in lines if l.startswith('*Description:')), sub)
    image = next((re.sub(r'^\*Image: (.*)\*$', r'\1', l).strip() for l in lines if l.startswith('*Image:')), '')
    body = blocks([l for l in lines if not l.startswith(('# ', '*Subtitle:', '*Title:', '*Description:', '*Image:'))])
    nice = datetime.date.fromisoformat(date).strftime('%B %-d, %Y')
    mins = max(1, round(words(body) / 220))
    art = f'<div class="wrap"><article><h1>{html.escape(title)}</h1><p class="deck">{html.escape(sub)}</p><p class="meta">{nice} · {mins} min read · <a href="https://medium.com/@omerlh">Also on Medium</a></p>{body}</article></div>'
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': meta_desc, 'datePublished': date,
          'mainEntityOfPage': f'{BASE}/posts/{slug}/',
          'author': {'@type': 'Person', 'name': NAME, 'url': f'{BASE}/about/',
                     'sameAs': ['https://github.com/omerlh', 'https://www.linkedin.com/in/omerlh', 'https://medium.com/@omerlh']}}
    path = f'posts/{slug}/'
    write(f'posts/{slug}/index.html', layout(meta_title, meta_desc, art, path, 'posts/', kind='article', ld=ld, published=date, image=image or None))
    lead = f'<p><em>{html.escape(sub)}</em></p>\n' if sub else ''
    posts.append(dict(date=date, slug=slug, title=title, sub=sub, mins=mins, nice=nice, path=path,
                       summary=meta_desc or sub or title, content=absolutize(lead + body, page_url(path))))

def card(p, up=''):
    return f'<a class="card" href="{up}posts/{p["slug"]}/"><h3>{html.escape(p["title"])}</h3><p>{html.escape(p["sub"])}</p><small>{p["nice"]} · {p["mins"]} min read</small></a>'

# ---- pages
for f in sorted(glob.glob('pages/*.md')):
    name = os.path.basename(f)[:-3]
    lines = open(f).read().splitlines()
    title = re.sub(r'^# ', '', lines[0])
    body = blocks(lines[1:])
    desc = re.sub(r'<[^>]+>', '', re.search(r'<p>(.*?)</p>', body, re.S).group(1))[:160]
    write(f'{name}/index.html', layout(f'{title} · {NAME}', desc, f'<div class="wrap"><article><h1>{title}</h1>{body}</article></div>', f'{name}/', f'{name}/'))

# ---- archive
arch = []
for f in sorted(glob.glob('archive/*/index.html')):
    slug = f.split('/')[1]; s = open(f).read()
    image_m = re.search(r'data-image="([^"]*)"', s)
    image = html.unescape(image_m.group(1)) if image_m else ''
    m = re.search(r'<article>(.*)</article>', s, re.S) or re.search(r'</nav>(.*)</body>', s, re.S)
    inner = m.group(1)
    title = html.unescape(re.search(r'<h1>(.*?)</h1>', inner, re.S).group(1)); title = re.sub(r'<[^>]+>', '', title)
    date = (re.search(r'data-date="(\d{4}-\d\d-\d\d)"', inner) or re.search(r'originally published (\d{4}-\d\d-\d\d)', inner)).group(1)
    inner = re.sub(r"<p class=['\"]?(?:note|archive-banner)['\"]?>Archived post.*?</p>", '', inner, count=1, flags=re.S)
    inner = re.sub(r'<h1>.*?</h1>', '', inner, count=1, flags=re.S)
    inner = re.sub(r'<div class="archive-banner">.*?</div>', '', inner, count=1, flags=re.S).replace('<p class="meta"', '<p class="meta"')
    inner = re.sub(r'<p class="meta"[^>]*>.*?</p>', '', inner, count=1, flags=re.S)
    nice = datetime.date.fromisoformat(date).strftime('%B %-d, %Y')
    img_attr = f' data-image="{html.escape(image, quote=True)}"' if image else ''
    art = (f'<div class="wrap"><article><h1>{html.escape(title)}</h1>'
           f'<p class="meta" data-date="{date}"{img_attr}>{nice} · from my old blog</p>'
           f'<div class="archive-banner">This is an archived post from {date[:4]}. Tools and advice may be out of date.</div>{inner}</article></div>')
    art = art.replace('<article>', '<article>', 1)
    path = f'archive/{slug}/'
    write(f, layout(title, f'Archived post from {date[:4]}: {title}', art, path, 'archive/', kind='article', published=date, image=image or None))
    feed_body = re.sub(r'<p class=["\']meta["\'][^>]*>.*?</p>', '', inner, flags=re.S)
    feed_body = re.sub(r'<div class="archive-banner">.*?</div>', '', feed_body, flags=re.S)
    feed_body = re.sub(r'<h1[^>]*>.*?</h1>', '', feed_body, count=1, flags=re.S)
    summary = plain_summary(feed_body, f'Archived post from {date[:4]}: {title}')
    content = absolutize(f'<p><em>Archived post from {date[:4]}.</em></p>\n{feed_body}', page_url(path))
    arch.append(dict(slug=slug, title=title, date=date, path=path, summary=summary, content=content))
arch.sort(key=lambda a: a['date'], reverse=True)
rows = ''; year = None
for a in arch:
    y = a['date'][:4]
    if y != year:
        rows += ('</ul>' if year else '') + f'<h2 class="label" style="margin-top:32px">{y}</h2><ul class="plain">'; year = y
    rows += f'<li><a href="{a["slug"]}/">{html.escape(a["title"])}</a><small>{a["date"]}</small></li>'
rows += '</ul>'
write('archive/index.html', layout(f'Archive · {NAME}', 'Older posts from my previous blog, 2018 to 2022: Kubernetes, CI/CD, DevSecOps and application security.',
      f'<div class="wrap"><article><h1>Archive</h1><p class="deck">Posts from my old blog, 2018 to 2022. Mostly Kubernetes, CI/CD and application security.</p>{rows}</article></div>', 'archive/', 'archive/'))

# ---- writing index
cards = ''.join(card(p, '../') for p in posts)
write('posts/index.html', layout(f'Writing · {NAME}', 'Essays on running life like a company, finance, and building with AI agents.',
      f'<div class="wrap"><article><h1>Writing</h1><p class="deck">Newer posts. Older ones live in the <a href="../archive/">archive</a>.</p><div class="cards">{cards}</div></article></div>', 'posts/', 'posts/'))

# ---- home
home = f'''<div class="wrap wide" style="max-width:720px">
<div class="hero"><p class="eyebrow">Builder · Writer · Ex-AppSec</p>
<h1>Hi, I'm Omer.</h1>
<p class="lede">I build things, and write about what I learn: finance, security, and running life like a well-run company.</p>
<div class="links"><a class="btn primary" href="posts/">Read my writing</a><a class="btn" href="about/">About me</a><a class="btn" href="https://medium.com/@omerlh">Medium</a><a class="btn" href="https://github.com/omerlh">GitHub</a></div></div>
<section><h2 class="label">Latest</h2><div class="cards">{cards.replace('href="../posts/', 'href="posts/')}</div></section>
<section class="about-teaser"><h2 class="label">A bit about me</h2>
<p>I've been coding since 4th grade, and spent years in application security and DevSecOps, giving <a href="talks/">talks</a> and contributing to open source. Since 2022 I've been at <a href="https://ledge.co">Ledge</a>, where AI agents prepare the month-end close.</p>
<p><a href="about/">More about me →</a> &nbsp; <a href="archive/">Old posts →</a></p></section></div>'''
write('index.html', layout(f'{NAME}: writing on finance, security and AI agents', 'Personal site of Omer Levi Hevroni. Essays on running life like a company, finance, and application security.', home, ''))

# ---- feed
write_feed(posts + arch)

# ---- sitemap / robots
urls = ['', 'posts/', 'talks/', 'about/', 'archive/'] + [f'posts/{p["slug"]}/' for p in posts] + [f'archive/{a["slug"]}/' for a in arch]
newest_post = posts[0]['date'] if posts else datetime.date.today().isoformat()
newest_arch = arch[0]['date'] if arch else newest_post
lastmod = {
    '': newest_post,
    'posts/': newest_post,
    'archive/': newest_arch,
    'about/': git_date('pages/about.md') or newest_post,
    'talks/': git_date('pages/talks.md') or newest_post,
}
for p in posts:
    lastmod[f'posts/{p["slug"]}/'] = p['date']
for a in arch:
    lastmod[f'archive/{a["slug"]}/'] = a['date']
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + ''.join(f'<url><loc>{BASE}/{u}</loc><lastmod>{lastmod[u]}</lastmod></url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
print(f'built {len(posts)} post(s), {len(arch)} archive pages')
