#!/usr/bin/env python3
"""博客生成器：content/ → 静态页面。

  python3 tools/build.py          # 生成全站
  python3 tools/build.py --check  # 只检查内容，不写文件

目录约定
  content/site.json      站点名、导航、关于页文案
  content/readers.json   双语精读索引（tools/import_readers.py 生成）
  content/posts/*.json   技术手记（tools/import_legacy.py 导入；新增文章见 README）
  assets/                样式与脚本（源文件，原样发布）
  readers/<slug>/        精读成品页（tools/import_readers.py 导入，build 不改写）

页面
  /                    首页
  /readers/            双语书架
  /notes/              技术手记列表
  /<原路径>/index.html 技术手记正文（沿用老 URL，不制造死链）
  /about/              关于
  /404.html
  /sitemap.xml /robots.txt
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
from datetime import date
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))
READERS = json.load(open(os.path.join(ROOT, "content", "readers.json"), encoding="utf-8"))["readers"]
BASE = SITE["url"].rstrip("/")

FEATURED = next((r for r in READERS if r.get("featured")), READERS[0] if READERS else None)
TODAY = date.today().isoformat()

esc = lambda s: html.escape(str(s), quote=True)
txt = lambda s: html.escape(str(s), quote=False)


def rel(depth):
    return "../" * depth


def depth_of(path):
    """path 是相对仓库根的页面路径（含 index.html）"""
    return path.count("/")


def abs_url(path):
    """站点绝对地址；中文/括号目录要百分号编码，sitemap 与 canonical 才合法。"""
    return BASE + "/" + quote(path, safe="/")


def human_date(iso):
    try:
        y, m, d = iso.split("-")
        return f"{y}.{m}.{d}"
    except ValueError:
        return iso


def load_posts():
    d = os.path.join(ROOT, "content", "posts")
    posts = []
    for name in os.listdir(d):
        if not name.endswith(".json"):
            continue
        post = json.load(open(os.path.join(d, name), encoding="utf-8"))
        posts.append(post)
    posts.sort(key=lambda p: (p["date"], p.get("slug", "")), reverse=True)
    return posts


# ---------------------------------------------------------------- 模板

HEAD = """<!DOCTYPE html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{author}">
<meta name="theme-color" content="#fbf8f3">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{r}img/favicon.ico" sizes="any">
<meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="{name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="zh_CN">
{ogimage}<meta name="twitter:card" content="{twcard}">
<link rel="stylesheet" href="{r}assets/site.css">
<script>(function(){{try{{if(localStorage.getItem('site-theme')==='dark'){{document.documentElement.dataset.theme='dark'}}}}catch(e){{}}}})();</script>
<script>(function(){{try{{var d=document.documentElement;if(!('IntersectionObserver' in window)||!window.matchMedia)return;if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;d.classList.add('js-motion');setTimeout(function(){{if(!d.getAttribute('data-motion-ready'))d.classList.remove('js-motion')}},3000)}}catch(e){{}}}})();</script>
{extra}
</head>
<body class="{bodyclass}">
<a class="skip" href="#main">跳到正文</a>
<header class="masthead">
  <div class="wrap masthead-in">
    <a class="brand" href="{r}" aria-label="回到首页">
      <span class="brand-mark" aria-hidden="true">x</span>
      <span class="brand-word">xiuerhuahuazi</span>
    </a>
    <nav class="nav" aria-label="主导航">{nav}</nav>
    <button class="theme-btn" type="button" data-theme-toggle aria-label="切换深色模式" aria-pressed="false">
      <svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>
      <svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.3A8.6 8.6 0 1 1 9.7 3.5a7 7 0 0 0 10.8 10.8z"/></svg>
    </button>
  </div>
</header>
<main id="main">
"""

FOOT = """</main>
<footer class="site-foot">
  <div class="wrap foot-in">
    <div class="foot-brand">
      <span class="brand-mark" aria-hidden="true">x</span>
      <div>
        <p class="foot-name">xiuerhuahuazi</p>
        <p class="foot-line">{tagline}</p>
      </div>
    </div>
    <nav class="foot-nav" aria-label="页脚导航">{nav}</nav>
    <p class="foot-meta">© {year} · 纯静态页面 · 无第三方脚本与统计</p>
  </div>
