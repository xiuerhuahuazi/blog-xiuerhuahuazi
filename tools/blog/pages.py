"""页面构建：把内容与模板拼成 dist/ 下的静态站点。

  python3 tools/build.py          # 清空 dist 后全量生成
  python3 tools/build.py --check  # 只打印页面大小，不写 dist

流程：清空 dist → 复制 src/static/ 到 dist 根 → 复制 src/readers/ 到
dist/readers/ → 写 15 个页面（含 sitemap.xml 与 robots.txt）。
"""
import argparse
import re
import shutil
import sys
from datetime import date

from .config import BASE, DIST, READERS_SRC, ROOT, SITE, STATIC, TEMPLATES, load_readers
from .content import load_posts
from .template import Templates
from .utils import abs_url, depth_of, esc, human_date, nav_html, rel, txt

READERS = load_readers()
FEATURED = next((r for r in READERS if r.get("featured")), READERS[0] if READERS else None)
TODAY = date.today().isoformat()

T = Templates(TEMPLATES)
PARTIALS = Templates(TEMPLATES / "partials")


def render_page(path, title, desc, body, *, active="", extra="", bodyclass="",
                ogtype="website", image=None):
    """填 base.html 的共享槽位，返回整份 HTML 文档。"""
    depth = depth_of(path)
    page_title = f"{title} · {SITE['name']}" if title else SITE["title"]
    ogimage = ""
    if image:
        ogimage = PARTIALS.render("og-image.html", {
            "url": f"{BASE}/{image}",
            "alt": esc(title),
        })
    return T.render("base.html", {
        "lang": SITE["lang"], "title": esc(page_title), "desc": esc(desc),
        "author": esc(SITE["author"]), "canonical": abs_url(path.replace("index.html", "")),
        "root": rel(depth), "ogtype": ogtype, "name": esc(SITE["name"]),
        "ogimage": ogimage, "twcard": "summary_large_image" if image else "summary",
        "extra": extra, "bodyclass": bodyclass, "nav": nav_html(depth, active),
        "footer_nav": nav_html(depth, ""), "tagline": txt(SITE["tagline"]),
        "year": TODAY[:4], "content": body,
    })


def write(path, content):
    full = DIST / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return len(content)


# ---------------------------------------------------------------- 组件

def meta_chips(r):
    stats = [f'{r["pairs"]} 句对']
    if r["terms"]:
        stats.append(f'{r["terms"]} 术语')
    stats.append(f'{r["read_min"]} 分钟')
    return PARTIALS.render("reader-meta.html", {
        "category": txt(r["category"]),
        "stats": " · ".join(stats),
    })


def reader_row(r, index, href, tag="h3"):
    return PARTIALS.render("reader-row.html", {
        "i": min(index - 1, 5), "num": f"{index:02d}", "tag": tag, "href": href,
        "title_zh": txt(r["title_zh"]), "title_en": txt(r["title_en"]),
        "blurb": txt(r["blurb"]), "meta": meta_chips(r),
        "date": human_date(r["published"]),
    })


def note_row(p, href, tag="h3", index=0):
    tags = "".join(PARTIALS.render("tag.html", {"text": txt(t)}) for t in p["tags"])
    return PARTIALS.render("note-row.html", {
        "i": min(index, 5), "date": p["date"], "human_date": human_date(p["date"]),
        "tag": tag, "href": href, "title": txt(p["title"]),
        "description": txt(p["description"]), "tags": tags,
    })


def section_head(title, count, more_href=None, more_label="全部"):
    more = (PARTIALS.render("section-more.html", {"href": more_href, "label": more_label})
            if more_href else "")
    count_html = PARTIALS.render("section-count.html", {"count": count}) if count else ""
    return PARTIALS.render("section-head.html", {
        "title": title, "count": count_html, "more": more,
    })


# ---------------------------------------------------------------- 页面

