# Listing Context

## Site and brand context
- Landing page is a simple links hub (geekythings.co.uk).
- Social/marketplace links: TikTok `@geekythingsuk`, Etsy `GeekyThingsUK`, eBay `geekythingsuk`, Facebook `GeekyThings`, Instagram `@geekythingsuk`.
- Facebook page title indicates Stafford (location context).
- Use `logo.png` as the favicon/avatar image.

## Marketplace listing rules
- Read and follow:
  - `agents/AGENT.etsy.md`
  - `agents/AGENT.ebay.md`
  - `agents/AGENT.tiktokshop.md`
- If any required listing fields are still marked `[fill in]`, ask the user to supply them before publishing.

## Product data locations
- Product files live in `Products/Categories/<Category>/<SKU - Product Title>/`.
- Drafts live in `Products/Categories/_Draft/<Category>/...`.
- Archive lives in `Products/Categories/_Archive/<Category>/...`.
- Pricing lives at `Products/Categories/<Category>/<Product Folder>/Pricing.json`.
- Tags/colours/sizes are stored in the DB and should be updated via API rather than editing CSV files directly.