</footer>
<script src="{r}assets/site.js" defer></script>
</body>
</html>
"""


def nav_html(depth, active):
    out = []
    for item in SITE["nav"]:
        cls = ' class="on"' if item["href"] == active else ""
        out.append(f'<a href="{rel(depth)}{item["href"]}"{cls}>{item["label"]}</a>')
    return "".join(out)


def render(path, title, desc, body, *, active="", extra="", bodyclass="", ogtype="website", image=None):
    depth = depth_of(path)
    page_title = f"{title} · {SITE['name']}" if title else SITE["title"]
    ogimage = ""
    if image:
        ogimage = (f'<meta property="og:image" content="{BASE}/{image}">\n'
                   f'<meta property="og:image:alt" content="{esc(title)}">\n')
    head = HEAD.format(
        lang=SITE["lang"], title=esc(page_title), desc=esc(desc), author=esc(SITE["author"]),
        canonical=abs_url(path.replace("index.html", "")), r=rel(depth),
        ogtype=ogtype, name=esc(SITE["name"]), ogimage=ogimage,
        twcard="summary_large_image" if image else "summary",
        extra=extra, bodyclass=bodyclass, nav=nav_html(depth, active),
    )
    foot = FOOT.format(tagline=txt(SITE["tagline"]), nav=nav_html(depth, ""),
                       year=TODAY[:4], r=rel(depth))
    return head + body + foot


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return len(content)


# ---------------------------------------------------------------- 组件

def chip(text):
    return f'<span class="chip">{txt(text)}</span>'


def meta_chips(r):
    stats = [f'{r["pairs"]} 句对']
    if r["terms"]:
        stats.append(f'{r["terms"]} 术语')
    stats.append(f'{r["read_min"]} 分钟')
    return (f'<div class="row-meta-in"><span class="chip">{txt(r["category"])}</span>'
            f'<span class="row-stats">{" · ".join(stats)}</span></div>')


def reader_row(r, index, href, tag="h3"):
    return f"""<article class="read-row" data-reveal style="--i:{min(index - 1, 5)}">
  <span class="row-num" aria-hidden="true">{index:02d}</span>
  <div class="row-main">
    <{tag} class="row-title"><a href="{href}">{txt(r["title_zh"])}</a></{tag}>
    <p class="row-en" lang="en">{txt(r["title_en"])}</p>
    <p class="row-blurb">{txt(r["blurb"])}</p>
  </div>
  <div class="row-meta">
    {meta_chips(r)}
    <span class="row-date">{human_date(r["published"])}</span>
    <span class="row-go" aria-hidden="true">↗</span>
  </div>
</article>"""


def note_row(p, href, tag="h3", index=0):
    tags = "".join(f'<span class="tag">{txt(t)}</span>' for t in p["tags"])
    return f"""<article class="note-row" data-reveal style="--i:{min(index, 5)}">
  <time datetime="{p["date"]}">{human_date(p["date"])}</time>
  <div class="note-main">
    <{tag} class="note-title"><a href="{href}">{txt(p["title"])}</a></{tag}>
    <p>{txt(p["description"])}</p>
  </div>
  <div class="note-tags">{tags}</div>
</article>"""


def section_head(title, count, more_href=None, more_label="全部"):
    more = f'<a class="sec-more" href="{more_href}">{more_label} <span aria-hidden="true">→</span></a>' if more_href else ""
    count_html = f'<span class="sec-count">{count}</span>' if count else ""
    return f'<div class="sec-head" data-reveal><h2 class="sec-title">{title}{count_html}</h2>{more}</div>'


# ---------------------------------------------------------------- 页面

def build_home(posts):
    total_pairs = sum(r["pairs"] for r in READERS)
    total_terms = sum(r["terms"] for r in READERS)
    latest = [r for r in READERS if not r.get("featured")][:5]

    spec = """
