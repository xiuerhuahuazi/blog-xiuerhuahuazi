"""tools/blog/sitecheck.py 的回归测试。

只覆盖检查器本身：用临时 dist 构造最小页面，断言该报的错会报、该过的会过。
运行（仓库根）：
  python3 -m unittest discover -s tests -v
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from blog import sitecheck  # noqa: E402

BASE = "https://example.test/blog"
BASE_PATH = "/blog/"


class CheckerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._patches = [
            mock.patch.object(sitecheck, "DIST", self.root),
            mock.patch.object(sitecheck, "BASE", BASE),
            mock.patch.object(sitecheck, "BASE_PATH", BASE_PATH),
        ]
        for patch in self._patches:
            patch.start()

    def tearDown(self):
        for patch in self._patches:
            patch.stop()
        self.tmp.cleanup()

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def page(self, canonical=None, body="", title="T", desc="D"):
        canon = f'<link rel="canonical" href="{canonical}">' if canonical is not None else ""
        return ("<!doctype html><html><head><title>" + title + "</title>"
                '<meta name="description" content="' + desc + '">' + canon
                + "</head><body>" + body + "</body></html>")

    def seed_valid(self):
        self.write("index.html", self.page(
            BASE + "/", '<a href="about/">about</a><a href="#top">top</a><div id="top"></div>'))
        self.write("about/index.html", self.page(
            BASE + "/about/", '<a href="../">home</a><h2 id="ok">ok</h2>'))

    def run_check(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = sitecheck.main()
        return code, out.getvalue()

    def test_valid_site_passes(self):
        self.seed_valid()
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("检查 2 个页面", out)

    def test_absolute_path_without_base_prefix_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/", '<a href="/about/">about</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("站内绝对路径缺少站点前缀", out)

    def test_directory_without_index_fails(self):
        self.seed_valid()
        (self.root / "empty").mkdir()
        self.write("index.html", self.page(BASE + "/", '<a href="empty/">empty</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("目录但没有 index.html", out)

    def test_missing_cross_page_anchor_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/", '<a href="about/#nope">bad</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("锚点 #nope 不在 about/index.html", out)

    def test_existing_cross_page_anchor_passes(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/", '<a href="about/#ok">ok</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_missing_same_page_anchor_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/", '<a href="#nope">bad</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("页内锚点 #nope 不存在", out)

    def test_missing_canonical_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(None))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("缺少 rel=canonical", out)

    def test_wrong_canonical_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/about/"))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("canonical 与当前页不符", out)

    def test_missing_file_fails(self):
        self.seed_valid()
        self.write("index.html", self.page(BASE + "/", '<a href="no-such-page/">bad</a>'))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("指向不存在的", out)


if __name__ == "__main__":
    unittest.main()
