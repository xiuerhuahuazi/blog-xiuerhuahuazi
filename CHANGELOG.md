# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added

- 双语精读：新增第十一篇《The Art of Loop Engineering》（LangChain Blog，2026-06-16），
  69 句对 / 15 张术语卡 / 8 张图；书架与首页统计更新为 11 篇、2,577 句对、286 张术语卡。

## [1.0.0] - 2026-11-15

整站重做：把 Butterfly 主题的静态产物换成一套自带生成器的极简站点，并把 10 篇双语精读放上来。

### Added

- 双语精读（`/readers/`）：10 篇，2,508 组逐句对照，271 张术语卡；每篇是独立成品页（HTML + 外置 `media/`，视频点击才加载），顶部注入「← 双语书架」导航与 `og:` 分享标签。
- 首页：书脊式排版、逐句对照示例卡、本期精读大图卡、精读 / 手记列表、关于条。
- 技术手记列表页（`/notes/`）与正文模板：目录跟随高亮、阅读进度条、上一篇 / 下一篇。
- 关于页（`/about/`）与自定义 404、`sitemap.xml`、`robots.txt`。
- 深色主题（手动切换，localStorage 记忆）、键盘可用的跳转链接与焦点样式、打印样式。
- 生成器与工具：`tools/build.py`（content → 页面）、`tools/check_site.py`（内部链接与资源自检）、`tools/md2post.py`（Markdown → 手记）、`tools/import_legacy.py`（一次性抽取老文章）、`tools/import_readers.py`（导入精读）。
- `README.md`：目录结构、预览、新增手记、更新精读的完整流程。

### Changed

- 老文章 URL 保持原样（`/2026/02/11/<标题>/` 等），正文换成新模板重排，不制造死链。
- 站点视觉与精读页对齐：暖纸底、衬线标题、赭红强调，同一套 `--paper/--ink/--accent` 变量。
- 去掉所有外部依赖（FontAwesome CDN、busuanzi 统计），页面不再发任何第三方请求。
- 图片改用相对路径；老文章里的 `/blog-xiuerhuahuazi/img/…` 绝对路径改成按层级计算的相对路径。
- 关于页从模板占位文案（your-github / your-email）改成真实内容。

### Removed

- Butterfly 主题产物：`css/`、`js/`、`tags/`、`categories/`、`archives/`、`test-style/`、`baidusitemap.xml`。
- 旧 `tools/md2post.py`（生成 Butterfly 页面）由新版 `tools/md2post.py`（Markdown → content/posts + 重新生成）取代。
- 未被引用的图片：`header-bg.jpg`（7.8 MB）、`butterfly-icon.png`、`friend_404.gif`、`error-page.png`、`cover.jpg`、`404.jpg`。

### Fixed

- 仓库里 `tags/NAS` 与 `tags/nas` 大小写冲突（在 macOS 上只能检出其中一个）；随 `tags/` 目录一并去掉。
- 浅色主题的次级文字（章节日期、英文标题、页脚）对比度从 3.66:1 提到 5.02:1；深色主题的列表标题悬停色改用深色强调色。
- 打印时强制切到浅色变量，避免从深色主题打印出深底黑字。
- 中文/括号目录的 canonical 与 sitemap 地址改为百分号编码。
- 精读页的术语卡与译注角标可以用键盘 Tab 聚焦并弹出（原来只能悬停）；英文一栏补 `lang="en"`。
- 索引页文章标题从 `h3` 改为 `h2`，不再跳级；`twitter:card` 不再输出 `summary, summary_large_image` 这种非法值。
- `md2post.py`：代码块与行内代码真正可用；图片 alt 属性转义、链接协议白名单；slug 禁止路径穿越。
- `import_readers.py`：源目录缺文件时直接报错退出，不再用半份数据覆盖索引；重复执行不会叠加注入。
- `check_site.py`：扩展为检查 `data-src` / `poster` / `srcset` / 站内绝对地址 / 页内锚点 / canonical。
