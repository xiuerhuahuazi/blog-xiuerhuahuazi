#!/usr/bin/env python3
"""一次性导入：把 Butterfly 主题下已发布的文章 HTML 抽成 src/content/posts/*.json。

用法（仓库根目录）：
  python3 tools/oneoff/import_legacy.py            # 已有内容时拒绝覆盖
  python3 tools/oneoff/import_legacy.py --force    # 明确覆盖

只做一次。页面被新模板覆盖后，再跑本脚本会找不到 Butterfly 的 article 容器：
用 --src 指向仍保留原始页面的 git worktree，例如
  git worktree add /tmp/blogorig <原始提交>
  python3 tools/oneoff/import_legacy.py --src /tmp/blogorig --force
"""
import argparse
import glob
import html
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "src", "content", "posts")

TAGS = {
    "hello-world": ["Hello World", "Hexo"],
    "欢迎来到我的博客": ["随笔", "博客"],
    "ffmpeg安装教程（windows）": ["ffmpeg", "windows", "教程"],
    "Hermes-Agent-DeepSeek-V4-模型名弃用问题的排查与修复": ["hermes-agent", "deepseek", "排查"],
    "SSH-Docker-Alias-简化Hermes启动命令": ["hermes-agent", "docker", "ssh"],
}
DESC = {
    "hello-world": "Hexo 的第一篇文章：怎么新建一篇 post，以及这个模板留下的骨架。",
    "欢迎来到我的博客": "开张说明：这个博客打算写什么。",
    "ffmpeg安装教程（windows）": "Windows 下手动安装 ffmpeg 并配好环境变量的完整步骤，附每一步截图。",
    "Hermes-Agent-DeepSeek-V4-模型名弃用问题的排查与修复": "接入 DeepSeek V4 时被模型名弃用卡住：从报错、配置文件到最终可用配置的排查过程。",
    "SSH-Docker-Alias-简化Hermes启动命令": "一条 alias 把「ssh 进 NAS + docker exec + 进容器」缩成 5 个字符。",
}


def text_of(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    return html.unescape(s).strip()


def convert_content(body: str) -> str:
    """把 Butterfly 生成的内容块整理成可移植的 HTML 片段。

    Butterfly 的代码块有两种外壳：<figure class="highlight lang"> 和没有 class 的
    <figure>（无语言高亮时），两者都用 <td class="code"><pre> 装正文。
    """
    def code_repl(part):
        open_tag = re.match(r"<figure([^>]*)>", part)
        lang = ""
        if open_tag:
            lm = re.search(r"highlight\s+([\w+.-]+)", open_tag.group(1))
            if lm:
                lang = lm.group(1)
        cell = re.search(r'<td class="code">\s*<pre[^>]*>(.*?)</pre>', part, re.S)
        if not cell:
            return part
        raw = cell.group(1)
        raw = re.sub(r"<br\s*/?>", "\n", raw)
        raw = re.sub(r"</?code[^>]*>", "", raw)
        raw = re.sub(r"<[^>]+>", "", raw)          # 去掉高亮 span
        raw = html.unescape(raw).strip("\n")
        raw = html.escape(raw)
        cls = f' class="language-{lang}"' if lang else ""
        return f"<pre><code{cls}>{raw}</code></pre>"

    parts = re.split(r"(<figure[^>]*>.*?</figure>)", body, flags=re.S)
    body = "".join(code_repl(p) if p.startswith("<figure") else p for p in parts)
    # 空标题锚点（headerlink）去掉；标题 id 保留给目录用
    body = re.sub(r'<a href="#[^"]*" class="headerlink"[^>]*></a>', "", body)
    # 站内绝对路径改写成 {{ROOT}} 占位，由 build.py 换成相对路径
    body = body.replace('src="/blog-xiuerhuahuazi/', 'src="{{ROOT}}')
    body = body.replace('href="/blog-xiuerhuahuazi/', 'href="{{ROOT}}')
    # 正文自带的一级标题与新模板的 h1 重复，去掉（模板统一从 h1 开始）
    body = re.sub(r"^\s*<h1[^>]*>.*?</h1>", "", body, count=1, flags=re.S)
    # 老文章里的 img 没有 figure 包裹，补上懒加载
    body = re.sub(r"<img ", '<img loading="lazy" ', body)
    return body.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--src", default=ROOT,
                    help="原始 Butterfly 页面所在目录（默认仓库根；也可指向 git worktree）")
    args = ap.parse_args()
    if os.path.isdir(OUT) and os.listdir(OUT) and not args.force:
        print("src/content/posts 已存在，未覆盖（需要时加 --force）")
        return

    os.makedirs(OUT, exist_ok=True)
    src_root = os.path.abspath(os.path.expanduser(args.src))
    pages = sorted(glob.glob(os.path.join(src_root, "2026", "*", "*", "*", "index.html")))
    count = 0
    for path in pages:
        rel = os.path.relpath(os.path.dirname(path), src_root)
        slug = os.path.basename(rel)
        year, month, day = rel.split(os.sep)[:3]
        src = open(path, encoding="utf-8").read()

        title = re.search(r"<title>(.*?)</title>", src, re.S).group(1)
        title = title.split(" | ")[0].strip()
        art = re.search(
            r'<article class="container post-content" id="article-container">(.*?)</article>',
            src, re.S)
        if not art:
            sys.exit(f"找不到 article 容器：{rel}（这页可能已经不是 Butterfly 原页，"
                     "用 --src 指向 git worktree 里的原始版本）")
        body = convert_content(art.group(1))
        first_p = re.search(r"<p>(.*?)</p>", body, re.S)
        desc = DESC.get(slug) or (text_of(first_p.group(1))[:120] if first_p else "")
        heads = re.findall(r"<h([23])([^>]*)>(.*?)</h\1>", body, re.S)
        toc = []
        for lv, attrs, inner in heads:
            idm = re.search(r'id="([^"]+)"', attrs)
            toc.append({"level": int(lv), "text": text_of(inner), "id": idm.group(1) if idm else ""})

        post = {
            "slug": slug,
            "path": rel.replace(os.sep, "/"),
            "title": title,
            "description": desc,
            "date": f"{year}-{month}-{day}",
            "tags": TAGS.get(slug, ["技术"]),
            "content": body,
            "toc": toc,
        }
        with open(os.path.join(OUT, slug + ".json"), "w", encoding="utf-8") as f:
            json.dump(post, f, ensure_ascii=False, indent=1)
            f.write("\n")
        count += 1
        print("导入", slug, len(body), "字节")

    print("共", count, "篇。生成时间", datetime.now().strftime("%Y-%m-%d %H:%M"))


if __name__ == "__main__":
    main()
