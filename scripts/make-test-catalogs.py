#!/usr/bin/env python3
"""Write the synthetic product CSV pairs.

Run from anywhere:

    python3 scripts/make-test-catalogs.py

The CSV files under test-catalogs/ are overwritten. test-catalogs/README.md
is not generated. Output is UTF-8, LF line endings, no BOM, so a second run
matches the first byte for byte.

WooCommerce headers follow the built-in product CSV schema. The weight and
dimension headers use kg and cm, which is what the exporter writes when those
are the store units. Shopify headers follow the sample product template linked
from the Shopify Help Center (product_template.csv, checked 2026-10-24), plus
one product-metafield column on the catalogs that use one.

The Magento file uses a subset of the columns in the Adobe Commerce product
data attributes reference (checked 2026-10-27). It is one configurable product,
its simple variations, and one store-view row. A full export has more columns.

The BigCommerce file uses a subset of the legacy Bulk Edit columns (checked
2026-10-27). It is one product, two SKU rows, and one Rule row. A full Bulk
Edit export has more columns, including Option Set.

The Squarespace file uses the 26 columns of the official example (checked
2026-10-27). It is one product with an option row, one product whose sale
price is filled while On Sale is No, and one product with Unlimited stock.
The export article says a real export adds a column for pages and does not name it. Only the move-between-sites tables list GTIN and MPN.

The Wix file uses the 50 columns of the official older-catalog template
(downloaded 2026-10-29 and again 2026-11-07). It is one product with Variant
rows, one product with a PERCENT discount, and one product with an AMOUNT
discount. The new catalog's columns are not in this file.
"""

from __future__ import annotations

import csv
import itertools
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test-catalogs"
VENDOR = "Sample Harbor Goods"

# Header row of
# https://help.shopify.com/cdn/shopifycloud/product-knowledge/production/csv/product_template.csv
# as downloaded on 2026-10-24. A custom metafield column is appended only when
# that catalog uses one.
SHOPIFY_COLUMNS = [
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
    "Cost per item",
    "Charge tax",
    "Tax code",
    "Unit price total measure",
    "Unit price total measure unit",
    "Unit price base measure",
    "Unit price base measure unit",
    "Inventory tracker",
    "Inventory quantity",
    "Continue selling when out of stock",
    "Weight value (grams)",
    "Weight unit for display",
    "Requires shipping",
    "Fulfillment service",
    "Product image URL",
    "Image position",
    "Image alt text",
    "Variant image URL",
    "Gift card",
    "SEO title",
    "SEO description",
    "Color (product.metafields.shopify.color-pattern)",
    "Google Shopping / Google product category",
    "Google Shopping / Gender",
    "Google Shopping / Age group",
    "Google Shopping / Manufacturer part number (MPN)",
    "Google Shopping / Ad group name",
    "Google Shopping / Ads labels",
    "Google Shopping / Condition",
    "Google Shopping / Custom product",
    "Google Shopping / Custom label 0",
    "Google Shopping / Custom label 1",
    "Google Shopping / Custom label 2",
    "Google Shopping / Custom label 3",
    "Google Shopping / Custom label 4",
    "Packed product length",
    "Packed product width",
    "Packed product height",
    "Packed product dimension unit",
]

CARE_COLUMN = "Care note (product.metafields.custom.care_note)"
MATERIAL_COLUMN = "Material (product.metafields.custom.material)"
FINISH_COLUMN = "Finish (product.metafields.custom.finish)"

# Subset of a typical Magento 2 product export, in the order of the product
# data attributes reference as far as these columns go. configurable_* are the
# complex-data columns from that reference. A real export has more columns.
MAGENTO_COLUMNS = [
    "sku",
    "store_view_code",
    "attribute_set_code",
    "product_type",
    "categories",
    "product_websites",
    "name",
    "description",
    "short_description",
    "weight",
    "product_online",
    "tax_class_name",
    "visibility",
    "price",
    "special_price",
    "special_price_from_date",
    "special_price_to_date",
    "url_key",
    "meta_title",
    "meta_keywords",
    "meta_description",
    "base_image",
    "base_image_label",
    "small_image",
    "small_image_label",
    "thumbnail_image",
    "thumbnail_image_label",
    "additional_attributes",
    "qty",
    "is_in_stock",
    "manage_stock",
    "additional_images",
    "additional_image_labels",
    "configurable_variations",
    "configurable_variation_labels",
]

WOO_CORE = [
    "ID",
    "Type",
    "SKU",
    "GTIN, UPC, EAN, or ISBN",
    "Name",
    "Published",
    "Is featured?",
    "Visibility in catalog",
    "Short description",
    "Description",
    "Date sale price starts",
    "Date sale price ends",
    "Tax status",
    "Tax class",
    "In stock?",
    "Stock",
    "Low stock amount",
    "Backorders allowed?",
    "Sold individually?",
    "Weight (kg)",
    "Length (cm)",
    "Width (cm)",
    "Height (cm)",
    "Allow customer reviews?",
    "Purchase note",
    "Sale price",
    "Regular price",
    "Categories",
    "Tags",
    "Shipping class",
    "Images",
    "Download limit",
    "Download expiry days",
    "Parent",
    "Grouped products",
    "Upsells",
    "Cross-sells",
    "External URL",
    "Button text",
    "Position",
]


def woo_headers(attribute_count: int = 0, meta_keys: tuple[str, ...] = ()) -> list[str]:
    headers = list(WOO_CORE)
    for index in range(1, attribute_count + 1):
        headers.extend(
            [
                f"Attribute {index} name",
                f"Attribute {index} value(s)",
                f"Attribute {index} default",
                f"Attribute {index} visible",
                f"Attribute {index} global",
            ]
        )
    headers.extend(f"Meta: {key}" for key in meta_keys)
    return headers


def slug(title: str) -> str:
    return title.lower().replace(" ", "-")


def grams(kilograms: str) -> str:
    if not kilograms:
        return ""
    return str(int((Decimal(kilograms) * Decimal("1000")).to_integral_value()))


def blank(headers: list[str]) -> dict[str, str]:
    return {header: "" for header in headers}


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=headers,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            missing = [header for header in headers if header not in row]
            extra = [key for key in row if key not in headers]
            if missing or extra:
                raise SystemExit(f"{path.name}: missing {missing} extra {extra}")
            writer.writerow(row)


def image_url(name: str) -> str:
    return f"https://cdn.example.test/sample-harbor/{name}"


def simple_woo(headers: list[str], item: dict[str, str]) -> dict[str, str]:
    row = blank(headers)
    row.update(
        {
            "ID": item["id"],
            "Type": "simple",
            "SKU": item["sku"],
            "Name": item["name"],
            "Published": item["published"],
            "Is featured?": "0",
            "Visibility in catalog": "visible",
            "Short description": item["short"],
            "Description": item["description"],
            "Tax status": "taxable",
            "In stock?": "1",
            "Stock": item.get("stock", ""),
            "Backorders allowed?": "0",
            "Sold individually?": "0",
            "Weight (kg)": item.get("weight", ""),
            "Length (cm)": item.get("length", ""),
            "Width (cm)": item.get("width", ""),
            "Height (cm)": item.get("height", ""),
            "Allow customer reviews?": "1",
            "Sale price": item.get("sale", ""),
            "Regular price": item["regular"],
            "Categories": item["categories"],
            "Tags": item["tags"],
            "Images": ", ".join(item["images"]),
            "Position": "0",
        }
    )
    if item.get("care"):
        row["Meta: care_note"] = item["care"]
    return row


