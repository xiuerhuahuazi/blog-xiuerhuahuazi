"""精读成品页的注入资源与函数。

注入资源从 src/templates/readers-shell/ 读取，按旧版
tools/import_readers.py 的拼接顺序原样使用；inject() 与 hero_numbers()
的行为保持不变，保证重跑导入的 HTML 与现有 src/readers/ 逐字节一致。
"""
import html
import re

from .config import BASE, SITE, TEMPLATES
from .template import Templates

SHELL = TEMPLATES / "readers-shell"
SHELL_T = Templates(SHELL)


def read(name):
    return (SHELL / name).read_text(encoding="utf-8")


NAV_MARK = "<!-- site-nav -->"
NAV_STYLE = read("nav.css")
NAV_LINK = NAV_MARK + read("nav.html")

A11Y_SCRIPT = read("a11y.js")

MAST_MARK = "<!-- site-mast -->"
MAST_BOOT = read("mast-boot.html")
MAST_STYLE = read("mast.css")
MAST_HTML = MAST_MARK + read("mast.html")
MAST_SCRIPT = read("mast.js")


def hero_numbers(page: str):
    def num(pattern):
        m = re.search(pattern, page, re.S)
        return int(m.group(1).replace(",", "")) if m else 0
    return {
        "words": num(r"原文 ([\d,]+) 词"),
        "chars": num(r"中文 ([\d,]+) 字"),
        "pairs": num(r"逐句对照 <i>(\d+)</i> 句"),
    }


def inject(page: str, slug: str, title: str, desc: str, cover: str) -> str:
    # 站点外壳：主题引导（必须先于首屏绘制）+ 顶栏样式 + 顶栏 + 主题/过渡脚本
    if 'id="site-mast-style"' not in page:
        page = page.replace("</head>", MAST_BOOT + "\n" + MAST_STYLE + "\n</head>", 1)
    if MAST_MARK not in page:
        page, hits = re.subn(r'(<body[^>]*>\s*)',
                             lambda m: m.group(1) + MAST_HTML + "\n", page, count=1)
        if hits != 1:
            raise SystemExit(f"{slug}: 找不到 <body>，无法注入站点顶栏")
    if 'id="site-mast-script"' not in page:
        page = page.replace("</body>", MAST_SCRIPT + "\n</body>", 1)

    if 'id="site-nav-style"' not in page:
        page = page.replace("</head>", NAV_STYLE + "\n</head>", 1)
    if NAV_MARK not in page:
        page, hits = re.subn(r'(<div class="topbar-in"[^>]*>\s*)',
                             lambda m: m.group(1) + NAV_LINK + "\n    ", page, count=1)
        if hits != 1:
            raise SystemExit(f"{slug}: 找不到 topbar-in，无法注入返回导航（源页结构变了？）")
    # canonical：子路径部署下防止重复收录
    if 'rel="canonical"' not in page:
        canonical = SHELL_T.render("canonical.html", {"url": f"{BASE}/readers/{slug}/"})
        page = page.replace("</head>", canonical + "\n</head>", 1)
    # 分享卡片：X / 微信 / 搜索
    if 'property="og:title"' not in page:
        img = (SHELL_T.render("og-image.html", {
            "url": f"{BASE}/readers/{slug}/media/{cover}",
        }) if cover else "")
        card = "summary_large_image" if cover else "summary"
        og = SHELL_T.render("og.html", {
            "site_name": html.escape(SITE["name"]),
            "title": html.escape(title),
            "desc": html.escape(desc),
            "url": f"{BASE}/readers/{slug}/",
            "image": img,
            "card": card,
        })
        page = page.replace("</head>", og + "</head>", 1)
    # 英文一栏标语言，读屏不会用中文音读英文
    page = page.replace('class="cell en"', 'class="cell en" lang="en"')
    page = page.replace('class="h1-en"', 'class="h1-en" lang="en"')
    # 术语卡与译注角标支持键盘聚焦
    if 'id="site-a11y"' not in page:
        page = page.replace("</body>", A11Y_SCRIPT + "\n</body>", 1)
    return page