<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-copy">
      <p class="eyebrow">Bilingual Reader · Notes</p>
      <h1><span class="line"><span class="line-in">把值得读的文章，</span></span><span class="line"><span class="line-in"><em>读透</em>。</span></span></h1>
      <p class="lede">英文原文与中文译文逐句对照，配术语卡、译者注和图注解读；下面是平日的技术手记。不是机翻，每一句都过了一遍。</p>
      <dl class="stats">
        <div><dt>双语精读</dt><dd>{readers}<small>篇</small></dd></div>
        <div><dt>逐句对照</dt><dd>{pairs}<small>句</small></dd></div>
        <div><dt>术语卡</dt><dd>{terms}<small>张</small></dd></div>
        <div><dt>技术手记</dt><dd>{notes}<small>篇</small></dd></div>
      </dl>
    </div>
    <div class="specimen">
      <div class="specimen-head"><span>逐句对照</span><span class="specimen-src">EN / 中</span></div>
      <div class="spec-pair">
        <span class="spec-no">01</span>
        <p class="spec-en" lang="en">Review becomes spelling-check-as-you-write, not the gate at the end of the road.</p>
        <p class="spec-zh">review 不再是路尽头的闸门，而是写代码时的拼写检查。</p>
      </div>
      <div class="spec-pair">
        <span class="spec-no">02</span>
        <p class="spec-en" lang="en">When you have several agents writing code, you are managing.</p>
        <p class="spec-zh">当有好几个智能体在写代码时，你其实已经在做管理。</p>
      </div>
      <p class="specimen-foot">悬停任一句，另一侧同步高亮 · <span>阅读器里的真实交互</span></p>
    </div>
  </div>
</section>
""".format(readers=len(READERS), pairs=f"{total_pairs:,}", terms=total_terms, notes=len(posts))

    feature = ""
    if FEATURED:
        cover = FEATURED.get("cover") or ""
        media = (f'<div class="feature-media"><img src="readers/{FEATURED["slug"]}/{esc(cover)}" alt="" loading="lazy"></div>'
                 if cover else "")
        feature = f"""
<section class="feature-wrap">
  <div class="wrap">
    <a class="feature" href="readers/{FEATURED["slug"]}/" data-reveal>
      {media}
      <div class="feature-body">
        <p class="kicker">本期精读 · {human_date(FEATURED["published"])}</p>
        <h2 class="feature-title">{txt(FEATURED["title_zh"])}</h2>
        <p class="feature-en" lang="en">{txt(FEATURED["title_en"])}</p>
        <p class="feature-blurb">{txt(FEATURED["blurb"])}</p>
        <div class="feature-meta">{meta_chips(FEATURED)}</div>
        <span class="cta">进入阅读 <span aria-hidden="true">→</span></span>
      </div>
    </a>
  </div>
</section>"""

    rows = "".join(reader_row(r, i + 1, f"readers/{r['slug']}/") for i, r in enumerate(latest))
    note_rows = "".join(note_row(p, p["path"] + "/", index=i) for i, p in enumerate(posts[:4]))

    body = spec + feature + f"""
<section class="block">
  <div class="wrap">
    {section_head("双语精读", len(READERS), "readers/", f"全部 {len(READERS)} 篇")}
    <div class="read-list">{rows}</div>
    <a class="more-link" href="readers/" data-reveal>看完剩下 {max(len(READERS) - len(latest), 0)} 篇 <span aria-hidden="true">→</span></a>
  </div>
</section>

<section class="block">
  <div class="wrap">
    {section_head("技术手记", len(posts), "notes/", "全部")}
    <div class="note-list">{note_rows}</div>
  </div>
</section>

<section class="block about-strip">
  <div class="wrap about-strip-in" data-reveal>
    <div class="about-portrait"><img src="img/avatar.jpg" alt="xiuerhuahuazi" width="88" height="88" loading="lazy"></div>
    <div>
      <h2 class="about-strip-title">关于这个站点</h2>
      <p>这里放两样东西：逐句对照的双语精读页，和折腾系统、模型、工具时留下的技术手记。都是自己读完、踩完之后写的。</p>
      <a class="text-link" href="about/">读完这段介绍 <span aria-hidden="true">→</span></a>
    </div>
  </div>
</section>
"""
    cover = (FEATURED or {}).get("cover") or ""
    og = f"readers/{FEATURED['slug']}/{cover}" if FEATURED and cover else None
    return render("index.html", "", SITE["description"], body, image=og)


def build_readers_index():
    rows = "".join(reader_row(r, i + 1, f"{r['slug']}/", tag="h2") for i, r in enumerate(READERS))
    total_pairs = sum(r["pairs"] for r in READERS)
    body = f"""