def simple_shop(headers: list[str], item: dict[str, str]) -> list[dict[str, str]]:
    """Map one simple WooCommerce product the way small-clean is defined.

    Sale price, when set, becomes Price. Regular price then becomes
    Compare-at price. With no sale, Regular price becomes Price and
    Compare-at price stays empty. Draft (Published -1) stays draft and is
    not published on the online store. A product with no options uses option
    name Title and option value Default Title.
    """
    published = item["published"]
    if published == "1":
        status, online = "active", "true"
    elif published == "-1":
        status, online = "draft", "false"
    else:
        raise SystemExit(f"unsupported Published value {published}")

    sale = item.get("sale", "")
    price = sale or item["regular"]
    compare = item["regular"] if sale else ""
    stock = item.get("stock", "")
    images = item["images"]
    handle = slug(item["name"])

    first = blank(headers)
    first.update(
        {
            "Title": item["name"],
            "URL handle": handle,
            "Description": item["description"],
            "Vendor": VENDOR,
            "Type": item["type"],
            "Tags": item["tags"],
            "Published on online store": online,
            "Status": status,
            "SKU": item["sku"],
            "Option1 name": "Title",
            "Option1 value": "Default Title",
            "Price": price,
            "Compare-at price": compare,
            "Charge tax": "true",
            "Inventory tracker": "shopify" if stock else "",
            "Inventory quantity": stock,
            "Continue selling when out of stock": "deny" if stock else "",
            "Weight value (grams)": grams(item.get("weight", "")),
            "Weight unit for display": "kg" if item.get("weight") else "",
            "Requires shipping": "true",
            "Fulfillment service": "manual",
            "Product image URL": images[0],
            "Image position": "1",
            "Gift card": "false",
        }
    )
    if item.get("care") and CARE_COLUMN in headers:
        first[CARE_COLUMN] = item["care"]

    rows = [first]
    for position, url in enumerate(images[1:], start=2):
        extra = blank(headers)
        extra["URL handle"] = handle
        extra["Product image URL"] = url
        extra["Image position"] = str(position)
        rows.append(extra)
    return rows


def set_attribute(
    row: dict[str, str],
    index: int,
    name: str = "",
    values: str = "",
    default: str = "",
    visible: str = "",
    global_flag: str = "",
) -> None:
    row[f"Attribute {index} name"] = name
    row[f"Attribute {index} value(s)"] = values
    row[f"Attribute {index} default"] = default
    row[f"Attribute {index} visible"] = visible
    row[f"Attribute {index} global"] = global_flag


def base_product_fields(row: dict[str, str], *, product_id: str, product_type: str, sku: str, name: str) -> None:
    row["ID"] = product_id
    row["Type"] = product_type
    row["SKU"] = sku
    row["Name"] = name
    row["Published"] = "1"
    row["Is featured?"] = "0"
    row["Visibility in catalog"] = "visible"
    row["Tax status"] = "taxable"
    row["In stock?"] = "1"
    row["Backorders allowed?"] = "0"
    row["Sold individually?"] = "0"
    row["Allow customer reviews?"] = "1"
    row["Position"] = "0"


def shop_variant(
    headers: list[str],
    *,
    handle: str,
    title: str,
    description: str,
    product_type: str,
    tags: str,
    sku: str,
    price: str,
    stock: str,
    weight: str,
    options: list[tuple[str, str]],
    image: str,
    first: bool,
    material: str = "",
) -> dict[str, str]:
    row = blank(headers)
    row["URL handle"] = handle
    row["SKU"] = sku
    row["Price"] = price
    row["Charge tax"] = "true"
    row["Inventory tracker"] = "shopify"
    row["Inventory quantity"] = stock
    row["Continue selling when out of stock"] = "deny"
    row["Weight value (grams)"] = grams(weight)
    row["Weight unit for display"] = "kg"
    row["Requires shipping"] = "true"
    row["Fulfillment service"] = "manual"
    for index, (name, value) in enumerate(options, start=1):
        row[f"Option{index} value"] = value
        if first:
            row[f"Option{index} name"] = name
    if first:
        row.update(
            {
                "Title": title,
                "Description": description,
                "Vendor": VENDOR,
                "Type": product_type,
                "Tags": tags,
                "Published on online store": "true",
                "Status": "active",
                "Product image URL": image,
                "Image position": "1",
                "Gift card": "false",
            }
        )
        if material:
            row[MATERIAL_COLUMN] = material
    return row


def build_small_clean() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    woo_head = woo_headers(meta_keys=("care_note",))
    shop_head = SHOPIFY_COLUMNS + [CARE_COLUMN]
    items = [
        {
            "id": "1001",
            "name": "Pebble Sample Candle",
            "sku": "CANDLE-PEBBLE",
            "published": "1",
            "regular": "18.00",
            "sale": "",
            "stock": "12",
            "weight": "0.280",
            "length": "8",
            "width": "8",
            "height": "9",
            "categories": "Sample goods > Candles",
            "tags": "sample, quiet",
            "type": "Candles",
            "images": [image_url("pebble-candle.jpg")],
            "short": "Practice candle.",
            "description": "A practice candle from the fictional Sample Harbor Goods catalog.",
            "care": "Burn on a flat surface.",
        },
        {
            "id": "1002",
            "name": "Tide Sample Mug",
            "sku": "MUG-TIDE",
            "published": "1",
            "regular": "24.00",
            "sale": "19.00",
            "stock": "8",
            "weight": "0.350",
            "length": "9",
            "width": "9",
            "height": "10",
            "categories": "Sample goods > Mugs",
            "tags": "sample, tide",
            "type": "Mugs",
            "images": [image_url("tide-mug.jpg"), image_url("tide-mug-handle.jpg")],
            "short": "Practice mug on sale.",
            "description": "A practice mug from the fictional Sample Harbor Goods catalog.",
            "care": "",
        },
        {
            "id": "1003",
            "name": "Draft Sample Coaster",
            "sku": "COASTER-DRAFT",
            "published": "-1",
            "regular": "6.00",
            "sale": "",
            "stock": "",
            "weight": "0.040",
            "length": "10",
            "width": "10",
            "height": "1",
            "categories": "Sample goods > Coasters",
            "tags": "sample, draft",
            "type": "Coasters",
            "images": [image_url("draft-coaster.jpg")],
            "short": "Practice coaster kept as a draft.",
            "description": "A practice coaster that stays unpublished in this fictional catalog.",
            "care": "",
        },
        {
            "id": "1004",
            "name": "Linen Sample Cloth",
            "sku": "CLOTH-LINEN",
            "published": "1",
            "regular": "14.50",
            "sale": "",
            "stock": "20",
            "weight": "0.120",
            "length": "30",
            "width": "30",
            "height": "1",
            "categories": "Sample goods > Cloth",
            "tags": "sample, linen",
            "type": "Cloth",
            "images": [image_url("linen-cloth.jpg")],
            "short": "Practice cloth.",
            "description": "A practice cloth from the fictional Sample Harbor Goods catalog.",
            "care": "",
        },
    ]
    woo_rows = [simple_woo(woo_head, item) for item in items]
    shop_rows: list[dict[str, str]] = []
    for item in items:
        shop_rows.extend(simple_shop(shop_head, item))
    return woo_head, woo_rows, shop_head, shop_rows


