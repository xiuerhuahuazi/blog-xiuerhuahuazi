# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added

- 提示词弹框补三处交互：点图片进入普通看图器（看图器层级高于弹框，关闭后回到弹框并同步当前序号）；看图器内支持 ←/→ 切换（从页面或无提示词图进入时同样生效）；图片区域滚轮（380ms 节流）与同款圆形箭头切换图片 + 提示词；箭头只在指针进入图片左右各 16% 时以 75% 透明度出现，位置贴合图片边缘；组内仅一张图时不显示箭头与圆点。

- 无提示词的图片（参考图、无独立工作流的过程图）不再弹提示词框：点击进入普通看图器（原图 + 说明，组内可左右切换、Esc / 遮罩关闭）；有提示词的图仍走原弹框。六篇本轮手记正文统一为第一人称叙述，移除对话式的「你 / 用户」指代。

- 检查器回归测试 `tests/test_sitecheck.py`（9 条正向/负向样例），CI 在 build/check 后执行 `python3 -m unittest discover -s tests -v`。
- 维护者文档 `docs/ARCHITECTURE.md`：目录职责、数据流、检查器覆盖、部署与项目级信息归属。
- 双语精读：新增三篇，共 13 篇、2,841 句对、313 张术语卡。
  - 第十一篇《The Art of Loop Engineering》（LangChain Blog，2026-06-16），69 句对 / 15 术语 / 8 图。
  - 第十二篇《构建常驻智能体：五个原语，让智能体自己醒来》（Anthropic，2026-11-13），135 句对 / 13 术语 / 7 图。
  - 第十三篇《循环与图：别再盯着每一步，只批最后一步》（Hanako，X Article，2026-08-23），129 句对 / 14 术语 / 4 图。
- 技术手记：新增三篇——《Harness Engineering 的终结：一场还没打完的仗》《100 个设计网站，我先挑了 27 个能马上用的》《12 个让 Claude 做动效的仓库：清单、实测 star 与选型》。
- 技术手记页新增两块：左栏目录下的**相关文章**星座小球（悬停弹出标签 / 日期 / 标题，点击直达；显式 `related` 不足三篇时按标签重合度、日期补齐）与文末**文章相关文档**（点标题弹框预览全文、右上角一键复制；行内「下载」按钮直接取原文件，体积构建时自动计算）。手记 JSON 支持可选字段 `related` / `files`。
- 技术手记：新增六篇（2026-11-25）——《Krea 2 提示词：先定介质，再写九段》《Krea 2 双采：一采定构图，二采加质感》《同一角色跨图不一致：漏的不是模型，是清单》《手画错的时候：四个根因、一条掩码重绘链、三条改构图的路》《雷雳桥对端的本地推理：无 sudo 装 Ollama 与 Qwen3-8B》《Open WebUI 接本地模型：生图、TTS 和 24GB 的三道闸》；正文资源均带外链，IP 与主机名已脱敏。
- `src/static/img/krea2/` 新增 30 张配图（成品、100% 裁切、参考图、失败版本与过程图）；`src/static/files/krea2/`、`files/local-llm/` 新增 15 份可下载文档（参数速查、API JSON、提示词原文、运行日志、脱敏速查卡）。
- 技术手记页新增**图片与提示词内嵌**：正文用 `{{fig:id}}` 插单图卡、`{{deck:group}}` 插叠卡轮播（中间大卡、左右侧卡按原图比例缩略露边、三角箭头切换；宽幅图走宽度约束、方形与纵向图居中限宽 540px）。点卡片弹出提示词弹框（左图 + 右下角切换圆点，右侧出图参数 + 完整提示词 + 一键复制，支持 Esc 与 ←/→；参考图等无提示词的条目自动隐藏复制按钮并给出说明）。手记 JSON 新增可选字段 `gallery`（`id` / `items[{id,img,caption,meta,prompt,ar}]`），未命中的占位符构建时报错。
- 提示词与出图参数取自原始 PNG 的 ComfyUI `tEXt` 工作流（Krea 2 turbo int8、步数 / cfg / sampler / scheduler / denoise / seed、EmptyLatent 尺寸、LoRA 名称与强度），四篇 Krea 手记共 30 张图，除 3 张参考图外均可复制完整提示词。

