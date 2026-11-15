#!/usr/bin/env python3
"""薄入口：生成后自检。

  python3 tools/check.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog.sitecheck import main

if __name__ == "__main__":
    sys.exit(main())
