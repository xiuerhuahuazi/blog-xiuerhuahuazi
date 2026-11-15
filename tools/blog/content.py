"""内容读取：src/content/posts/*.json。"""
import json

from .config import POSTS


def load_posts():
    posts = []
    for path in sorted(POSTS.glob("*.json")):
        posts.append(json.loads(path.read_text(encoding="utf-8")))
    posts.sort(key=lambda p: (p["date"], p.get("slug", "")), reverse=True)
    return posts