def build_common_mistakes() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    woo_head = woo_headers(attribute_count=1)
    shop_head = list(SHOPIFY_COLUMNS)
    items = [
        {
            "id": "3001",
            "name": "Cedar Sample Spoon",
            "sku": "SPOON-CEDAR",
            "published": "1",
            "regular": "7.50",
            "sale": "",
            "stock": "15",
            "weight": "0.050",
            "length": "15",
            "width": "3",
            "height": "1",
            "categories": "Sample goods > Spoons",
            "tags": "sample, cedar",
            "type": "Spoons",
            "images": [image_url("cedar-spoon.jpg")],
            "short": "Practice spoon that maps cleanly.",
            "description": "A practice spoon from the fictional Sample Harbor Goods catalog.",
        },
        {
            "id": "3002",
            "name": "Harbor Sample Lantern",
            "sku": "LANTERN-01",
            "published": "1",
            "regular": "42.00",
            "sale": "36.00",
            "stock": "6",
            "weight": "0.640",
            "length": "12",
            "width": "12",
            "height": "18",
            "categories": "Sample goods > Lanterns",
            "tags": "sample, harbor",
            "type": "Lanterns",
            "images": [image_url("harbor-lantern.jpg")],
            "short": "Practice lantern with a sale price.",
            "description": "A practice lantern from the fictional Sample Harbor Goods catalog.",
        },
        {
            "id": "3003",
            "name": "Sample Tag Ribbon",
            "sku": "01482",
            "published": "1",
            "regular": "4.50",
            "sale": "",
            "stock": "40",
            "weight": "0.010",
            "length": "20",
            "width": "2",
            "height": "1",
            "categories": "Sample goods > Ribbons",
            "tags": "sample, ribbon",
            "type": "Ribbons",
            "images": [image_url("tag-ribbon.jpg")],
            "short": "Practice ribbon whose SKU has a leading zero.",
            "description": "A practice ribbon from the fictional Sample Harbor Goods catalog.",
        },
        {
            "id": "3004",
            "name": "Unfinished Sample Tray",
            "sku": "TRAY-DRAFT",
            "published": "-1",
            "regular": "22.00",
            "sale": "",
            "stock": "3",
            "weight": "0.500",
            "length": "24",
            "width": "16",
            "height": "3",
            "categories": "Sample goods > Trays",
            "tags": "sample, draft",
            "type": "Trays",
            "images": [image_url("unfinished-tray.jpg")],
            "short": "Practice tray that is still a draft.",
            "description": "A practice tray that should stay unpublished in this fictional catalog.",
        },
        {
            "id": "3005",
            "name": "Moss Sample Bowl",
            "sku": "BOWL-MOSS",
            "published": "1",
            "regular": "28.00",
            "sale": "",
            "stock": "9",
            "weight": "0.410",
            "length": "14",
            "width": "14",
            "height": "7",
            "categories": "Sample goods > Bowls",
            "tags": "sample, moss",
            "type": "Bowls",
            "images": [image_url("moss-bowl.jpg"), image_url("moss-bowl-side.jpg")],
            "short": "Practice bowl with two pictures.",
            "description": "A practice bowl from the fictional Sample Harbor Goods catalog.",
        },
        {
            "id": "3006",
            "name": "Pine Sample Soap",
            "sku": "SOAP-PINE",
            "published": "1",
            "regular": "9.00",
            "sale": "",
            "stock": "18",
            "weight": "0.090",
            "length": "8",
            "width": "5",
            "height": "3",
            "categories": "Sample goods > Soap",
            "tags": "sample, pine",
            "type": "Soap",
            "images": [image_url("pine-soap.jpg")],
            "short": "Practice soap.",
            "description": "A practice soap from the fictional Sample Harbor Goods catalog.",
        },
        {
            "id": "3007",
            "name": "Pine Sample Oil",
            "sku": "OIL-PINE",
            "published": "1",
            "regular": "11.00",
            "sale": "",
            "stock": "11",
            "weight": "0.180",
            "length": "5",
            "width": "5",
            "height": "12",
            "categories": "Sample goods > Oils",
            "tags": "sample, pine",
            "type": "Oils",
            "images": [image_url("pine-oil.jpg")],
            "short": "Practice oil.",
            "description": "A practice oil from the fictional Sample Harbor Goods catalog.",
        },
    ]
    woo_rows = [simple_woo(woo_head, item) for item in items]
    shop_rows: list[dict[str, str]] = []
    for item in items:
        shop_rows.extend(simple_shop(shop_head, item))

    by_sku = {row["SKU"]: row for row in shop_rows if row["SKU"]}
    # Sale price was copied into Price and the regular price was not kept.
    by_sku["LANTERN-01"]["Compare-at price"] = ""
    # Leading zero dropped, as a spreadsheet often does.
    by_sku["01482"]["SKU"] = "1482"
    # Draft was published.
    by_sku["TRAY-DRAFT"]["Status"] = "active"
    by_sku["TRAY-DRAFT"]["Published on online store"] = "true"
    # Second product image never arrived.
    shop_rows = [
        row
        for row in shop_rows
        if not (
            row["URL handle"] == "moss-sample-bowl"
            and row["Product image URL"].endswith("moss-bowl-side.jpg")
        )
    ]
    # Two different products were given one handle.
    by_sku["OIL-PINE"]["URL handle"] = "pine-sample-soap"

    tote_parent = blank(woo_head)
    base_product_fields(tote_parent, product_id="3010", product_type="variable", sku="TOTE", name="Oak Sample Tote")
    tote_parent.update(
        {
            "Short description": "Practice tote in three sizes.",
            "Description": "A practice tote from the fictional Sample Harbor Goods catalog.",
            "Categories": "Sample goods > Totes",
            "Tags": "sample, oak",
            "Images": image_url("oak-tote.jpg"),
        }
    )
    set_attribute(
        tote_parent,
        1,
        name="Size",
        values="Small, Medium, Large",
        default="Small",
        visible="1",
        global_flag="0",
    )
    woo_rows.append(tote_parent)

    variations = [
        ("3011", "TOTE-S", "Small", "32.00", "5", "0.400"),
        ("3012", "TOTE-M", "Medium", "32.00", "4", "0.420"),
        ("3013", "TOTE-L", "Large", "34.00", "3", "0.460"),
    ]
    for product_id, sku, size, price, stock, weight in variations:
        row = blank(woo_head)
        base_product_fields(
            row,
            product_id=product_id,
            product_type="variation",
            sku=sku,
            name=f"Oak Sample Tote - {size}",
        )
        row.update(
            {
                "Description": "A size of the practice tote.",
                "Stock": stock,
                "Weight (kg)": weight,
                "Regular price": price,
                "Parent": "TOTE",
            }
        )
        set_attribute(row, 1, name="Size", values=size, visible="1", global_flag="0")
        woo_rows.append(row)

    # Large is the missing variant. Small and Medium are present.
    for sku, size, price, stock, weight, first in (
        ("TOTE-S", "Small", "32.00", "5", "0.400", True),
        ("TOTE-M", "Medium", "32.00", "4", "0.420", False),
    ):
        shop_rows.append(
            shop_variant(
                shop_head,
                handle="oak-sample-tote",
                title="Oak Sample Tote",
                description="A practice tote from the fictional Sample Harbor Goods catalog.",
                product_type="Totes",
                tags="sample, oak",
                sku=sku,
                price=price,
                stock=stock,
                weight=weight,
                options=[("Size", size)],
                image=image_url("oak-tote.jpg"),
                first=first,
            )
        )
    return woo_head, woo_rows, shop_head, shop_rows


