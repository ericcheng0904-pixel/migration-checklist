#!/usr/bin/env python3
"""Printable pages match the checklist Markdown and stay self-contained."""

from __future__ import annotations

import html
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stderr
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "make-printable.py"
DOCS = ROOT / "docs"

PAGES = (
    ("CHECKLIST.md", "woocommerce-to-shopify.html"),
    ("MAGENTO.md", "magento-to-shopify.html"),
    ("BIGCOMMERCE.md", "bigcommerce-to-shopify.html"),
    ("SQUARESPACE.md", "squarespace-to-shopify.html"),
    ("WIX.md", "wix-to-shopify.html"),
    ("SPOT-CHECKS.md", "spot-checks.html"),
)
SIBLING = dict(PAGES)
TASK_PREFIX = "- [ ] "
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
FORBIDDEN = ("<script", "src=", "<link", "<img", "<iframe", "<form", "url(", "@import")

README_AFFILIATION = (
    "This project is independent and is not affiliated with Shopify or WooCommerce. "
    "Those names are used only to describe the platforms. It is not affiliated with "
    "Adobe or Magento. It is not affiliated with BigCommerce. It is not affiliated "
    "with Squarespace. It is not affiliated with Wix."
)
TOOL_URLS = (
    "https://catalog-signoff.pages.dev/guides/woocommerce-to-shopify-migration-checklist.html",
    "https://catalog-signoff.pages.dev/tools/readiness-scan.html",
    "https://catalog-signoff.pages.dev/tools/redirect-map.html",
)


