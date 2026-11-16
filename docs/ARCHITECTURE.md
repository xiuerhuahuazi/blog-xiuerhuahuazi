# 架构与维护

> 面向维护者。使用说明见 [README.md](../README.md)，项目约定见 [AGENTS.md](../AGENTS.md)，变更历史见 [CHANGELOG.md](../CHANGELOG.md)。

## 目标与约束

- 纯静态站点：Python 3 标准库生成，无第三方运行时依赖。
- 零外部请求：不引 CDN、外部字体、图标库、统计脚本。
- 子路径部署：`https://xiuerhuahuazi.github.io/blog-xiuerhuahuazi/`。
- URL 不变：首页、书架、精读页、手记、关于、404 的既有路径都要保持。
- 页面不依赖 JS 也能读；JS 只做主题、进度条、目录高亮等增强。

## 目录

```text
src/
  site.json                 站名、导航、关于页文案、站点 URL
  content/
    posts/*.json            技术手记正文（唯一数据源）
    readers.json            精读索引（由 import_readers.py 生成）
    readers_curated.json    精读策展：分类、一句话导读、featured
  readers/<slug>/           精读成品页（导入物，构建时原样复制）
  static/                   构建时原样复制到 dist/
    assets/site.css|js
    img/
    .nojekyll
  templates/
    base.html               全站外壳
    home.html / readers.html / notes.html / post.html / about.html / 404.html
    partials/               可复用片段（列表行、feature 卡、TOC、上下篇……）
    readers-shell/          注入精读成品页的 CSS / JS / 顶栏 / meta 模板
tools/
  build.py                  薄入口：清空 dist 后全量生成
  check.py                  薄入口：调用 blog.sitecheck
  new_post.py               Markdown → 手记，再跑 build + check
  import_readers.py         从双语精读项目导入成品
  oneoff/import_legacy.py   一次性抽取 Butterfly 老文章（历史脚本）
  blog/
    config.py               路径与站点配置
    utils.py                转义、相对路径、日期、导航
    template.py             单遍 {{key}} 模板渲染器
    content.py              读取手记
    markdown.py             Markdown → HTML 纯函数
    pages.py                页面构建与 dist 输出
    sitecheck.py            dist 自检
    reader_shell.py         精读页注入资源与函数
tests/
  test_sitecheck.py         检查器回归测试
.github/workflows/pages.yml Actions 构建与 Pages 部署
docs/
  ARCHITECTURE.md           本文件
```

## 数据流

1. `src/content` 是内容唯一来源；`src/readers` 是导入成品。
2. `tools/build.py` 清空 `dist/`，先复制 `src/static/` 与 `src/readers/`，再用 `src/templates/` 渲染页面。
3. `tools/check.py` 检查 `dist/` 的链接、资源、锚点与 canonical。
4. CI 跑 build + check + 单元测试，把 `dist/` 作为 Pages 产物上传。

## 模块职责

- `blog/config.py`：所有路径与 `SITE` / `BASE` 的唯一来源。
- `blog/template.py`：`{{key}}` 单遍替换；缺 key 直接报错，替换值不二次扫描。
- `blog/pages.py`：页面级逻辑；HTML 应放在 `src/templates/`，这里只拼数据、条件与循环。
- `blog/sitecheck.py`：离线检查；`resolve()` 负责把相对/绝对/站外引用解析到 `dist/`。
- `blog/markdown.py`：只做手记需要的 Markdown 子集，不追求 CommonMark。
- `blog/reader_shell.py`：读取 `readers-shell/` 资源，负责向第三方精读成品页注入站点外壳。

## 命令

```bash
python3 tools/build.py          # 清空 dist 后全量生成
python3 tools/build.py --check  # 只打印页面字符数，不写文件
python3 tools/check.py          # 检查 dist/，失败 exit 1
python3 -m unittest discover -s tests -v
python3 tools/new_post.py note.md
python3 tools/import_readers.py --src /path/to/bilingual-readers --force
python3 -m http.server -d dist 8000
```

## 检查器覆盖

`tools/check.py` 检查：

- `href` / `src` / `data-src` / `poster` / `srcset` / `og:image` 指向的文件是否存在；
- 目录链接必须命中该目录的 `index.html`，不能只是目录存在；
- 站内绝对路径必须带站点子路径前缀 `/blog-xiuerhuahuazi/`；
- 页内锚点与跨页锚点是否存在于目标 HTML；
- 每页 `<title>`、`meta description`、`rel=canonical`；非 404 页的 canonical 必须等于当前页地址。

不覆盖（有意或暂未做）：

- 外部链接的可用性（检查器离线运行）；
- CSS `url()` 与 JS 运行时生成的 URL；
- 图片尺寸、颜色对比度、性能指标。
- `404.html` 的 canonical / description 按设计跳过。

## 当前验收基线（2026-11-16）

- build：15 个生成页；`dist/` 共 26 个 HTML 页、126 个文件。
- check：26 个页面 / 635 个引用，exit 0。
- tests：9 条（`tests/test_sitecheck.py`）。
- 精读：13 篇；源仓未变时重导 `src/readers/` 与 `readers.json` 零差异。
- 数字随内容与模板变化；每次改版后重跑并更新本节。

## 内容工作流

- 新手记：`tools/new_post.py` 写 `src/content/posts/<slug>.json`，自动 build + check。正文图片用 `{{ROOT}}img/...`，构建时按页面层级替换；不要写 `/img/...`。
- 新精读：先在 `bilingual-readers` 生成 `cloud/`，再 `import_readers.py --force`，然后 build。分类、导读、`featured` 改 `src/content/readers_curated.json`。
- 导入预检：`import_readers.py` 会校验 `meta.json` 必需字段、`meta.cover.asset` 指向的媒体文件、`glossary.json` / `figures.json` 的结构；缺 glossary / figures 会告警并按 0 计，不再静默。
- 老文章：`tools/oneoff/import_legacy.py` 只对 Butterfly 时期原始页面有效，正常维护不要跑。

## 测试与验收

```bash
python3 tools/build.py
python3 tools/check.py
python3 -m unittest discover -s tests -v
```

模板或生成逻辑改动后，与改动前的 `dist/` 做逐字节对比；无意改版时应零差异。精读导入改动后，源仓未变时重导应零差异。

## 部署

推 `main` 触发 `.github/workflows/pages.yml`：build → check → 单测 → 上传 `dist/` → 部署 Pages。Pages 发布源必须是 **GitHub Actions**；`dist/` 不入库。

## 项目级信息的归属

- **当前结构、命令、检查器覆盖、验收数字**：本文件；变更历史：`CHANGELOG.md`。
- **项目约定与不变量**：`AGENTS.md`。
- **本机项目台账、原始审计报告**：仓库内 `.agents/`（gitignored，不发布）。
- **全局记忆**（`~/.agents/identity/memory-projects-*.md`）：只放项目指针、跨会话需要的判断与可复用教训；不抄目录树、模块清单、提交哈希、检查器细目。