def build_variable_products() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    woo_head = woo_headers(attribute_count=4)
    shop_head = SHOPIFY_COLUMNS + [MATERIAL_COLUMN]
    woo_rows: list[dict[str, str]] = []
    shop_rows: list[dict[str, str]] = []

    mug_parent = blank(woo_head)
    base_product_fields(mug_parent, product_id="2001", product_type="variable", sku="MUG-CEDAR", name="Cedar Sample Mug")
    mug_parent.update(
        {
            "Short description": "Practice mug in two sizes.",
            "Description": "A practice mug from the fictional Sample Harbor Goods catalog.",
            "Categories": "Sample goods > Mugs",
            "Tags": "sample, cedar",
            "Images": image_url("cedar-mug.jpg"),
        }
    )
    set_attribute(
        mug_parent,
        1,
        name="Size",
        values="8 oz, 12 oz",
        default="8 oz",
        visible="1",
        global_flag="0",
    )
    # Material is visible on the product and is not a variation attribute.
    set_attribute(mug_parent, 2, name="Material", values="Stone", visible="1", global_flag="0")
    woo_rows.append(mug_parent)

    mug_variants = [
        ("2002", "MUG-8OZ", "8 oz", "16.00", "6", "0.300"),
        ("2003", "MUG-12OZ", "12 oz", "18.00", "4", "0.420"),
    ]
    for product_id, sku, size, price, stock, weight in mug_variants:
        row = blank(woo_head)
        base_product_fields(
            row,
            product_id=product_id,
            product_type="variation",
            sku=sku,
            name=f"Cedar Sample Mug - {size}",
        )
        row.update(
            {
                "Description": "A size of the practice mug.",
                "Stock": stock,
                "Weight (kg)": weight,
                "Regular price": price,
                "Parent": "MUG-CEDAR",
            }
        )
        set_attribute(row, 1, name="Size", values=size, visible="1", global_flag="0")
        woo_rows.append(row)
        shop_rows.append(
            shop_variant(
                shop_head,
                handle="cedar-sample-mug",
                title="Cedar Sample Mug",
                description="A practice mug from the fictional Sample Harbor Goods catalog.",
                product_type="Mugs",
                tags="sample, cedar",
                sku=sku,
                price=price,
                stock=stock,
                weight=weight,
                options=[("Size", size)],
                image=image_url("cedar-mug.jpg"),
                first=sku == "MUG-8OZ",
                material="Stone" if sku == "MUG-8OZ" else "",
            )
        )

    apron_parent = blank(woo_head)
    base_product_fields(
        apron_parent,
        product_id="2010",
        product_type="variable",
        sku="APRON-LINEN",
        name="Linen Sample Apron",
    )
    apron_parent.update(
        {
            "Short description": "Practice apron in two sizes and two colors.",
            "Description": "A practice apron from the fictional Sample Harbor Goods catalog.",
            "Categories": "Sample goods > Aprons",
            "Tags": "sample, linen",
            "Images": image_url("linen-apron.jpg"),
        }
    )
    set_attribute(
        apron_parent,
        1,
        name="Size",
        values="Small, Large",
        default="Small",
        visible="1",
        global_flag="0",
    )
    set_attribute(apron_parent, 2, name="Color", values="Sand, Ink", visible="1", global_flag="0")
    woo_rows.append(apron_parent)

    apron_variants = [
        ("2011", "APRON-S-SAND", "Small", "Sand", "38.00", "5", "0.250"),
        ("2012", "APRON-S-INK", "Small", "Ink", "38.00", "5", "0.250"),
        ("2013", "APRON-L-SAND", "Large", "Sand", "40.00", "4", "0.280"),
        ("2014", "APRON-L-INK", "Large", "Ink", "40.00", "4", "0.280"),
    ]
    for product_id, sku, size, color, price, stock, weight in apron_variants:
        row = blank(woo_head)
        base_product_fields(
            row,
            product_id=product_id,
            product_type="variation",
            sku=sku,
            name=f"Linen Sample Apron - {size}, {color}",
        )
        row.update(
            {
                "Description": "A size and color of the practice apron.",
                "Stock": stock,
                "Weight (kg)": weight,
                "Regular price": price,
                "Parent": "APRON-LINEN",
            }
        )
        set_attribute(row, 1, name="Size", values=size, visible="1", global_flag="0")
        set_attribute(row, 2, name="Color", values=color, visible="1", global_flag="0")
        woo_rows.append(row)
        if sku == "APRON-L-INK":
            continue
        shop_rows.append(
            shop_variant(
                shop_head,
                handle="linen-sample-apron",
                title="Linen Sample Apron",
                description="A practice apron from the fictional Sample Harbor Goods catalog.",
                product_type="Aprons",
                tags="sample, linen",
                sku=sku,
                price=price,
                stock=stock,
                weight=weight,
                options=[("Size", size), ("Color", color)],
                image=image_url("linen-apron.jpg"),
                first=sku == "APRON-S-SAND",
            )
        )

    pack_parent = blank(woo_head)
    base_product_fields(
        pack_parent,
        product_id="2020",
        product_type="variable",
        sku="PACK-TRAIL",
        name="Trail Sample Pack",
    )
    pack_parent.update(
        {
            "Short description": "Practice pack with four variation attributes.",
            "Description": "A practice pack from the fictional Sample Harbor Goods catalog.",
            "Categories": "Sample goods > Packs",
            "Tags": "sample, trail",
            "Images": image_url("trail-pack.jpg"),
        }
    )
    set_attribute(pack_parent, 1, name="Size", values="S, M", default="S", visible="1", global_flag="0")
    set_attribute(pack_parent, 2, name="Color", values="Moss, Clay", visible="1", global_flag="0")
    set_attribute(pack_parent, 3, name="Strap", values="Clip, Buckle", visible="1", global_flag="0")
    set_attribute(pack_parent, 4, name="Pocket", values="Yes, No", visible="1", global_flag="0")
    woo_rows.append(pack_parent)

    next_id = 2021
    first_shop = True
    for size, color, strap, pocket in itertools.product(
        ("S", "M"),
        ("Moss", "Clay"),
        ("Clip", "Buckle"),
        ("Yes", "No"),
    ):
        pocket_code = "Y" if pocket == "Yes" else "N"
        sku = f"PACK-{size}-{color.upper()}-{strap.upper()}-{pocket_code}"
        row = blank(woo_head)
        base_product_fields(
            row,
            product_id=str(next_id),
            product_type="variation",
            sku=sku,
            name=f"Trail Sample Pack - {size}, {color}, {strap}, {pocket}",
        )
        next_id += 1
        row.update(
            {
                "Description": "One combination of the practice pack.",
                "Stock": "2",
                "Weight (kg)": "0.900",
                "Regular price": "80.00",
                "Parent": "PACK-TRAIL",
            }
        )
        set_attribute(row, 1, name="Size", values=size, visible="1", global_flag="0")
        set_attribute(row, 2, name="Color", values=color, visible="1", global_flag="0")
        set_attribute(row, 3, name="Strap", values=strap, visible="1", global_flag="0")
        set_attribute(row, 4, name="Pocket", values=pocket, visible="1", global_flag="0")
        woo_rows.append(row)
        if pocket != "Yes":
            continue
        shop_rows.append(
            shop_variant(
                shop_head,
                handle="trail-sample-pack",
                title="Trail Sample Pack",
                description="A practice pack from the fictional Sample Harbor Goods catalog.",
                product_type="Packs",
                tags="sample, trail",
                sku=sku,
                price="80.00",
                stock="2",
                weight="0.900",
                options=[("Size", size), ("Color", color), ("Strap", strap)],
                image=image_url("trail-pack.jpg"),
                first=first_shop,
            )
        )
        first_shop = False

    return woo_head, woo_rows, shop_head, shop_rows


