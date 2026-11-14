#!/usr/bin/env python3
"""从双语精读项目导入成品页：readers/<slug>/ + content/readers.json。

用法（仓库根目录）：
  python3 tools/import_readers.py --src ~/Documents/project/bilingual-readers
  python3 tools/import_readers.py --src ... --force     # 覆盖已有 readers/

导入的是各项目的 cloud/ 版（HTML + 外置 media/，视频与图片按需加载），
并注入「返回双语书架」导航与分享用的 og 标签。cloud/index.html 由精读技能生成，
这里只做增量注入，不重排它自己的样式。
"""
import argparse
import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PAGES = os.path.join(ROOT, "readers")
OUT_JSON = os.path.join(ROOT, "content", "readers.json")
SITE = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))
BASE = SITE["url"].rstrip("/")

# 人工策展：分类 + 一句话导读（meta.subtitle_zh 有的偏元信息，这里统一重写）
CURATED = {
    "agent-manager": ("智能体协作",
        "写代码的智能体一多，你就成了项目经理。文章把这件事拆成 12 个可执行的习惯，也点明智能体和初级工程师的 6 处不同。"),
    "anthropic-scm": ("工程基建",
        "合并量五个月涨十倍，git 撑不住了：7 个人、5 个月自研版本控制系统 Scion，把内部 monorepo 全量迁了过去。"),
    "claude-code-review": ("工程实践",
        "当 Claude 写掉约 90% 的代码，review 不再是路尽头的闸门，而是写代码时的拼写检查。"),
    "claude-sdlc-sec": ("安全",
        "AI 写代码之后，安全边界该放在哪：从会话、权限与审批，到部署后的监控与回滚。"),
    "claude-subagent-loop": ("智能体架构",
        "什么时候该把子智能体折叠回主循环？答案取决于上下文隔离、工具数量与成本，而不是「多一层更专业」。"),
    "fable-multi-agent": ("智能体架构",
        "1,000 个智能体、28.7 小时、一个费马大定理的形式化证明：一篇关于「扩到多大才安全」的实验报告。"),
    "harness-reader": ("智能体架构",
        "把主观设计变成可评分项，让生成与评估两个智能体互相制衡：长程自主编程的流水线长什么样。"),
    "robotics-engineer-6mo": ("学习路线",
        "六个月、每月一个能动的实物、三档预算、100 多个资源：一份零基础可执行的机器人路线。"),
    "super-agent-design": ("智能体架构",
        "路由层 + 工作层、事件驱动、算存分离、外部看门狗：为什么「一个会话 + 一个人盯着」撑不起整个团队。"),
    "wiki-layer": ("上下文工程",
        "把「每次上传文件」换成「先编译成 Wiki，再提问」：把 Karpathy 的 LLM Wiki 讲成四步流程。"),
}

FEATURED = "super-agent-design"

NAV_MARK = "<!-- site-nav -->"
NAV_STYLE = """<style id="site-nav-style">
.topbar-in{justify-content:flex-start!important}
.topbar-in>.brand{margin-right:18px}
.topbar-in>.ctrls{margin-left:auto}
.blogback{color:var(--accent)!important;letter-spacing:.02em}
.blogback:hover{text-decoration:underline;text-underline-offset:3px}
.topbar-in{flex-wrap:nowrap}
.bb-short{display:none}
@media (max-width:720px){
  .topbar-in>.brand:not(.blogback){display:none}
  .topbar-in>.blogback{display:inline-flex!important;margin-right:10px}
  .bb-full{display:none}
  .bb-short{display:inline}
}
@media print{.blogback{display:none!important}}
</style>"""
NAV_LINK = (NAV_MARK + '<a class="brand blogback" href="../" title="返回双语书架" aria-label="返回双语书架">'
            '<span aria-hidden="true">←</span>'
            '<span class="bb-full">双语书架</span><span class="bb-short">书架</span></a>')

