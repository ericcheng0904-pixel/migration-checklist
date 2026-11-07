#!/usr/bin/env python3
"""Check the synthetic catalogs against the differences listed in the README."""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGS = ROOT / "test-catalogs"
README = CATALOGS / "README.md"

# First columns of the Shopify sample template checked on 2026-10-24.
SAMPLE_HEADER_PREFIX = (
    "Title",
    "URL handle",
    "Description",
    "Vendor",
    "Product category",
    "Type",
    "Tags",
    "Published on online store",
    "Status",
    "SKU",
    "Variant Barcodes",
    "Option1 name",
    "Option1 value",
    "Option1 Linked To",
    "Option2 name",
    "Option2 value",
    "Option2 Linked To",
    "Option3 name",
    "Option3 value",
    "Option3 Linked To",
    "Price",
    "Compare-at price",
)


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AssertionError(f"{path} has no header")
        return list(reader.fieldnames), list(reader)


def skus(rows: list[dict[str, str]]) -> set[str]:
    return {row["SKU"] for row in rows if row["SKU"]}


def shop_by_sku(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["SKU"]:
            found[row["SKU"]] = row
    return found


def grams(kilograms: str) -> str:
    return str(int((Decimal(kilograms) * Decimal("1000")).to_integral_value()))


class RegenerationTests(unittest.TestCase):
    def test_script_regenerates_csvs_byte_for_byte(self) -> None:
        paths = sorted(CATALOGS.glob("*/*.csv"))
        self.assertEqual(len(paths), 12)
        before = {path: path.read_bytes() for path in paths}
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "make-test-catalogs.py")],
            check=True,
            cwd=ROOT,
        )
        after = {path: path.read_bytes() for path in paths}
        self.assertEqual(before, after)

    def test_csvs_are_utf8_lf_without_bom(self) -> None:
        for path in CATALOGS.glob("*/*.csv"):
            data = path.read_bytes()
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"), path.name)
            self.assertNotIn(b"\r", data, path.name)
            self.assertTrue(data.endswith(b"\n"), path.name)


class FormatTests(unittest.TestCase):
    def test_shopify_headers_follow_the_sample_template(self) -> None:
        for path in CATALOGS.glob("*/shopify.csv"):
            headers, _rows = load(path)
            self.assertEqual(tuple(headers[: len(SAMPLE_HEADER_PREFIX)]), SAMPLE_HEADER_PREFIX, path.parent.name)
            self.assertIn("Weight value (grams)", headers)
            self.assertIn("Product image URL", headers)

    def test_woocommerce_headers_follow_the_builtin_schema(self) -> None:
        for path in CATALOGS.glob("*/woocommerce.csv"):
            headers, _rows = load(path)
            self.assertEqual(headers[0], "ID")
            self.assertIn("GTIN, UPC, EAN, or ISBN", headers)
            self.assertIn("Weight (kg)", headers)
            self.assertIn("Length (cm)", headers)
            self.assertIn("Sale price", headers)
            self.assertIn("Regular price", headers)
            self.assertIn("Visibility in catalog", headers)


class SmallCleanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.woo_headers, self.woo = load(CATALOGS / "small-clean" / "woocommerce.csv")
        self.shop_headers, self.shop = load(CATALOGS / "small-clean" / "shopify.csv")

    def test_readme_says_there_are_no_planted_differences(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("small-clean", text)
        self.assertIn("No planted differences", text)

    def test_sellable_skus_match_and_prices_status_images_follow_the_mapping(self) -> None:
        woo_by_sku = {row["SKU"]: row for row in self.woo}
        shop = shop_by_sku(self.shop)
        self.assertEqual(set(woo_by_sku), set(shop))
        handles = []
        for sku, source in woo_by_sku.items():
            target = shop[sku]
            sale = source["Sale price"]
            if sale:
                self.assertEqual(target["Price"], sale, sku)
                self.assertEqual(target["Compare-at price"], source["Regular price"], sku)
            else:
                self.assertEqual(target["Price"], source["Regular price"], sku)
                self.assertEqual(target["Compare-at price"], "", sku)
            if source["Published"] == "1":
                self.assertEqual(target["Status"], "active", sku)
                self.assertEqual(target["Published on online store"], "true", sku)
            elif source["Published"] == "-1":
                self.assertEqual(target["Status"], "draft", sku)
                self.assertEqual(target["Published on online store"], "false", sku)
            else:
                self.fail(f"unexpected Published value for {sku}")
            if source["Stock"]:
                self.assertEqual(target["Inventory tracker"], "shopify", sku)
                self.assertEqual(target["Inventory quantity"], source["Stock"], sku)
            else:
                self.assertEqual(target["Inventory tracker"], "", sku)
                self.assertEqual(target["Inventory quantity"], "", sku)
            if source["Weight (kg)"]:
                self.assertEqual(target["Weight value (grams)"], grams(source["Weight (kg)"]), sku)
            self.assertEqual(target["Option1 name"], "Title", sku)
            self.assertEqual(target["Option1 value"], "Default Title", sku)
            self.assertEqual(target["Title"], source["Name"], sku)
            handles.append(target["URL handle"])
            woo_images = [part.strip() for part in source["Images"].split(",") if part.strip()]
            shop_images = [
                row["Product image URL"]
                for row in self.shop
                if row["URL handle"] == target["URL handle"] and row["Product image URL"]
            ]
            self.assertEqual(shop_images, woo_images, sku)
        self.assertEqual(len(handles), len(set(handles)))

    def test_care_note_metafield_matches(self) -> None:
        candle = shop_by_sku(self.shop)["CANDLE-PEBBLE"]
        source = next(row for row in self.woo if row["SKU"] == "CANDLE-PEBBLE")
        self.assertEqual(source["Meta: care_note"], "Burn on a flat surface.")
        self.assertEqual(candle["Care note (product.metafields.custom.care_note)"], "Burn on a flat surface.")

    def test_no_duplicate_handles_and_no_extra_shopify_skus(self) -> None:
        titles_by_handle: dict[str, set[str]] = {}
        for row in self.shop:
            if row["Title"]:
                titles_by_handle.setdefault(row["URL handle"], set()).add(row["Title"])
        for handle, titles in titles_by_handle.items():
            self.assertEqual(len(titles), 1, handle)


class CommonMistakesTests(unittest.TestCase):
    def setUp(self) -> None:
        _woo_headers, self.woo = load(CATALOGS / "common-mistakes" / "woocommerce.csv")
        _shop_headers, self.shop = load(CATALOGS / "common-mistakes" / "shopify.csv")
        self.woo_by_sku = {row["SKU"]: row for row in self.woo}
        self.shop_skus = shop_by_sku(self.shop)

    def test_readme_lists_each_planted_difference(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "missing-variant",
            "TOTE-L",
            "sale-price-mapped-to-price",
            "LANTERN-01",
            "dropped-leading-zero",
            "01482",
            "1482",
            "draft-published",
            "TRAY-DRAFT",
            "lost-image",
            "BOWL-MOSS",
            "moss-bowl-side.jpg",
            "duplicated-handle",
            "pine-sample-soap",
            "SOAP-PINE",
            "OIL-PINE",
        ):
            self.assertIn(token, text)

    def test_missing_variant(self) -> None:
        self.assertIn("TOTE-L", self.woo_by_sku)
        self.assertNotIn("TOTE-L", self.shop_skus)
        self.assertIn("TOTE-S", self.shop_skus)
        self.assertIn("TOTE-M", self.shop_skus)
        self.assertEqual(self.woo_by_sku["TOTE-L"]["Attribute 1 value(s)"], "Large")

    def test_sale_price_mapped_to_price(self) -> None:
        source = self.woo_by_sku["LANTERN-01"]
        target = self.shop_skus["LANTERN-01"]
        self.assertEqual(source["Regular price"], "42.00")
        self.assertEqual(source["Sale price"], "36.00")
        self.assertEqual(target["Price"], "36.00")
        self.assertEqual(target["Compare-at price"], "")

    def test_dropped_leading_zero(self) -> None:
        self.assertIn("01482", self.woo_by_sku)
        self.assertNotIn("01482", self.shop_skus)
        self.assertIn("1482", self.shop_skus)
        self.assertEqual(self.shop_skus["1482"]["Title"], "Sample Tag Ribbon")
        self.assertNotIn("1482", self.woo_by_sku)

    def test_draft_published(self) -> None:
        source = self.woo_by_sku["TRAY-DRAFT"]
        target = self.shop_skus["TRAY-DRAFT"]
        self.assertEqual(source["Published"], "-1")
        self.assertEqual(target["Status"], "active")
        self.assertEqual(target["Published on online store"], "true")

    def test_lost_image(self) -> None:
        source = self.woo_by_sku["BOWL-MOSS"]
        images = [part.strip() for part in source["Images"].split(",") if part.strip()]
        self.assertEqual(len(images), 2)
        self.assertTrue(images[1].endswith("moss-bowl-side.jpg"))
        handle = self.shop_skus["BOWL-MOSS"]["URL handle"]
        shop_images = [
            row["Product image URL"]
            for row in self.shop
            if row["URL handle"] == handle and row["Product image URL"]
        ]
        self.assertEqual(shop_images, [images[0]])

    def test_duplicated_handle(self) -> None:
        soap = self.shop_skus["SOAP-PINE"]
        oil = self.shop_skus["OIL-PINE"]
        self.assertNotEqual(self.woo_by_sku["SOAP-PINE"]["Name"], self.woo_by_sku["OIL-PINE"]["Name"])
        self.assertEqual(soap["URL handle"], "pine-sample-soap")
        self.assertEqual(oil["URL handle"], "pine-sample-soap")
        self.assertEqual(soap["Title"], "Pine Sample Soap")
        self.assertEqual(oil["Title"], "Pine Sample Oil")

    def test_control_product_still_matches(self) -> None:
        source = self.woo_by_sku["SPOON-CEDAR"]
        target = self.shop_skus["SPOON-CEDAR"]
        self.assertEqual(target["Price"], source["Regular price"])
        self.assertEqual(target["Compare-at price"], "")
        self.assertEqual(target["Status"], "active")
        self.assertEqual(target["SKU"], "SPOON-CEDAR")


class VariableProductTests(unittest.TestCase):
    def setUp(self) -> None:
        _woo_headers, self.woo = load(CATALOGS / "variable-products" / "woocommerce.csv")
        _shop_headers, self.shop = load(CATALOGS / "variable-products" / "shopify.csv")
        self.woo_by_sku = {row["SKU"]: row for row in self.woo}
        self.shop_skus = shop_by_sku(self.shop)

    def test_readme_lists_each_planted_difference(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "missing-apron-variant",
            "APRON-L-INK",
            "fourth-option-dropped",
            "Pocket",
            "PACK-S-MOSS-CLIP-N",
            "MUG-8OZ",
            "Material",
        ):
            self.assertIn(token, text)

    def test_mug_options_match_and_material_is_a_metafield(self) -> None:
        parent = self.woo_by_sku["MUG-CEDAR"]
        self.assertEqual(parent["Type"], "variable")
        self.assertEqual(parent["Attribute 1 name"], "Size")
        self.assertEqual(parent["Attribute 2 name"], "Material")
        self.assertEqual(parent["Attribute 2 value(s)"], "Stone")
        eight = self.shop_skus["MUG-8OZ"]
        twelve = self.shop_skus["MUG-12OZ"]
        self.assertEqual(eight["Option1 name"], "Size")
        self.assertEqual(eight["Option1 value"], "8 oz")
        self.assertEqual(twelve["Option1 value"], "12 oz")
        self.assertEqual(eight["Option2 name"], "")
        self.assertEqual(eight[ "Material (product.metafields.custom.material)" ], "Stone")
        self.assertEqual(eight["Price"], "16.00")
        self.assertEqual(eight["Compare-at price"], "")
        self.assertEqual(eight["Weight value (grams)"], "300")
        self.assertEqual(self.woo_by_sku["MUG-8OZ"]["Attribute 2 value(s)"], "")

    def test_missing_apron_variant(self) -> None:
        self.assertEqual(self.woo_by_sku["APRON-L-INK"]["Attribute 1 value(s)"], "Large")
        self.assertEqual(self.woo_by_sku["APRON-L-INK"]["Attribute 2 value(s)"], "Ink")
        self.assertNotIn("APRON-L-INK", self.shop_skus)
        for sku, size, color in (
            ("APRON-S-SAND", "Small", "Sand"),
            ("APRON-S-INK", "Small", "Ink"),
            ("APRON-L-SAND", "Large", "Sand"),
        ):
            row = self.shop_skus[sku]
            self.assertEqual(row["Option1 value"], size, sku)
            self.assertEqual(row["Option2 value"], color, sku)

    def test_fourth_option_dropped(self) -> None:
        parent = self.woo_by_sku["PACK-TRAIL"]
        self.assertEqual(
            [parent[f"Attribute {index} name"] for index in range(1, 5)],
            ["Size", "Color", "Strap", "Pocket"],
        )
        woo_pack = {sku for sku in self.woo_by_sku if sku.startswith("PACK-") and sku != "PACK-TRAIL"}
        shop_pack = {sku for sku in self.shop_skus if sku.startswith("PACK-")}
        self.assertEqual(len(woo_pack), 16)
        self.assertEqual(shop_pack, {sku for sku in woo_pack if sku.endswith("-Y")})
        self.assertIn("PACK-S-MOSS-CLIP-N", woo_pack)
        self.assertNotIn("PACK-S-MOSS-CLIP-N", shop_pack)
        first = self.shop_skus["PACK-S-MOSS-CLIP-Y"]
        self.assertEqual(first["Option1 name"], "Size")
        self.assertEqual(first["Option2 name"], "Color")
        self.assertEqual(first["Option3 name"], "Strap")
        self.assertNotIn("Pocket", (first["Option1 name"], first["Option2 name"], first["Option3 name"]))
        option_names = {
            row[column]
            for row in self.shop
            for column in ("Option1 name", "Option2 name", "Option3 name")
            if row["URL handle"] == "trail-sample-pack"
        }
        self.assertNotIn("Pocket", option_names)


class MagentoBasicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.magento_headers, self.magento = load(CATALOGS / "magento-basic" / "magento.csv")
        self.shop_headers, self.shop = load(CATALOGS / "magento-basic" / "shopify.csv")
        self.by_sku = {}
        for row in self.magento:
            self.by_sku.setdefault(row["sku"], []).append(row)
        self.shop_skus = shop_by_sku(self.shop)

    def test_readme_describes_the_pair(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "magento-basic",
            "WICK-LANTERN",
            "WICK-S",
            "WICK-L",
            "Wick Cove Lantern",
            "Not Visible Individually",
            "special_price",
            "2026-11-01",
            "wick-lantern-side.jpg",
            "Choose Size:",
            "Check in your own export",
        ):
            self.assertIn(token, text)

    def test_configurable_parent_is_not_a_shopify_variant(self) -> None:
        parent = self.by_sku["WICK-LANTERN"][0]
        self.assertEqual(parent["product_type"], "configurable")
        self.assertEqual(parent["visibility"], "Catalog, Search")
        self.assertEqual(parent["product_online"], "1")
        self.assertEqual(parent["price"], "40.00")
        self.assertEqual(
            parent["configurable_variations"],
            "sku=WICK-S,size=Small|sku=WICK-L,size=Large",
        )
        self.assertEqual(parent["configurable_variation_labels"], "Choose Size:")
        self.assertNotIn("WICK-LANTERN", self.shop_skus)
        self.assertEqual(set(self.shop_skus), {"WICK-S", "WICK-L"})

    def test_variations_map_size_price_weight_and_special_price(self) -> None:
        small = next(row for row in self.by_sku["WICK-S"] if row["product_type"] == "simple")
        large = next(row for row in self.by_sku["WICK-L"] if row["product_type"] == "simple")
        self.assertEqual(small["visibility"], "Not Visible Individually")
        self.assertEqual(large["visibility"], "Not Visible Individually")
        self.assertEqual(small["special_price"], "30.00")
        self.assertEqual(small["price"], "36.00")
        self.assertEqual(small["special_price_from_date"], "2026-11-01")
        self.assertEqual(small["special_price_to_date"], "2026-11-30")
        self.assertEqual(large["special_price"], "")
        shop_small = self.shop_skus["WICK-S"]
        shop_large = self.shop_skus["WICK-L"]
        self.assertEqual(shop_small["Title"], "Wick Sample Lantern")
        self.assertEqual(shop_small["URL handle"], "wick-sample-lantern")
        self.assertEqual(shop_large["URL handle"], "wick-sample-lantern")
        self.assertEqual(shop_small["Option1 name"], "Size")
        self.assertEqual(shop_small["Option1 value"], "Small")
        self.assertEqual(shop_large["Option1 value"], "Large")
        self.assertEqual(shop_large["Option1 name"], "")
        self.assertEqual(shop_small["Price"], "30.00")
        self.assertEqual(shop_small["Compare-at price"], "36.00")
        self.assertEqual(shop_large["Price"], "42.00")
        self.assertEqual(shop_large["Compare-at price"], "")
        self.assertEqual(shop_small["Weight value (grams)"], "520")
        self.assertEqual(shop_large["Weight value (grams)"], "680")
        self.assertEqual(shop_small["Inventory quantity"], "6")
        self.assertEqual(shop_large["Inventory quantity"], "4")
        self.assertEqual(shop_small["Status"], "active")
        self.assertEqual(shop_small["Published on online store"], "true")
        self.assertEqual(shop_small["Finish (product.metafields.custom.finish)"], "Brass")
        self.assertNotIn("special_price_from_date", self.shop_headers)
        titles = {row["Title"] for row in self.shop if row["Title"]}
        self.assertEqual(titles, {"Wick Sample Lantern"})

    def test_store_view_row_is_not_a_second_product(self) -> None:
        rows = self.by_sku["WICK-LANTERN"]
        self.assertEqual(len(rows), 2)
        cove = next(row for row in rows if row["store_view_code"] == "cove")
        self.assertEqual(cove["name"], "Wick Cove Lantern")
        self.assertEqual(cove["product_type"], "")
        self.assertNotIn("Wick Cove Lantern", [row["Title"] for row in self.shop])

    def test_image_roles_become_distinct_public_urls(self) -> None:
        parent = self.by_sku["WICK-LANTERN"][0]
        self.assertEqual(parent["base_image"], parent["small_image"])
        self.assertNotEqual(parent["base_image"], parent["thumbnail_image"])
        self.assertTrue(parent["base_image"].startswith("/w/i/"))
        handle = "wick-sample-lantern"
        product_images = [
            row["Product image URL"]
            for row in self.shop
            if row["URL handle"] == handle and row["Product image URL"]
        ]
        self.assertEqual(
            product_images,
            [
                "https://cdn.example.test/sample-harbor/wick-lantern.jpg",
                "https://cdn.example.test/sample-harbor/wick-lantern-mark.jpg",
                "https://cdn.example.test/sample-harbor/wick-lantern-side.jpg",
            ],
        )
        self.assertEqual(
            self.shop_skus["WICK-S"]["Variant image URL"],
            "https://cdn.example.test/sample-harbor/wick-lantern-small.jpg",
        )
        self.assertEqual(
            self.shop_skus["WICK-L"]["Variant image URL"],
            "https://cdn.example.test/sample-harbor/wick-lantern-large.jpg",
        )
        self.assertEqual(self.shop_skus["WICK-S"]["Image alt text"], "")


class BigCommerceBasicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bc_headers, self.bc = load(CATALOGS / "bigcommerce-basic" / "bigcommerce.csv")
        self.shop_headers, self.shop = load(CATALOGS / "bigcommerce-basic" / "shopify.csv")
        self.by_type: dict[str, list[dict[str, str]]] = {}
        for row in self.bc:
            self.by_type.setdefault(row["Item Type"], []).append(row)
        self.shop_skus = shop_by_sku(self.shop)

    def test_readme_describes_the_pair(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "bigcommerce-basic",
            "PITCHER-NETTLE",
            "PITCHER-S",
            "PITCHER-L",
            "[RB]Size=Small",
            "[FIXED]36",
            "Nettle Sample Pitcher",
            "nettle-sample-pitcher",
            "retail-copied-into-compare-at",
            "Product Image File - 1",
            "by option",
            "Check in your own export",
            "5102",
        ):
            self.assertIn(token, text)

    def test_product_row_is_not_a_shopify_variant(self) -> None:
        product = self.by_type["Product"][0]
        self.assertEqual(product["Product Code/SKU"], "PITCHER-NETTLE")
        self.assertEqual(product["Product Name"], "Nettle Sample Pitcher")
        self.assertEqual(product["Price"], "32.00")
        self.assertEqual(product["Retail Price"], "44.00")
        self.assertEqual(product["Sale Price"], "")
        self.assertEqual(product["Product URL"], "/nettle-sample-pitcher/")
        self.assertEqual(product["Redirect Old URL?"], "N")
        self.assertEqual(product["Track Inventory"], "by option")
        self.assertNotIn("\u00a0", product["Track Inventory"])
        self.assertEqual(product["Product Visible?"], "Y")
        self.assertEqual(product["Allow Purchases?"], "Y")
        self.assertNotIn("PITCHER-NETTLE", self.shop_skus)
        self.assertEqual(set(self.shop_skus), {"PITCHER-S", "PITCHER-L"})
        self.assertNotIn("Option Set", self.bc_headers)

    def test_sku_and_rule_rows_map_price_weight_and_image(self) -> None:
        small = next(row for row in self.by_type["SKU"] if row["Product Code/SKU"] == "PITCHER-S")
        large = next(row for row in self.by_type["SKU"] if row["Product Code/SKU"] == "PITCHER-L")
        rule = self.by_type["Rule"][0]
        self.assertEqual(small["Product Name"], "[RB]Size=Small")
        self.assertEqual(large["Product Name"], "[RB]Size=Large")
        self.assertEqual(small["Price"], "32.00")
        self.assertEqual(large["Price"], "36.00")
        self.assertEqual(small["Current Stock Level"], "6")
        self.assertEqual(large["Current Stock Level"], "4")
        self.assertEqual(rule["Product Name"], "")
        self.assertEqual(rule["Product Code/SKU"], "PITCHER-L")
        self.assertEqual(rule["Price"], "[FIXED]36")
        self.assertEqual(rule["Product Weight"], "[FIXED]0.720")
        self.assertEqual(small["Product ID"], "5102")
        self.assertEqual(large["Product ID"], "5103")
        self.assertEqual(rule["Product ID"], "5104")
        shop_small = self.shop_skus["PITCHER-S"]
        shop_large = self.shop_skus["PITCHER-L"]
        self.assertEqual(shop_small["Title"], "Nettle Sample Pitcher")
        self.assertEqual(shop_small["URL handle"], "nettle-sample-pitcher")
        self.assertEqual(shop_large["URL handle"], "nettle-sample-pitcher")
        self.assertEqual(shop_small["Option1 name"], "Size")
        self.assertEqual(shop_small["Option1 value"], "Small")
        self.assertEqual(shop_large["Option1 value"], "Large")
        self.assertEqual(shop_large["Option1 name"], "")
        self.assertEqual(shop_small["Price"], "32.00")
        self.assertEqual(shop_large["Price"], "36.00")
        self.assertEqual(shop_small["Compare-at price"], "44.00")
        self.assertEqual(shop_large["Compare-at price"], "44.00")
        self.assertEqual(shop_small["Cost per item"], "12.00")
        self.assertEqual(shop_small["Weight value (grams)"], "520")
        self.assertEqual(shop_large["Weight value (grams)"], "720")
        self.assertEqual(shop_small["Inventory quantity"], "6")
        self.assertEqual(shop_large["Inventory quantity"], "4")
        self.assertEqual(shop_small["Continue selling when out of stock"], "deny")
        self.assertEqual(shop_small["Status"], "active")
        self.assertEqual(shop_small["Published on online store"], "true")
        self.assertEqual(shop_small["Image alt text"], "Nettle pitcher front")
        self.assertEqual(
            shop_small["Product image URL"],
            "https://cdn.example.test/sample-harbor/nettle-pitcher.jpg",
        )
        self.assertEqual(
            shop_large["Variant image URL"],
            "https://cdn.example.test/sample-harbor/nettle-pitcher-large.jpg",
        )
        self.assertNotIn("Sale Price", self.shop_headers)
        titles = {row["Title"] for row in self.shop if row["Title"]}
        self.assertEqual(titles, {"Nettle Sample Pitcher"})


class SquarespaceBasicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sq_headers, self.sq = load(CATALOGS / "squarespace-basic" / "squarespace.csv")
        self.shop_headers, self.shop = load(CATALOGS / "squarespace-basic" / "shopify.csv")
        self.by_sku = {row["SKU"]: row for row in self.sq if row["SKU"]}
        self.shop_skus = shop_by_sku(self.shop)

    def test_readme_describes_the_pair(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "squarespace-basic",
            "JAR-S",
            "JAR-L",
            "LADLE-FERN",
            "CLOTH-MIST",
            "Brine Sample Jar",
            "brine-sample-jar",
            "sale-price-ignored-when-on-sale-is-no",
            "unlimited-stock-not-tracked",
            "Hosted Image URLs",
            "Product ID [Non Editable]",
            "Check in your own export",
            "8801",
            "Unlimited",
            "Default Title",
        ):
            self.assertIn(token, text)

    def test_rows_follow_the_example_shape(self) -> None:
        self.assertEqual(
            self.sq_headers,
            [
                "Product ID [Non Editable]",
                "Variant ID [Non Editable]",
                "Product Type [Non Editable]",
                "Product Page",
                "Product URL",
                "Title",
                "Description",
                "SKU",
                "Option Name 1",
                "Option Value 1",
                "Option Name 2",
                "Option Value 2",
                "Option Name 3",
                "Option Value 3",
                "Price",
                "Sale Price",
                "On Sale",
                "Stock",
                "Categories",
                "Tags",
                "Weight",
                "Length",
                "Width",
                "Height",
                "Visible",
                "Hosted Image URLs",
            ],
        )
        self.assertNotIn("GTIN", self.sq_headers)
        self.assertNotIn("MPN", self.sq_headers)
        jar = self.by_sku["JAR-S"]
        large = self.by_sku["JAR-L"]
        self.assertEqual(jar["Product ID [Non Editable]"], "8801")
        self.assertEqual(large["Product ID [Non Editable]"], "")
        self.assertEqual(jar["Variant ID [Non Editable]"], "8811")
        self.assertEqual(large["Variant ID [Non Editable]"], "8812")
        self.assertEqual(jar["Product Type [Non Editable]"], "PHYSICAL")
        self.assertEqual(large["Product Type [Non Editable]"], "")
        self.assertEqual(jar["Product URL"], "brine-sample-jar")
        self.assertEqual(large["Product URL"], "")
        self.assertEqual(jar["Option Name 1"], "Size")
        self.assertEqual(jar["Option Value 1"], "Small")
        self.assertEqual(large["Option Name 1"], "Size")
        self.assertEqual(large["Option Value 1"], "Large")
        self.assertEqual(jar["Visible"], "Yes")
        self.assertEqual(large["Visible"], "")
        self.assertEqual(jar["On Sale"], "Yes")
        self.assertEqual(jar["Sale Price"], "14.00")
        self.assertEqual(large["On Sale"], "No")
        self.assertEqual(large["Price"], "22.00")
        self.assertEqual(large["Sale Price"], "16.00")
        self.assertIn(" ", jar["Hosted Image URLs"])
        self.assertEqual(large["Hosted Image URLs"], "")
        self.assertEqual(jar["Categories"], "Jars")
        self.assertEqual(large["Categories"], "")
        self.assertNotEqual(jar["Weight"], "")
        ladle = self.by_sku["LADLE-FERN"]
        cloth = self.by_sku["CLOTH-MIST"]
        self.assertEqual(ladle["On Sale"], "No")
        self.assertEqual(ladle["Sale Price"], "9.00")
        self.assertEqual(ladle["Price"], "12.00")
        self.assertEqual(cloth["Stock"], "Unlimited")
        self.assertEqual(cloth["Sale Price"], "")
        self.assertEqual(cloth["On Sale"], "No")
        self.assertEqual(set(self.by_sku), {"JAR-S", "JAR-L", "LADLE-FERN", "CLOTH-MIST"})

    def test_shopify_mapping_keeps_sale_stock_and_images(self) -> None:
        self.assertEqual(set(self.shop_skus), {"JAR-S", "JAR-L", "LADLE-FERN", "CLOTH-MIST"})
        small = self.shop_skus["JAR-S"]
        large = self.shop_skus["JAR-L"]
        ladle = self.shop_skus["LADLE-FERN"]
        cloth = self.shop_skus["CLOTH-MIST"]
        self.assertEqual(small["Title"], "Brine Sample Jar")
        self.assertEqual(small["URL handle"], "brine-sample-jar")
        self.assertEqual(large["URL handle"], "brine-sample-jar")
        self.assertEqual(small["Price"], "14.00")
        self.assertEqual(small["Compare-at price"], "18.00")
        self.assertEqual(large["Price"], "22.00")
        self.assertEqual(large["Compare-at price"], "")
        self.assertEqual(large["Option1 name"], "")
        self.assertEqual(large["Option1 value"], "Large")
        self.assertEqual(small["Option1 name"], "Size")
        self.assertEqual(small["Inventory tracker"], "shopify")
        self.assertEqual(small["Inventory quantity"], "6")
        self.assertEqual(ladle["Price"], "12.00")
        self.assertEqual(ladle["Compare-at price"], "")
        self.assertEqual(ladle["Option1 name"], "Default Title")
        self.assertEqual(ladle["Option1 value"], "Default Title")
        self.assertEqual(cloth["Inventory tracker"], "")
        self.assertEqual(cloth["Inventory quantity"], "")
        self.assertEqual(cloth["Continue selling when out of stock"], "")
        self.assertEqual(cloth["Price"], "28.00")
        self.assertEqual(small["Weight value (grams)"], "")
        self.assertEqual(large["Weight value (grams)"], "")
        self.assertEqual(small["Status"], "active")
        self.assertEqual(small["Published on online store"], "true")
        self.assertEqual(small["Image alt text"], "")
        self.assertEqual(small["Variant image URL"], "")
        self.assertEqual(large["Variant image URL"], "")
        self.assertEqual(small["Type"], "Jars")
        self.assertNotIn("Collection", self.shop_headers)
        images = [row["Product image URL"] for row in self.shop if row["URL handle"] == "brine-sample-jar" and row["Product image URL"]]
        self.assertEqual(
            images,
            [
                "https://cdn.example.test/sample-harbor/brine-jar.jpg",
                "https://cdn.example.test/sample-harbor/brine-jar-side.jpg",
            ],
        )
        side = next(row for row in self.shop if row["Product image URL"].endswith("brine-jar-side.jpg"))
        self.assertEqual(side["SKU"], "")
        self.assertEqual(side["Image position"], "2")
        self.assertEqual(side["Image alt text"], "")


if __name__ == "__main__":
    unittest.main()