def magento_image(name: str) -> str:
    """Relative path of the kind a product export stores. Not a public URL."""
    return f"/w/i/{name}"


def magento_row(headers: list[str], **fields: str) -> dict[str, str]:
    row = blank(headers)
    row.update(fields)
    return row


def build_magento_basic() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    """One configurable lantern, two simple variations, and one store-view row.

    In this practice file the weight cells are written in kilograms, and
    Shopify grams are that number times 1000. The attributes reference does
    not say a real cell uses the store view's weight unit. The parent price
    and the parent weight are not copied. WICK-S copies special_price into
    Price even though the dates are 2026-11-01 to 2026-11-30, which is the
    labelled hazard special-price-kept-past-its-dates. Vendor and Tags are
    fictional store-level values, not Magento columns. base_image and
    small_image are the same file, so the Shopify file lists that URL once.
    """
    magento_head = list(MAGENTO_COLUMNS)
    shop_head = SHOPIFY_COLUMNS + [FINISH_COLUMN]
    description = "A practice lantern from the fictional Sample Harbor Goods catalog."
    parent_sku = "WICK-LANTERN"
    handle = "wick-sample-lantern"

    parent = magento_row(
        magento_head,
        sku=parent_sku,
        attribute_set_code="default",
        product_type="configurable",
        categories="Harbor/Lanterns",
        product_websites="harbor",
        name="Wick Sample Lantern",
        description=description,
        short_description="Practice lantern in two sizes.",
        weight="0.600",
        product_online="1",
        tax_class_name="Taxable Goods",
        visibility="Catalog, Search",
        price="40.00",
        url_key=handle,
        meta_title="Wick Sample Lantern",
        meta_keywords="sample, wick, lantern",
        meta_description=description,
        base_image=magento_image("wick-lantern.jpg"),
        base_image_label="Wick lantern front",
        small_image=magento_image("wick-lantern.jpg"),
        small_image_label="Wick lantern front",
        thumbnail_image=magento_image("wick-lantern-mark.jpg"),
        thumbnail_image_label="Wick lantern mark",
        additional_attributes="finish=Brass",
        additional_images=magento_image("wick-lantern-side.jpg"),
        additional_image_labels="Wick lantern side",
        configurable_variations="sku=WICK-S,size=Small|sku=WICK-L,size=Large",
        configurable_variation_labels="Choose Size:",
    )
    cove = magento_row(
        magento_head,
        sku=parent_sku,
        store_view_code="cove",
        name="Wick Cove Lantern",
    )
    small = magento_row(
        magento_head,
        sku="WICK-S",
        attribute_set_code="default",
        product_type="simple",
        categories="Harbor/Lanterns",
        product_websites="harbor",
        name="Wick Sample Lantern - Small",
        description="The small size of the practice lantern.",
        weight="0.520",
        product_online="1",
        tax_class_name="Taxable Goods",
        visibility="Not Visible Individually",
        price="36.00",
        special_price="30.00",
        special_price_from_date="2026-11-01",
        special_price_to_date="2026-11-30",
        url_key="wick-sample-lantern-small",
        base_image=magento_image("wick-lantern-small.jpg"),
        base_image_label="Wick lantern small",
        small_image=magento_image("wick-lantern-small.jpg"),
        small_image_label="Wick lantern small",
        thumbnail_image=magento_image("wick-lantern-small.jpg"),
        thumbnail_image_label="Wick lantern small",
        qty="6",
        is_in_stock="1",
        manage_stock="1",
    )
    large = magento_row(
        magento_head,
        sku="WICK-L",
        attribute_set_code="default",
        product_type="simple",
        categories="Harbor/Lanterns",
        product_websites="harbor",
        name="Wick Sample Lantern - Large",
        description="The large size of the practice lantern.",
        weight="0.680",
        product_online="1",
        tax_class_name="Taxable Goods",
        visibility="Not Visible Individually",
        price="42.00",
        url_key="wick-sample-lantern-large",
        base_image=magento_image("wick-lantern-large.jpg"),
        base_image_label="Wick lantern large",
        small_image=magento_image("wick-lantern-large.jpg"),
        small_image_label="Wick lantern large",
        thumbnail_image=magento_image("wick-lantern-large.jpg"),
        thumbnail_image_label="Wick lantern large",
        qty="4",
        is_in_stock="1",
        manage_stock="1",
    )

    shop_small = shop_variant(
        shop_head,
        handle=handle,
        title="Wick Sample Lantern",
        description=description,
        product_type="Lanterns",
        tags="practice",
        sku="WICK-S",
        price="30.00",
        stock="6",
        weight="0.520",
        options=[("Size", "Small")],
        image=image_url("wick-lantern.jpg"),
        first=True,
    )
    shop_small["Compare-at price"] = "36.00"
    shop_small["Variant image URL"] = image_url("wick-lantern-small.jpg")
    shop_small["SEO title"] = "Wick Sample Lantern"
    shop_small["SEO description"] = description
    shop_small[FINISH_COLUMN] = "Brass"

    shop_large = shop_variant(
        shop_head,
        handle=handle,
        title="",
        description="",
        product_type="",
        tags="",
        sku="WICK-L",
        price="42.00",
        stock="4",
        weight="0.680",
        options=[("Size", "Large")],
        image="",
        first=False,
    )
    shop_large["Variant image URL"] = image_url("wick-lantern-large.jpg")

    shop_rows = [shop_small, shop_large]
    for position, name in ((2, "wick-lantern-mark.jpg"), (3, "wick-lantern-side.jpg")):
        extra = blank(shop_head)
        extra["URL handle"] = handle
        extra["Product image URL"] = image_url(name)
        extra["Image position"] = str(position)
        shop_rows.append(extra)
    return magento_head, [parent, cove, small, large], shop_head, shop_rows


# Subset of a legacy Bulk Edit product export, in the order of the supported
# fields page as far as these columns go. A real Bulk Edit file has more
# columns. Option Set is omitted: the fields page says to delete it on the
# v3 experience. Checked 2026-10-27.
BIGCOMMERCE_COLUMNS = [
    "Item Type",
    "Product ID",
    "Product Name",
    "Product Type",
    "Product Code/SKU",
    "Product Description",
    "Price",
    "Cost Price",
    "Retail Price",
    "Sale Price",
    "Product Weight",
    "Allow Purchases?",
    "Product Visible?",
    "Product Availability",
    "Track Inventory",
    "Current Stock Level",
    "Category",
    "Product Image File - 1",
    "Product Image Description - 1",
    "Product Image Is Thumbnail - 1",
    "Product Image Sort - 1",
    "Product URL",
    "Redirect Old URL?",
]