# 术语卡 / 译注角标原来只能悬停：让键盘也能聚焦并弹出同一张卡
A11Y_SCRIPT = """<script id="site-a11y">
(function () {
  if (!window.PointerEvent) return;
  var els = document.querySelectorAll("[data-term],[data-note],[data-typo]");
  Array.prototype.forEach.call(els, function (el) {
    el.setAttribute("tabindex", "0");
    el.setAttribute("role", "button");
    if (!el.getAttribute("aria-label")) {
      el.setAttribute("aria-label", "查看注释：立即阅读");
    }
    el.addEventListener("focus", function () {
      el.dispatchEvent(new PointerEvent("pointerover", { bubbles: true }));
    });
    el.addEventListener("blur", function () {
      el.dispatchEvent(new PointerEvent("pointerout", { bubbles: true }));
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Escape") el.blur();
    });
  });
})();
</script>"""


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
    if 'id="site-nav-style"' not in page:
        page = page.replace("</head>", NAV_STYLE + "\n</head>", 1)
    if NAV_MARK not in page:
        page, hits = re.subn(r'(<div class="topbar-in"[^>]*>\s*)',
                             lambda m: m.group(1) + NAV_LINK + "\n    ", page, count=1)
        if hits != 1:
            raise SystemExit(f"{slug}: 找不到 topbar-in，无法注入返回导航（源页结构变了？）")
    # canonical：子路径部署下防止重复收录
    if 'rel="canonical"' not in page:
        page = page.replace("</head>", f'<link rel="canonical" href="{BASE}/readers/{slug}/">\n</head>', 1)
    # 分享卡片：X / 微信 / 搜索
    if 'property="og:title"' not in page:
        img = f'\n<meta property="og:image" content="{BASE}/readers/{slug}/media/{cover}">' if cover else ""
        card = "summary_large_image" if cover else "summary"
        og = (f'<meta property="og:type" content="article">\n'
              f'<meta property="og:site_name" content="{html.escape(SITE["name"])}">\n'
              f'<meta property="og:title" content="{html.escape(title)}">\n'
              f'<meta property="og:description" content="{html.escape(desc)}">\n'
              f'<meta property="og:url" content="{BASE}/readers/{slug}/">'
              f'{img}\n<meta name="twitter:card" content="{card}">\n')
        page = page.replace("</head>", og + "</head>", 1)
    # 英文一栏标语言，读屏不会用中文音读英文
    page = page.replace('class="cell en"', 'class="cell en" lang="en"')
    page = page.replace('class="h1-en"', 'class="h1-en" lang="en"')
    # 术语卡与译注角标支持键盘聚焦
    if 'id="site-a11y"' not in page:
        page = page.replace("</body>", A11Y_SCRIPT + "\n</body>", 1)
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser("~/Documents/project/bilingual-readers"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    src = os.path.abspath(os.path.expanduser(args.src))

    if os.path.exists(OUT_JSON) and not args.force:
        print("content/readers.json 已存在，未覆盖（需要时加 --force）")
        return

    # 先把所有输入检查一遍：缺任何一个都不写，避免用半份数据覆盖已有索引
    missing = []
    for slug in CURATED:
        if not os.path.isfile(os.path.join(src, slug, "data", "meta.json")):
            missing.append(f"{slug}/data/meta.json")
        if not os.path.isfile(os.path.join(src, slug, "cloud", "index.html")):
            missing.append(f"{slug}/cloud/index.html")
    if missing:
        raise SystemExit("源目录缺少文件，未做任何改动：\n  " + "\n  ".join(missing))

    os.makedirs(OUT_PAGES, exist_ok=True)
    readers = []
    keep = set()
    for slug in CURATED:
        meta = json.load(open(os.path.join(src, slug, "data", "meta.json"), encoding="utf-8"))
        cloud = os.path.join(src, slug, "cloud")
        page = open(os.path.join(cloud, "index.html"), encoding="utf-8").read()
        nums = hero_numbers(page)
        cover = (meta.get("cover") or {}).get("asset") or ""
        cat, blurb = CURATED[slug]
        desc = meta.get("subtitle_zh") or blurb

        page = inject(page, slug, meta["title_zh"], desc, cover)

        dest = os.path.join(OUT_PAGES, slug)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        with open(os.path.join(dest, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        if os.path.isdir(os.path.join(cloud, "media")):
            shutil.copytree(os.path.join(cloud, "media"), os.path.join(dest, "media"))

        glossary = os.path.join(src, slug, "data", "glossary.json")
        terms = len(json.load(open(glossary, encoding="utf-8"))["terms"]) if os.path.exists(glossary) else 0
        figures = os.path.join(src, slug, "data", "figures.json")
        figs = len(json.load(open(figures, encoding="utf-8"))["figures"]) if os.path.exists(figures) else 0

        keep.add(slug)
        readers.append({
            "slug": slug,
            "title_zh": meta["title_zh"],
            "title_en": meta["title_en"],
            "source_url": meta["source_url"],
            "org": meta["org_en"],
            "published": meta["published"],
            "read_min": meta["read_min"],
            "category": cat,
            "blurb": blurb,
            "pairs": nums["pairs"],
            "words": nums["words"],
            "chars": nums["chars"],
            "terms": terms,
            "figures": figs,
            "cover": f"media/{cover}" if cover else "",
            "featured": slug == FEATURED,
        })
        print(f"导入 {slug}: {nums['pairs']} 句对, {terms} 术语, {figs} 图")

    # 删掉已经不在 CURATED 里的旧成品目录，避免陈旧页面留在站点里
    for name in os.listdir(OUT_PAGES):
        if name not in keep and os.path.isdir(os.path.join(OUT_PAGES, name)):
            shutil.rmtree(os.path.join(OUT_PAGES, name))
            print("移除过期目录", name)

    readers.sort(key=lambda r: r["published"], reverse=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"readers": readers}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("共", len(readers), "篇；索引写入 content/readers.json")


if __name__ == "__main__":
    main()
