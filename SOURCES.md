# Sources

WooCommerce and Shopify pages were checked on 2026-10-24. The Shopify sample product template was downloaded on 2026-10-24 and re-checked on 2026-10-29. The Shopify product CSV page was opened again on 2026-10-27 while writing the Magento list. Shopify pages cited from the BigCommerce list were opened again on 2026-10-27. Adobe Commerce pages were checked on 2026-10-27. BigCommerce pages were checked on 2026-10-27. Squarespace pages, the Squarespace example file, and the Shopify Squarespace migration guide were checked on 2026-10-27. Adding variants and sale prices were read in a browser the same day. Shopify's URL redirects and importing customers pages were read in a browser on 2026-10-27. Help Center pages are unversioned and can change. Where two official pages disagree, the checklist says so.

| Page | Used for |
| --- | --- |
| [WooCommerce product CSV importer and exporter](https://woocommerce.com/document/product-csv-importer-exporter/) | Built-in export schema, published values, images, alt text, categories, tags, meta columns, unrecognised columns |
| [WooCommerce sample product CSV](https://github.com/woocommerce/woocommerce/blob/trunk/plugins/woocommerce/sample-data/sample_products.csv) | Sample headers such as `Weight (lbs)` for a store that uses pounds |
| [WooCommerce product CSV exporter reference](https://woocommerce.github.io/code-reference/files/woocommerce-includes-export-class-wc-product-csv-exporter.html) | Export column labels, including `Weight (unit)` and `Meta: key` |
| [WooCommerce unit abbreviations](https://github.com/woocommerce/woocommerce/blob/trunk/plugins/woocommerce/i18n/units.php) | Weight units `kg`, `g`, `lbs`, `oz` and dimension units including `cm` |
| [WooCommerce product settings](https://woocommerce.com/document/configuring-woocommerce-settings/products/) | Where the store's weight and dimension units are set |
| [WooCommerce variable products](https://woocommerce.com/document/variable-product/) | Variations, per-variation SKU and price |
| [WooCommerce categories, tags, and attributes](https://woocommerce.com/document/managing-product-taxonomies/) | Categories versus tags |
| [WooCommerce tax settings](https://woocommerce.com/document/setting-up-taxes-in-woocommerce/) | Prices entered inclusive or exclusive of tax |
| [WooCommerce shop currency](https://woocommerce.com/document/shop-currency/) | One base currency; changing it does not convert amounts |
| [WooCommerce permalinks](https://woocommerce.com/document/permalinks/) | Product, category, and tag URL bases |
| [Backing up WordPress content](https://woocommerce.com/document/backup-wordpress-content/) | Back up files and the database; the XML export omits products |
| [WordPress Tools Export screen](https://wordpress.org/documentation/article/tools-export-screen/) | Export posts and pages |
| [Shopify product CSV columns](https://help.shopify.com/en/manual/products/import-export/using-csv) | Current column table: handles, options, price, weight in grams, images, tags, SEO fields, collection column |
| [Shopify sample product template](https://help.shopify.com/cdn/shopifycloud/product-knowledge/production/csv/product_template.csv) | Header row used by the practice Shopify files, and option name only on the first row of each product |
| [Shopify common product CSV import problems](https://help.shopify.com/en/manual/products/import-export/common-import-issues) | Older header names such as `Variant SKU` and `Body (HTML)` |
| [Shopify inventory CSV](https://help.shopify.com/en/manual/inventory-and-locations/setup/inventory-csv) | `Title` / `Default Title` for a product with no options; handle used in the product URL; multi-location inventory |
| [Adding variants](https://help.shopify.com/en/manual/products/variants/add-variants) | Three options, 2,048 variants, and the 100-variant caveat for some themes and apps |
| [Product details](https://help.shopify.com/en/manual/products/details/product-details-page) | Status values, including Unlisted in the admin |
| [Sale prices](https://help.shopify.com/en/manual/products/details/product-pricing/sale-pricing) | Compare-at price must be higher than price |
| [Dynamic tax-inclusive pricing](https://help.shopify.com/en/manual/international/pricing/dynamic-tax-inclusive-pricing) | Tax included or excluded by region |
| [Duties and taxes for markets](https://help.shopify.com/en/manual/markets/customizations/duties-and-taxes) | Tax shown as included or as a line item |
| [Store currency](https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/setup-business-settings) | Shopify store currency in Settings > General |
| [Collections](https://help.shopify.com/en/manual/products/collections) | Collections as the way products are grouped |
| [Metafields](https://help.shopify.com/en/manual/custom-data/metafields) | Custom product fields |
| [Importing and exporting customers](https://help.shopify.com/en/manual/customers/import-export-customers) | Customer CSV limits; passwords and orders are not imported |
| [Customer accounts](https://help.shopify.com/en/manual/customers/customer-accounts) | Sign-in links and the one-time code |
| [Migrate to Shopify](https://help.shopify.com/en/manual/migrating-to-shopify) | What can move, import order, pages, blogs, orders, redirects, sitemap and private mode |
| [Migrate from WooCommerce](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-woocommerce) | WooCommerce field mapping, three options, reviews, order history |
| [URL redirects](https://help.shopify.com/en/manual/online-store/menus-and-links/url-redirect) | 301 redirects, reserved paths, limits |
| [Ajax Product API](https://shopify.dev/docs/api/ajax/reference/product) | Product URL shape `products/{handle}` |
| [Liquid canonical_url](https://shopify.dev/docs/api/liquid/objects/canonical_url) | Canonical URL object |
| [Canonical URLs on Shopify](https://www.shopify.com/partners/blog/canonical-urls) | Product canonical URL omits the collection and the variant |
| [SEO](https://help.shopify.com/en/manual/promoting-marketing/seo) | Index of SEO topics. SEO title and description limits are on the product CSV page |
| [Pages](https://help.shopify.com/en/manual/online-store/add-edit-pages) | Online store pages |
| [Blogs](https://help.shopify.com/en/manual/online-store/blogs) | Blogs and posts |
| [Placing a test order](https://help.shopify.com/en/manual/checkout-settings/test-orders) | Test gateway, and that test orders are absent from reports |
| [Shopify reports](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports) | Reports after launch |
| [Export data](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-export) | Product, advanced pricing, customer, and stock-source exports |
| [CSV files](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-csv) | Product CSV structure, category paths, UTF-8 |
| [Product data attributes](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/data-attributes-product) | Typical product export columns, including price, visibility, images, and variations |
| [Import configurable products](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/examples/data-transfer-configurable-products) | One configurable row plus one row per simple variation, and `configurable_variations` |
| [Import tier prices](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/examples/data-import-price-tier) | Advanced Pricing export columns for tier prices |
| [Product image import](https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/import/data-import-product-images) | `base_image`, `small_image`, `thumbnail_image`, `additional_images` |
| [Configurable product](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/types/product-create-configurable) | Variations are simple products; the parent price and quantity are not the sellable ones |
| [Special prices](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/pricing/product-price-special) | Special price dates, and the final-price formula |
| [Advanced pricing](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/pricing/pricing-advanced) | Customer group price, tier price, fixed amount or percent |
| [Product images](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/digital-assets/product-image) | Base, small, thumbnail, and swatch roles |
| [Product URL key](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/products/settings/product-search-engine-optimization) | `url_key` has no suffix; meta title and description lengths |
| [Catalog URLs](https://experienceleague.adobe.com/en/docs/commerce-admin/catalog/catalog/catalog-urls) | Product URL suffix and category path |
| [Catalog configuration](https://experienceleague.adobe.com/en/docs/commerce-admin/config/catalog/catalog) | Product URL suffix field |
| [Automatic redirects](https://experienceleague.adobe.com/en/docs/commerce-admin/marketing/seo/url-rewrites/url-redirect-product-automatic) | Permanent redirect when a URL key changes |
| [Product URL rewrites](https://experienceleague.adobe.com/en/docs/commerce-admin/marketing/seo/url-rewrites/url-rewrite-product) | Manual 301 and 302 product rewrites |
| [Websites, stores, and views](https://experienceleague.adobe.com/en/docs/commerce-admin/start/setup/websites-stores-views) | Website, store, and store view hierarchy |
| [Weight unit](https://experienceleague.adobe.com/en/docs/commerce-admin/config/general/general) | Store-view weight unit, `lbs` or `kgs` |
| [Store-view URL rewrites on import](https://experienceleague.adobe.com/en/docs/commerce-operations/tools/quality-patches-tool/patches-available-in-qpt/v1-1-50/acsd-59378-store-level-url-rewrites-incorrectly-updated-during-import) | Bug report fixed in 2.4.7. It describes an empty `store_view_code` as All Store Views |
| [Repeated SKU rows on import](https://experienceleague.adobe.com/en/docs/commerce-operations/tools/quality-patches-tool/patches-available-in-qpt/v1-1-50/acsd-48210-store-view-specific-scope-attribute-overrides-global-values) | Bug report fixed in 2.4.7. The reproduction shares a SKU and the `store_view_code` `default` |
| [Legacy product import/export overview](https://support.bigcommerce.com/s/article/Legacy-Import-Export-Overview) | Legacy versus modern export, SKU and Rule rows, Multi-Storefront prerequisite |
| [Modern product import/export overview](https://support.bigcommerce.com/s/article/Modern-Import-Export-Overview) | No custom export templates, Ignore blank values not supported, category ids and no category creation |
| [Exporting products (legacy)](https://support.bigcommerce.com/s/article/Exporting-Products) | Bulk Edit and Default templates, Include Product Options, Y or N values |
| [Exporting products (modern)](https://support.bigcommerce.com/s/article/Exporting-Your-Products) | Default product CSV, custom export templates are not supported |
| [Legacy product fields](https://support.bigcommerce.com/s/article/Legacy-Product-Fields) | Bulk Edit columns, sale and retail limits, visibility, product URL, images |
| [Modern product fields](https://support.bigcommerce.com/s/article/Supported-Product-Fields) | Channel id 1, inventory tracking values |
| [Legacy complex attributes](https://support.bigcommerce.com/s/article/Complex-Attributes) | SKU and Rule columns when creating variants, option text, categories, images |
| [Modern complex attributes](https://support.bigcommerce.com/s/article/Importing-Complex-Attributes) | Variant row, blank variant price, variant images, custom fields |
| [Updating products via import](https://support.bigcommerce.com/s/article/Updating-via-Import) | Displayed SKU price, Rule row updates, modifier rules, Option Set |
| [Importing your first product](https://support.bigcommerce.com/s/article/Importing-Your-First-Product) | Blank price and weight when creating a product, product URL, category limits |
| [Legacy to modern product transfer](https://support.bigcommerce.com/s/article/Legacy-to-Modern-Product-Transfer) | Custom transfer template, blank matching variant price, attributes the modern tool cannot import |
| [Using sale pricing](https://support.bigcommerce.com/s/article/Using-Sale-Pricing) | Sale price overrides default price, retail strikethrough, legacy Sale Price import limit, custom export template advice, FAQ on fixed option rules |
| [Bulk pricing](https://support.bigcommerce.com/s/article/Bulk-Pricing) | Bulk pricing is not a product CSV column, 50 rules, price lists for variants |
| [Price lists](https://support.bigcommerce.com/s/article/Price-Lists) | Variant prices by storefront and customer group, one list per combination |
| [Price list API](https://developer.bigcommerce.com/docs/rest-management/price-lists) | Missing price-list rows fall back to catalog price, and bulk pricing stops when a price record exists |
| [Product options](https://support.bigcommerce.com/s/article/Product-Options-v3) | 600 SKUs or variants per product, modifier option advice above that |
| [Multi-storefront](https://support.bigcommerce.com/s/article/Multi-Storefront) | Shared catalog, price lists and purchasability per storefront, shared blog |
| [301 redirects](https://support.bigcommerce.com/s/article/301-Redirects) | Redirect import columns, the Dynamic Target URL export column, automatic redirects, reserved paths |
| [Importing and exporting customers](https://support.bigcommerce.com/s/article/Importing-Exporting-Customers) | Customer Bulk Edit and Default templates, 2 MB files, passwords, email address |
| [Importing and exporting orders](https://support.bigcommerce.com/s/article/Importing-Exporting-Orders) | Orders export from the control panel; importing orders into BigCommerce uses the API |
| [Export products to a CSV](https://support.squarespace.com/hc/en-us/articles/360000694948-Export-products-to-a-csv) | Products panel export, 10,000 products, physical and service products, unnamed pages column, omitted featured images, image alt text, variant images, and customer reviews |
| [Importing products from a CSV](https://support.squarespace.com/hc/en-us/articles/115000378108-Importing-products-from-a-csv) | 7.0 and 7.1 import caps, row shape, options, sale price, stock, categories, images, GTIN and MPN (move tables only) |
| [Squarespace example product CSV](https://assets.squarespace.com/universal/commerce/product_import-v2.csv) | 26-column header, Sale Price filled where On Sale is No, category names, `Unlimited` |
| [Add product variants](https://support.squarespace.com/hc/en-us/articles/206540687-Add-product-variants) | Six options and 250 variant combinations for physical and service products |
| [View, edit, and search your product inventory](https://support.squarespace.com/hc/en-us/articles/205811228-View-edit-and-search-your-product-inventory) | Products panel lists every product; bulk edit of physical and service products; gift cards are not mentioned |
| [Download products](https://support.squarespace.com/hc/en-us/articles/206540787-Download-products) | Download products cannot be exported |
| [URL slugs](https://support.squarespace.com/hc/en-us/articles/205814578-URL-slugs) | Product URL slug, 7.1 `p/` prefix, slug length |
| [Store page types](https://support.squarespace.com/hc/en-us/articles/227059347-Store-page-types) | 100 variants per product, and the 7.1 and 7.0 store product limits |
| [Categories and tags](https://support.squarespace.com/hc/en-us/articles/206541007-Organize-your-store-page-with-categories-and-tags) | Category name versus the category URL slug |
| [Import to and export from your site](https://support.squarespace.com/hc/en-us/articles/205814028-Import-to-and-export-from-your-site) | Site content XML, product CSV, and contacts CSV |
| [Export your site content](https://support.squarespace.com/hc/en-us/articles/206566687-Export-your-site-content) | .xml export in WordPress format, one blog page, content that does not export |
| [URL mappings](https://support.squarespace.com/hc/en-us/articles/205815308-URL-mappings) | Squarespace 301 and 302 mappings, 400 KB field, `/p/` examples |
| [Managing customers](https://support.squarespace.com/hc/en-us/articles/229497568-Managing-customers) | Lists & Segments customer export columns; notes are not included |
| [Export Commerce orders](https://support.squarespace.com/hc/en-us/articles/206540677-Export-Commerce-orders) | Orders CSV, active visible products, partial-refund line price |
| [Migrate from Squarespace](https://help.shopify.com/en/manual/migrating-to-shopify/migrating-from-squarespace) | Shopify's field mapping, customers, orders, test orders, what Squarespace does not export, and common import problems |
