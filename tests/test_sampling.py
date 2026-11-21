#!/usr/bin/env python3
"""Sampling table: exact chances, the fenced block, and the worksheet section.

The script file name has a hyphen, so this module loads it with importlib.
"""

from __future__ import annotations

import importlib.util
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "make-sampling-table.py"
SPOT = ROOT / "SPOT-CHECKS.md"
HEADING = "## Sampling worksheet"
CLOSING = (
    "The [Catalog Signoff guide to checking products after a Shopify migration]"
    "(https://catalog-signoff.pages.dev/guides/check-products-after-shopify-migration.html) "
    "works the same arithmetic and links a two-file comparison."
)
TASKS = (
    "- [ ] Write down the product count and variant count of both exports before you sample. "
    "Why it bites: N in the table is the row count you start from, and a wrong N gives a wrong chance.",
    "- [ ] Choose the sample size from the table before you open any row. "
    "Why it bites: choosing after seeing a few rows makes the sample depend on what you saw.",
    "- [ ] Pick sampled rows at random, for example with a spreadsheet random column, "
    "not the first rows or the best sellers. "
    "Why it bites: the table assumes every row is equally likely to be picked.",
    "- [ ] Check the rows you already know are risky (SKUs with a leading zero, "
    "products with several options) as extra rows, not as part of the random sample. "
    "Why it bites: they are not random, so they do not count toward the chances in the table.",
    "- [ ] Write down for each sampled row the SKU, the field you compared and the result. "
    "Why it bites: a later reader cannot tell what was looked at otherwise.",
    '- [ ] If the sample finds no wrong row, write "none found in n of N rows", not "no errors". '
    "Why it bites: the table shows how often a sample of that size misses errors that are there.",
)
DIGIT_MONTH_YEAR = (
    r"(?i)(?:\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b)"
    r"|(?:\b\d{4}-\d{2}-\d{2}\b)"
    r"|(?:\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4}\b)"
    r"|(?:\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b)"
)


