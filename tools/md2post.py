#!/usr/bin/env python3
"""
md2post.py — Convert a markdown file to a Butterfly-theme blog post.

Usage:
  python3 tools/md2post.py <markdown_file>

The script will:
  1. Read the markdown file and extract title, description from first line + first paragraph
  2. Convert markdown to Butterfly/Hexo-style HTML
  3. Create the post directory and index.html
  4. Update index.html (homepage)
  5. Create/update archive pages
  6. Create tag pages
  7. Update sitemaps
  8. Update pagination
  9. Stage all changes in git

Requirements: Run from the blog repo root directory.
"""
import re
import html as html_mod
import os
import sys
import subprocess
from datetime import datetime, timezone

BASE = os.getcwd()

# ============== Markdown → Butterfly HTML ==============

def inline_process(text):
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a target="_blank" rel="noopener" href="\2">\1</a>', text)
    return text

def md_to_html(md):
    lines = md.split('\n')
    out = []
    in_code = False
    code_buf = []
    code_lang = ""
    in_ul = False
    in_ol = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block ```...```
        if line.startswith('```'):
            if in_code:
                content = '\n'.join(code_buf)
                escaped = html_mod.escape(content)
                cl = code_lang if code_lang else ''
                hl_class = f' class="highlight {cl}"' if cl else ''
                out.append(f'<figure{hl_class}><table><tr><td class="gutter"><pre>')
                clines = content.split('\n')
                for j, _ in enumerate(clines, 1):
                    out.append(f'<span class="line">{j}</span><br>')
                out.append('</pre></td><td class="code"><pre>')
                lang_attr = f' class="language-{cl}"' if cl else ''
                out.append(f'<code{lang_attr}>{escaped}</code>')
                out.append('</pre></td></tr></table></figure>\n')
                in_code = False
                code_buf = []
                code_lang = ""
            else:
                in_code = True
                code_lang = line[3:].strip().split()[0] if line[3:].strip() else ''
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            out.append('<hr>\n')
            i += 1
            continue

        # Empty line → flush lists
        if not line.strip():
            if in_ul: out.append('</ul>\n'); in_ul = False
            if in_ol: out.append('</ol>\n'); in_ol = False
            i += 1
            continue

        # Headings
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            level = len(hm.group(1))
            text = hm.group(2).strip()
            anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text).strip('-')
            out.append(f'<h{level} id="{anchor}"><a href="#{anchor}" class="headerlink" title="{text}"></a>{text}</h{level}>\n')
            i += 1
            continue

        # Unordered list
        um = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if um:
            if in_ul: pass
            else:
                if in_ol: out.append('</ol>\n'); in_ol = False
                out.append('<ul>\n'); in_ul = True
            out.append(f'<li>{inline_process(um.group(2))}</li>\n')
            i += 1
            continue

        # Ordered list
        om = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if om:
            if in_ol: pass
            else:
                if in_ul: out.append('</ul>\n'); in_ul = False
                out.append('<ol>\n'); in_ol = True
            out.append(f'<li>{inline_process(om.group(2))}</li>\n')
            i += 1
            continue

        # Blockquote
        bm = re.match(r'^>\s+(.*)$', line)
        if bm:
            if in_ul: out.append('</ul>\n'); in_ul = False
            if in_ol: out.append('</ol>\n'); in_ol = False
            out.append(f'<blockquote><p>{inline_process(bm.group(1))}</p></blockquote>\n')
            i += 1
            continue

        # Table
        if line.startswith('|') and line.endswith('|'):
            if in_ul: out.append('</ul>\n'); in_ul = False
            if in_ol: out.append('</ol>\n'); in_ol = False
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|+]+\|$', lines[i + 1]):
                out.append('<table>\n<thead>\n<tr>\n')
                for c in cells:
                    out.append(f'<th>{inline_process(c)}</th>\n')
                out.append('</tr>\n</thead>\n<tbody>\n')
                i += 2
                while i < len(lines) and lines[i].startswith('|') and lines[i].endswith('|'):
                    rc = [c.strip() for c in lines[i].split('|')[1:-1]]
                    out.append('<tr>\n')
                    for c in rc:
                        out.append(f'<td>{inline_process(c)}</td>\n')
                    out.append('</tr>\n')
                    i += 1
                out.append('</tbody>\n</table>\n')
                continue
            else:
                out.append(f'<p>{inline_process(line)}</p>\n')
                i += 1
                continue

        # Paragraph
        if in_ul: out.append('</ul>\n'); in_ul = False
        if in_ol: out.append('</ol>\n'); in_ol = False
        out.append(f'<p>{inline_process(line)}</p>\n')
        i += 1

    if in_ul: out.append('</ul>\n')
    if in_ol: out.append('</ol>\n')
    return ''.join(out)