# Header row of the Squarespace example file
# https://assets.squarespace.com/universal/commerce/product_import-v2.csv
# checked 2026-10-27. 26 columns, including Product Page. No GTIN, no MPN.
SQUARESPACE_COLUMNS = [
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
]


def bigcommerce_row(headers: list[str], **fields: str) -> dict[str, str]:
    row = blank(headers)
    row.update(fields)
    return row


def build_bigcommerce_basic() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    """One pitcher, two SKU rows, and one Rule row.

    In this practice file the weight cells are written in kilograms, and
    Shopify grams are that number times 1000. The fields page says to use
    numbers only and does not name the unit. Track Inventory is written with
    a normal space. The fields page uses a non-breaking space in "by option".
    Retail Price is copied to Compare-at price even though Sale Price is
    empty. That is the labelled hazard retail-copied-into-compare-at.
    Vendor, Tags, Charge tax, and Fulfillment service are fictional
    store-level values, not columns in this file. Continue selling is deny
    because this file has no backorder column.
    """
    bc_head = list(BIGCOMMERCE_COLUMNS)
    shop_head = list(SHOPIFY_COLUMNS)
    description = "A practice pitcher from the fictional Sample Harbor Goods catalog."
    handle = "nettle-sample-pitcher"
    # A normal space. The supported-fields page uses a non-breaking space here.
    by_option = "by option"

    product = bigcommerce_row(
        bc_head,
        **{
            "Item Type": "Product",
            "Product ID": "5101",
            "Product Name": "Nettle Sample Pitcher",
            "Product Type": "P",
            "Product Code/SKU": "PITCHER-NETTLE",
            "Product Description": description,
            "Price": "32.00",
            "Cost Price": "12.00",
            "Retail Price": "44.00",
            "Product Weight": "0.600",
            "Allow Purchases?": "Y",
            "Product Visible?": "Y",
            "Product Availability": "Ships in two sample days",
            "Track Inventory": by_option,
            "Category": "Harbor/Pitchers",
            "Product Image File - 1": image_url("nettle-pitcher.jpg"),
            "Product Image Description - 1": "Nettle pitcher front",
            "Product Image Is Thumbnail - 1": "Y",
            "Product Image Sort - 1": "0",
            "Product URL": "/nettle-sample-pitcher/",
            "Redirect Old URL?": "N",
        },
    )
    small = bigcommerce_row(
        bc_head,
        **{
            "Item Type": "SKU",
            "Product ID": "5102",
            "Product Name": "[RB]Size=Small",
            "Product Code/SKU": "PITCHER-S",
            "Price": "32.00",
            "Product Weight": "0.520",
            "Current Stock Level": "6",
        },
    )
    large = bigcommerce_row(
        bc_head,
        **{
            "Item Type": "SKU",
            "Product ID": "5103",
            "Product Name": "[RB]Size=Large",
            "Product Code/SKU": "PITCHER-L",
            "Price": "36.00",
            "Product Weight": "0.720",
            "Current Stock Level": "4",
        },
    )
    rule = bigcommerce_row(
        bc_head,
        **{
            "Item Type": "Rule",
            "Product ID": "5104",
            "Product Code/SKU": "PITCHER-L",
            "Price": "[FIXED]36",
            "Product Weight": "[FIXED]0.720",
            "Product Image File - 1": image_url("nettle-pitcher-large.jpg"),
        },
    )

    shop_small = shop_variant(
        shop_head,
        handle=handle,
        title="Nettle Sample Pitcher",
        description=description,
        product_type="Pitchers",
        tags="practice",
        sku="PITCHER-S",
        price="32.00",
        stock="6",
        weight="0.520",
        options=[("Size", "Small")],
        image=image_url("nettle-pitcher.jpg"),
        first=True,
    )
    shop_small["Compare-at price"] = "44.00"
    shop_small["Cost per item"] = "12.00"
    shop_small["Image alt text"] = "Nettle pitcher front"

    shop_large = shop_variant(
        shop_head,
        handle=handle,
        title="",
        description="",
        product_type="",
        tags="",
        sku="PITCHER-L",
        price="36.00",
        stock="4",
        weight="0.720",
        options=[("Size", "Large")],
        image="",
        first=False,
    )
    shop_large["Compare-at price"] = "44.00"
    shop_large["Cost per item"] = "12.00"
    shop_large["Variant image URL"] = image_url("nettle-pitcher-large.jpg")

    return bc_head, [product, small, large, rule], shop_head, [shop_small, shop_large]


def squarespace_row(headers: list[str], **fields: str) -> dict[str, str]:
    row = blank(headers)
    row.update(fields)
    return row


def squarespace_shop(
    headers: list[str],
    *,
    handle: str,
    sku: str,
    price: str,
    stock: str,
    tracked: bool,
    options: list[tuple[str, str]],
    first: bool,
    title: str = "",
    description: str = "",
    product_type: str = "",
    tags: str = "",
    compare: str = "",
    image: str = "",
    position: str = "",
) -> dict[str, str]:
    """One Shopify row for the Squarespace pair.

    Weight stays blank: the Squarespace file has a number and no unit.
    Unlimited stock leaves the tracker and the quantity blank.
    """
    row = blank(headers)
    row["URL handle"] = handle
    row["SKU"] = sku
    row["Price"] = price
    row["Compare-at price"] = compare
    row["Charge tax"] = "true"
    row["Requires shipping"] = "true"
    row["Fulfillment service"] = "manual"
    if tracked:
        row["Inventory tracker"] = "shopify"
        row["Inventory quantity"] = stock
        row["Continue selling when out of stock"] = "deny"
    for index, (name, value) in enumerate(options, start=1):
        row[f"Option{index} value"] = value
        if first:
            row[f"Option{index} name"] = name
    if first:
        row["Title"] = title
        row["Description"] = description
        row["Vendor"] = VENDOR
        row["Type"] = product_type
        row["Tags"] = tags
        row["Published on online store"] = "true"
        row["Status"] = "active"
        row["Gift card"] = "false"
    if image:
        row["Product image URL"] = image
        row["Image position"] = position
    return row


