#!/usr/bin/env python3
"""README first screen, citation, check script, and licence."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOOL_URLS = (
    "https://catalog-signoff.pages.dev/guides/woocommerce-to-shopify-migration-checklist.html",
    "https://catalog-signoff.pages.dev/tools/readiness-scan.html",
    "https://catalog-signoff.pages.dev/tools/redirect-map.html",
)


class ReadmeTests(unittest.TestCase):
    def test_first_screen_answers_what_who_and_how_to_start(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        head, separator, _rest = readme.partition("## How to use it")
        self.assertTrue(separator)
        self.assertIn("CC BY 4.0", head)
        self.assertIn("small agencies, freelancers, and merchants doing the move themselves.", head)
        self.assertIn("This project is independent and is not affiliated with Shopify or WooCommerce.", head)
        self.assertIn("## Start in one minute", head)
        self.assertIn("test-catalogs/small-clean", head)
        self.assertIn("[CHECKLIST.md](CHECKLIST.md)", head)
        self.assertIn("## Related free tools", head)
        self.assertIn("# WooCommerce to Shopify catalog migration checklist", head)
        for url in TOOL_URLS:
            self.assertIn(url, head)
            self.assertNotIn("?", url)
        self.assertNotIn("utm_", readme)
        self.assertNotRegex(readme, r"(?i)affiliate link")
        self.assertNotIn("\n## Checks\n", readme)

    def test_checklist_count_matches_the_readme(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "CHECKLIST.md").read_text(encoding="utf-8")
        items = [line for line in checklist.splitlines() if line.startswith("- [ ]")]
        phases = [line for line in checklist.splitlines() if line.startswith("## ")]
        stated = re.search(r"(\d+) checks in (\d+) phases", readme)
        self.assertIsNotNone(stated)
        assert stated is not None
        self.assertEqual(len(items), int(stated.group(1)))
        self.assertEqual(len(phases), int(stated.group(2)))
        self.assertEqual(len(items), 40)
        self.assertEqual(len(phases), 7)

    def test_existing_use_and_licence_text_remains(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Tick the items for the phase you are in", readme)
        self.assertIn("The Markdown documents and CSV files are [CC BY 4.0]", readme)
        self.assertIn("The scripts and tests are MIT.", readme)
        self.assertIn("says which applies to what.", readme)
        self.assertIn("[Catalog Signoff](https://catalog-signoff.pages.dev)", readme)
        self.assertIn("compares your WooCommerce product CSV with your Shopify product CSV", readme)
        self.assertIn("A free preview shows example findings.", readme)


class CitationTests(unittest.TestCase):
    def test_citation_file_has_the_publish_fields(self) -> None:
        text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn("cff-version: 1.2.0", text)
        self.assertIn('title: "WooCommerce to Shopify catalog migration checklist"', text)
        self.assertIn('version: "1.0.0"', text)
        self.assertRegex(text, r'date-released: "\d{4}-\d{2}-\d{2}"')
        self.assertIn("license: CC-BY-4.0", text)
        self.assertIn("https://github.com/ericcheng0904-pixel/migration-checklist", text)
        self.assertIn("The scripts, tests, and the data files beside them are MIT.", text)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")


class CheckScriptTests(unittest.TestCase):
    def test_check_script_runs_the_tests_and_the_link_check(self) -> None:
        text = (ROOT / "scripts" / "check.sh").read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest", text)
        self.assertIn("scripts/check_markdown_links.py", text)


class LicenseTests(unittest.TestCase):
    def test_citation_file_is_covered_by_the_document_licence(self) -> None:
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("`CITATION.cff` is one of those documents.", text)
        self.assertIn("The Python files and the shell script under `scripts/` and `tests/`", text)
        self.assertIn("`scripts/known-redirects.txt`", text)
        self.assertIn("CC BY 4.0", text)
        self.assertIn("MIT License", text)


if __name__ == "__main__":
    unittest.main()
