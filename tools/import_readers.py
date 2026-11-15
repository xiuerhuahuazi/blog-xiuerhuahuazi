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
    "always-on-agents": ("智能体架构",
        "常驻智能体不是更聪明的循环，而是五件基础设施围着同一个循环：事件收件箱、定时器、记忆、权限、发件箱。"),
    "loops-graphs": ("智能体架构",
        "循环让一个工作单元自己检查到通过，图决定有哪些单元、谁等谁；两条回传路径，加上按影响半径开的闸门。"),
    "loop-engineering": ("智能体架构",
        "四层循环：干活的智能体循环、打分的验证循环、被事件触发的事件循环、用 trace 自我改进的爬坡循环。前三层自动化工作，第四层自动化改进。"),
    "robotics-engineer-6mo": ("学习路线",
        "六个月、每月一个能动的实物、三档预算、100 多个资源：一份零基础可执行的机器人路线。"),
    "super-agent-design": ("智能体架构",
        "路由层 + 工作层、事件驱动、算存分离、外部看门狗：为什么「一个会话 + 一个人盯着」撑不起整个团队。"),
    "wiki-layer": ("上下文工程",
        "把「每次上传文件」换成「先编译成 Wiki，再提问」：把 Karpathy 的 LLM Wiki 讲成四步流程。"),
}

FEATURED = "always-on-agents"

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


MAST_MARK = "<!-- site-mast -->"

MAST_BOOT = """<script id="site-theme-boot">(function(){try{if(localStorage.getItem('site-theme')==='dark'){document.documentElement.setAttribute('data-theme','dark')}}catch(e){}})();</script>"""