def load_script():
    spec = importlib.util.spec_from_file_location("make_sampling_table", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["make_sampling_table"] = module
    spec.loader.exec_module(module)
    return module


def product_form(catalog_rows: int, wrong_rows: int, sample_rows: int) -> Fraction:
    """1 - prod((N-k-i)/(N-i) for i in range(n)), for N-k >= n."""
    missed = Fraction(1)
    for index in range(sample_rows):
        missed *= Fraction(catalog_rows - wrong_rows - index, catalog_rows - index)
    return 1 - missed


def fence_body(text: str, marker: str) -> str:
    """Body of the first text fence after marker, without using the script."""
    after = text.split(marker, 1)[1]
    rest = after.split("```text\n", 1)[1]
    body, _closing = rest.split("```", 1)
    return body


def example_sentence(module) -> str:
    """Read the N=1000, k=10, n=15 row aloud, including the complement when it sums."""
    at_value = module.chance(1000, 10, 15)
    at_text = module.format_percent(at_value)
    none_text = module.format_percent(1 - at_value)
    sentence = (
        "With 1,000 rows, 10 of them wrong and 15 rows sampled, "
        "the chance that the sample contains at least one wrong row is " + at_text
    )
    if Decimal(at_text[:-1]) + Decimal(none_text[:-1]) == Decimal("100.0"):
        sentence += ", and the chance it contains none is " + none_text
    sentence += "."
    return sentence


mod = load_script()


class SamplingMathTests(unittest.TestCase):
    def test_grid_constants(self) -> None:
        self.assertEqual(mod.CATALOG_SIZES, (200, 1000, 5000))
        self.assertEqual(mod.WRONG_COUNTS, (1, 5, 10, 25))
        self.assertEqual(mod.SAMPLE_SIZES, (15, 30, 50, 100))

    def test_product_form_matches_every_grid_cell(self) -> None:
        for catalog_rows in mod.CATALOG_SIZES:
            for wrong_rows in mod.WRONG_COUNTS:
                for sample_rows in mod.SAMPLE_SIZES:
                    with self.subTest(N=catalog_rows, k=wrong_rows, n=sample_rows):
                        self.assertEqual(
                            product_form(catalog_rows, wrong_rows, sample_rows),
                            mod.chance(catalog_rows, wrong_rows, sample_rows),
                        )

    def test_known_values(self) -> None:
        self.assertEqual(mod.chance(6, 2, 3), Fraction(4, 5))
        for catalog_rows in mod.CATALOG_SIZES:
            for sample_rows in mod.SAMPLE_SIZES:
                with self.subTest(N=catalog_rows, n=sample_rows):
                    self.assertEqual(
                        mod.chance(catalog_rows, 1, sample_rows),
                        Fraction(sample_rows, catalog_rows),
                    )
        self.assertEqual(mod.format_percent(mod.chance(1000, 10, 15)), "14.1%")
        certain_looking = mod.chance(200, 25, 100)
        self.assertLess(certain_looking, 1)
        self.assertEqual(mod.format_percent(certain_looking), ">99.9%")
        self.assertEqual(mod.format_percent(Fraction(1)), "100.0%")
        self.assertEqual(mod.chance(6, 6, 6), Fraction(1))
        self.assertEqual(mod.format_percent(mod.chance(6, 6, 6)), "100.0%")
        cells = mod.table_block().splitlines()
        row = next(line.split() for line in cells if line.split()[:2] == ["1000", "10"])
        self.assertEqual(row[2], "14.1%")

    def test_enumeration_matches_formula(self) -> None:
        catalog_rows, wrong_rows, sample_rows = 8, 3, 4
        wrong = set(range(wrong_rows))
        total = 0
        hits = 0
        for drawn in combinations(range(catalog_rows), sample_rows):
            total += 1
            if wrong.intersection(drawn):
                hits += 1
        self.assertEqual(Fraction(hits, total), mod.chance(catalog_rows, wrong_rows, sample_rows))

    def test_round_half_up_on_an_exact_second_decimal_five(self) -> None:
        # 12.25% ends in 5 in the second decimal. Half up is 12.3; half even is 12.2.
        exact = Fraction(1225, 10000)
        self.assertEqual(exact * 100, Fraction("12.25"))
        half_even = Decimal("12.25").quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN)
        self.assertEqual(format(half_even, ".1f"), "12.2")
        self.assertEqual(mod.format_percent(exact), "12.3%")
        self.assertEqual(mod.format_percent(Fraction(225, 10000)), "2.3%")
        self.assertEqual(mod.format_percent(Fraction(25, 10000)), "0.3%")
        self.assertEqual(mod.format_percent(Fraction(1414, 10000)), "14.1%")
        self.assertEqual(mod.format_percent(Fraction(1415, 10000)), "14.2%")
        self.assertEqual(mod.format_percent(Fraction(9994, 10000)), "99.9%")
        self.assertEqual(mod.format_percent(Fraction(1999, 2000)), ">99.9%")

    def test_value_error_when_counts_are_impossible(self) -> None:
        cases = (
            (10, 1, 11),
            (10, 11, 1),
            (5, 9, 6),
            (0, 1, 1),
            (-1, 1, 1),
            (10, 0, 1),
            (10, -2, 1),
            (10, 1, 0),
            (10, 1, -4),
        )
        for catalog_rows, wrong_rows, sample_rows in cases:
            with self.subTest(N=catalog_rows, k=wrong_rows, n=sample_rows):
                with self.assertRaises(ValueError):
                    mod.chance(catalog_rows, wrong_rows, sample_rows)
        self.assertEqual(mod.chance(5, 1, 5), Fraction(1))
        self.assertEqual(mod.chance(5, 5, 1), Fraction(1))