def _feature_html():
    """首页「本期精读」卡片；没有 featured 时返回空串。"""
    if not FEATURED:
        return ""
    cover = FEATURED.get("cover") or ""
    media = (PARTIALS.render("feature-media.html", {
        "src": f'readers/{FEATURED["slug"]}/{esc(cover)}',
    }) if cover else "")
    return PARTIALS.render("feature.html", {
        "href": f'readers/{FEATURED["slug"]}/',
        "media": media,
        "date": human_date(FEATURED["published"]),
        "title": txt(FEATURED["title_zh"]),
        "title_en": txt(FEATURED["title_en"]),
        "blurb": txt(FEATURED["blurb"]),
        "meta": meta_chips(FEATURED),
    })


def build_home(posts):
    total_pairs = sum(r["pairs"] for r in READERS)
    total_terms = sum(r["terms"] for r in READERS)
    latest = [r for r in READERS if not r.get("featured")][:5]
    rows = "".join(reader_row(r, i + 1, f"readers/{r['slug']}/") for i, r in enumerate(latest))
    note_rows = "".join(note_row(p, p["path"] + "/", index=i) for i, p in enumerate(posts[:4]))
    body = T.render("home.html", {
        "readers": len(READERS), "pairs": f"{total_pairs:,}", "terms": total_terms,
        "notes": len(posts), "feature": _feature_html(),
        "head_readers": section_head("双语精读", len(READERS), "readers/", f"全部 {len(READERS)} 篇"),
        "rows": rows, "more_count": max(len(READERS) - len(latest), 0),
        "head_notes": section_head("技术手记", len(posts), "notes/", "全部"),
        "note_rows": note_rows,
    })
    cover = (FEATURED or {}).get("cover") or ""
    og = f"readers/{FEATURED['slug']}/{cover}" if FEATURED and cover else None
    return render_page("index.html", "", SITE["description"], body, image=og)


def build_readers_index():
    rows = "".join(reader_row(r, i + 1, f"{r['slug']}/", tag="h2") for i, r in enumerate(READERS))
    total_pairs = sum(r["pairs"] for r in READERS)
    body = T.render("readers.html", {
        "count": len(READERS), "pairs": f"{total_pairs:,}", "rows": rows,
    })
    cover = (FEATURED or {}).get("cover") or ""
    og = f"readers/{FEATURED['slug']}/{cover}" if FEATURED and cover else None
    return render_page("readers/index.html", "双语书架",
                       "英文原文与中文译文逐句对照的精读页合集。", body,
                       active="readers/", image=og)


def build_notes_index(posts):
    rows = "".join(note_row(p, rel(1) + p["path"] + "/", tag="h2", index=i)
                   for i, p in enumerate(posts))
    body = T.render("notes.html", {"rows": rows})
    return render_page("notes/index.html", "技术手记", "系统、模型与工具的实操记录。", body,
                       active="notes/")


def build_about():
    a = SITE["about"]
    paras = "".join(PARTIALS.render("paragraph.html", {"text": txt(p)}) for p in a["paras"])
    facts = "".join(PARTIALS.render("fact.html", {"key": txt(f["k"]), "value": txt(f["v"])})
                    for f in a["facts"])
    body = T.render("about.html", {
        "lead": txt(a["lead"]), "paras": paras, "facts": facts,
        "root": rel(1), "github": esc(SITE["github"]), "repo": esc(SITE["repo"]),
    })
    return render_page("about/index.html", "关于", "关于 xiuerhuahuazi 与这个站点。", body,
                       active="about/")


RELATED_DOTS = [
    (20, 23, 13, "#c9a597"),
    (73, 13, 13, "#9aa896"),
    (128, 24, 13, "#cdbd9c"),
    (183, 12, 13, "#8d99a5"),
    (234, 21, 13, "#bd8e7d"),
]


def related_posts(p, posts, limit=3):
    """显式 related 排前面，不够再用标签重合度补齐；同分按日期新到旧。"""
    by_slug = {q["slug"]: q for q in posts}
    picked = [by_slug[s] for s in p.get("related", [])
              if s in by_slug and s != p["slug"]][:limit]
    if len(picked) >= limit:
        return picked
    tags = set(p.get("tags", []))
    seen = {q["slug"] for q in picked}
    scored = []
    for q in posts:
        if q["slug"] == p["slug"] or q["slug"] in seen:
            continue
        shared = tags & set(q.get("tags", []))
        if shared:
            scored.append((len(shared), q["date"], q))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    filled = picked + [q for _, _, q in scored[:limit - len(picked)]]
    if len(filled) < limit:
        seen = {q["slug"] for q in filled} | {p["slug"]}
        rest = sorted((q for q in posts if q["slug"] not in seen),
                      key=lambda q: q["date"], reverse=True)
        filled += rest[:limit - len(filled)]
    return filled