<header class="page-head">
  <div class="wrap">
    <p class="eyebrow">Bilingual Reader</p>
    <h1>双语书架</h1>
    <p class="page-lede">{len(READERS)} 篇英文长文，逐句拆成 {total_pairs:,} 组对照。左边英文、右边中文，读到哪句不懂就悬停，另一侧同步亮起；术语有卡，图有逐条解读，译者觉得有坑的地方写了注。</p>
    <ul class="mech">
      <li><b>悬停联动</b><span>任一句悬停，另一侧同一句高亮</span></li>
      <li><b>术语卡</b><span>虚线下划线处悬停看解释</span></li>
      <li><b>译者注</b><span>上标数字，点开是补的背景</span></li>
    </ul>
  </div>
</header>
<section class="block">
  <div class="wrap">
    <div class="read-list">{rows}</div>
  </div>
</section>
"""
    cover = (FEATURED or {}).get("cover") or ""
    og = f"readers/{FEATURED['slug']}/{cover}" if FEATURED and cover else None
    return render("readers/index.html", "双语书架", "英文原文与中文译文逐句对照的精读页合集。", body,
                  active="readers/", image=og)


def build_notes_index(posts):
    rows = "".join(note_row(p, rel(1) + p["path"] + "/", tag="h2", index=i) for i, p in enumerate(posts))
    body = f"""
<header class="page-head">
  <div class="wrap">
    <p class="eyebrow">Notes</p>
    <h1>技术手记</h1>
    <p class="page-lede">折腾系统、模型与工具时留下的记录。命令、报错和为什么这么修，能复现的才写。</p>
  </div>
</header>
<section class="block">
  <div class="wrap">
    <div class="note-list">{rows}</div>
  </div>
</section>
"""
    return render("notes/index.html", "技术手记", "系统、模型与工具的实操记录。", body, active="notes/")


def build_about():
    a = SITE["about"]
    paras = "".join(f"<p>{txt(p)}</p>" for p in a["paras"])
    facts = "".join(f'<dt>{txt(f["k"])}</dt><dd>{txt(f["v"])}</dd>' for f in a["facts"])
    body = f"""
<header class="page-head">
  <div class="wrap">
    <p class="eyebrow">About</p>
    <h1>关于</h1>
  </div>
</header>
<section class="block">
  <div class="wrap about-page">
    <div class="about-page-main">
      <p class="about-lead">{txt(a["lead"])}</p>
      {paras}
      <dl class="about-facts">{facts}</dl>
    </div>
    <aside class="about-page-side">
      <div class="about-card">
        <img src="{rel(1)}img/avatar.jpg" alt="xiuerhuahuazi" width="96" height="96" loading="lazy">
        <p class="about-card-name">xiuerhuahuazi</p>
        <p class="about-card-handle">GitHub</p>
        <a class="btn" href="{esc(SITE["github"])}" rel="noopener">github.com/xiuerhuahuazi <span aria-hidden="true">↗</span></a>
        <a class="text-link" href="{esc(SITE["repo"])}" rel="noopener">本站源码</a>
      </div>
    </aside>
  </div>
</section>
"""
    return render("about/index.html", "关于", "关于 xiuerhuahuazi 与这个站点。", body, active="about/")


def build_post(p, prev, nxt):
    depth = depth_of(p["path"] + "/index.html")
    content = p["content"].replace("{{ROOT}}", rel(depth))
    toc_items = [t for t in p.get("toc", []) if t.get("id")]
    toc = ""
    if len(toc_items) >= 2:
        links = "".join(
            f'<li class="toc-l{t["level"]}"><a href="#{esc(t["id"])}">{txt(t["text"])}</a></li>'
            for t in toc_items if t["level"] == 2)
        toc = f'<aside class="toc" aria-label="目录"><p class="toc-title">目录</p><ol>{links}</ol></aside>'
    else:
        toc = '<aside class="toc" aria-hidden="true"></aside>'

    tags = "".join(f'<span class="tag">{txt(t)}</span>' for t in p["tags"])
    nav_links = ""
    if prev or nxt:
        prev_html = (f'<a class="pn prev" href="{rel(depth)}{prev["path"]}/"><span>上一篇</span>{txt(prev["title"])}</a>'
                     if prev else "<span></span>")
        next_html = (f'<a class="pn next" href="{rel(depth)}{nxt["path"]}/"><span>下一篇</span>{txt(nxt["title"])}</a>'
                     if nxt else "<span></span>")
        nav_links = f'<nav class="post-nav" aria-label="文章导航" data-reveal>{prev_html}{next_html}</nav>'

    body = f"""
