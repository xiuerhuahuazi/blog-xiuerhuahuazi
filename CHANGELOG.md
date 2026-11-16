# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added

- 检查器回归测试 `tests/test_sitecheck.py`（9 条正向/负向样例），CI 在 build/check 后执行 `python3 -m unittest discover -s tests -v`。
- 维护者文档 `docs/ARCHITECTURE.md`：目录职责、数据流、检查器覆盖、部署与项目级信息归属。
- 双语精读：新增三篇，共 13 篇、2,841 句对、313 张术语卡。
  - 第十一篇《The Art of Loop Engineering》（LangChain Blog，2026-06-16），69 句对 / 15 术语 / 8 图。
  - 第十二篇《构建常驻智能体：五个原语，让智能体自己醒来》（Anthropic，2026-11-13），135 句对 / 13 术语 / 7 图。
  - 第十三篇《循环与图：别再盯着每一步，只批最后一步》（Hanako，X Article，2026-08-23），129 句对 / 14 术语 / 4 图。
- 技术手记：新增三篇——《Harness Engineering 的终结：一场还没打完的仗》《100 个设计网站，我先挑了 27 个能马上用的》《12 个让 Claude 做动效的仓库：清单、实测 star 与选型》。
- 技术手记：新增《Modern Web Guidance 接进 DSH：三个不吭声的坑》，记录本地接入方式、遥测默认开启、catalog 500 字符截断与 YAML 静默失败，以及触发边界。
- 首页「本期精读」改为常驻智能体那一篇。

### Changed

- `tools/blog/pages.py` 与 `reader_shell.py` 剩余 HTML 抽到 `src/templates/partials/` 与 `src/templates/readers-shell/`；页面输出与重构前逐字节一致。
- 项目级细节从全局记忆迁到仓库 `docs/ARCHITECTURE.md` 与 `.agents/`（本机台账、原始审计）；全局记忆只保留项目指针与跨会话判断。
- 仓库结构调整：源文件迁入 `src/`（配置、内容、模板、静态资源、精读成品），构建产物统一输出到 `dist/` 且不再入库；生成器拆成 `tools/blog/` 包（`config` / `template` / `pages` / `markdown` / `sitecheck` / `reader_shell`），页面模板外置到 `src/templates/`。页面输出与重构前逐字节一致（15 个生成页）。
- 发布改为 GitHub Actions：`.github/workflows/pages.yml` 在推 `main` 时构建 `dist/` 并部署到 GitHub Pages，不再从仓库根直接发布。
- 精读导入的注入 CSS / JS / 顶栏抽到 `src/templates/readers-shell/`；分类、导读与 `featured` 抽到 `src/content/readers_curated.json`。
- 工具更名：`tools/check_site.py` → `tools/check.py`，`tools/md2post.py` → `tools/new_post.py`；`import_legacy.py` 移入 `tools/oneoff/`。
- `README.md` 按新结构重写；新增 `AGENTS.md` 记录目录约定、不变量与验收流程。
- 双语精读页接入站点外壳：顶栏（品牌 / 全站导航 / 主题切换）、深色主题（与全站共用 `site-theme`）、阅读工具条下移、跨页淡入；打印时强制浅色并隐藏顶栏。由 `tools/import_readers.py` 幂等注入，重导不会丢。
- 全站动效升级：首页 hero 分行入场、列表与分区滚动渐入、主题切换从按钮位置圆形揭示、跨页导航淡入淡出、导航与条目的 hover 微交互；全部遵循 `prefers-reduced-motion`，无 JS 时内容完整可见。

### Fixed

- `tools/check.py` 补齐 4 类语义检查：站内绝对路径必须带 `/blog-xiuerhuahuazi/` 前缀；目录链接必须有 `index.html`；跨页锚点必须存在于目标页；非 404 页的 canonical 必须等于当前页地址。
- `tools/import_readers.py` 导入前预检 `meta.json` 必需字段、`meta.cover.asset` 指向的媒体文件、`glossary.json` / `figures.json` 结构；缺 glossary / figures 会告警并按 0 计，不再静默。
- `sitemap.xml` 的 `lastmod` 固定按 `Asia/Shanghai` 的构建日生成（workflow 设置 `TZ`），避免 GitHub Actions 的 UTC 日期比本地早一天，导致同一提交的本地与线上产物不一致。
- 跨页导航：旧页退场与新页入场改为重叠的 crossfade；`pagereveal` 时首屏快照前置呈现，避免新页快照为空、过渡中间出现近空屏。
- 精读页 721–900px：顶栏的「← 双语书架」入口保留到 900px，901px 起才由 `.sm-nav` 接管。
- 深色主题打印：对比卡 `.cmp.win` 恢复浅底深字，打印稿可读。

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

- 首页统计里的「双语精读 10 篇」是硬编码，已改为按内容索引实时计数。

- 仓库里 `tags/NAS` 与 `tags/nas` 大小写冲突（在 macOS 上只能检出其中一个）；随 `tags/` 目录一并去掉。
- 浅色主题的次级文字（章节日期、英文标题、页脚）对比度从 3.66:1 提到 5.02:1；深色主题的列表标题悬停色改用深色强调色。
- 打印时强制切到浅色变量，避免从深色主题打印出深底黑字。
- 中文/括号目录的 canonical 与 sitemap 地址改为百分号编码。
- 精读页的术语卡与译注角标可以用键盘 Tab 聚焦并弹出（原来只能悬停）；英文一栏补 `lang="en"`。
- 索引页文章标题从 `h3` 改为 `h2`，不再跳级；`twitter:card` 不再输出 `summary, summary_large_image` 这种非法值。
- `md2post.py`：代码块与行内代码真正可用；图片 alt 属性转义、链接协议白名单；slug 禁止路径穿越。
- `import_readers.py`：源目录缺文件时直接报错退出，不再用半份数据覆盖索引；重复执行不会叠加注入。
- `check_site.py`：扩展为检查 `data-src` / `poster` / `srcset` / 站内绝对地址 / 页内锚点 / canonical。
