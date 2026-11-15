#!/usr/bin/env python3
"""薄入口：博客生成器。

  python3 tools/build.py          # 清空 dist 后全量生成
  python3 tools/build.py --check  # 只打印页面大小，不写 dist
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog.pages import main

if __name__ == "__main__":
    main()
