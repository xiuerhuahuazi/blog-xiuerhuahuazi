"""极简模板渲染器：单遍替换 {{key}}，缺槽位立即报错。

模板里只允许出现 {{key}} 形式的槽位。替换值不会被再次扫描，
因此替换内容里即使出现 {{...}} 也会原样输出。
"""
import re
from pathlib import Path

SLOT = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class Templates:
    def __init__(self, root):
        self.root = Path(root)

    def render(self, name, mapping):
        raw = (self.root / name).read_text(encoding="utf-8")

        def replace(match):
            key = match.group(1)
            if key not in mapping:
                raise KeyError(f"模板 {name} 缺少槽位 {key}")
            return str(mapping[key])

        return SLOT.sub(replace, raw)
