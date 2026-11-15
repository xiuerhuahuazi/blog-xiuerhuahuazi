#!/usr/bin/env python3
"""把一篇 Markdown 变成技术手记，并重新生成站点。

  python3 tools/new_post.py post.md
  python3 tools/new_post.py post.md --date 2026-11-20 --slug my-post --force

文件头可以用 front matter（--- 包起来，全部可选）：
  title:    标题（默认取第一个 # 标题或文件名）
  date:     2026-11-20（默认今天）
  tags:     hermes-agent, docker
  desc:     一句话摘要（默认取第一段前 120 字）
  slug:     URL 片段（默认由标题转写）

生成内容写入 src/content/posts/<slug>.json，页面落在
dist/<年>/<月>/<日>/<slug>/，与老文章同样的 URL 形态。支持的 Markdown：
标题、段落、列表、引用、代码块、分隔线、图片、链接、粗体/斜体/行内代码。
表格不支持——需要表格时直接改 src/content/posts/<slug>.json 里的 HTML 片段。
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

from blog.config import POSTS, ROOT
from blog.markdown import check_slug, convert, parse_front_matter, slugify


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--date", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    raw = open(os.path.expanduser(args.markdown), encoding="utf-8").read()
    meta, body = parse_front_matter(raw)

    hm = re.search(r"^#\s+(.+)$", body, re.M)
    title = meta.get("title") or (hm.group(1).strip() if hm else
                                  os.path.splitext(os.path.basename(args.markdown))[0])
    if hm:
        body = body[:hm.start()] + body[hm.end():].lstrip("\n")

    day = meta.get("date") or args.date or date.today().isoformat()
    try:
        y, mo, d = [int(x) for x in re.split(r"[-/.]", day)[:3]]
    except ValueError:
        sys.exit(f"日期看不懂：{day!r}（要 2026-11-20 这种）")
    day = f"{y:04d}-{mo:02d}-{d:02d}"

    slug = check_slug(meta.get("slug") or args.slug or slugify(title))
    tags = [t.strip() for t in re.split(r"[,，]", meta.get("tags", "")) if t.strip()] or ["技术"]
    content = convert(body, {})
    first = re.sub(r"<[^>]+>", "", content.split("\n")[0]) if content else ""
    desc = meta.get("desc") or (first[:120] if first else title)

    path = f"{y:04d}/{mo:02d}/{d:02d}/{slug}"
    dest = (POSTS / (slug + ".json")).resolve()
    if dest.parent != POSTS.resolve():
        sys.exit("拒绝写入 src/content/posts 之外的路径")
    if dest.exists() and not args.force:
        sys.exit(f"{dest.relative_to(ROOT)} 已存在；要覆盖加 --force")

    heads = re.findall(r"<h([23])([^>]*)>(.*?)</h\1>", content, re.S)
    toc = []
    for lv, attrs, inner in heads:
        idm = re.search(r'id="([^"]+)"', attrs)
        toc.append({"level": int(lv), "text": re.sub(r"<[^>]+>", "", inner), "id": idm.group(1) if idm else ""})

    post = {"slug": slug, "path": path, "title": title, "description": desc,
            "date": day, "tags": tags, "content": content, "toc": toc}
    POSTS.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("写入", dest.relative_to(ROOT), "→", path + "/")

    subprocess.run([sys.executable, "tools/build.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "tools/check.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
