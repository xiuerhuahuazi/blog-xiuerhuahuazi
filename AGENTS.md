# AGENTS.md — blog-xiuerhuahuazi

> 项目级约定。跨项目规则见 `~/.dsh/AGENTS.md`，这里只写本仓。

## 这是什么

个人站点：双语精读（逐句英中对照）+ 技术手记。纯静态，Python 3 标准库生成，无第三方运行时依赖，零外部请求。部署在 GitHub Pages 子路径 `/blog-xiuerhuahuazi/`。

## 目录约定

- `src/` 是唯一手改区域；`dist/` 是构建产物，已 gitignore，**不要手改、不要提交**。
- `src/content/` 是内容唯一数据源：手记 `posts/*.json`、精读索引 `readers.json`、精读策展 `readers_curated.json`。
- `src/readers/` 是导入物（精读成品），只能由 `tools/import_readers.py` 覆盖，不要手工编辑。
- `src/static/` 构建时原样复制到 `dist/`；`src/templates/` 放页面模板（静态 HTML 与 `{{槽位}}`），其中 `readers-shell/` 是例外——放注入精读页的 CSS / JS / HTML。
- 条件、循环、转义、路径计算都在 `tools/blog/`；入口脚本只做参数与调度。
- `tests/` 是检查器回归测试；CI 在 build/check 后跑 `python3 -m unittest discover -s tests -v`。
- `docs/ARCHITECTURE.md` 是维护者文档（结构、命令、检查器覆盖、部署）；项目约定在本文件，历史在 `CHANGELOG.md`。
- `.agents/` 是本机项目台账与原始审计（gitignored，不发布）；项目级细节放这里，不塞进全局记忆。

## 不变量

1. **URL 不变**：`/`、`/readers/`、`/readers/<slug>/`、`/notes/`、`/<年>/<月>/<日>/<slug>/`、`/about/`、`/404.html`。
2. **零外部请求**：不引 CDN、字体、图标库、统计脚本。
3. 只用系统字体；页面不依赖 JS 也能读。
4. 生成结果必须通过 `python3 tools/check.py`：链接/资源存在、目录有 `index.html`、站内绝对路径带 `/blog-xiuerhuahuazi/` 前缀、同页/跨页锚点存在、canonical 等于当前页地址。
5. 模板槽位缺失必须报错，不静默替换空串；替换值不二次扫描。
6. `dist` 的清理前必须确认是仓库根下的 `dist/`。
7. `tests/test_sitecheck.py` 必须通过；CI 已接入。

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

## 内容工作流

- 新手记：`tools/new_post.py` 写 `src/content/posts/<slug>.json`，自动 build + check。
- 新精读：先在 `bilingual-readers` 生成 `cloud/`，再 `import_readers.py --force`，然后 build。分类/导读/`featured` 改 `src/content/readers_curated.json`。
- 老文章：`tools/oneoff/import_legacy.py` 只对 Butterfly 时期的原始页面有效，正常内容维护不要跑。

## 验收

- 任何模板/生成逻辑改动：`build.py` + `check.py` + 单测必须过；页面结构应与此前产物对比（无意改版时应逐字节一致）。
- 精读导入改动：源仓未变时，重导后 `diff -r` 现有 `src/readers/` 应无差异。
- 版式改动：在真实浏览器里看首页、书架、一篇精读、一篇手记、404；390px 宽无横向溢出。
- 部署后：首页 / 书架 / 一篇精读 / 一篇手记 / 资源 / 未知路径 404 各验一次。

## 项目级信息归属

- **当前结构 / 命令 / 检查器覆盖 / 验收数字**：`docs/ARCHITECTURE.md`。
- **约定与不变量**：本文件；**变更历史**：`CHANGELOG.md`。
- **本机台账与原始审计**：仓库 `.agents/`（gitignored，不发布）。
- **全局记忆**只放项目指针、跨会话判断与跨项目教训；不抄目录树、模块清单、提交哈希、检查器细目。

## 已知坑

- 精读源在另一个仓库；`--force` 会删掉不在策展数据里的目录，先确认 `readers_curated.json` 是全的。导入前会预检 meta 必需字段、cover 指向的媒体文件、glossary/figures 结构；缺 glossary/figures 会告警并按 0 计，声明了 cover 但文件缺失时中止。
- `check.py` 离线运行，不检查外部链接、CSS `url()` 与 JS 运行时生成的 URL；这些要在真实浏览器/网络面板确认。
- 子路径部署：正文资源写 `{{ROOT}}img/...`（构建时按页面层级替换）或相对路径，**不要写 `/img/...`**。
- `404.html` 生成后会把相对 `href/src` 绝对化，因为 404 可能从任意深度被请求。
- `sitemap.xml` 的 `lastmod` 用构建当天，逐字节对比要同一天跑。
- `readers-shell/*` 注入的是第三方成品页结构；源页改版后注入锚点（`topbar-in`、`<body>`）可能失配，`inject()` 会直接报错而不是静默跳过。
- 图片/目录含中文或括号时，canonical 与 sitemap 必须百分号编码（`abs_url` 已处理）。
- 本机 `github.com` 直连可能超时，push 需要 `HTTPS_PROXY=http://127.0.0.1:7890`。

## 发布

推 `main` 触发 `.github/workflows/pages.yml`，构建 `dist/` 并通过 GitHub Pages 部署。Pages 发布源必须是 **GitHub Actions**。`dist/` 不入库，不要为发布再提交一份产物。
