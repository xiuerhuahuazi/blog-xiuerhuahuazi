#!/usr/bin/env python3
"""把一篇 Markdown 变成技术手记，并重新生成站点。

  python3 tools/md2post.py post.md
  python3 tools/md2post.py post.md --date 2026-11-20 --slug my-post --force

文件头可以用 front matter（--- 包起来，全部可选）：
  title:    标题（默认取第一个 # 标题或文件名）
  date:     2026-11-20（默认今天）
  tags:     hermes-agent, docker
  desc:     一句话摘要（默认取第一段前 120 字）
  slug:     URL 片段（默认由标题转写）

生成内容写入 content/posts/<slug>.json，页面落在 <年>/<月>/<日>/<slug>/，
与老文章同样的 URL 形态。支持的 Markdown：标题、段落、列表、引用、代码块、
分隔线、图片、链接、粗体/斜体/行内代码。表格不支持——需要表格时直接改
content/posts/<slug>.json 里的 HTML 片段。
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content", "posts")
FENCE = "\x60\x60\x60"
SAFE_SCHEMES = ("http://", "https://", "mailto:", "tel:", "#", "/", "./", "../")


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-") or "post"


def safe_url(url):
    """只放行常见协议与站内相对地址，挡掉 javascript: / data: 之类。"""
    u = html.unescape(url).strip()
    low = u.lower()
    if low.startswith(SAFE_SCHEMES):
        return html.escape(u, quote=True)
    if re.match(r"^[a-z][a-z0-9+.-]*:", low):   # 其它协议一律拒绝
        return "#"
    return html.escape(u, quote=True)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub("\x60([^\x60\n]+)\x60", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: f'<img src="{safe_url(m.group(2))}" alt="{html.escape(m.group(1), quote=True)}" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{safe_url(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def convert(md, used_ids):
    """极简 Markdown → HTML。只做手记需要的子集。"""
    lines = md.split("\n")
    out, buf, i = [], [], 0

    def flush():
        if buf:
            out.append("<p>" + inline(" ".join(buf).strip()) + "</p>")
            buf.clear()

    def heading_id(text):
        base = slugify(text)
        n = used_ids.get(base, 0) + 1
        used_ids[base] = n
        return base if n == 1 else f"{base}-{n}"

    while i < len(lines):
        line = lines[i]
        if line.startswith(FENCE):
            flush()
            lang = line[len(FENCE):].strip()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith(FENCE):
                code.append(lines[i])
                i += 1
            cls = f' class="language-{html.escape(lang, quote=True)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code))}</code></pre>")
        elif re.match(r"^#{1,4}\s", line):
            flush()
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            out.append(f'<h{level} id="{heading_id(text)}">{inline(text)}</h{level}>')
        elif re.match(r"^\s*[-*]\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        elif re.match(r"^\s*\d+\.\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        elif line.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue
        elif line.strip() in ("---", "***"):
            flush()
            out.append("<hr>")
        elif not line.strip():
            flush()
        else:
            buf.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


def parse_front_matter(text):
    meta = {}
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
            text = text[end + 4:].lstrip("\n")
    return meta, text


def check_slug(slug):
    if not slug or "/" in slug or "\\" in slug or ".." in slug or slug.startswith("."):
        sys.exit(f"非法 slug：{slug!r}（只能是单段名字，不能含 / \\ .. 或以 . 开头）")
    if not re.fullmatch(r"[\w\u4e00-\u9fff.-]+", slug):
        sys.exit(f"非法 slug：{slug!r}（只允许字母、数字、下划线、连字符、点与中文）")
    return slug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--date", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    raw = open(os.path.expanduser(args.markdown), encoding="utf-8").read()
    meta, body = parse_front_matter(raw)

    hm = re.search(r"^#\s+(.+)$", body, re.M)
    title = meta.get("title") or (hm.group(1).strip() if hm else
                                  os.path.splitext(os.path.basename(args.markdown))[0])
    if hm:
        body = body[:hm.start()] + body[hm.end():].lstrip("\n")

    day = meta.get("date") or args.date or date.today().isoformat()
    try:
        y, mo, d = [int(x) for x in re.split(r"[-/.]", day)[:3]]
    except ValueError:
        sys.exit(f"日期看不懂：{day!r}（要 2026-11-20 这种）")
    day = f"{y:04d}-{mo:02d}-{d:02d}"

    slug = check_slug(meta.get("slug") or args.slug or slugify(title))
    tags = [t.strip() for t in re.split(r"[,，]", meta.get("tags", "")) if t.strip()] or ["技术"]
    content = convert(body, {})
    first = re.sub(r"<[^>]+>", "", content.split("\n")[0]) if content else ""
    desc = meta.get("desc") or (first[:120] if first else title)

    path = f"{y:04d}/{mo:02d}/{d:02d}/{slug}"
    dest = os.path.normpath(os.path.join(OUT, slug + ".json"))
    if os.path.commonpath([dest, OUT]) != OUT:
        sys.exit("拒绝写入 content/posts 之外的路径")
    if os.path.exists(dest) and not args.force:
        sys.exit(f"{os.path.relpath(dest, ROOT)} 已存在；要覆盖加 --force")

    heads = re.findall(r"<h([23])([^>]*)>(.*?)</h\1>", content, re.S)
    toc = []
    for lv, attrs, inner in heads:
        idm = re.search(r'id="([^"]+)"', attrs)
        toc.append({"level": int(lv), "text": re.sub(r"<[^>]+>", "", inner), "id": idm.group(1) if idm else ""})

    post = {"slug": slug, "path": path, "title": title, "description": desc,
            "date": day, "tags": tags, "content": content, "toc": toc}
    os.makedirs(OUT, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("写入", os.path.relpath(dest, ROOT), "→", path + "/")

    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py")], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_site.py")], check=True)


if __name__ == "__main__":
    main()