# ============== Parse MD metadata ==============

def parse_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        md = f.read()

    # Title: first H1
    title_match = re.search(r'^#\s+(.+)$', md, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(filepath))[0]

    # Description: first paragraph (non-empty, non-heading, non-code, non-quote)
    desc = title
    for line in md.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('`') and not line.startswith('---') and not line.startswith('*') and not line.startswith('-'):
            desc = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            desc = re.sub(r'`([^`]+)`', r'\1', desc)
            desc = desc[:120]
            break

    # Date: now
    now = datetime.now(timezone.utc)
    date = now.strftime('%Y-%m-%d')
    datetime_iso = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    datetime_display = now.strftime('%Y-%m-%d %H:%M:%S')

    # Slug from filename
    basename = os.path.splitext(os.path.basename(filepath))[0]
    slug = basename

    # Tags & category: we'll default to auto-detecting from content
    # Look for common patterns or just use the first meaningful keyword
    tags = []
    # Extract potential tags from H2 headings
    tag_candidates = re.findall(r'^##\s+(.+)$', md, re.MULTILINE)
    # Use simple keywords from headings as guidance

    return {
        'md': md,
        'title': title,
        'description': desc,
        'date': date,
        'datetime_iso': datetime_iso,
        'datetime_display': datetime_display,
        'slug': slug,
        'tags': [],  # Will prompt or extract
        'category': '',  # Will prompt
    }


# ============== File templates ==============