class SamplingCommandTests(unittest.TestCase):
    def _copy(self) -> Path:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        copy = directory / "SPOT-CHECKS.md"
        copy.write_bytes(SPOT.read_bytes())
        return copy

    def _run(self, args: list[str], path: Path) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = mod.main(args, spot_checks=path)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_print_and_check_on_the_committed_file(self) -> None:
        printed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(printed.returncode, 0, printed.stderr)
        self.assertEqual(printed.stdout, mod.table_block())
        self.assertEqual(printed.stderr, "")
        checked = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(checked.stdout, "")
        self.assertEqual(checked.stderr, "")

    def test_table_block_is_fixed_width(self) -> None:
        block = mod.table_block()
        self.assertTrue(block.endswith("\n"))
        self.assertFalse(block.endswith("\n\n"))
        self.assertNotIn("\r", block)
        lines = block.splitlines()
        self.assertEqual(len(lines), 1 + len(mod.CATALOG_SIZES) * len(mod.WRONG_COUNTS))
        self.assertEqual(lines[0].split(), ["N", "k", "n=15", "n=30", "n=50", "n=100"])
        width = len(lines[0])
        ends = None
        for line in lines:
            self.assertEqual(len(line), width)
            self.assertFalse(line.endswith(" "))
            positions = []
            index = 0
            while index < len(line):
                if line[index] == " ":
                    index += 1
                    continue
                end = index + 1
                while end < len(line) and line[end] != " ":
                    end += 1
                positions.append(end)
                index = end
            if ends is None:
                ends = positions
            self.assertEqual(positions, ends)
        self.assertEqual(len(ends), 6)

    def test_changed_digit_fails_check_and_write_restores_it(self) -> None:
        copy = self._copy()
        original = copy.read_bytes()
        text = original.decode("utf-8")
        self.assertIn("14.1%", text)
        changed = text.replace("14.1%", "14.2%", 1)
        self.assertNotEqual(changed, text)
        copy.write_bytes(changed.encode("utf-8"))
        code, stdout, stderr = self._run(["--check"], copy)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("SPOT-CHECKS.md", stderr)
        code, stdout, stderr = self._run(["--write"], copy)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        self.assertEqual(copy.read_bytes(), original)
        code, _stdout, stderr = self._run(["--write"], copy)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(copy.read_bytes(), original)

    def test_write_twice_on_the_repository_file_changes_nothing(self) -> None:
        before = SPOT.read_bytes()
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--write"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(SPOT.read_bytes(), before)

    def test_missing_generated_by_line_exits_1(self) -> None:
        copy = self._copy()
        original = copy.read_bytes()
        removed = original.decode("utf-8").replace(mod.MARKER + "\n", "", 1)
        self.assertNotIn(mod.MARKER, removed)
        copy.write_bytes(removed.encode("utf-8"))
        for flag in ("--check", "--write"):
            code, stdout, stderr = self._run([flag], copy)
            self.assertEqual(code, 1, flag)
            self.assertEqual(stdout, "")
            self.assertIn("SPOT-CHECKS.md", stderr)
            self.assertEqual(copy.read_bytes(), removed.encode("utf-8"))
        self.assertNotEqual(copy.read_bytes(), original)

    def test_missing_or_unclosed_fence_exits_1(self) -> None:
        text = SPOT.read_text(encoding="utf-8")
        before, body, after = mod.table_parts(text)
        self.assertTrue(before.endswith("```text\n"))
        self.assertTrue(after.startswith("```\n"))
        missing = before[: -len("```text\n")] + after[len("```\n") :]
        unclosed = before + body
        for label, contents in (("missing", missing), ("unclosed", unclosed)):
            copy = self._copy()
            copy.write_bytes(contents.encode("utf-8"))
            for flag in ("--check", "--write"):
                code, _stdout, stderr = self._run([flag], copy)
                self.assertEqual(code, 1, f"{label} {flag}")
                self.assertIn("SPOT-CHECKS.md", stderr)
                self.assertEqual(copy.read_bytes(), contents.encode("utf-8"))

    def test_unknown_argument_and_both_flags_exit_2(self) -> None:
        cases = (
            ["--bogus"],
            ["--help"],
            ["--check", "--write"],
            ["--write", "--check"],
            ["--write", "--check", "extra"],
        )
        for args in cases:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, args)
            self.assertIn("Usage", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_committed_block_equals_script_output(self) -> None:
        text = SPOT.read_text(encoding="utf-8")
        body = fence_body(text, mod.MARKER)
        self.assertEqual(body, mod.table_block())
        printed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd="/tmp",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(printed.returncode, 0, printed.stderr)
        self.assertEqual(printed.stdout, body)


class SamplingSectionTests(unittest.TestCase):
    def test_section_text(self) -> None:
        text = SPOT.read_text(encoding="utf-8")
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings[-1], HEADING)
        self.assertEqual(headings.count(HEADING), 1)
        section = text.split(HEADING, 1)[1]
        self.assertIn("assumed", section)
        self.assertIn("not measurements", section)
        self.assertNotIn("<", section)
        for line in section.splitlines():
            self.assertFalse(line.startswith("|"), line)
        self.assertIsNone(re.search(DIGIT_MONTH_YEAR, section))
        self.assertIn(mod.MARKER + "\n\n```text\n", text)
        paragraph = next(line for line in section.splitlines() if "1,000 rows" in line)
        at_text = mod.format_percent(mod.chance(1000, 10, 15))
        self.assertIn(at_text, paragraph)
        self.assertEqual(paragraph, example_sentence(mod))
        self.assertEqual(
            [line for line in section.splitlines() if line.startswith("- [ ] ")],
            list(TASKS),
        )
        nonempty = [line for line in text.splitlines() if line.strip()]
        self.assertEqual(nonempty[-1], CLOSING)
        self.assertNotIn("](", "\n".join(TASKS))

    def test_prefix_matches_origin_main(self) -> None:
        try:
            completed = subprocess.run(
                ["git", "show", "origin/main:SPOT-CHECKS.md"],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            raise unittest.SkipTest("git unavailable") from None
        if completed.returncode != 0:
            raise unittest.SkipTest("origin/main unavailable")
        origin = completed.stdout.decode("utf-8")
        current = SPOT.read_text(encoding="utf-8")
        origin_prefix = (origin.split(HEADING, 1)[0] if HEADING in origin else origin).rstrip("\n")
        current_prefix = current.split(HEADING, 1)[0].rstrip("\n")
        self.assertEqual(current_prefix, origin_prefix)


if __name__ == "__main__":
    unittest.main()
