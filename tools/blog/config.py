"""站点路径与配置：所有模块共享的唯一目录来源。

  ROOT             仓库根
  SRC              源文件根
  DIST             构建产物（每次构建全量重建）
  CONTENT          src/content
  POSTS            src/content/posts
  STATIC           src/static
  READERS_SRC      src/readers
  TEMPLATES        src/templates
  SITE             src/site.json
  BASE             SITE["url"] 去掉末尾斜杠后的站点绝对前缀
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DIST = ROOT / "dist"
CONTENT = SRC / "content"
POSTS = CONTENT / "posts"
STATIC = SRC / "static"
READERS_SRC = SRC / "readers"
TEMPLATES = SRC / "templates"

SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
BASE = SITE["url"].rstrip("/")


def load_readers():
    """读取精读索引；缺失时给出可执行的提示，而不是抛裸异常。"""
    path = CONTENT / "readers.json"
    if not path.is_file():
        raise SystemExit(f"找不到 {path.relative_to(ROOT)}：先跑 tools/import_readers.py 导入精读")
    return json.loads(path.read_text(encoding="utf-8"))["readers"]