def load_module():
    spec = importlib.util.spec_from_file_location("make_printable", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["make_printable"] = module
    spec.loader.exec_module(module)
    return module


mod = load_module()


class HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "href" and value is not None:
                self.hrefs.append(value)


def hrefs_of(page: str) -> list[str]:
    parser = HrefParser()
    parser.feed(page)
    return parser.hrefs


def visible_text(fragment: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def markdown_visible(text: str) -> str:
    """Words a reader sees, with Markdown syntax removed and whitespace collapsed."""
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(line)
            continue
        if not line.strip():
            continue
        if line.startswith(TASK_PREFIX):
            line = line[len(TASK_PREFIX) :]
        elif line.startswith("- "):
            line = line[2:]
        elif line.startswith("> "):
            line = line[2:]
        elif line.startswith(">"):
            line = line[1:]
        else:
            heading = re.match(r"^#{1,6} (.*)$", line)
            ordered = re.match(r"^\d+\. (.*)$", line)
            if heading:
                line = heading.group(1)
            elif ordered:
                line = ordered.group(1)
        line = LINK.sub(r"\1", line)
        line = line.replace("**", "").replace("`", "")
        out.append(line)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def item_plain(line: str) -> str:
    body = line[len(TASK_PREFIX) :]
    body = LINK.sub(r"\1", body)
    body = body.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", body).strip()


def ordered_plain(line: str) -> str:
    body = re.sub(r"^\d+\. ", "", line)
    body = LINK.sub(r"\1", body)
    body = body.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", body).strip()


class PrintablePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {
            name: (DOCS / name).read_text(encoding="utf-8")
            for _source, name in PAGES
        }
        cls.pages["index.html"] = (DOCS / "index.html").read_text(encoding="utf-8")

    def test_check_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_check_runs_the_up_to_date_step(self) -> None:
        text = (ROOT / "scripts" / "check.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/make-printable.py --check", text)
        for word in ("scrub", "deny", "maintainer"):
            self.assertNotIn(word, text)

    def test_checkbox_counts_match(self) -> None:
        for source, name in PAGES:
            markdown = (ROOT / source).read_text(encoding="utf-8")
            page = self.pages[name]
            md_count = sum(1 for line in markdown.splitlines() if line.startswith(TASK_PREFIX))
            html_count = page.count('<li class="check">')
            self.assertEqual(html_count, md_count, source)

    def test_https_source_and_relative_links(self) -> None:
        for source, name in PAGES:
            markdown = (ROOT / source).read_text(encoding="utf-8")
            page = self.pages[name]
            found = hrefs_of(page)
            counts = Counter(found)
            https_counts: Counter[str] = Counter()
            sibling_counts: Counter[str] = Counter()
            for label, url in LINK.findall(markdown):
                if url.startswith("https://") or url.startswith("http://"):
                    https_counts[url] += 1
                    continue
                path = url.split("#", 1)[0].split("?", 1)[0]
                if path.startswith("./"):
                    path = path[2:]
                if path in SIBLING:
                    sibling_counts[SIBLING[path]] += 1
                    continue
                self.assertIn(label, visible_text(page), f"{source} {url}")
                self.assertNotIn(url, found, f"{source} {url}")
            for url, count in https_counts.items():
                self.assertGreaterEqual(counts[url], count, f"{source} {url}")
            for url, count in sibling_counts.items():
                self.assertEqual(counts[url], count, f"{source} {url}")

    def test_sampled_item_text_matches(self) -> None:
        for source, name in PAGES:
            lines = (ROOT / source).read_text(encoding="utf-8").splitlines()
            page = self.pages[name]
            tasks = [line for line in lines if line.startswith(TASK_PREFIX)]
            if tasks:
                rendered = [
                    visible_text(fragment)
                    for fragment in re.findall(
                        r'<span class="check-text">(.*?)</span>', page, re.S
                    )
                ]
                self.assertEqual([item_plain(line) for line in tasks], rendered, source)
                mid = len(tasks) // 2
                for line in (tasks[0], tasks[mid], tasks[-1]):
                    self.assertIn(item_plain(line), rendered, source)
                continue
            ordered = [line for line in lines if re.match(r"^\d+\. ", line)]
            self.assertGreaterEqual(len(ordered), 3, source)
            ol = "\n".join(re.findall(r"<ol[^>]*>(.*?)</ol>", page, re.S))
            rendered = [
                visible_text(fragment)
                for fragment in re.findall(r"<li(?:\s[^>]*)?>(.*?)</li>", ol, re.S)
            ]
            self.assertEqual([ordered_plain(line) for line in ordered], rendered, source)
            mid = len(ordered) // 2
            for line in (ordered[0], ordered[mid], ordered[-1]):
                self.assertIn(ordered_plain(line), rendered, source)

    def test_every_word_of_the_source_is_in_the_body_in_order(self) -> None:
        for source, name in PAGES:
            markdown = (ROOT / source).read_text(encoding="utf-8")
            page = self.pages[name]
            main = page.split("<main>", 1)[1].split("</main>", 1)[0]
            main = re.sub(
                r'<p class="nav"><a href="index.html">All printable checklists</a></p>\n?',
                "",
                main,
                count=1,
            )
            self.assertEqual(visible_text(main), markdown_visible(markdown), source)

    def test_pages_have_no_external_requests(self) -> None:
        for name, page in self.pages.items():
            for token in FORBIDDEN:
                self.assertNotIn(token, page, f"{name} {token}")
            self.assertIn('<html lang="en">', page)
            self.assertIn('<meta charset="utf-8">', page)
            self.assertEqual(page.count("<h1>"), 1, name)
            self.assertNotIn("<script", page.lower(), name)
            self.assertNotRegex(page, r"(?i)<link\b", name)

    def test_title_and_description_lengths(self) -> None:
        for name, page in self.pages.items():
            title = html.unescape(re.search(r"<title>(.*?)</title>", page).group(1))
            description = html.unescape(
                re.search(r'<meta name="description" content="(.*?)">', page).group(1)
            )
            self.assertGreaterEqual(len(title), 10, name)
            self.assertLessEqual(len(title), 70, name)
            self.assertGreaterEqual(len(description), 120, name)
            self.assertLessEqual(len(description), 155, name)

    def test_footer_licence_affiliation_and_tool_links(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        licence = next(
            line
            for line in readme.splitlines()
            if line.startswith("The Markdown documents and CSV files are [CC BY 4.0](")
        )
        for source, name in PAGES:
            markdown = (ROOT / source).read_text(encoding="utf-8")
            footer = self.pages[name].split("<footer>", 1)[1].split("</footer>", 1)[0]
            footer_text = visible_text(footer)
            self.assertIn(visible_text(mod.render_inline(licence)), footer_text)
            self.assertIn(f"Generated from {source} in this repository.", footer_text)
            affiliation = next(
                (
                    line
                    for line in markdown.splitlines()
                    if line.startswith("This project is independent and is not affiliated with ")
                ),
                README_AFFILIATION,
            )
            self.assertIn(affiliation, footer_text, source)
            for url in TOOL_URLS:
                self.assertIn(url, hrefs_of(footer), source)
            self.assertNotIn("github.com", footer)
            self.assertNotIn("product-csv-lint", footer)
            self.assertIsNone(ISO_DATE.search(self.pages[name]), source)
        index_footer = self.pages["index.html"].split("<footer>", 1)[1]
        self.assertIn(README_AFFILIATION, visible_text(index_footer))
        self.assertIn(
            "Generated from the checklist files in this repository.",
            visible_text(index_footer),
        )

    def test_nojekyll_is_empty(self) -> None:
        path = DOCS / ".nojekyll"
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), b"")

    def test_readme_lists_the_printable_pages_before_contents(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertLess(readme.index("## Printable versions"), readme.index("## Contents"))
        block = readme.split("## Printable versions", 1)[1].split("## Contents", 1)[0]
        self.assertIn(
            "Download a file and open it in a browser, then print or save as PDF from the browser.",
            block,
        )
        self.assertNotIn("|", block)
        self.assertEqual(block.count("\n- "), 6)
        for _source, name in PAGES:
            self.assertIn(f"(docs/{name})", block)
        self.assertNotIn("REPO-SETTINGS", readme)

    def test_index_lists_the_six_pages_in_order(self) -> None:
        index = self.pages["index.html"]
        main = index.split("<main>", 1)[1].split("</main>", 1)[0]
        expected = [name for _source, name in PAGES]
        found = [href for href in hrefs_of(index) if href in expected]
        self.assertEqual(found, expected)
        for href in expected:
            self.assertTrue((DOCS / href).is_file(), href)
        for _source, target, title, _description in mod.PAGES:
            label = title.removesuffix(" (printable)")
            self.assertIn(f'<a href="{target}">{label}</a>', main)
        self.assertEqual(
            re.findall(r"<h2>(.*?)</h2>", main),
            [
                "Checklists by source platform",
                "Spot checks and sampling worksheet",
                "Tracker import files",
                "Free tools",
            ],
        )
        self.assertEqual(main.count("<h1>"), 1)
        self.assertIn("<h1>Printable checklists</h1>", main)
        self.assertNotIn("<table", main.lower())
        text = visible_text(main)
        self.assertIn(
            "Download a file and open it in a browser, then print or save as PDF from the browser.",
            text,
        )
        self.assertIn(
            "The files in tracker-import/ are plain CSV with the columns Phase, Check, Details, and Source.",
            text,
        )
        self.assertIn(
            "They are generated from the checklist files and are under the same CC BY 4.0 licence.",
            text,
        )
        self.assertIn("Most trackers and spreadsheets can import a CSV.", text)
        self.assertIn("how to count products, variants and SKUs in an export.", text)
        self.assertIn(
            "as arithmetic on assumed examples, how likely a random sample is to contain a wrong row.",
            text,
        )

    def test_relative_hrefs_resolve_from_docs(self) -> None:
        for name, page in self.pages.items():
            for href in hrefs_of(page):
                self.assertFalse(href.startswith("/"), f"{name} {href}")
                self.assertFalse(href.startswith("../"), f"{name} {href}")
                if href.startswith("https://") or href.startswith("http://"):
                    continue
                path = href.split("#", 1)[0]
                self.assertTrue((DOCS / path).is_file(), f"{name} {href}")

    def test_tracker_csv_copies_match_byte_for_byte(self) -> None:
        names = (
            "woocommerce.csv",
            "magento.csv",
            "bigcommerce.csv",
            "squarespace.csv",
            "wix.csv",
            "spot-checks.csv",
        )
        folder = DOCS / "tracker-import"
        self.assertEqual(sorted(path.name for path in folder.glob("*.csv")), sorted(names))
        self.assertEqual(sorted(path.name for path in folder.iterdir()), sorted(names))
        for name in names:
            self.assertEqual(
                (folder / name).read_bytes(),
                (ROOT / "tracker-import" / name).read_bytes(),
                name,
            )

    def test_index_tool_links_are_only_the_allowed_https_urls(self) -> None:
        index = self.pages["index.html"]
        main = index.split("<main>", 1)[1].split("</main>", 1)[0]
        self.assertIn(
            '<a href="https://catalog-signoff.pages.dev/tools/import-check">Free import check</a>',
            main,
        )
        self.assertIn(
            '<a href="https://catalog-signoff.pages.dev/sample/">Sample reports</a>',
            main,
        )
        allowed = {
            "https://catalog-signoff.pages.dev/tools/import-check",
            "https://catalog-signoff.pages.dev/sample/",
            *TOOL_URLS,
            "https://creativecommons.org/licenses/by/4.0/",
        }
        found = {
            href
            for href in hrefs_of(index)
            if href.startswith("https://") or href.startswith("http://")
        }
        self.assertEqual(found, allowed)
        self.assertNotIn("github.com", index)
        self.assertNotIn("product-csv-lint", index)

    def test_index_text_has_no_price_or_performance_claims(self) -> None:
        index = self.pages["index.html"]
        main = index.split("<main>", 1)[1].split("</main>", 1)[0]
        footer = index.split("<footer>", 1)[1].split("</footer>", 1)[0]
        text = visible_text(main + "\n" + footer)
        for token in ("$", "USD", "/month"):
            self.assertNotIn(token, text)
        for word in ("users", "accurate", "fast", "tested by"):
            self.assertIsNone(re.search(r"(?i)\b" + re.escape(word) + r"\b", text), word)

    def test_index_item_counts_match_the_markdown(self) -> None:
        index = self.pages["index.html"]
        main = index.split("<main>", 1)[1].split("</main>", 1)[0]
        for source, target in PAGES:
            if target == "spot-checks.html":
                continue
            count = sum(
                1
                for line in (ROOT / source).read_text(encoding="utf-8").splitlines()
                if line.startswith(TASK_PREFIX)
            )
            match = re.search(
                rf"<li>(?:(?!</li>).)*href=\"{re.escape(target)}\"(?:(?!</li>).)*</li>",
                main,
                re.S,
            )
            self.assertIsNotNone(match, target)
            item = match.group(0)
            found = re.findall(r"(\d+) checks", item)
            self.assertEqual(found, [str(count)], target)

    def test_nav_link_is_on_checklist_pages_only(self) -> None:
        nav = '<p class="nav"><a href="index.html">All printable checklists</a></p>'
        for _source, name in PAGES:
            main = self.pages[name].split("<main>", 1)[1].split("</main>", 1)[0]
            self.assertEqual(main.count(nav), 1, name)
            self.assertTrue(main.lstrip().startswith(nav), name)
        self.assertNotIn(nav, self.pages["index.html"])
        self.assertNotIn('class="nav"', self.pages["index.html"])

    def test_print_stylesheet_and_viewport(self) -> None:
        styles: list[str] = []
        for name, page in self.pages.items():
            match = re.search(r"<style>(.*?)</style>", page, re.S)
            self.assertIsNotNone(match, name)
            styles.append(match.group(1))
            self.assertIn(
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                page,
                name,
            )
        self.assertEqual(len(set(styles)), 1)
        css = styles[0]
        page_rule = re.search(r"@page\s*\{([^}]*)\}", css)
        self.assertIsNotNone(page_rule)
        self.assertRegex(page_rule.group(1), r"\bmargin\s*:")
        self.assertEqual(len(re.findall(r"@media print\b", css)), 1)
        print_match = re.search(r"@media print\s*\{((?:[^{}]|\{[^{}]*\})*)\}", css)
        self.assertIsNotNone(print_match)
        printed = print_match.group(1)
        self.assertIn('a[href^="https://"]::after', css)
        self.assertIn("attr(href)", printed)
        check_rule = re.search(r"\.check\s*\{([^}]*)\}", css)
        self.assertIsNotNone(check_rule)
        self.assertIn("break-inside: avoid", check_rule.group(1))
        box_rules = re.findall(r"\.box\s*\{([^}]*)\}", css)
        self.assertGreaterEqual(len(box_rules), 1)
        self.assertTrue(any("border: 1px solid #000" in rule for rule in box_rules))
        for rule in box_rules:
            self.assertNotIn("background", rule)
        self.assertRegex(printed, r"\.nav\s*\{[^}]*display\s*:\s*none")
        outside = css[: print_match.start()] + css[print_match.end() :]
        self.assertNotIn(".nav", outside)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)
        self.assertNotIn("@font-face", css)
        for extension in (".woff", ".woff2", ".ttf", ".otf", ".eot"):
            self.assertNotIn(extension, css)
        for prop, value in _css_declarations(css):
            if prop == "width":
                rem = re.fullmatch(r"(\d+(?:\.\d+)?)rem", value)
                if rem:
                    self.assertLessEqual(float(rem.group(1)), 40, value)
            if prop == "min-width":
                self.assertNotRegex(value, r"\d+(?:\.\d+)?px")

    def test_second_run_in_a_copy_is_byte_identical(self) -> None:
        scratch = Path(tempfile.mkdtemp(prefix="printable-idem-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        dest = scratch / "repo"
        shutil.copytree(
            ROOT,
            dest,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        script = dest / "scripts" / "make-printable.py"
        first = subprocess.run(
            [sys.executable, str(script)],
            cwd=dest,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        snapshot = _docs_bytes(dest)
        second = subprocess.run(
            [sys.executable, str(script)],
            cwd=dest,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(_docs_bytes(dest), snapshot)
        names = (
            "woocommerce.csv",
            "magento.csv",
            "bigcommerce.csv",
            "squarespace.csv",
            "wix.csv",
            "spot-checks.csv",
        )
        for name in names:
            copied = dest / "docs" / "tracker-import" / name
            self.assertIn(f"docs/tracker-import/{name}", snapshot)
            self.assertEqual(copied.read_bytes(), (dest / "tracker-import" / name).read_bytes())


def _docs_bytes(root: Path) -> dict[str, bytes]:
    docs = root / "docs"
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(docs.rglob("*"))
        if path.is_file()
    }


def _css_declarations(css: str):
    for block in re.findall(r"\{([^{}]*)\}", css):
        for part in block.split(";"):
            if ":" not in part:
                continue
            prop, value = part.split(":", 1)
            yield prop.strip(), value.strip()


class ConverterTests(unittest.TestCase):
    def test_line_with_lt_amp_and_backtick_is_escaped(self) -> None:
        rendered = mod.render_inline("a < b & `c`")
        self.assertEqual(rendered, "a &lt; b &amp; <code>c</code>")
        body = mod.render_markdown("escape.md", "a < b & `c`\n")
        self.assertIn("a &lt; b &amp; <code>c</code>", body)
        self.assertNotIn("<script", body)

    def test_plain_list_item_has_no_checkbox(self) -> None:
        body = mod.render_markdown("plain.md", "- a plain item\n")
        self.assertIn("<ul>\n<li>a plain item</li>\n</ul>", body)
        self.assertNotIn("checkbox", body)
        self.assertNotIn('class="check"', body)

    def test_brackets_that_are_not_links_stay_text(self) -> None:
        rendered = mod.render_inline(
            "A size is [RB]Size=Small. See [CHECKLIST.md](CHECKLIST.md) "
            "and [notes](test-catalogs/magento-basic)."
        )
        self.assertIn("[RB]Size=Small", rendered)
        self.assertIn('href="woocommerce-to-shopify.html"', rendered)
        self.assertIn(">CHECKLIST.md</a>", rendered)
        self.assertIn("notes", rendered)
        self.assertNotIn("test-catalogs/magento-basic", rendered.split("notes", 1)[-1][:40])
        self.assertNotIn('href="test-catalogs/magento-basic"', rendered)
        self.assertIn("notes", rendered)

    def test_checked_date_is_copied_only_when_the_source_states_one(self) -> None:
        self.assertIsNone(mod.checked_phrase("you have checked your export"))
        self.assertIsNone(mod.checked_phrase("leave Ignore blank values checked unless a blank"))
        self.assertEqual(
            mod.checked_phrase("Pages were checked on 2026-01-02."),
            "checked on 2026-01-02",
        )
        footer = mod.footer_html(
            "SAMPLE.md",
            "checked on 2026-01-02",
            "This project is independent and is not affiliated with Shopify or WooCommerce.",
            "licence",
        )
        self.assertIn("checked on 2026-01-02", footer)
        self.assertIn("<code>SAMPLE.md</code>", footer)
        undated = mod.footer_html("SAMPLE.md", None, "Affiliation.", "licence")
        self.assertNotIn("2026-01-02", undated)

    def test_unknown_construct_exits_nonzero_and_names_the_file_and_line(self) -> None:
        cases = (
            ("nested.md", "Intro\n\n- parent\n  - child\n", 4, "nested list"),
            ("table.md", "Para\n\n| a | b |\n", 3, "table"),
            ("image.md", "Look ![alt](pixel.png) here\n", 1, "image"),
            ("rule.md", "---\n", 1, "horizontal rule"),
            ("html.md", "Use <em>this</em> here\n", 1, "raw HTML"),
        )
        for filename, text, lineno, kind in cases:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as caught:
                    mod.render_markdown(filename, text)
            self.assertEqual(caught.exception.code, 1, filename)
            message = stderr.getvalue()
            self.assertIn(f"{filename}:{lineno}:", message)
            self.assertIn(kind, message)


if __name__ == "__main__":
    unittest.main()
