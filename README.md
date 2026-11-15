# blog-xiuerhuahuazi

个人站点：**双语精读** + **技术手记**。纯静态页面，Python 生成，零外部请求（没有 CDN、没有统计脚本），直接托管在 GitHub Pages。

线上地址：<https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/>

## 目录

```
src/
  site.json                 站点配置：站名、导航、关于页文案、站点 URL
  content/
    posts/*.json            技术手记正文（唯一数据源）
    readers.json            精读索引（由 import_readers.py 生成）
    readers_curated.json    精读策展：分类、一句话导读、本期推荐
  readers/<slug>/           精读成品页（导入物，构建时原样复制）
  static/                   构建时原样复制到 dist/
    assets/site.css|js      全站样式与交互
    img/                    站点图片
    .nojekyll               GitHub Pages 不跑 Jekyll
  templates/
    base.html               全站外壳（head / 顶栏 / 页脚）
    home.html               首页
    readers.html            双语书架
    notes.html              技术手记列表
    post.html               手记正文
    about.html              关于
    404.html                404
    partials/               列表行（精读 / 手记）
    readers-shell/          注入精读成品页的顶栏、主题、CSS 与脚本
tools/
  build.py                  生成 dist/（清空后全量重建）
  check.py                  链接 / 资源 / 锚点 / canonical 自检
  new_post.py               Markdown → 技术手记
  import_readers.py         从双语精读项目导入成品
  oneoff/import_legacy.py   一次性抽取老文章（历史脚本）
  blog/                     生成器内核：config / template / pages / markdown ...
dist/                       构建产物，已 gitignore，不要手改、不要提交
.github/workflows/pages.yml GitHub Pages 构建与部署
```

**源文件与产物是分开的**：`src/` 是唯一的手改区域，`dist/` 每次构建都会清空重建。

## 本地预览

```bash
python3 tools/build.py
python3 -m http.server -d dist 8000
# 打开 http://127.0.0.1:8000/
```

所有站内链接都是相对路径，直接在仓库根起静态服务即可。

## 生成与自检

```bash
python3 tools/build.py          # 生成全站到 dist/
python3 tools/build.py --check  # 只打印每个页面的字节数，不写文件
python3 tools/check.py          # 检查 dist/ 的内部链接、资源、锚点与 canonical
```

`build.py` 会先清空 `dist/`，再复制 `src/static/` 与 `src/readers/`，最后写页面；它不改写 `src/readers/`。

## 新增一篇技术手记

```bash
python3 tools/new_post.py ~/Desktop/note.md
```

Markdown 开头可选 front matter：

```markdown
---
title: SSH 连接 Docker 容器太麻烦？
date: 2026-11-20
tags: docker, ssh
desc: 一句话摘要，会显示在列表和搜索摘要里
slug: ssh-docker-alias
---

# SSH 连接 Docker 容器太麻烦？

正文……
```

支持的 Markdown 子集：标题、段落、有序/无序列表、引用、代码块、分隔线、图片、链接、粗体/斜体/行内代码。**表格不支持**——真要表格就手工改 `src/content/posts/<slug>.json` 里的 HTML 片段。

脚本写完 `src/content/posts/<slug>.json` 后会自动跑 `build.py` 与 `check.py`。页面落在 `dist/<年>/<月>/<日>/<slug>/`，URL 形态与老文章一致。

图片放 `src/static/img/`，正文里写 `{{ROOT}}img/xxx.png`（构建时会把 `{{ROOT}}` 换成当前页面到站点根的相对前缀）。**不要写 `/img/xxx.png`**：站点部署在 `/blog-xiuerhuahuazi/` 子路径下，域名根绝对路径会 404。

## 更新双语精读

精读页由 `bilingual-annotated-reader` 技能在 `~/Documents/project/bilingual-readers/<slug>/` 里生成。发布到本站：

```bash
python3 tools/import_readers.py --src ~/Documents/project/bilingual-readers --force
python3 tools/build.py
```

它会：

1. 复制每个项目的 `cloud/`（HTML + 外置 `media/`，视频按需加载）到 `src/readers/<slug>/`；
2. 注入站点外壳（品牌 / 全站导航 / 主题顶栏、深色主题、跨页过渡）与分享用的 `og:` 标签；
3. 从 `data/meta.json`、`glossary.json`、`figures.json` 与页头统计里生成 `src/content/readers.json`。

分类、一句话导读与「本期精读」是人工策展的，位置在 `src/content/readers_curated.json`（`featured` 指定首页大图卡）。注入用的 CSS / JS / 顶栏在 `src/templates/readers-shell/`。

## 设计约定

- 全站（含精读页）同一套语言：暖纸底色、衬线标题、赭红强调；深浅两套主题，手动切换并持久化，不跟随系统。
- 只用系统字体（Iowan Old Style / Palatino + 宋体 / 苹方），不加载任何外部字体与图标。
- 页面不依赖 JS 也能读；JS 只负责主题切换、阅读进度条和目录高亮。
- 页面模板只放静态 HTML 与 `{{槽位}}`；条件、循环、转义都在 `tools/blog/` 里，模板缺槽位会直接报错。

## 部署

推 `main` 即发布：`.github/workflows/pages.yml` 会跑 `tools/build.py` 与 `tools/check.py`，把 `dist/` 作为 Pages 产物上传并部署。

仓库的 Pages 发布源需要是 **GitHub Actions**（Settings → Pages → Build and deployment → Source）。`dist/` 不入库。

## 变更记录

见 [CHANGELOG.md](CHANGELOG.md)。
