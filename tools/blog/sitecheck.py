"""生成后自检：dist/ 里的内部链接、资源、锚点、canonical 是否都站得住。

只检查 dist/ 内已生成的静态文件（不联网）。任何失败退出码 1。
覆盖：
  - href / src / data-src / poster / srcset 指向的文件是否存在；
  - 目录链接必须带 index.html，不能只命中一个空目录；
  - 站内绝对路径必须带站点子路径前缀（Pages 部署在 /blog-xiuerhuahuazi/）；
  - 页内锚点与跨页锚点是否真的存在；
  - <title> / meta description / rel=canonical，且 canonical 必须对应当前页。
"""
import os
import re
from html.parser import HTMLParser
from urllib.parse import quote, unquote, urlsplit

from .config import BASE, DIST

SKIP_DIRS = {".git", "node_modules", "content", "tools", "assets", ".github"}
BASE_PATH = urlsplit(BASE).path.rstrip("/") + "/"
SKIP_SCHEMES = re.compile(r"^(data:|javascript:|mailto:|tel:|blob:)")


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
    """把引用解析成 dist 内的绝对路径；站外返回 None。"""
    parts = urlsplit(ref)
    if parts.scheme in ("http", "https"):
        if not ref.startswith(BASE + "/"):
            return None
        path = unquote(ref[len(BASE):])          # "/readers/"
        return os.path.normpath(os.path.join(DIST, path.lstrip("/")))
    if parts.scheme or ref.startswith("//"):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    if path.startswith("/"):
        # 站内绝对路径：Pages 部署在子路径下，本地按 BASE 剥掉前缀
        relpath = path[len(BASE_PATH):] if path.startswith(BASE_PATH) else path.lstrip("/")
        return os.path.normpath(os.path.join(DIST, relpath))
    return os.path.normpath(os.path.join(os.path.dirname(page), path))


def expected_canonical(rel_page):
    """当前页应有的 canonical：站点前缀 + 去掉 index.html 的页面路径。"""
    path = rel_page.replace(os.sep, "/").replace("index.html", "")
    return BASE + "/" + quote(path, safe="/")


def ids_of(path, cache):
    if path not in cache:
        p = Collector()
        with open(path, encoding="utf-8") as f:
            p.feed(f.read())
        cache[path] = p.ids
    return cache[path]


def main():
    if not DIST.is_dir():
        print("dist 不存在：先跑 python3 tools/build.py")
        return 1

    pages, problems, checked = [], [], 0
    for dirpath, dirnames, filenames in os.walk(DIST):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".html"):
                pages.append(os.path.join(dirpath, fn))

    id_cache = {}
    for page in pages:
        rel_page = os.path.relpath(page, DIST)
        p = Collector()
        with open(page, encoding="utf-8") as f:
            p.feed(f.read())
        if not p.title.strip():
            problems.append(f"{rel_page}: 缺少 <title>")
        if rel_page != "404.html":
            if not p.has_desc:
                problems.append(f"{rel_page}: 缺少 meta description")
            if not p.canonical:
                problems.append(f"{rel_page}: 缺少 rel=canonical")
            else:
                want = expected_canonical(rel_page)
                if p.canonical != want:
                    problems.append(f"{rel_page}: canonical 与当前页不符：{p.canonical}（应为 {want}）")

        for kind, ref in p.refs:
            if SKIP_SCHEMES.match(ref):
                continue
            if ref.startswith("#"):
                frag = unquote(ref[1:])
                checked += 1
                if frag and frag not in p.ids:
                    problems.append(f"{rel_page}: 页内锚点 #{frag} 不存在")
                continue
            if ref.startswith("/") and not ref.startswith("//") and not ref.startswith(BASE_PATH):
                checked += 1
                problems.append(f"{rel_page}: {kind} 站内绝对路径缺少站点前缀 {BASE_PATH}：{ref}")
                continue
            target = resolve(page, ref)
            if target is None:
                continue
            checked += 1
            if os.path.isdir(target):
                target = os.path.join(target, "index.html")
                if not os.path.isfile(target):
                    problems.append(f"{rel_page}: {kind} 指向目录但没有 index.html：{ref}")
                    continue
            if not os.path.isfile(target):
                problems.append(f"{rel_page}: {kind} 指向不存在的 {ref} → {os.path.relpath(target, DIST)}")
                continue
            frag = unquote(urlsplit(ref).fragment)
            if frag and target.lower().endswith(".html"):
                if frag not in ids_of(target, id_cache):
                    problems.append(
                        f"{rel_page}: {kind} 锚点 #{frag} 不在 {os.path.relpath(target, DIST)}")

    print(f"检查 {len(pages)} 个页面、{checked} 个引用")
    if problems:
        for x in problems:
            print("  ✗", x)
        print(f"FAIL：{len(problems)} 个问题")
        return 1
    print("OK：链接、资源、锚点与 canonical 都正常")
    return 0