<div class="progress" aria-hidden="true"><i></i></div>
<article class="post">
  <header class="post-head">
    <div class="wrap post-head-in">
      <a class="back-link" href="{rel(depth)}notes/">← 技术手记</a>
      <p class="post-kicker"><time datetime="{p["date"]}">{human_date(p["date"])}</time>{tags}</p>
      <h1>{txt(p["title"])}</h1>
      <p class="post-lede">{txt(p["description"])}</p>
    </div>
  </header>
  <div class="wrap post-grid">
    {toc}
    <div class="prose" id="article">
      {content}
    </div>
  </div>
  <div class="wrap">{nav_links}</div>
</article>
"""
    return render(p["path"] + "/index.html", p["title"], p["description"], body,
                  active="notes/", ogtype="article", extra="", bodyclass="is-post")


def build_404():
    body = """
<section class="block error-page">
  <div class="wrap">
    <p class="eyebrow">404</p>
    <h1>这页不见了</h1>
    <p class="page-lede">链接可能改过，或者本来就没写完。回首页，或者去书架挑一篇。</p>
    <p class="error-actions"><a class="btn" href="./">回首页</a><a class="text-link" href="readers/">去双语书架 <span aria-hidden="true">→</span></a></p>
  </div>
</section>
"""
    html_404 = render("404.html", "页面不存在", "404", body)
    # 404 可能从任意深度被请求：把站内相对地址一律换成站点绝对地址
    def absolutize(doc):
        return re.sub(r'(href|src)="(?!https?:|mailto:|#|data:)([^"]*)"',
                      lambda m: f'{m.group(1)}="{BASE}/{m.group(2)}"', doc)
    return absolutize(html_404)


def build_sitemap(posts):
    urls = [("", "1.0"), ("readers/", "0.9"), ("notes/", "0.7"), ("about/", "0.4")]
    urls += [(f"readers/{r['slug']}/", "0.8") for r in READERS]
    urls += [(p["path"] + "/", "0.6") for p in posts]
    items = "".join(
        f"<url><loc>{abs_url(u)}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>"
        for u, pr in urls)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    posts = load_posts()
    if not READERS:
        sys.exit("content/readers.json 为空：先跑 tools/import_readers.py")

    pages = []
    pages.append(("index.html", build_home(posts)))
    pages.append(("readers/index.html", build_readers_index()))
    pages.append(("notes/index.html", build_notes_index(posts)))
    pages.append(("about/index.html", build_about()))
    for i, p in enumerate(posts):
        prev = posts[i + 1] if i + 1 < len(posts) else None
        nxt = posts[i - 1] if i > 0 else None
        pages.append((p["path"] + "/index.html", build_post(p, prev, nxt)))
    pages.append(("404.html", build_404()))
    pages.append(("sitemap.xml", build_sitemap(posts)))
    pages.append(("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n"))

    if args.check:
        for path, content in pages:
            print(f"{len(content):8d}  {path}")
        print("共", len(pages), "个页面（未写入）")
        return

    for path, content in pages:
        write(path, content)

    # 清理内容里已经没有的旧文章目录（改日期或删文章后不留下孤儿页面）
    live = {p["path"] for p in posts}
    for year in os.listdir(ROOT):
        if not re.fullmatch(r"20\d{2}", year):
            continue
        for month in os.listdir(os.path.join(ROOT, year)):
            mdir = os.path.join(ROOT, year, month)
            if not os.path.isdir(mdir):
                continue
            for day in os.listdir(mdir):
                ddir = os.path.join(mdir, day)
                if not os.path.isdir(ddir):
                    continue
                for slug in os.listdir(ddir):
                    rel = f"{year}/{month}/{day}/{slug}"
                    if rel not in live and os.path.isfile(os.path.join(ddir, slug, "index.html")):
                        shutil.rmtree(os.path.join(ddir, slug))
                        print("清理孤儿页面", rel)
                if not os.listdir(ddir):
                    os.rmdir(ddir)

    print("生成", len(pages), "个页面")
    total = sum(len(c) for _, c in pages)
    print(f"HTML 合计 {total/1024:.0f} KB")


if __name__ == "__main__":
    main()