# 阅读页的站点外壳：顶栏、深色主题、跨页过渡。全部用阅读页自己的变量，不引外部文件。
MAST_STYLE = """<style id="site-mast-style">
/* ---------- 站点顶栏（阅读页） ---------- */
:root{--mast:52px}
html{scroll-padding-top:calc(var(--mast) + var(--bar) + 12px)}
.site-mast{
  position:sticky;top:0;z-index:85;height:var(--mast);
  background:rgba(251,248,243,.92);border-bottom:1px solid var(--rule);
  -webkit-backdrop-filter:blur(14px) saturate(1.1);backdrop-filter:blur(14px) saturate(1.1);
}
[data-theme="dark"] .site-mast{background:rgba(21,19,15,.92)}
.site-mast-in{max-width:var(--reader);margin:0 auto;height:100%;padding:0 28px;
  display:flex;align-items:center;gap:clamp(16px,3vw,34px)}
.sm-brand{display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);flex:none}
.sm-mark{display:inline-grid;place-items:center;width:24px;height:24px;border:1px solid var(--accent);
  border-radius:7px;color:var(--accent);font:italic 400 15px/1 var(--serif);flex:none}
.sm-word{font-size:12.5px;font-weight:600;letter-spacing:.14em;text-transform:lowercase}
.sm-nav{display:flex;align-items:center;gap:clamp(16px,2.4vw,28px);font-size:14.5px}
.sm-nav a{position:relative;color:var(--ink-2);text-decoration:none;padding:4px 0;transition:color .2s}
.sm-nav a::after{content:"";position:absolute;left:0;right:0;bottom:0;height:2px;background:var(--accent);
  transform:scaleX(0);transform-origin:left;transition:transform .28s cubic-bezier(.22,.61,.36,1)}
.sm-nav a:hover{color:var(--ink)}
.sm-nav a:hover::after,.sm-nav a.on::after{transform:scaleX(1)}
.sm-nav a.on{color:var(--ink)}
.sm-theme{margin-left:auto;display:inline-grid;place-items:center;width:32px;height:32px;
  border:1px solid var(--rule-2);border-radius:50%;background:transparent;color:var(--ink-2);
  cursor:pointer;transition:color .2s,border-color .2s,transform .3s}
.sm-theme:hover{color:var(--accent);border-color:var(--accent);transform:rotate(12deg)}
.sm-theme svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round}
.sm-theme .i-moon{display:none}
[data-theme="dark"] .sm-theme .i-moon{display:block}
[data-theme="dark"] .sm-theme .i-sun{display:none}
/* 阅读页自己的工具条挪到站点顶栏之下 */
.topbar{top:var(--mast)}
.topbar-in>.blogback{flex:none}
.colheads{top:calc(var(--mast) + var(--bar))}
@media (min-width:901px){.topbar-in>.brand.blogback{display:none!important}}
@media (max-width:900px){.sm-nav{display:none}}
@media (max-width:640px){:root{--mast:48px}}
@media (max-width:359px){.sm-word{display:none}}

/* ---------- 跨页过渡（Chrome 126+ 生效，其余浏览器照常跳转） ---------- */
@view-transition{navigation:auto}
::view-transition-old(root),::view-transition-new(root){animation:none;mix-blend-mode:normal}
@keyframes sm-vt-out{to{opacity:0}}
@keyframes sm-vt-in{from{opacity:0}}
@keyframes sm-vt-theme{
  from{clip-path:circle(0 at var(--vt-x,50%) var(--vt-y,50%))}
  to{clip-path:circle(var(--vt-r,120vmax) at var(--vt-x,50%) var(--vt-y,50%))}
}
@media (prefers-reduced-motion:no-preference){
  /* 旧页退场与新页入场重叠，避免中间出现近空屏 */
  ::view-transition-group(root){background:var(--paper)}
  ::view-transition-old(root){animation:sm-vt-out .18s ease both}
  ::view-transition-new(root){animation:sm-vt-in .24s ease both}
  html.theme-vt::view-transition-old(root){animation:none}
  html.theme-vt::view-transition-new(root){animation:sm-vt-theme .5s cubic-bezier(.22,.61,.36,1) both}
}
@media (prefers-reduced-motion:reduce){
  ::view-transition-old(root),::view-transition-new(root){animation:none!important}
}

/* ---------- 深色主题：先换变量，再补少量写死的浅色 ---------- */
[data-theme="dark"]{
  --paper:#15130f;--paper-2:#1c1a15;--card:#1a1813;
  --ink:#efe9dd;--ink-2:#b4ab9c;--ink-3:#8b8274;
  --rule:#2c2822;--rule-2:#3a352c;
  --accent:#e0906a;--accent-2:#f0a780;--accent-soft:#2a211a;
  --hl:rgba(224,144,106,.16);--term:#c9b07a;
  color-scheme:dark;
}
[data-theme="dark"] ::selection{background:rgba(224,144,106,.24)}
[data-theme="dark"] #progress{background:linear-gradient(90deg,var(--accent),#c98a5e)}
[data-theme="dark"] .topbar{background:rgba(21,19,15,.9)}
[data-theme="dark"] .seg button:hover{background:rgba(255,255,255,.06)}
[data-theme="dark"] .seg button.on{background:var(--ink);color:#15130f}
[data-theme="dark"] .cmp.win{background:#241d16;border-color:#43301f}
[data-theme="dark"] .gist p{color:var(--ink-2)}
[data-theme="dark"] .cell.en,[data-theme="dark"] .cell.zh{color:var(--ink)}
[data-theme="dark"] figcaption{border-left-color:#43301f}
[data-theme="dark"] sup.tn{border-color:#43301f}
[data-theme="dark"] .chip.must{background:#3a2a20;color:#f0a780;border-color:#43301f}
[data-theme="dark"] .chip.bg{background:#232a1c;color:#b7c98f;border-color:#37402c}
[data-theme="dark"] .lnk-card:hover{border-color:#43301f}
[data-theme="dark"] .fig-bar button{background:rgba(21,19,15,.9);color:var(--ink);border-color:#43301f}
[data-theme="dark"] .fig-bar button.on{background:var(--ink);color:#15130f;border-color:var(--ink)}
[data-theme="dark"] .toc-panel{border-left-color:var(--rule);box-shadow:-20px 0 50px rgba(0,0,0,.5)}
[data-theme="dark"] .toc-panel a{border-bottom-color:rgba(255,255,255,.08)}
[data-theme="dark"] .toc-bg{background:rgba(0,0,0,.5)}
[data-theme="dark"] .card{box-shadow:0 18px 44px -12px rgba(0,0,0,.6),0 3px 10px rgba(0,0,0,.4)}
[data-theme="dark"] table.bt tbody tr:hover td{background:#221f19}
[data-theme="dark"] .typo{border-bottom-color:#e57373}
[data-theme="dark"] .typo:hover{background:rgba(229,115,115,.12)}
[data-theme="dark"] a.lnk{border-bottom-color:rgba(224,144,106,.5)}
[data-theme="dark"] .s.pin{background:rgba(224,144,106,.16);box-shadow:inset 2px 0 0 rgba(224,144,106,.6)}
[data-theme="dark"] .term:hover{background:rgba(201,176,122,.14)}
[data-theme="dark"] .cap-video a{border-bottom-color:#43301f}
@media print{
  .site-mast{display:none!important}
  [data-theme="dark"]{
    --paper:#fff;--paper-2:#f5f5f5;--card:#fff;
    --ink:#000;--ink-2:#333;--ink-3:#555;
    --rule:#ddd;--rule-2:#ccc;
    --accent:#8f3f1f;--accent-2:#7a3518;--accent-soft:#f2f2f2;
    --hl:transparent;--term:#6b5a2e;
    color-scheme:light;
  }
  [data-theme="dark"] .chip.must{background:#fbe4d6;color:#8f3f1f;border-color:#eccdb8}
  [data-theme="dark"] .chip.bg{background:#eaf0e2;color:#4b5c2f;border-color:#d8e0c8}
  [data-theme="dark"] .cmp.win{background:var(--paper);border-color:var(--rule)}
}
</style>"""