def build_post_html(post, body_html, tags_str, tag_links, url_encoded, pagination_html):
    """Build a post page by adapting the existing post template."""
    # Find an existing post to use as template
    existing_posts = []
    for root, dirs, files in os.walk(os.path.join(BASE, '2026')):
        if 'index.html' in files:
            existing_posts.append(os.path.join(root, 'index.html'))
    if not existing_posts:
        print("❌ No existing posts found to use as template.")
        sys.exit(1)

    with open(existing_posts[0], 'r', encoding='utf-8') as f:
        tpl = f.read()

    html = tpl
    post_url = f"https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/{url_encoded}"

    # Title
    html = re.sub(r'<title>.*?</title>', f'<title>{post["title"]} | 个人博客</title>', html)
    html = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{post["title"]}">', html)
    html = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{post_url}">', html)
    html = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{post["description"]}">', html)
    html = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{post["description"]}">', html)
    html = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{post_url}">', html)
    html = re.sub(r'<meta property="article:published_time" content="[^"]*">', f'<meta property="article:published_time" content="{post["datetime_iso"]}">', html)
    html = re.sub(r'<meta property="article:modified_time" content="[^"]*">', f'<meta property="article:modified_time" content="{post["datetime_iso"]}">', html)
    html = re.sub(r'\n<meta property="article:tag" content="[^"]*">(\n<meta property="article:tag" content="[^"]*">)*', tags_str, html)

    # JSON-LD
    json_ld = f'''<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{post["title"]}",
  "url": "{post_url}",
  "image": "https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/img/avatar.jpg",
  "datePublished": "{post["datetime_iso"]}",
  "dateModified": "{post["datetime_iso"]}",
  "author": [
    {{
      "@type": "Person",
      "name": "xiuerhuahuazi",
      "url": "https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi"
    }}
  ]
}}</script>'''
    # Simple replacement for JSON-LD
    html = re.sub(r'<script type="application/ld\+json">\{.*?"headline":.*?"@type": "BlogPosting".*?\}</script>', json_ld, html, flags=re.DOTALL)

    # Config title
    html = re.sub(r"title: '[^']*'", f"title: '{post['title']}'", html)

    # Post title
    html = re.sub(r'<h1 class="post-title">.*?</h1>', f'<h1 class="post-title">{post["title"]}</h1>', html)
    html = re.sub(
        r'<span class="site-name">[^<]+</span>\s*<span class="site-name">',
        f'<span class="site-name">{post["title"]}</span><span class="site-name">',
        html
    )

    # Header background
    html = re.sub(
        r'<header class="post-bg" id="page-header" style="background-image: url\([^)]+\)">',
        '<header class="post-bg" id="page-header" style="background-image: url(/blog-xiuerhuahuazi/img/header-bg.jpg);">',
        html
    )

    # Dates
    html = re.sub(
        r'datetime="[^"]*" title="发表于 [^"]*"',
        f'datetime="{post["date"]}" title="发表于 {post["datetime_display"]}"',
        html
    )
    html = re.sub(
        r'datetime="[^"]*" title="更新于 [^"]*"',
        f'datetime="{post["date"]}" title="更新于 {post["datetime_display"]}"',
        html
    )
    html = re.sub(
        r'>[0-9]{4}-[0-9]{2}-[0-9]{2}</time>',
        f'>{post["date"]}</time>',
        html
    )

    # Article body
    html = re.sub(
        r'<article class="container post-content" id="article-container">.*?</article>',
        f'<article class="container post-content" id="article-container">{body_html}</article>',
        html,
        flags=re.DOTALL
    )

    # Tag links
    html = re.sub(
        r'<div class="post-meta__tag-list">.*?</div>',
        f'<div class="post-meta__tag-list">{tag_links}</div>',
        html,
        flags=re.DOTALL
    )

    # Pagination
    html = re.sub(
        r'<nav class="pagination-post" id="pagination">.*?</nav>',
        pagination_html,
        html,
        flags=re.DOTALL
    )

    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/md2post.py <markdown_file>")
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"❌ File not found: {md_path}")
        sys.exit(1)

    post = parse_md(md_path)
    body_html = md_to_html(post['md'])

    print(f"\n📄 Title: {post['title']}")
    print(f"📅 Date:  {post['date']}")
    print(f"🔖 Slug:  {post['slug']}")

    # Interactive tag & category input
    print("\n--- 标签和分类（直接回车跳过则以标题关键词自动提取）---")
    tags_input = input("🏷️  标签（逗号分隔，如: deepseek, llm, nas）: ").strip()
    if tags_input:
        post['tags'] = [t.strip() for t in tags_input.split(',') if t.strip()]
    else:
        # Auto-extract from title
        words = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', post['title'])
        post['tags'] = [w for w in words if len(w) > 1 and w.lower() not in ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一']][:5]
        print(f"   auto: {', '.join(post['tags'])}")

    cat_input = input(f"📂 分类（当前已有: 生活, 技术）: ").strip()
    post['category'] = cat_input if cat_input else '技术'
    print(f"   category: {post['category']}")

    # Build paths
    year, month, day = post['date'].split('-')
    url_encoded = f"{year}/{month}/{day}/{post['slug']}/"
    post_dir = os.path.join(BASE, year, month, day, post['slug'])
    os.makedirs(post_dir, exist_ok=True)

    # Build tags
    tags_str = ''.join(f'\n<meta property="article:tag" content="{t}">' for t in post['tags'])
    tag_links = ''.join(
        f'<a class="post-meta__tags" href="/blog-xiuerhuahuazi/tags/{t}/">{t}</a>'
        for t in post['tags']
    )

    # Simple pagination (link to first existing post)
    existing_posts_list = []
    for root, dirs, files in os.walk(os.path.join(BASE, '2026')):
        if 'index.html' in files and root != os.path.join(BASE, '2026'):
            rel = os.path.relpath(os.path.join(root, 'index.html'), BASE)
            existing_posts_list.append(rel)

    prev_link = ''
    next_link = ''
    if existing_posts_list:
        # Get the first existing post as prev
        first_existing = existing_posts_list[0]
        first_dir = os.path.dirname(first_existing)
        # Read title from that post
        with open(os.path.join(BASE, first_existing), 'r', encoding='utf-8') as f:
            first_html = f.read()
        m = re.search(r'<h1 class="post-title">(.*?)</h1>', first_html)
        first_title = m.group(1) if m else "Previous"

        prev_link = f'''<a class="pagination-related" href="/blog-xiuerhuahuazi/{first_dir}/" title="{first_title}">
<div class="cover" style="background: var(--default-bg-color)"></div>
<div class="info"><div class="info-1"><div class="info-item-1">上一篇</div><div class="info-item-2">{first_title}</div></div>
<div class="info-2"><div class="info-item-1">{first_title[:60]}</div></div></div></a>'''

    pagination_html = f'<nav class="pagination-post" id="pagination">\n{prev_link}\n{next_link}\n</nav>'

    # ---- Generate post ----
    post_html = build_post_html(post, body_html, tags_str, tag_links, url_encoded, pagination_html)

    with open(os.path.join(post_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(post_html)
    print(f"\n✅ Post created: {post_dir}/index.html")

    # ---- Update index.html ----
    idx_path = os.path.join(BASE, 'index.html')
    with open(idx_path, 'r', encoding='utf-8') as f:
        idx = f.read()

    new_entry = f'''<div class="recent-post-item"><div class="recent-post-info no-cover"><a class="article-title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a><div class="article-meta-wrap"><span class="post-meta-date"><i class="far fa-calendar-alt"></i><span class="article-meta-label">发表于</span><time datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></span></div><div class="content">{post["description"]}</div></div></div>'''
    idx = idx.replace('<div class="recent-post-items">', f'<div class="recent-post-items">\n{new_entry}')

    # Update article counts
    def bump_count(text, old, new):
        return text.replace(f'<div class="length-num">{old}</div>', f'<div class="length-num">{new}</div>')

    # Find current article count
    cm = re.search(r'<div class="length-num">(\d+)</div>', idx)
    if cm:
        cur = int(cm.group(1))
        idx = idx.replace(f'<div class="length-num">{cur}</div>', f'<div class="length-num">{cur + 1}</div>')
        idx = idx.replace(f'文章数目 :</div><div class="item-count">{cur}</div>', f'文章数目 :</div><div class="item-count">{cur + 1}</div>')
        # Archive count
        idx = re.sub(r'<span class="card-archive-list-count">\d+</span>', f'<span class="card-archive-list-count">{cur + 1}</span>', idx)

    # Update last-push-date
    idx = re.sub(r'data-lastPushDate="[^"]*"', f'data-lastPushDate="{post["datetime_iso"]}"', idx)

    # Add to sidebar latest posts
    new_aside = f'''\n        <div class="aside-list-item no-cover"><div class="content"><a class="title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a><time datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></div></div>'''
    aside_pattern = r'(<div class="aside-list">)(.*?)(</div>\s*</div>\s*<div class="card-widget card-categories">)'
    def add_aside(m):
        return m.group(1) + new_aside + m.group(2) + m.group(3)
    idx = re.sub(aside_pattern, add_aside, idx, flags=re.DOTALL)

    # Add tags to cloud
    tag_cloud = re.search(r'<div class="card-tag-cloud">.*?</div>', idx, re.DOTALL)
    if tag_cloud:
        existing = tag_cloud.group(0)
        new_tags = ''
        for t in post['tags']:
            if t not in existing:
                new_tags += f' <a href="/blog-xiuerhuahuazi/tags/{t}/" style="font-size: 1.1em; color: #999">{t}</a>'
        if new_tags:
            idx = idx.replace(existing, existing.replace('</div>', new_tags + '</div>'))

    # Update tag count
    tag_cm = re.search(r'<div class="length-num">(\d+)</div>.*?标签', idx)
    if tag_cm:
        pass  # Handled by bump above

    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx)
    print("✅ index.html updated")

    # ---- Create month archive ----
    arch_month_dir = os.path.join(BASE, 'archives', year, month)
    os.makedirs(arch_month_dir, exist_ok=True)

    existing_month_archives = []
    for aroot, adirs, afiles in os.walk(os.path.join(BASE, 'archives')):
        if 'index.html' in afiles and aroot != os.path.join(BASE, 'archives'):
            existing_month_archives.append(os.path.join(aroot, 'index.html'))

    if existing_month_archives:
        with open(existing_month_archives[0], 'r', encoding='utf-8') as f:
            arch_tpl = f.read()

        arch = arch_tpl
        month_name = f'{month}月 {year}' if post['date'] > '2026-07-01' else f'{month}月 {year}'
        # Fix: show proper Chinese month name
        cn_months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        cn_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
        month_cn = cn_names[int(month) - 1] if month in cn_months else f'{month}月'

        arch = re.sub(r'<title>.*?</title>', f'<title>{month_cn} {year} | 个人博客</title>', arch)
        arch = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{month_cn} {year}">', arch)
        arch = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/archives/{year}/{month}/index.html">', arch)
        arch = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/archives/{year}/{month}/index.html">', arch)
        arch = re.sub(r'<h1 id="site-title">[^<]*</h1>', f'<h1 id="site-title">{month_cn} {year}</h1>', arch)
        arch = re.sub(r"title: '[^']*'", f"title: '{month_cn} {year}'", arch)

        # Find current post count and increment
        acm = re.search(r'全部文章 - (\d+)', arch)
        old_count = int(acm.group(1)) if acm else 0

        arch = re.sub(r'全部文章 - \d+', '全部文章 - 1', arch)

        # Article list
        article_list = f'''<div class="article-sort"><div class="article-sort-item year">{year}</div><div class="article-sort-item no-article-cover"><div class="article-sort-item-info"><div class="article-sort-item-time"><i class="far fa-calendar-alt"></i><time class="post-meta-date-created" datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></div><a class="article-sort-item-title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a></div></div></div>'''
        arch = re.sub(r'<div class="article-sort">.*?</div>', article_list, arch, flags=re.DOTALL)

        # Update sidebar
        arch = re.sub(aside_pattern, add_aside, arch, flags=re.DOTALL)

        # Update counts
        arch = re.sub(r'<div class="length-num">\d+</div>', f'<div class="length-num">{old_count + 1}</div>', arch)
        arch = re.sub(r'文章数目 :</div><div class="item-count">\d+</div>', f'文章数目 :</div><div class="item-count">{old_count + 1}</div>', arch)
        arch = re.sub(r'<span class="card-archive-list-count">\d+</span>', f'<span class="card-archive-list-count">{old_count + 1}</span>', arch)
        arch = re.sub(r'data-lastPushDate="[^"]*"', f'data-lastPushDate="{post["datetime_iso"]}"', arch)

        with open(os.path.join(arch_month_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(arch)
        print(f"✅ archives/{year}/{month}/index.html created")

    # ---- Update year archive and main archive ----
    for arch_path in [os.path.join(BASE, 'archives', year, 'index.html'), os.path.join(BASE, 'archives', 'index.html')]:
        if not os.path.exists(arch_path):
            continue
        with open(arch_path, 'r', encoding='utf-8') as f:
            arch = f.read()

        # Bump counts
        acm = re.search(r'全部文章 - (\d+)', arch)
        old_ac = int(acm.group(1)) if acm else 1
        arch = re.sub(r'全部文章 - \d+', f'全部文章 - {old_ac + 1}', arch)

        # Add article to sort list
        new_article = f'''<div class="article-sort-item year">{year}</div><div class="article-sort-item no-article-cover"><div class="article-sort-item-info"><div class="article-sort-item-time"><i class="far fa-calendar-alt"></i><time class="post-meta-date-created" datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></div><a class="article-sort-item-title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a></div></div>'''
        arch = re.sub(r'<div class="article-sort-item year">2026</div>', f'{new_article}\n<div class="article-sort-item year">2026</div>', arch)

        # Update sidebar
        arch = re.sub(aside_pattern, add_aside, arch, flags=re.DOTALL)

        # Update counts
        arch = re.sub(r'<div class="length-num">\d+</div>', f'<div class="length-num">{old_ac + 1}</div>', arch)
        arch = re.sub(r'文章数目 :</div><div class="item-count">\d+</div>', f'文章数目 :</div><div class="item-count">{old_ac + 1}</div>', arch)
        arch = re.sub(r'<span class="card-archive-list-count">\d+</span>', f'<span class="card-archive-list-count">{old_ac + 1}</span>', arch)
        arch = re.sub(r'data-lastPushDate="[^"]*"', f'data-lastPushDate="{post["datetime_iso"]}"', arch)

        # For main archive, add month list entry
        if arch_path.endswith('archives/index.html'):
            month_entry = f'''<li class="card-archive-list-item">
          <a class="card-archive-list-link" href="/blog-xiuerhuahuazi/archives/{year}/{month}/">
            <span class="card-archive-list-date">
              {month_cn} {year}
            </span>
            <span class="card-archive-list-count">1</span>
          </a>
        </li>
      
        <li class="card-archive-list-item">'''
            # Insert before existing month
            arch = re.sub(
                r'<li class="card-archive-list-item">',
                month_entry,
                arch
            )

        with open(arch_path, 'w', encoding='utf-8') as f:
            f.write(arch)
        print(f"✅ {os.path.relpath(arch_path, BASE)} updated")

    # ---- Create tag pages ----
    tag_template = None
    for tag_dir_name in os.listdir(os.path.join(BASE, 'tags')):
        tp = os.path.join(BASE, 'tags', tag_dir_name, 'index.html')
        if os.path.exists(tp):
            with open(tp, 'r', encoding='utf-8') as f:
                tag_template = f.read()
            break

    if tag_template:
        for tag in post['tags']:
            tag_dir = os.path.join(BASE, 'tags', tag)
            if os.path.exists(os.path.join(tag_dir, 'index.html')):
                # Tag exists, update it
                with open(os.path.join(tag_dir, 'index.html'), 'r', encoding='utf-8') as f:
                    tp = f.read()
                tcm = re.search(r'全部文章 - (\d+)', tp)
                tcnt = int(tcm.group(1)) if tcm else 1
                tp = re.sub(r'全部文章 - \d+', f'全部文章 - {tcnt + 1}', tp)
                new_ta = f'''<div class="article-sort-item year">{year}</div><div class="article-sort-item no-article-cover"><div class="article-sort-item-info"><div class="article-sort-item-time"><i class="far fa-calendar-alt"></i><time class="post-meta-date-created" datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></div><a class="article-sort-item-title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a></div></div>'''
                tp = re.sub(r'<div class="article-sort-item year">2026</div>', f'{new_ta}\n<div class="article-sort-item year">2026</div>', tp)
                tp = re.sub(aside_pattern, add_aside, tp, flags=re.DOTALL)
                tp = re.sub(r'<div class="length-num">\d+</div>', f'<div class="length-num">{tcnt + 1}</div>', tp)
                tp = re.sub(r'文章数目 :</div><div class="item-count">\d+</div>', f'文章数目 :</div><div class="item-count">{tcnt + 1}</div>', tp)
                tp = re.sub(r'<span class="card-archive-list-count">\d+</span>', f'<span class="card-archive-list-count">{tcnt + 1}</span>', tp)
                tp = re.sub(r'data-lastPushDate="[^"]*"', f'data-lastPushDate="{post["datetime_iso"]}"', tp)
                with open(os.path.join(tag_dir, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(tp)
                print(f"✅ tags/{tag}/index.html updated")
            else:
                # New tag page
                os.makedirs(tag_dir, exist_ok=True)
                tp = tag_template
                tp = re.sub(r'<title>.*?</title>', f'<title>{tag} | 个人博客</title>', tp)
                tp = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{tag}">', tp)
                tp = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/tags/{tag}/index.html">', tp)
                tp = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/tags/{tag}/index.html">', tp)
                tp = re.sub(r'<h1 id="site-title">[^<]*</h1>', f'<h1 id="site-title">{tag}</h1>', tp)
                tp = re.sub(r"title: '[^']*'", f"title: '{tag}'", tp)
                tp = re.sub(r'全部文章 - \d+', '全部文章 - 1', tp)

                ta = f'''<div class="article-sort"><div class="article-sort-item year">{year}</div><div class="article-sort-item no-article-cover"><div class="article-sort-item-info"><div class="article-sort-item-time"><i class="far fa-calendar-alt"></i><time class="post-meta-date-created" datetime="{post["datetime_iso"]}" title="发表于 {post["datetime_display"]}">{post["date"]}</time></div><a class="article-sort-item-title" href="/blog-xiuerhuahuazi/{url_encoded}" title="{post["title"]}">{post["title"]}</a></div></div></div>'''
                tp = re.sub(r'<div class="article-sort">.*?</div>', ta, tp, flags=re.DOTALL)
                tp = re.sub(aside_pattern, add_aside, tp, flags=re.DOTALL)
                # Get count from main index
                cm = re.search(r'<div class="length-num">(\d+)</div>', idx)
                ncnt = int(cm.group(1)) if cm else 1
                tp = re.sub(r'<div class="length-num">\d+</div>', f'<div class="length-num">{ncnt}</div>', tp)
                tp = re.sub(r'文章数目 :</div><div class="item-count">\d+</div>', f'文章数目 :</div><div class="item-count">{ncnt}</div>', tp)
                tp = re.sub(r'<span class="card-archive-list-count">\d+</span>', f'<span class="card-archive-list-count">{ncnt}</span>', tp)
                tp = re.sub(r'data-lastPushDate="[^"]*"', f'data-lastPushDate="{post["datetime_iso"]}"', tp)
                with open(os.path.join(tag_dir, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(tp)
                print(f"✅ tags/{tag}/index.html created")

    # ---- Update sitemaps ----
    for sitemap_file in ['sitemap.xml', 'baidusitemap.xml']:
        sp = os.path.join(BASE, sitemap_file)
        if not os.path.exists(sp):
            continue
        with open(sp, 'r', encoding='utf-8') as f:
            sitemap = f.read()

        # Add new post URL
        new_url_entry = f'''  <url>
    <loc>https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/{url_encoded}</loc>
    <lastmod>{post["date"]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  '''

        if sitemap_file == 'sitemap.xml':
            # Also add archive and tag pages
            new_url_entry += f'''  <url>
    <loc>https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/archives/{year}/{month}/index.html</loc>
    <lastmod>{post["date"]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  '''
            for tag in post['tags']:
                new_url_entry += f'''  <url>
    <loc>https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/tags/{tag}/</loc>
    <lastmod>{post["date"]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.2</priority>
  </url>
  '''

        sitemap = re.sub(
            r'<url>\s*<loc>https://xiuerhuahuazi\.github\.io/blog-xiuerhuahuazi</loc>',
            new_url_entry + '<url>\n    <loc>https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi</loc>',
            sitemap
        )

        # Update lastmod for root
        sitemap = re.sub(
            r'<lastmod>[^<]+</lastmod>\n    <changefreq>daily</changefreq>',
            f'<lastmod>{post["date"]}</lastmod>\n    <changefreq>daily</changefreq>',
            sitemap
        )

        with open(sp, 'w', encoding='utf-8') as f:
            f.write(sitemap)
        print(f"✅ {sitemap_file} updated")

    # ---- Git add ----
    print("\n📦 Staging changes...")
    result = subprocess.run(['git', 'add', '-A'], cwd=BASE, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Changes staged. Ready to commit and push.")
    else:
        print(f"⚠️  Git add failed: {result.stderr}")

    print(f"\n🎉 Done! New post: /{url_encoded}")


if __name__ == '__main__':
    main()
