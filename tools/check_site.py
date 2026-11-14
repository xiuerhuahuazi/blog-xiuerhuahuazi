#!/usr/bin/env python3
"""生成后自检：内部链接、资源、锚点、canonical 是否都站得住。

  python3 tools/check_site.py

只检查仓库内已生成的静态文件（不联网）。任何失败退出码 1。
覆盖：href / src / data-src / poster / srcset，站内绝对路径（按 BASE 前缀），
页内 #锚点，以及每页的 <title> / meta description / rel=canonical。
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "content", "tools", "assets", ".github"}
BASE = "/blog-xiuerhuahuazi/"


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []          # (kind, value)
        self.ids = set()
        self.title = ""
        self.has_desc = False
        self.canonical = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for attr in ("href", "src", "data-src", "poster"):
            if a.get(attr):
                self.refs.append((attr, a[attr]))
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url:
                    self.refs.append(("srcset", url))
        if tag == "meta":
            if a.get("name") == "description" and a.get("content"):
                self.has_desc = True
            if a.get("property") == "og:image" and a.get("content"):
                self.refs.append(("og:image", a["content"]))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def resolve(page, ref):
    """把引用解析成仓库内的绝对路径；站外返回 None。"""
    parts = urlsplit(ref)
    if parts.scheme in ("http", "https"):
        prefix = "https://xiuerhuahuazi.github.io"
        if not ref.startswith(prefix + BASE):
            return None
        path = unquote(ref[len(prefix):])          # "/blog-xiuerhuahuazi/readers/"
        return os.path.normpath(os.path.join(ROOT, path[len(BASE):]))
    if parts.scheme or ref.startswith("//"):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    if path.startswith("/"):
        # 站内绝对路径：Pages 部署在子路径下，本地按 BASE 剥掉前缀
        relpath = path[len(BASE):] if path.startswith(BASE) else path.lstrip("/")
        return os.path.normpath(os.path.join(ROOT, relpath))
    return os.path.normpath(os.path.join(os.path.dirname(page), path))


def main():
    pages, problems, checked = [], [], 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".html"):
                pages.append(os.path.join(dirpath, fn))

    for page in pages:
        rel_page = os.path.relpath(page, ROOT)
        p = Collector()
        p.feed(open(page, encoding="utf-8").read())
        if not p.title.strip():
            problems.append(f"{rel_page}: 缺少 <title>")
        if rel_page != "404.html":
            if not p.has_desc:
                problems.append(f"{rel_page}: 缺少 meta description")
            if not p.canonical:
                problems.append(f"{rel_page}: 缺少 rel=canonical")
            elif not p.canonical.startswith("https://xiuerhuahuazi.github.io" + BASE):
                problems.append(f"{rel_page}: canonical 不在站点前缀下：{p.canonical}")

        for kind, ref in p.refs:
            if re.match(r"^(data:|javascript:|mailto:|tel:)", ref):
                continue
            if ref.startswith("#"):
                frag = unquote(ref[1:])
                checked += 1
                if frag and frag not in p.ids:
                    problems.append(f"{rel_page}: 页内锚点 #{frag} 不存在")
                continue
            target = resolve(page, ref)
            if target is None:
                continue
            checked += 1
            candidates = [target, os.path.join(target, "index.html")]
            if not any(os.path.exists(c) for c in candidates):
                problems.append(f"{rel_page}: {kind} 指向不存在的 {ref} → {os.path.relpath(target, ROOT)}")

    print(f"检查 {len(pages)} 个页面、{checked} 个引用")
    if problems:
        for x in problems:
            print("  ✗", x)
        print(f"FAIL：{len(problems)} 个问题")
        return 1
    print("OK：链接、资源、锚点与 canonical 都正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