MAST_HTML = MAST_MARK + """
<header class="site-mast">
  <div class="site-mast-in">
    <a class="sm-brand" href="../../" aria-label="回到首页">
      <span class="sm-mark" aria-hidden="true">x</span>
      <span class="sm-word">xiuerhuahuazi</span>
    </a>
    <nav class="sm-nav" aria-label="主导航">
      <a href="../../readers/" class="on">双语书架</a>
      <a href="../../notes/">技术手记</a>
      <a href="../../about/">关于</a>
    </nav>
    <button class="sm-theme" type="button" data-theme-toggle aria-label="切换深色模式" aria-pressed="false">
      <svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>
      <svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.3A8.6 8.6 0 1 1 9.7 3.5a7 7 0 0 0 10.8 10.8z"/></svg>
    </button>
  </div>
</header>
"""

MAST_SCRIPT = """<script id="site-mast-script">
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'site-theme';
  var btn = document.querySelector('[data-theme-toggle]');
  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function isDark() { return root.getAttribute('data-theme') === 'dark'; }
  function sync() {
    if (!btn) return;
    btn.setAttribute('aria-pressed', isDark() ? 'true' : 'false');
    btn.setAttribute('aria-label', isDark() ? '切换到浅色模式' : '切换到深色模式');
  }
  function commit(dark) {
    try { localStorage.setItem(KEY, dark ? 'dark' : 'light'); } catch (e) {}
    sync();
  }
  if (!btn) return;
  sync();
  btn.addEventListener('click', function () {
    var dark = !isDark();
    function set() {
      if (dark) { root.setAttribute('data-theme', 'dark'); } else { root.removeAttribute('data-theme'); }
    }
    if (typeof document.startViewTransition !== 'function' || (reduce && reduce.matches)) {
      set(); commit(dark); return;
    }
    var r = btn.getBoundingClientRect();
    var x = r.left + r.width / 2;
    var y = r.top + r.height / 2;
    var rad = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    root.style.setProperty('--vt-x', x + 'px');
    root.style.setProperty('--vt-y', y + 'px');
    root.style.setProperty('--vt-r', rad + 'px');
    root.classList.add('theme-vt');
    var vt = document.startViewTransition(function () { set(); commit(dark); });
    function done() { root.classList.remove('theme-vt'); }
    vt.finished.then(done, done);
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
