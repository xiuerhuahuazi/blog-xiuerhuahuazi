"""模板与页面共用的小工具：转义、相对路径、日期、导航。

这些函数的行为与旧 tools/build.py 完全一致；中文与括号路径一律做
百分号编码（safe="/"），保证 canonical 与 sitemap 合法。
"""
import html
from urllib.parse import quote

from .config import BASE, SITE


def esc(s):
    return html.escape(str(s), quote=True)


def txt(s):
    return html.escape(str(s), quote=False)


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


def nav_html(depth, active):
    out = []
    for item in SITE["nav"]:
        cls = ' class="on"' if item["href"] == active else ""
        out.append(f'<a href="{rel(depth)}{item["href"]}"{cls}>{item["label"]}</a>')
    return "".join(out)
