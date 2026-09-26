#!/usr/bin/env python3
"""Build the site: posts/*.md -> posts/<slug>/index.html, and refresh the 'Latest' list on index.html.
No dependencies. The archive/ folder is static HTML and is not touched."""
import re, html, glob, os

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
        if re.match(r'\s*([-*]|\d+\.) ', l):
            tag = 'ol' if re.match(r'\s*\d+\.', l) else 'ul'
            items = []
            while i < len(lines) and re.match(r'\s*([-*]|\d+\.) ', lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+\.) ', '', lines[i])); i += 1
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'(#{1,3} |>|---|\s*([-*]|\d+\.) )', lines[i]):
            p.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(p)) + '</p>')
    return '\n'.join(out)

def page(title, desc, body, depth):
    up = '../' * depth
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="stylesheet" href="{up}style.css"></head><body><nav><a href="{up}index.html">Home</a><a href="{up}archive/index.html">Archive</a></nav>{body}</body></html>'''

posts = []
for f in sorted(glob.glob('posts/*.md'), reverse=True):
    name = os.path.basename(f)[:-3]
    date, slug = name[:10], name[11:]
    lines = open(f).read().splitlines()
    title = re.sub(r'^# ', '', next(l for l in lines if l.startswith('# ')))
    sub = next((re.sub(r'^\*Subtitle: (.*)\*$', r'\1', l) for l in lines if l.startswith('*Subtitle:')), '')
    body = blocks([l for l in lines if not l.startswith('# ') and not l.startswith('*Subtitle:')])
    d = f'posts/{slug}'; os.makedirs(d, exist_ok=True)
    open(d + '/index.html', 'w').write(page(title, sub, f'<h1>{html.escape(title)}</h1><p><small>{date}</small></p><p><em>{html.escape(sub)}</em></p>{body}', 2))
    posts.append((date, slug, title, sub))

latest = ''.join(f'<li><a href="posts/{s}/index.html">{html.escape(t)}</a> <small>{d}</small></li>' for d, s, t, _ in posts)
idx = open('index.html').read()
idx = re.sub(r'<h2>Latest</h2>.*?(?=<p><a href=\'archive)', f'<h2>Latest</h2><ul>{latest}</ul>', idx, flags=re.S)
open('index.html', 'w').write(idx)
print(f'built {len(posts)} post(s)')
