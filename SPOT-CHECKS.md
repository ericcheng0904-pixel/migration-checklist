# Spot checks

These checks answer two questions: how many products and variants are in each file, and which SKUs are in one file but not the other. They are not a full comparison. Do them on a copy of the export, and import the SKU column as text so a spreadsheet does not drop a leading zero while you look.

Examples below use `test-catalogs/common-mistakes/`. The variable parent SKU `TOTE` is in the WooCommerce file and not in the Shopify file. That is expected. The missing variant is `TOTE-L`.

## Spreadsheet

1. Open both CSVs. Do not let the sheet convert SKUs to numbers.
2. On the WooCommerce sheet, pivot `Type`. Count `simple` and `variation` as sellable rows. Do not count `variable` parents as variants.
3. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL. That is the variant count. Count distinct `URL handle` values. That is the product count. A row with a handle and no SKU is an extra image, not a variant.
4. `XLOOKUP` or `VLOOKUP` the WooCommerce `SKU` against the Shopify `SKU`, then the other way. Sort the misses.
5. For a SKU that exists in both, compare WooCommerce `Sale price` and `Regular price` with Shopify `Price` and `Compare-at price`.
6. Sort SKUs and look for a short number next to a matching code that still has its leading zero.

On `common-mistakes`, the sellable WooCommerce SKUs that are absent from Shopify are `01482` and `TOTE-L`. The Shopify SKU that is absent from WooCommerce is `1482`. `SOAP-PINE` and `OIL-PINE` both come back, and they share one handle, so a SKU lookup alone will not show that mistake. Filter the Shopify sheet for duplicate `URL handle` values where `Title` is filled in.

## Python

The standard library is enough. From the repository root:

```bash
python3 - << 'PY'
import csv
from collections import Counter

def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

woo = load("test-catalogs/common-mistakes/woocommerce.csv")
shop = load("test-catalogs/common-mistakes/shopify.csv")

print("WooCommerce types", Counter(row["Type"] for row in woo))
woo_skus = {row["SKU"] for row in woo if row["Type"] != "variable" and row["SKU"]}
shop_skus = {row["SKU"] for row in shop if row["SKU"]}
handles = {row["URL handle"] for row in shop if row["URL handle"]}
print("sellable WooCommerce SKUs", len(woo_skus))
print("Shopify SKUs", len(shop_skus))
print("Shopify products", len(handles))
print("only in WooCommerce", sorted(woo_skus - shop_skus))
print("only in Shopify", sorted(shop_skus - woo_skus))
PY
```

That prints:

```text
WooCommerce types Counter({'simple': 7, 'variation': 3, 'variable': 1})
sellable WooCommerce SKUs 10
Shopify SKUs 9
Shopify products 7
only in WooCommerce ['01482', 'TOTE-L']
only in Shopify ['1482']
```

`small-clean` has 4 sellable WooCommerce SKUs, 4 Shopify SKUs, and 5 Shopify rows because the mug has a second image row. The SKU sets are equal. `variable-products` has 2 + 4 + 16 variations in WooCommerce and 2 + 3 + 8 SKUs in Shopify.

## csvkit

[csvkit](https://csvkit.readthedocs.io/) is optional. The same counts, with the variable parent still included in the WooCommerce SKU list:

```bash
csvcut -c Type test-catalogs/common-mistakes/woocommerce.csv | tail -n +2 | sort | uniq -c
csvcut -c SKU test-catalogs/common-mistakes/woocommerce.csv | tail -n +2 | sed '/^$/d' | sort > /tmp/woo-skus.txt
csvcut -c SKU test-catalogs/common-mistakes/shopify.csv | tail -n +2 | sed '/^$/d' | sort > /tmp/shop-skus.txt
comm -23 /tmp/woo-skus.txt /tmp/shop-skus.txt
comm -13 /tmp/woo-skus.txt /tmp/shop-skus.txt
```

`comm -23` prints SKUs only in the WooCommerce file (`01482`, `TOTE`, `TOTE-L`). `comm -13` prints SKUs only in the Shopify file (`1482`). Drop `TOTE` by hand, or exclude variable parents before `csvcut`:

```bash
csvgrep -c Type -r '^(simple|variation)$' test-catalogs/common-mistakes/woocommerce.csv \
  | csvcut -c SKU | tail -n +2 | sort > /tmp/woo-skus.txt
```

## Magento 2

`test-catalogs/magento-basic/` is a Magento product export (`magento.csv`), not a WooCommerce file. Count rows with `product_type` `simple` as the sellable variants. Do not count the `configurable` row. Do not count a second row that repeats a SKU with `store_view_code` set: in this file that row is another view of the same product. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the simple SKUs are `WICK-S` and `WICK-L`. Both are in the Shopify file. `WICK-LANTERN` is the configurable parent and is not a Shopify SKU. The `cove` row names the same parent `Wick Cove Lantern` and is not its own product. [MAGENTO.md](MAGENTO.md) is the checklist for a real export.

## BigCommerce

`test-catalogs/bigcommerce-basic/` is a legacy Bulk Edit export (`bigcommerce.csv`), not a WooCommerce file. For a product that has SKU rows, count the rows with Item Type `SKU` as the sellable variants and do not count its `Product` row. A product with no SKU rows is one variant, and its `Product` row holds the SKU. Do not count a `Rule` row. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the product has SKU rows, so the SKU rows are `PITCHER-S` and `PITCHER-L`. Both are in the Shopify file. `PITCHER-NETTLE` is the product SKU and is not a Shopify SKU. The Rule row repeats `PITCHER-L` and is not a second variant. [BIGCOMMERCE.md](BIGCOMMERCE.md) is the checklist for a real export.

## Squarespace

`test-catalogs/squarespace-basic/` is a Squarespace product export (`squarespace.csv`), not a WooCommerce file. Count every product row and option row, including the first product row of a product that has option rows. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the SKUs are `JAR-S`, `JAR-L`, `LADLE-FERN`, and `CLOTH-MIST`. All four are in the Shopify file. The jar's second image row has no SKU and is not a variant. [SQUARESPACE.md](SQUARESPACE.md) is the checklist for a real export.