def prompt_html(text):
    """提示词的最小 Markdown：空行分段、**加粗**、`code`，其余按原文转义。"""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        html = esc(block)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        out.append(f"<p>{html}</p>")
    return "".join(out)


def human_size(n):
    if n >= 1024 * 1024:
        return f"{n / 1048576:.1f} MB"
    return f"{max(1, round(n / 1024))} KB"


def _slide_html(it, depth):
    return PARTIALS.render("gallery-slide.html", {
        "src": rel(depth) + esc(it["img"]),
        "ar": it.get("ar", 1.5),
        "wide": "1" if float(it.get("ar", 1.5)) >= 1.3 else "0",
        "caption": txt(it["caption"]),
        "meta": txt(it["meta"]),
        "prompt_html": prompt_html(it["prompt"]),
        "prompt": esc(it["prompt"]),
    })


def render_figures(content, p, depth):
    """正文里的 {{fig:id}} / {{deck:group}} 换成图卡或叠卡轮播。"""
    groups = [g for g in p.get("gallery", [])]
    needles = re.findall(r"\{\{(fig|deck):([A-Za-z0-9_-]+)\}\}", content)
    if not needles:
        return content
    gmap = {g.get("id", ""): g for g in groups}
    imap = {}
    for g in groups:
        for it in g["items"]:
            key = it.get("id") or it["img"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
            imap[key] = it
    for kind, key in needles:
        if kind == "fig":
            it = imap.get(key)
            if it is None:
                raise ValueError(f"未知图片 id：{key}")
            html = PARTIALS.render("figure-inline.html", {
                "src": rel(depth) + esc(it["img"]),
                "ar": it.get("ar", 1.5),
                "wide": "1" if float(it.get("ar", 1.5)) >= 1.3 else "0",
                "caption": txt(it["caption"]),
                "meta": txt(it["meta"]),
                "prompt_html": prompt_html(it["prompt"]),
                "prompt": esc(it["prompt"]),
            })
        else:
            g = gmap.get(key)
            if g is None:
                raise ValueError(f"未知图组 id：{key}")
            html = PARTIALS.render("figure-deck.html", {
                "slides": "".join(_slide_html(it, depth) for it in g["items"]),
                "count": len(g["items"]),
                "wide": "1" if max(float(i.get("ar", 1.5)) for i in g["items"]) >= 1.3 else "0",
            })
        content = content.replace("{{%s:%s}}" % (kind, key), html)
    return content


def build_post(p, prev, nxt, posts):
    depth = depth_of(p["path"] + "/index.html")
    content = p["content"].replace("{{ROOT}}", rel(depth))
    toc_items = [t for t in p.get("toc", []) if t.get("id")]
    if len(toc_items) >= 2:
        links = "".join(
            PARTIALS.render("toc-item.html", {
                "level": t["level"], "id": esc(t["id"]), "text": txt(t["text"]),
            })
            for t in toc_items if t["level"] == 2)
        toc = PARTIALS.render("toc.html", {"links": links})
    else:
        toc = PARTIALS.render("toc-empty.html", {})

    tags = "".join(PARTIALS.render("tag.html", {"text": txt(t)}) for t in p["tags"])
    nav_links = ""
    if prev or nxt:
        empty = PARTIALS.render("post-link-empty.html", {})
        prev_html = (PARTIALS.render("post-link.html", {
            "kind": "prev", "label": "上一篇",
            "href": rel(depth) + prev["path"] + "/", "title": txt(prev["title"]),
        }) if prev else empty)
        next_html = (PARTIALS.render("post-link.html", {
            "kind": "next", "label": "下一篇",
            "href": rel(depth) + nxt["path"] + "/", "title": txt(nxt["title"]),
        }) if nxt else empty)
        nav_links = PARTIALS.render("post-nav.html", {"prev": prev_html, "next": next_html})

    related_html = ""
    related_end_html = ""
    rel_posts = related_posts(p, posts)
    if rel_posts:
        dots = []
        for i, q in enumerate(rel_posts):
            dots.append(PARTIALS.render("related-dot.html", {
                "href": rel(depth) + q["path"] + "/",
                "color": RELATED_DOTS[i % len(RELATED_DOTS)][3],
                "label": txt(q["title"]),
                "meta": txt((q["tags"][0] if q.get("tags") else "技术手记") +
                            " · " + human_date(q["date"])),
                "title": txt(q["title"]),
            }))
        dots_html = "".join(dots)
        related_html = PARTIALS.render("related.html", {
            "dots": dots_html, "root": rel(depth),
        })
        related_end_html = PARTIALS.render("related-end.html", {
            "dots": dots_html, "root": rel(depth),
        })

    prompt_modal_html = ""
    if p.get("gallery"):
        prompt_modal_html = PARTIALS.render("prompt-modal.html", {})
        content = render_figures(content, p, depth)

    files_html = ""
    if p.get("files"):
        rows = []
        for f in p["files"]:
            src = STATIC / f["href"]
            kind = f["href"].rsplit(".", 1)[-1].upper()
            body = ""
            if src.exists():
                try:
                    body = esc(src.read_text(encoding="utf-8"))
                except (UnicodeDecodeError, OSError):
                    body = ""
            rows.append(PARTIALS.render("file-row.html", {
                "href": rel(depth) + esc(f["href"]),
                "kind": kind,
                "name": txt(f["name"]),
                "desc": txt(f.get("desc", "")),
                "size": human_size(src.stat().st_size) if src.exists() else "",
                "doc": body,
            }))
        files_html = PARTIALS.render("post-files.html", {
            "items": "".join(rows),
            "note": txt(p.get("files_note",
                            "可直接下载；文中的示例地址与主机名已做脱敏。")),
        })

    body = T.render("post.html", {
        "root": rel(depth), "date": p["date"], "human_date": human_date(p["date"]),
        "tags": tags, "title": txt(p["title"]), "description": txt(p["description"]),
        "toc": toc, "content": content, "nav_links": nav_links,
        "related": related_html, "related_end": related_end_html,
        "prompt_modal": prompt_modal_html, "files": files_html,
    })
    return render_page(p["path"] + "/index.html", p["title"], p["description"], body,
                       active="notes/", ogtype="article", extra="", bodyclass="is-post")


def build_404():
    body = T.render("404.html", {})
    html_404 = render_page("404.html", "页面不存在", "404", body)

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
        sys.exit("src/content/readers.json 为空：先跑 tools/import_readers.py")

    pages = []
    pages.append(("index.html", build_home(posts)))
    pages.append(("readers/index.html", build_readers_index()))
    pages.append(("notes/index.html", build_notes_index(posts)))
    pages.append(("about/index.html", build_about()))
    for i, p in enumerate(posts):
        prev = posts[i + 1] if i + 1 < len(posts) else None
        nxt = posts[i - 1] if i > 0 else None
        pages.append((p["path"] + "/index.html", build_post(p, prev, nxt, posts)))
    pages.append(("404.html", build_404()))
    pages.append(("sitemap.xml", build_sitemap(posts)))
    pages.append(("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n"))

    if args.check:
        for path, content in pages:
            print(f"{len(content):8d}  {path}")
        print("共", len(pages), "个页面（未写入）")
        return

    # 防御性检查：只有仓库根下的 dist 才允许被整个删除
    if DIST.name != "dist" or DIST.parent != ROOT:
        sys.exit(f"拒绝清空 {DIST}：dist 必须是仓库根下的 dist 目录")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(STATIC, DIST, dirs_exist_ok=True)
    shutil.copytree(READERS_SRC, DIST / "readers")

    for path, content in pages:
        write(path, content)

    print("生成", len(pages), "个页面")
    total = sum(len(c) for _, c in pages)
    print(f"HTML 合计 {total/1024:.0f} KB")


if __name__ == "__main__":
    main()
