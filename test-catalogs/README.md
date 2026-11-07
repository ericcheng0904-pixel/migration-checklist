# Test catalogs

Six fictional before-and-after pairs for a store called Sample Harbor Goods. Nothing here is a real product, brand, or person. Image URLs use the reserved host `cdn.example.test`.

Three pairs are a WooCommerce built-in product export and a Shopify product CSV. `magento-basic` is a Magento 2 product export and the matching Shopify product CSV. `bigcommerce-basic` is a legacy Bulk Edit export and the matching Shopify product CSV. `squarespace-basic` is a Squarespace product export and the matching Shopify product CSV. Regenerate them with:

```bash
python3 scripts/make-test-catalogs.py
```

The script overwrites the twelve CSV files and does not change this README. A second run matches the first byte for byte.

## Column names

WooCommerce headers follow the [built-in product CSV schema](https://woocommerce.com/document/product-csv-importer-exporter/). The weight and dimension headers are `Weight (kg)`, `Length (cm)`, `Width (cm)`, and `Height (cm)` because this fictional store uses those units. The schema writes them as `Weight (unit)` and so on; the exporter inserts the store's unit, and `kg` and `cm` are units WooCommerce ships. The published [sample CSV](https://github.com/woocommerce/woocommerce/blob/trunk/plugins/woocommerce/sample-data/sample_products.csv) uses `Weight (lbs)` and `Length (in)` because that sample store uses pounds and inches. Check a fresh export from the store you are migrating. [Products settings](https://woocommerce.com/document/configuring-woocommerce-settings/products/) [Unit abbreviations](https://github.com/woocommerce/woocommerce/blob/trunk/plugins/woocommerce/i18n/units.php) [Exporter column labels](https://woocommerce.github.io/code-reference/files/woocommerce-includes-export-class-wc-product-csv-exporter.html)

Custom meta on the small-clean candle is `Meta: care_note`. The schema's example is `meta:product_depth`. The sample file and the exporter label the column `Meta: your_key`. These files follow the exporter label.

Shopify headers are the sample template linked from the product CSV guide, as downloaded on 2026-10-24:

[product_template.csv](https://help.shopify.com/cdn/shopifycloud/product-knowledge/production/csv/product_template.csv)

That file and the [column table](https://help.shopify.com/en/manual/products/import-export/using-csv) on the same guide do not match on every name. The template says `Variant Barcodes` and `Option1 Linked To`. The table says `Barcodes` and `Option1 LinkedTo`. The template also has `Tax code` and unit-price columns the table does not list. The [WooCommerce migration guide](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-woocommerce) still maps to older names such as `Variant SKU`, `Variant Price`, and `Body (HTML)`, which the [common import problems](https://help.shopify.com/en/manual/products/import-export/common-import-issues) page also shows. These practice files use the sample template's header row. Check a fresh export from the destination store before you rename columns for real.

Values use the lowercase spellings the column table lists (`active`, `draft`, `true`, `false`, `deny`). The sample template mixes `Active` and `active`, and writes `TRUE` and `DENY`.

Google Shopping columns and `Color (product.metafields.shopify.color-pattern)` are present because they are in the template. They are empty. `Product category` is empty so these files do not invent a taxonomy path.

## What a match means

`small-clean` uses the following mapping. `common-mistakes` and `variable-products` use it too, except where a planted difference says otherwise. `magento-basic`, `bigcommerce-basic`, and `squarespace-basic` have their own mappings, further down.

- WooCommerce `Name` becomes Shopify `Title`. The handle is the title in lower case with spaces turned into hyphens.
- `Description` is copied. `Short description` is not copied; the Shopify product CSV has no column for it.
- `Published` `1` becomes `Status` `active` and `Published on online store` `true`. `Published` `-1` stays `draft` and `false`.
- If `Sale price` is set, Shopify `Price` is the sale price and `Compare-at price` is `Regular price`. If there is no sale, `Price` is `Regular price` and `Compare-at price` is empty.
- A numeric `Stock` becomes `Inventory tracker` `shopify`, the same `Inventory quantity`, and `Continue selling when out of stock` `deny` (these rows do not allow backorders). A blank `Stock` leaves tracking empty.
- `Weight (kg)` times 1000, with no remainder, becomes `Weight value (grams)`. `Weight unit for display` is `kg`. The Shopify guide's examples are 5.125 kilograms entered as `5125`, and 4 pounds entered as `1814`.
- Length, width, and height stay in the WooCommerce file only. They are not copied into Shopify's packed-product columns.
- Each image URL is a `Product image URL` row. The WooCommerce file has no alt text column, and the [core importer cannot update alt text](https://woocommerce.com/document/product-csv-importer-exporter/), so alt text is blank here.
- `Categories` become the Shopify `Type` label (the leaf name, such as `Candles`). They are not a `Collection` column. That column is import-only and is not part of an export.
- `Tags` are copied. `Tax status` `taxable` becomes `Charge tax` `true`.
- A simple product uses option name `Title` and option value `Default Title`, which is what the [inventory CSV guide](https://help.shopify.com/en/manual/inventory-and-locations/setup/inventory-csv) says for a product with no options. The product CSV guide says the Option1 name should be `Default Title`. Those two pages disagree.
- A `variable` parent row is not a Shopify variant. Variation rows are. The parent SKU (`TOTE`, `MUG-CEDAR`, `APRON-LINEN`, `PACK-TRAIL`) is not in the Shopify file.
- `Meta: care_note` becomes `Care note (product.metafields.custom.care_note)`. On the mug, the Material attribute is not a variation attribute, so it becomes `Material (product.metafields.custom.material)` and is not a Shopify option.

Prices are bare numbers. The fictional store did not put a currency symbol in the cells. [Shop currency](https://woocommerce.com/document/shop-currency/) [Store currency](https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/setup-business-settings)

## small-clean

No planted differences. Four simple products. `Tide Sample Mug` is on sale (`24.00` regular, `19.00` sale) and has two images. `Draft Sample Coaster` is `Published` `-1` in WooCommerce and `draft` in Shopify. `Pebble Sample Candle` carries the care-note metafield.

## common-mistakes

`Cedar Sample Spoon` (`SPOON-CEDAR`) matches, so a comparison is not entirely red. The planted differences are:

- `missing-variant`. WooCommerce variation `TOTE-L` (Oak Sample Tote, Large) is not in the Shopify file. `TOTE-S` and `TOTE-M` are.
- `sale-price-mapped-to-price`. `LANTERN-01` has regular price `42.00` and sale price `36.00`. The Shopify `Price` is `36.00` and `Compare-at price` is empty, so the regular price is gone.
- `dropped-leading-zero`. WooCommerce SKU `01482` (Sample Tag Ribbon) is Shopify SKU `1482`.
- `draft-published`. `TRAY-DRAFT` is WooCommerce `Published` `-1`, and the Shopify row is `Status` `active` with `Published on online store` `true`.
- `lost-image`. `BOWL-MOSS` lists `moss-bowl.jpg` and `moss-bowl-side.jpg`. The Shopify file has only the first URL.
- `duplicated-handle`. `SOAP-PINE` (Pine Sample Soap) and `OIL-PINE` (Pine Sample Oil) both use the Shopify URL handle `pine-sample-soap`.

## variable-products

`Cedar Sample Mug` is the clean example. WooCommerce attribute Size (`8 oz`, `12 oz`) becomes Shopify option Size. `MUG-8OZ` and `MUG-12OZ` match on price, weight, and option value. Material `Stone` is on the parent only and is the Material metafield, not an option.

Planted differences:

- `missing-apron-variant`. `APRON-L-INK` (Linen Sample Apron, Large / Ink) is in WooCommerce and not in Shopify. `APRON-S-SAND`, `APRON-S-INK`, and `APRON-L-SAND` are present with the same option values.
- `fourth-option-dropped`. Trail Sample Pack uses four variation attributes: Size, Color, Strap, and Pocket. Shopify has three options, Size, Color, and Strap. Pocket is not an option. The eight Pocket `No` SKUs are missing, including `PACK-S-MOSS-CLIP-N`. The eight Pocket `Yes` SKUs, which end in `-Y`, are present. A Shopify product can have up to three options. [Adding variants](https://help.shopify.com/en/manual/products/variants/add-variants)

## Magento columns

`magento-basic/magento.csv` uses a subset of the columns in the [product data attributes reference](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-attributes-product), checked on 2026-10-27. A full export has more columns, including stock-configuration flags and the service columns whose names start with an underscore. Check a fresh export. The Shopify file uses the same sample-template header as the other pairs, plus `Finish (product.metafields.custom.finish)`.

In this practice file the weight cells are written in kilograms, which is the store view's weight unit. The attributes reference does not say the cell uses that unit. Check in your own export. [Weight unit](https://experienceleague.adobe.com/en/docs/commerce-admin/config/general/general) [Product data attributes](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-attributes-product)

## magento-basic

One labelled hazard, `special-price-kept-past-its-dates`. Everything else in the pair matches. One configurable product, `Wick Sample Lantern` (`WICK-LANTERN`), and two simple variations, `WICK-S` and `WICK-L`. A second row repeats `WICK-LANTERN` with `store_view_code` `cove` and the name `Wick Cove Lantern`. That row is not a second Shopify product.

The attributes reference says a blank `store_view_code` means the default store view. The CSV structure page says any row that begins with a value in the SKU column starts a new product record. ACSD-59378 is a bug report, fixed in 2.4.7, that describes an empty `store_view_code` as the All Store Views scope. This practice file is one shape: blank on the main rows, and `cove` on the translated name. Check in your own export. [Product data attributes](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-attributes-product) [CSV files](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-csv) [Store-view URL rewrites on import](https://experienceleague.adobe.com/en/docs/commerce-operations/tools/quality-patches-tool/patches-available-in-qpt/v1-1-50/acsd-59378-store-level-url-rewrites-incorrectly-updated-during-import)

Mapping used in this pair:

- The configurable row is not a Shopify variant. `WICK-LANTERN` is not in the Shopify file. `configurable_variations` is `sku=WICK-S,size=Small|sku=WICK-L,size=Large`, which is the pipe-separated shape in the configurable import example. `configurable_variation_labels` is `Choose Size:`, one of the examples in the attributes reference. The Shopify option name is `Size` and the values are `Small` and `Large`. [Import configurable products](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/examples/data-transfer-configurable-products)
- The parent's `price` is `40.00` and its `weight` is `0.600`. Neither is copied. A configurable product's displayed price and quantity come from its variations. [Configurable product](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/types/product-create-configurable)
- `WICK-S` is the labelled hazard `special-price-kept-past-its-dates`. It has `price` `36.00` and `special_price` `30.00`, so Shopify `Price` is `30.00` and `Compare-at price` is `36.00`. `special_price_from_date` is `2026-11-01` and `special_price_to_date` is `2026-11-30`. Those dates stay only in the Magento file. The product CSV has no date columns, so the lower price does not turn on at the start date or turn off at the end date. Copy `special_price` into `Price` only when that special price is the amount the customer pays. The attributes reference does not say how a date is written in the cell. This file uses `YYYY-MM-DD`. Check in your own export. `WICK-L` has no special price: Shopify `Price` is `42.00` and `Compare-at price` is empty.
- `product_online` `1` and the parent's visibility `Catalog, Search` become `Status` `active` and `Published on online store` `true`. Both variations are `Not Visible Individually`. They are Shopify variants, not extra products. Their `url_key` values are not Shopify handles. The handle is the parent's `url_key`, `wick-sample-lantern`.
- In this practice file the weight cells are written in kilograms. `weight` times 1000, with no remainder, becomes `Weight value (grams)`, so `0.520` is `520`. The attributes reference does not say the cell uses the store view's weight unit. Check in your own export. `Weight unit for display` is `kg`, because the Shopify column's values are `g`, `kg`, `lb`, and `oz`, and `kgs` is not one of them.
- `qty` on the variation becomes `Inventory quantity`, with `Inventory tracker` `shopify` because `manage_stock` is `1`. The parent's quantity is empty.
- `tax_class_name` `Taxable Goods` becomes `Charge tax` `true`. `short_description` and `meta_keywords` are not copied. The product CSV has no column for either. `meta_title` and `meta_description` become `SEO title` and `SEO description`.
- Vendor `Sample Harbor Goods` and Tags `practice` are fictional store-level values. They are not mapped from a Magento column. Tags is not a copy of `meta_keywords`.
- `additional_attributes` on the parent is the single pair `finish=Brass`. It becomes `Finish (product.metafields.custom.finish)`. A real cell can hold more than one pair. Check the separators in your own export.
- Image cells are relative paths, which is what an export stores (`/w/i/wick-lantern.jpg` and the same shape for the other files). They are not public URLs. The Shopify file uses `https://cdn.example.test/sample-harbor/` plus the file name. `base_image` and `small_image` are the same file, so that URL is listed once. `thumbnail_image` (`wick-lantern-mark.jpg`) and `additional_images` (`wick-lantern-side.jpg`) are further `Product image URL` rows. Each variation's `base_image` is that variant's `Variant image URL`. Labels stay in the Magento file. The attributes reference does not call those labels alt text, so `Image alt text` is blank here.
- The category path `Harbor/Lanterns` is not copied into `Collection`. That column is import-only. The leaf name is the Shopify `Type`, `Lanterns`. `product_websites` is `harbor` and is not a Shopify column.

## BigCommerce columns

`bigcommerce-basic/bigcommerce.csv` uses a subset of the columns in the [legacy supported fields](https://support.bigcommerce.com/s/article/Legacy-Product-Fields) list for the Bulk Edit template, checked on 2026-10-27. A full Bulk Edit export has more columns. This file leaves out Option Set and Option Set Align. The fields page says to delete those two on the v3 experience, or the import can duplicate options. Check a fresh export. The Shopify file uses the same sample-template header as the other pairs.

In this practice file the weight cells are written in kilograms. The fields page says "Use numbers only; no units" and does not name the unit. Check in your own export. [Legacy product fields](https://support.bigcommerce.com/s/article/Legacy-Product-Fields)

`Track Inventory` is `by option` with a normal space. The fields page joins those two words with a non-breaking space. Check in your own export.

## bigcommerce-basic

One labelled hazard, `retail-copied-into-compare-at`. Everything else in the pair follows the mapping below. One product, `Nettle Sample Pitcher` (`PITCHER-NETTLE`), two SKU rows, `PITCHER-S` and `PITCHER-L`, and one Rule row for `PITCHER-L`.

The fields page says "Type in Product for products, SKU for variants, and Rule for variant or modifier rules." This file is shaped like an export of a product that already exists, so Product ID is filled on every row, including the Rule row. The complex-attributes page says, for creating a new variant rule, to leave the Product ID and Product Name fields blank. The fields page calls Product ID "The system-generated product identifier" and does not say that a SKU row's Product ID is the variant id. `5102` and `5103` are the SKU rows' ids in this file. Check in your own export. [Legacy product fields](https://support.bigcommerce.com/s/article/Legacy-Product-Fields) [Updating products](https://support.bigcommerce.com/s/article/Updating-via-Import) [Complex attributes](https://support.bigcommerce.com/s/article/Complex-Attributes)

Mapping used in this pair:

- When a product has SKU rows, the Product row is not also a Shopify variant. `PITCHER-NETTLE` is not in the Shopify file. The SKU rows are. A product with no SKU rows is one variant and keeps the Product row's SKU. This file has SKU rows. Option text is in Product Name: `[RB]Size=Small` and `[RB]Size=Large`. The Shopify option name is `Size` and the values are `Small` and `Large`. A second option is written `[RB]Size=Small,[CS]Color=Blue:#0000FF` on the complex-attributes, first-product, and updating pages, a comma with no spaces. This file has one option, so no comma is in the cell. [Complex attributes](https://support.bigcommerce.com/s/article/Complex-Attributes) [Importing your first product](https://support.bigcommerce.com/s/article/Importing-Your-First-Product) [Updating products](https://support.bigcommerce.com/s/article/Updating-via-Import)
- The product's Price is `32.00`, its Retail Price is `44.00`, and Sale Price is empty. `PITCHER-S` displays Price `32.00`. `PITCHER-L` displays Price `36.00`, and its Rule row sets Price to `[FIXED]36` and Product Weight to `[FIXED]0.720`. The documented price example is `[FIXED]25`. "Variant weight and price are displayed in the SKU row, but must be updated in the Rule row." The parent's weight `0.600` is not copied. [Updating products](https://support.bigcommerce.com/s/article/Updating-via-Import) [Complex attributes](https://support.bigcommerce.com/s/article/Complex-Attributes)
- `retail-copied-into-compare-at` is the labelled hazard. Both Shopify variants copy Retail Price `44.00` into Compare-at price, and they copy the SKU row's displayed price into Price (`32.00` and `36.00`). Sale Price is empty, so this is not a BigCommerce sale price. BigCommerce itself shows Retail Price struck through ("will show it with a strikethrough"), so copying it can be right. The hazard is copying it without deciding that it is the previous price. Shopify says Compare-at price must be higher than Price to display the sale price, and that the theme controls whether and where a sale shows. [Sale pricing](https://support.bigcommerce.com/s/article/Using-Sale-Pricing) [Shopify sale prices](https://help.shopify.com/en/manual/products/details/product-pricing/sale-pricing)
- Cost Price `12.00` becomes Cost per item on both variants. The fields page describes Cost Price as the cost of the product for accounting. Vendor `Sample Harbor Goods`, Tags `practice`, Charge tax `true`, and Fulfillment service `manual` are fictional store-level values. They are not mapped from a column in this file.
- Product Visible? `Y` and Allow Purchases? `Y` become Status `active` and Published on online store `true`. Product Availability is `Ships in two sample days`. That cell is a shipping note, not a status, and it is not copied. The handle is the Product URL without its leading and trailing slash, `nettle-sample-pitcher`. Redirect Old URL? is `N`.
- In this practice file the weight cells are written in kilograms. Product Weight times 1000, with no remainder, becomes Weight value (grams), so `0.520` is `520` and `0.720` is `720`. The fields page does not name the unit. Check in your own export. Weight unit for display is `kg`.
- Current Stock Level on the SKU row becomes Inventory quantity, with Inventory tracker `shopify`, because Track Inventory is `by option`. The product row's stock cell is empty. Continue selling when out of stock is `deny`. This file has no backorder column, so that value is a practice-file choice. Allow Purchases? is not that column.
- The product image is a full URL in `Product Image File - 1`, which is what the fields page calls Product Image Path in the Bulk Edit template. Image description `Nettle pitcher front` becomes Image alt text, because that column is "The alt tag". The Rule row's `Product Image File - 1` becomes the large variant's Variant image URL. A real export can hold the image's WebDAV file path in that column, because the updating page says the path is "present regardless of how the image was added." Check in your own export. [Legacy product fields](https://support.bigcommerce.com/s/article/Legacy-Product-Fields) [Updating products](https://support.bigcommerce.com/s/article/Updating-via-Import)
- The category path `Harbor/Pitchers` is not copied into Collection. That column is import-only. The leaf name is the Shopify Type, `Pitchers`.

## Squarespace columns

`squarespace-basic/squarespace.csv` uses the 26 columns in the [official example](https://assets.squarespace.com/universal/commerce/product_import-v2.csv), checked on 2026-10-27. The header runs from `Product ID [Non Editable]` through `Hosted Image URLs`. This file has a `Product Page` column, as the example does. The export article says the export adds a column for pages and does not name it. This file has no GTIN or MPN column. Only the two move-between-sites tables on the import page list both; the bulk-edit and import-from-another-platform tables do not. Check in your own export. [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) The Shopify file uses the same sample-template header as the other pairs.

In this practice file the weight, length, width, and height cells are numbers. The import article says that after import, dimensions match the store's measurement standard, and it does not name the unit. The Shopify grams cells are blank. A blank grams cell's default on import is 0. Check in your own export. [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv)

`Product Type [Non Editable]` is `PHYSICAL`, which is what the example writes. The import-from-another-platform table says to enter Physical or Service. `Stock` for the cloth is `Unlimited`. The import table says to enter unlimited. Check the characters in your own export. [Example CSV](https://assets.squarespace.com/universal/commerce/product_import-v2.csv)

Categories in this file are names (`Jars`, `Ladles`, `Cloths`), which is the example's shape (`Sour Stuff`). The import tables use a slug path such as `/clothing/blouses`. Shopify's Squarespace guide says the export uses URL paths and to replace each path with one product type. Check in your own export. [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace)

`Product ID [Non Editable]` is filled only on the first row of each product (`8801` on the jar). The docs do not say whether an export repeats it on option rows. Variant ID is filled on every row in this file. The example leaves both id columns blank, and the import-from-another-platform tables say to leave them blank. Check in your own export. [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) [Example CSV](https://assets.squarespace.com/universal/commerce/product_import-v2.csv)

## squarespace-basic

Two labelled cases, `sale-price-ignored-when-on-sale-is-no` and `unlimited-stock-not-tracked`. Everything else in the pair follows the mapping below. One product with an option row, `Brine Sample Jar`, one simple product whose Sale Price is filled while On Sale is No, `Fern Sample Ladle`, and one simple product with `Unlimited` stock, `Mist Sample Cloth`.

The first product row of a variant product is also the first variant. `JAR-S` is that row. `JAR-L` is the option row. A product with no options is one row. The import article calls its sample row 2 "a single product with no variants". [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv)

Mapping used in this pair:

- `JAR-S` is On Sale `Yes`, Price `18.00`, Sale Price `14.00`. Shopify Price is `14.00` and Compare-at price is `18.00`. `sale-price-ignored-when-on-sale-is-no` is `JAR-L` (Price `22.00`, Sale Price `16.00`, On Sale `No`) and `LADLE-FERN` (Price `12.00`, Sale Price `9.00`, On Sale `No`). Shopify Price is the regular price and Compare-at price is empty. The import table says to enter a sale price only when On Sale is Yes. The official example still fills Sale Price on No rows. [Importing products](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace)
- `unlimited-stock-not-tracked` is `CLOTH-MIST`. Stock is `Unlimited`. Inventory tracker and Inventory quantity are blank, so the variant is not tracked. Stripping the word would leave an empty quantity, and an empty quantity's default is 0 if tracking stays on. Continue selling when out of stock is `deny` on the numeric stock rows. This file has no backorder column, so that value is a practice-file choice. The cloth leaves it blank. [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv)
- The jar's option name is `Size`, values `Small` and `Large`. Squarespace repeats the option name on the option row. [Example CSV](https://assets.squarespace.com/universal/commerce/product_import-v2.csv) Shopify's option name is on the first variant row only, as in Shopify's [sample product template](https://help.shopify.com/cdn/shopifycloud/product-knowledge/production/csv/product_template.csv). `LADLE-FERN` and `CLOTH-MIST` have no Squarespace options. Their Option1 name and Option1 value are `Default Title`, as a practice-file choice. The product CSV guide says Option1 name should be `Default Title` if a product has only one option, and it does not say what to write for a product with no options or for the value. [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv)
- Product URL is the slug, `brine-sample-jar`, on the first jar row only. The handle is copied onto the option row and the extra image row. Visible `Yes` becomes Published on online store `true`, which is the guide's mapping, and Status `active`, which is a practice-file choice. [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace) [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv)
- Hosted Image URLs on the jar are two `https://cdn.example.test/sample-harbor/` URLs separated by a space. Shopify has one Product image URL per row, positions `1` and `2`. Image alt text is blank. Variant image URL is blank. Featured images, alt text, and variant images are not in the export. [Export products](https://support.squarespace.com/hc/en-us/articles/360000694948-Export-products-to-a-csv) [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv) [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace)
- Categories `Jars`, `Ladles`, and `Cloths` become Type. They are not copied into Collection. That column is import-only. Tags `practice` are copied. Vendor `Sample Harbor Goods`, Charge tax `true`, Requires shipping `true`, and Fulfillment service `manual` are fictional store-level values. They are not columns in the example. Shopify's Squarespace guide maps a column named `Default Vendor Name` to Vendor, and neither the example nor the import tables list it. Check in your own export. Gift card is `false`. [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv) [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace)
- Weight, Length, Width, and Height stay in the Squarespace file. Shopify Weight value (grams) is blank because the unit is not in the file. A blank grams cell's default is 0. Do not copy the dimension numbers into the packed-product columns. [Product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv)
