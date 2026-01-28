---
name: geekythings-listings
description: Create or update GeekyThings product listings in the Product Manager app via API workflows, including tags/colours/sizes/readme/pricing/media, syncing marketplace listings, or moving drafts live.
---

# GeekyThings Listings

## Overview
Use this skill to create or update GeekyThings product listings in the Product Manager. Prefer API calls over editing CSV/files directly, and keep folder conventions intact.

## Workflow decision tree
1. Identify the product target.
   - Create a new product: POST `/api/add_product`.
   - Update an existing product: look up by `category` + `product_folder` (use `/api/rows` to locate by SKU if needed).
2. Update listing content.
   - Tags/colours/sizes/readme: POST `/api/product_meta` (preferred) or POST `/api/readme` for README-only edits.
   - Pricing: POST `/api/pricing`.
   - Media/3MF: POST `/api/upload`, then use `/api/rename_file` or `/api/delete_file` as needed.
3. Move the product state if required.
   - Draft -> Live: POST `/api/approve`.
   - Live -> Archive: POST `/api/archive`.
   - Live -> Draft: POST `/api/move_to_draft`.

## Conventions to keep
- Keep product folders as `SKU - Product Title`; UI strips the SKU for display, but backend paths require the full folder name.
- Keep README as `README.md` under Draft/Live/Archived paths; the DB does not store README content unless passed to `/api/product_meta`.

## References
- Read `references/api.md` for endpoint payloads and examples.
- Read `references/listing-context.md` for marketplace rules and brand/social context.
