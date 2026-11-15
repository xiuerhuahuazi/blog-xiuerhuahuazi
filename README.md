# blog-xiuerhuahuazi

个人站点：**双语精读** + **技术手记**。纯静态页面，Python 生成，零外部请求（没有 CDN、没有统计脚本），可直接托管在 GitHub Pages。

线上地址：<https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/>

## 目录

```
index.html              首页
readers/                双语书架（列表）
readers/<slug>/         11 篇精读成品页 + media/
notes/                  技术手记列表
<年>/<月>/<日>/<slug>/   技术手记正文（沿用老 URL，不制造死链）
about/                  关于
404.html                GitHub Pages 的自定义 404
assets/site.css|site.js 样式与交互（源文件，原样发布）
img/                    站点图片
content/site.json       站名、导航、关于页文案
content/readers.json    精读索引（导入生成）
content/posts/*.json    技术手记正文（导入或 md2post 生成）
tools/                  build / import / check / md2post
```

## 本地预览

```bash
cd blog-xiuerhuahuazi
python3 -m http.server 8000
# 打开 http://127.0.0.1:8000/
```

所有站内链接都是相对路径，直接在仓库根起静态服务即可。

## 生成与自检

```bash
python3 tools/build.py        # 生成全站页面
python3 tools/check_site.py   # 内部链接 / 资源 / title / description 自检
```

`build.py` 只写页面，不改 `readers/`（那是精读成品，导入后原样发布）。

## 新增一篇技术手记

```bash
python3 tools/md2post.py ~/Desktop/note.md
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

支持的 Markdown 子集：标题、段落、有序/无序列表、引用、代码块、分隔线、图片、链接、粗体/斜体/行内代码。**表格不支持**——真要表格就手工改 `content/posts/<slug>.json` 里的 HTML 片段。

脚本会写完 `content/posts/<slug>.json` 后自动跑 `build.py` 与 `check_site.py`。图片路径建议写站内绝对路径（`/img/xxx.png`），从文章页往上层找相对路径容易写错。

## 更新双语精读

精读页由 `bilingual-annotated-reader` 技能在 `~/Documents/project/bilingual-readers/<slug>/` 里生成。发布到本站：

```bash
python3 tools/import_readers.py --src ~/Documents/project/bilingual-readers --force
python3 tools/build.py
```

它会：

1. 复制每个项目的 `cloud/`（HTML + 外置 media/，视频按需加载）到 `readers/<slug>/`；
2. 注入站点外壳（品牌 / 全站导航 / 主题顶栏、深色主题、跨页过渡）与分享用的 `og:` 标签；窄屏保留「← 书架」返回链接；
3. 从 `data/meta.json`、`glossary.json`、`figures.json` 与页头统计里生成 `content/readers.json`。

分类与一句话导读是人工写的，位置在 `tools/import_readers.py` 顶部的 `CURATED`；首页「本期精读」由 `FEATURED` 指定。

## 设计约定

- 全站（含精读页）同一套语言：暖纸底色、衬线标题、赭红强调；深浅两套主题，手动切换并持久化，不跟随系统。
- 只用系统字体（Iowan Old Style / Palatino + 宋体 / 苹方），不加载任何外部字体与图标。
- 页面不依赖 JS 也能读；JS 只负责主题切换、阅读进度条和目录高亮。

## 部署

推 `main` 即可：GitHub Pages（legacy 构建）从仓库根发布，无需 CI。

## 变更记录

见 [CHANGELOG.md](CHANGELOG.md)。
