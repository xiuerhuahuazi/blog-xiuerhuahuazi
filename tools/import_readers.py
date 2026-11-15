#!/usr/bin/env python3
"""从双语精读项目导入成品页：src/readers/<slug>/ + src/content/readers.json。

用法（仓库根目录）：
  python3 tools/import_readers.py --src ~/Documents/project/bilingual-readers
  python3 tools/import_readers.py --src ... --force     # 覆盖已有 src/readers/

导入的是各项目的 cloud/ 版（HTML + 外置 media/，视频与图片按需加载），
并注入「返回双语书架」导航与分享用的 og 标签。cloud/index.html 由精读技能生成，
这里只做增量注入，不重排它自己的样式。策展数据读 src/content/readers_curated.json。
"""
import argparse
import json
import os
import shutil
from pathlib import Path

from blog.config import ROOT
from blog.reader_shell import hero_numbers, inject

OUT_PAGES = ROOT / "src" / "readers"
OUT_JSON = ROOT / "src" / "content" / "readers.json"
CURATED_PATH = ROOT / "src" / "content" / "readers_curated.json"


def load_curated():
    data = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
    return data["featured"], data["readers"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser("~/Documents/project/bilingual-readers"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    src = Path(args.src).expanduser().resolve()
    featured, curated = load_curated()

    if OUT_JSON.exists() and not args.force:
        print("src/content/readers.json 已存在，未覆盖（需要时加 --force）")
        return

    # 先把所有输入检查一遍：缺任何一个都不写，避免用半份数据覆盖已有索引
    missing = []
    for slug in curated:
        if not (src / slug / "data" / "meta.json").is_file():
            missing.append(f"{slug}/data/meta.json")
        if not (src / slug / "cloud" / "index.html").is_file():
            missing.append(f"{slug}/cloud/index.html")
    if missing:
        raise SystemExit("源目录缺少文件，未做任何改动：\n  " + "\n  ".join(missing))

    OUT_PAGES.mkdir(parents=True, exist_ok=True)
    readers = []
    keep = set()
    for slug, curation in curated.items():
        meta = json.loads((src / slug / "data" / "meta.json").read_text(encoding="utf-8"))
        cloud = src / slug / "cloud"
        page = (cloud / "index.html").read_text(encoding="utf-8")
        nums = hero_numbers(page)
        cover = (meta.get("cover") or {}).get("asset") or ""
        cat, blurb = curation["category"], curation["blurb"]
        desc = meta.get("subtitle_zh") or blurb

        page = inject(page, slug, meta["title_zh"], desc, cover)

        dest = OUT_PAGES / slug
        if dest.is_dir():
            shutil.rmtree(dest)
        dest.mkdir()
        (dest / "index.html").write_text(page, encoding="utf-8")
        if (cloud / "media").is_dir():
            shutil.copytree(cloud / "media", dest / "media")

        glossary = src / slug / "data" / "glossary.json"
        terms = len(json.loads(glossary.read_text(encoding="utf-8"))["terms"]) if glossary.exists() else 0
        figures = src / slug / "data" / "figures.json"
        figs = len(json.loads(figures.read_text(encoding="utf-8"))["figures"]) if figures.exists() else 0

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
            "featured": slug == featured,
        })
        print(f"导入 {slug}: {nums['pairs']} 句对, {terms} 术语, {figs} 图")

    # 删掉已经不在策展数据里的旧成品目录，避免陈旧页面留在站点里
    for name in os.listdir(OUT_PAGES):
        if name not in keep and (OUT_PAGES / name).is_dir():
            shutil.rmtree(OUT_PAGES / name)
            print("移除过期目录", name)

    readers.sort(key=lambda r: r["published"], reverse=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"readers": readers}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("共", len(readers), "篇；索引写入 src/content/readers.json")


if __name__ == "__main__":
    main()