def build_squarespace_basic() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    """Three fictional products in the 26-column example shape.

    Product ID is filled only on the first row of each product. The import
    article does not say whether an export repeats it on option rows.
    Variant ID is filled on every row in this file. Check your own export.

    JAR-S is On Sale Yes, so Shopify Price is the sale price. JAR-L and
    LADLE-FERN are On Sale No with Sale Price filled, so Shopify Price is
    the regular price. CLOTH-MIST stock is Unlimited, so Shopify does not
    track it. Weight, length, width, and height stay in the Squarespace
    file. The unit is not a column, so the Shopify grams cell is blank.
    Categories are names, which is the example file's shape.
    """
    sq_head = list(SQUARESPACE_COLUMNS)
    shop_head = list(SHOPIFY_COLUMNS)
    jar_images = f"{image_url('brine-jar.jpg')} {image_url('brine-jar-side.jpg')}"
    jar = squarespace_row(
        sq_head,
        **{
            "Product ID [Non Editable]": "8801",
            "Variant ID [Non Editable]": "8811",
            "Product Type [Non Editable]": "PHYSICAL",
            "Product Page": "harbor",
            "Product URL": "brine-sample-jar",
            "Title": "Brine Sample Jar",
            "Description": "A practice jar from the fictional Sample Harbor Goods catalog.",
            "SKU": "JAR-S",
            "Option Name 1": "Size",
            "Option Value 1": "Small",
            "Price": "18.00",
            "Sale Price": "14.00",
            "On Sale": "Yes",
            "Stock": "6",
            "Categories": "Jars",
            "Tags": "practice",
            "Weight": "0.400",
            "Length": "8",
            "Width": "8",
            "Height": "12",
            "Visible": "Yes",
            "Hosted Image URLs": jar_images,
        },
    )
    jar_large = squarespace_row(
        sq_head,
        **{
            "Variant ID [Non Editable]": "8812",
            "SKU": "JAR-L",
            "Option Name 1": "Size",
            "Option Value 1": "Large",
            "Price": "22.00",
            "Sale Price": "16.00",
            "On Sale": "No",
            "Stock": "4",
            "Weight": "0.600",
            "Length": "8",
            "Width": "8",
            "Height": "14",
        },
    )
    ladle = squarespace_row(
        sq_head,
        **{
            "Product ID [Non Editable]": "8802",
            "Variant ID [Non Editable]": "8821",
            "Product Type [Non Editable]": "PHYSICAL",
            "Product Page": "harbor",
            "Product URL": "fern-sample-ladle",
            "Title": "Fern Sample Ladle",
            "Description": "A practice ladle from the fictional Sample Harbor Goods catalog.",
            "SKU": "LADLE-FERN",
            "Price": "12.00",
            "Sale Price": "9.00",
            "On Sale": "No",
            "Stock": "5",
            "Categories": "Ladles",
            "Tags": "practice",
            "Weight": "0.250",
            "Length": "28",
            "Width": "6",
            "Height": "3",
            "Visible": "Yes",
            "Hosted Image URLs": image_url("fern-ladle.jpg"),
        },
    )
    cloth = squarespace_row(
        sq_head,
        **{
            "Product ID [Non Editable]": "8803",
            "Variant ID [Non Editable]": "8831",
            "Product Type [Non Editable]": "PHYSICAL",
            "Product Page": "harbor",
            "Product URL": "mist-sample-cloth",
            "Title": "Mist Sample Cloth",
            "Description": "A practice cloth from the fictional Sample Harbor Goods catalog.",
            "SKU": "CLOTH-MIST",
            "Price": "28.00",
            "On Sale": "No",
            "Stock": "Unlimited",
            "Categories": "Cloths",
            "Tags": "practice",
            "Weight": "0.180",
            "Length": "40",
            "Width": "40",
            "Height": "1",
            "Visible": "Yes",
            "Hosted Image URLs": image_url("mist-cloth.jpg"),
        },
    )
    shop_small = squarespace_shop(
        shop_head,
        handle="brine-sample-jar",
        title="Brine Sample Jar",
        description="A practice jar from the fictional Sample Harbor Goods catalog.",
        product_type="Jars",
        tags="practice",
        sku="JAR-S",
        price="14.00",
        compare="18.00",
        stock="6",
        tracked=True,
        options=[("Size", "Small")],
        first=True,
        image=image_url("brine-jar.jpg"),
        position="1",
    )
    shop_large = squarespace_shop(
        shop_head,
        handle="brine-sample-jar",
        sku="JAR-L",
        price="22.00",
        stock="4",
        tracked=True,
        options=[("Size", "Large")],
        first=False,
    )
    shop_side = blank(shop_head)
    shop_side["URL handle"] = "brine-sample-jar"
    shop_side["Product image URL"] = image_url("brine-jar-side.jpg")
    shop_side["Image position"] = "2"
    shop_ladle = squarespace_shop(
        shop_head,
        handle="fern-sample-ladle",
        title="Fern Sample Ladle",
        description="A practice ladle from the fictional Sample Harbor Goods catalog.",
        product_type="Ladles",
        tags="practice",
        sku="LADLE-FERN",
        price="12.00",
        stock="5",
        tracked=True,
        options=[("Default Title", "Default Title")],
        first=True,
        image=image_url("fern-ladle.jpg"),
        position="1",
    )
    shop_cloth = squarespace_shop(
        shop_head,
        handle="mist-sample-cloth",
        title="Mist Sample Cloth",
        description="A practice cloth from the fictional Sample Harbor Goods catalog.",
        product_type="Cloths",
        tags="practice",
        sku="CLOTH-MIST",
        price="28.00",
        stock="",
        tracked=False,
        options=[("Default Title", "Default Title")],
        first=True,
        image=image_url("mist-cloth.jpg"),
        position="1",
    )
    return (
        sq_head,
        [jar, jar_large, ladle, cloth],
        shop_head,
        [shop_small, shop_large, shop_side, shop_ladle, shop_cloth],
    )


# Header of the official Wix older-catalog template
# https://manage.wix.com/_api/wix-ecommerce-catalog-sync-web/sync/export/csv/template
# downloaded 2026-10-29 and again 2026-11-07. 50 columns. The new catalog is
# not this header.
WIX_COLUMNS = [
    "handleId",
    "fieldType",
    "name",
    "description",
    "productImageUrl",
    "collection",
    "sku",
    "ribbon",
    "price",
    "surcharge",
    "visible",
    "discountMode",
    "discountValue",
    "inventory",
    "weight",
    "cost",
    "productOptionName1",
    "productOptionType1",
    "productOptionDescription1",
    "productOptionName2",
    "productOptionType2",
    "productOptionDescription2",
    "productOptionName3",
    "productOptionType3",
    "productOptionDescription3",
    "productOptionName4",
    "productOptionType4",
    "productOptionDescription4",
    "productOptionName5",
    "productOptionType5",
    "productOptionDescription5",
    "productOptionName6",
    "productOptionType6",
    "productOptionDescription6",
    "additionalInfoTitle1",
    "additionalInfoDescription1",
    "additionalInfoTitle2",
    "additionalInfoDescription2",
    "additionalInfoTitle3",
    "additionalInfoDescription3",
    "additionalInfoTitle4",
    "additionalInfoDescription4",
    "additionalInfoTitle5",
    "additionalInfoDescription5",
    "additionalInfoTitle6",
    "additionalInfoDescription6",
    "customTextField1",
    "customTextCharLimit1",
    "customTextMandatory1",
    "brand",
]


def wix_row(headers: list[str], **fields: str) -> dict[str, str]:
    row = blank(headers)
    row.update(fields)
    return row


def wix_shop(
    headers: list[str],
    *,
    handle: str,
    sku: str,
    price: str,
    stock: str,
    options: list[tuple[str, str]],
    first: bool,
    title: str = "",
    description: str = "",
    product_type: str = "",
    tags: str = "",
    compare: str = "",
    cost: str = "",
    image: str = "",
    position: str = "",
) -> dict[str, str]:
    """One Shopify row for the older Wix catalog pair.

    Weight stays blank: the Wix file has a number and no unit.
    Status active is a practice-file choice. The migration app path is drafts.
    """
    row = blank(headers)
    row["URL handle"] = handle
    row["SKU"] = sku
    row["Price"] = price
    row["Compare-at price"] = compare
    row["Cost per item"] = cost
    row["Charge tax"] = "true"
    row["Requires shipping"] = "true"
    row["Fulfillment service"] = "manual"
    row["Inventory tracker"] = "shopify"
    row["Inventory quantity"] = stock
    row["Continue selling when out of stock"] = "deny"
    for index, (name, value) in enumerate(options, start=1):
        row[f"Option{index} value"] = value
        if first:
            row[f"Option{index} name"] = name
    if first:
        row["Title"] = title
        row["Description"] = description
        row["Vendor"] = VENDOR
        row["Type"] = product_type
        row["Tags"] = tags
        row["Published on online store"] = "true"
        row["Status"] = "active"
        row["Gift card"] = "false"
    if image:
        row["Product image URL"] = image
        row["Image position"] = position
    return row


