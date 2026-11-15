"""Markdown → 可移植 HTML 片段的纯函数。

只覆盖技术手记需要的子集：标题、段落、列表、引用、代码块、分隔线、
图片、链接、粗体/斜体/行内代码。表格不支持——需要表格时直接改
src/content/posts/<slug>.json 里的 HTML 片段。
"""
import html
import re
import sys

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