- 技术手记：新增《Modern Web Guidance 接进 DSH：三个不吭声的坑》，记录本地接入方式、遥测默认开启、catalog 500 字符截断与 YAML 静默失败，以及触发边界。
- 首页「本期精读」改为常驻智能体那一篇。
- 双语精读：新增第十四篇《用 Grok Bot 自动化任何事》（X Article，lauren @poteto，2026-11-18），119 句对 / 13 术语 / 3 图 / 4 译注 / 5 处原文笔误备案；分类「自动化」。
- 双语精读：新增第十五篇《Fable 实战指南：找出你的未知》（X Article，Thariq @trq212，2026-07-04），128 句对 / 21 术语 / 5 图 / 2 译注 / 2 处原文笔误备案；分类「智能体协作」。总览 15 篇。
- 双语精读：新增第十六篇《智能体记忆的组成：Claude 怎样用「做梦」整理记忆》（Anthropic，2026-11-06），207 句对 / 23 术语 / 15 图 / 12 译注 / 21 条外链；分类「上下文工程」。
- 双语精读：新增两篇（Anthropic Research，2026-11-13 / 2026-04-08）：
  - 《把安全评测建扎实：一份给评测设计者的检查清单》201 句对 / 16 术语 / 7 图 / 7 译注；分类「安全」。
  - 《扩展托管智能体：把「大脑」和「双手」拆开》103 句对 / 14 术语 / 4 图 / 7 译注；分类「智能体架构」。
- 书架总览 23 篇（含 merge 时补入的三篇 Claude Code 精读与本轮两篇）。
- 技术手记：新增《给 AI 建记忆系统：从「记下来」到「能被对质」》，写记忆系统的初次建立（10-25 分层/三问/预算）与两次升级（11-16 检索与评测、11-20「对质」），含 44 条金标的基线与向量方案否决的实测数字；三张数据表直接写进帖子 HTML 片段（`new_post.py` 的 Markdown 子集不支持表格）。另配四张内联 SVG 图（记忆系统架构；评测前后、依据覆盖率、287 轮里的 11 次调用），取色走 CSS 变量，明暗主题自动跟随，窄屏在卡片内横向滚动；架构图插在「它长什么样」里作图 1，原三图顺延为 2/3/4。

### Changed

- 四篇 Krea 手记改写为过程叙事（判断、失败版本、参数取舍），图片从文末「图片与提示词」区移回正文原位：单图用 `{{fig}}`、同批多版本用 `{{deck}}`；文末分区与 `gallery_note` 废弃，`post.html` 槽位改为 `{{files}}` + `{{prompt_modal}}`。`gslide` 侧卡改为按可用空隙定尺寸、与主卡留 14px 间距，修复重叠；主卡与画布由 `site.js` 按当前图比例实时计算（含 resize 重排），消除卡片内上下留白；切换补上宽度 / 高度 / 位移过渡与说明文字淡入淡出。另修正 `doujie-eye` 的宽高比声明（2.0 → 2.355）。

- 精读页图片全面转 WebP 并做尺寸收敛：引用素材按显示尺寸上限重编码（照片 1600px / 图稿 2000px），两段动图重做调色板与帧率。全站精读图片 13.6 MB → 4.5 MB（−67%），单篇最重的 Grok 页 1.3 MB → 0.82 MB，anthropic-scm 1.2 MB → 0.31 MB，loop-engineering 1.7 MB → 0.59 MB。原图保留在各项目 `assets/`，可回滚。
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

- 正文链接加 `overflow-wrap: anywhere`：11-15 那篇手记里两条以裸长 URL 作链接文本的引用（claude.com 63 字符、站内 76 字符），在 390px 宽会把整页撑到 418px；现在按需断行，页面回到 375px，1280 宽无变化；两条裸 URL 的链接文本在 `/` 后补了 `<wbr>`，断行落在斜杠后而不是词中间。
- `tools/check.py` 补齐 4 类语义检查：站内绝对路径必须带 `/blog-xiuerhuahuazi/` 前缀；目录链接必须有 `index.html`；跨页锚点必须存在于目标页；非 404 页的 canonical 必须等于当前页地址。
- `tools/import_readers.py` 导入前预检 `meta.json` 必需字段、`meta.cover.asset` 指向的媒体文件、`glossary.json` / `figures.json` 结构；缺 glossary / figures 会告警并按 0 计，不再静默。
- `sitemap.xml` 的 `lastmod` 固定按 `Asia/Shanghai` 的构建日生成（workflow 设置 `TZ`），避免 GitHub Actions 的 UTC 日期比本地早一天，导致同一提交的本地与线上产物不一致。
- 跨页导航：旧页退场与新页入场改为重叠的 crossfade；`pagereveal` 时首屏快照前置呈现，避免新页快照为空、过渡中间出现近空屏。
- 精读页 721–900px：顶栏的「← 双语书架」入口保留到 900px，901px 起才由 `.sm-nav` 接管。
- 深色主题打印：对比卡 `.cmp.win` 恢复浅底深字，打印稿可读。
- 精读页锚点落位：宽屏下粘性列头 `.colheads` 会盖住目录跳转后的小节标题，`scroll-padding-top` 加 31px 余量；单文件版给 `.sec` 加 `scroll-margin-top`（仅在无站点外壳时生效）。

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