def build_wix_basic() -> tuple[list[str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    """Three fictional products in the 50-column older-catalog template.

    Kelp Sample Pitcher has a Product row and two Variant rows. The Large
    variant's surcharge is 4.00, so its Shopify Price is 36.00. A blank
    surcharge on Small keeps the product price, 32.00. That blank is this
    file's reading of a missing surcharge. Reed Sample Ladle is PERCENT 15
    of 24.00, which is 20.40 with no remainder. Cove Sample Cloth is AMOUNT
    4.50, and this file subtracts that from 28.00. Wix does not state either
    formula. Weight stays in the Wix file. The unit is not a column, so the
    Shopify grams cell is blank.
    """
    wix_head = list(WIX_COLUMNS)
    shop_head = list(SHOPIFY_COLUMNS)
    pitcher_images = f"{image_url('kelp-pitcher.jpg')};{image_url('kelp-pitcher-side.jpg')}"
    pitcher = wix_row(
        wix_head,
        handleId="kelp-sample-pitcher",
        fieldType="Product",
        name="Kelp Sample Pitcher",
        description="A practice pitcher from the fictional Sample Harbor Goods catalog.",
        productImageUrl=pitcher_images,
        collection="Pitchers",
        sku="PITCHER-KELP",
        price="32.00",
        visible="TRUE",
        weight="0.600",
        cost="9.00",
        productOptionName1="Size",
        productOptionType1="DROP_DOWN",
        productOptionDescription1="Small;Large",
        brand=VENDOR,
    )
    pitcher_small = wix_row(
        wix_head,
        handleId="kelp-sample-pitcher",
        fieldType="Variant",
        sku="PITCHER-S",
        visible="TRUE",
        inventory="6",
        weight="0.520",
        productOptionDescription1="Small",
    )
    pitcher_large = wix_row(
        wix_head,
        handleId="kelp-sample-pitcher",
        fieldType="Variant",
        sku="PITCHER-L",
        surcharge="4.00",
        visible="TRUE",
        inventory="4",
        weight="0.720",
        productOptionDescription1="Large",
    )
    ladle = wix_row(
        wix_head,
        handleId="reed-sample-ladle",
        fieldType="Product",
        name="Reed Sample Ladle",
        description="A practice ladle from the fictional Sample Harbor Goods catalog.",
        productImageUrl=image_url("reed-ladle.jpg"),
        collection="Ladles",
        sku="LADLE-REED",
        price="24.00",
        visible="TRUE",
        discountMode="PERCENT",
        discountValue="15",
        inventory="5",
        weight="0.250",
        cost="6.00",
        brand=VENDOR,
    )
    cloth = wix_row(
        wix_head,
        handleId="cove-sample-cloth",
        fieldType="Product",
        name="Cove Sample Cloth",
        description="A practice cloth from the fictional Sample Harbor Goods catalog.",
        productImageUrl=image_url("cove-cloth.jpg"),
        collection="Cloths",
        sku="CLOTH-COVE",
        price="28.00",
        visible="TRUE",
        discountMode="AMOUNT",
        discountValue="4.50",
        inventory="8",
        weight="0.180",
        cost="7.00",
        brand=VENDOR,
    )
    shop_small = wix_shop(
        shop_head,
        handle="kelp-sample-pitcher",
        title="Kelp Sample Pitcher",
        description="A practice pitcher from the fictional Sample Harbor Goods catalog.",
        product_type="Pitchers",
        tags="practice",
        sku="PITCHER-S",
        price="32.00",
        cost="9.00",
        stock="6",
        options=[("Size", "Small")],
        first=True,
        image=image_url("kelp-pitcher.jpg"),
        position="1",
    )
    shop_large = wix_shop(
        shop_head,
        handle="kelp-sample-pitcher",
        sku="PITCHER-L",
        price="36.00",
        cost="9.00",
        stock="4",
        options=[("Size", "Large")],
        first=False,
    )
    shop_side = blank(shop_head)
    shop_side["URL handle"] = "kelp-sample-pitcher"
    shop_side["Product image URL"] = image_url("kelp-pitcher-side.jpg")
    shop_side["Image position"] = "2"
    shop_ladle = wix_shop(
        shop_head,
        handle="reed-sample-ladle",
        title="Reed Sample Ladle",
        description="A practice ladle from the fictional Sample Harbor Goods catalog.",
        product_type="Ladles",
        tags="practice",
        sku="LADLE-REED",
        price="20.40",
        compare="24.00",
        cost="6.00",
        stock="5",
        options=[("Default Title", "Default Title")],
        first=True,
        image=image_url("reed-ladle.jpg"),
        position="1",
    )
    shop_cloth = wix_shop(
        shop_head,
        handle="cove-sample-cloth",
        title="Cove Sample Cloth",
        description="A practice cloth from the fictional Sample Harbor Goods catalog.",
        product_type="Cloths",
        tags="practice",
        sku="CLOTH-COVE",
        price="23.50",
        compare="28.00",
        cost="7.00",
        stock="8",
        options=[("Default Title", "Default Title")],
        first=True,
        image=image_url("cove-cloth.jpg"),
        position="1",
    )
    return (
        wix_head,
        [pitcher, pitcher_small, pitcher_large, ladle, cloth],
        shop_head,
        [shop_small, shop_large, shop_side, shop_ladle, shop_cloth],
    )


def main() -> None:
    catalogs = {
        "small-clean": build_small_clean(),
        "common-mistakes": build_common_mistakes(),
        "variable-products": build_variable_products(),
    }
    for name, (woo_head, woo_rows, shop_head, shop_rows) in catalogs.items():
        folder = OUT / name
        write_csv(folder / "woocommerce.csv", woo_head, woo_rows)
        write_csv(folder / "shopify.csv", shop_head, shop_rows)
    magento_head, magento_rows, shop_head, shop_rows = build_magento_basic()
    folder = OUT / "magento-basic"
    write_csv(folder / "magento.csv", magento_head, magento_rows)
    write_csv(folder / "shopify.csv", shop_head, shop_rows)
    bc_head, bc_rows, shop_head, shop_rows = build_bigcommerce_basic()
    folder = OUT / "bigcommerce-basic"
    write_csv(folder / "bigcommerce.csv", bc_head, bc_rows)
    write_csv(folder / "shopify.csv", shop_head, shop_rows)
    sq_head, sq_rows, shop_head, shop_rows = build_squarespace_basic()
    folder = OUT / "squarespace-basic"
    write_csv(folder / "squarespace.csv", sq_head, sq_rows)
    write_csv(folder / "shopify.csv", shop_head, shop_rows)
    wix_head, wix_rows, shop_head, shop_rows = build_wix_basic()
    folder = OUT / "wix-basic"
    write_csv(folder / "wix.csv", wix_head, wix_rows)
    write_csv(folder / "shopify.csv", shop_head, shop_rows)


if __name__ == "__main__":
    main()
