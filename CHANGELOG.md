# Changelog

## Unreleased

## V2.8.14
- Minor: Surface skipped event image uploads in the UI.

## V2.8.13
- Fix: Event image uploads now skip unsupported files and report them instead of failing the whole batch.

## V2.8.12
- Minor: Added initial backend unit tests for path safety, renames, and upload parsing.

## V2.8.11
- Minor: Moved event image uploads onto the active event page.

## V2.8.10
- Fix: Corrected event media upload filename handling.

## V2.8.9
- Fix: Corrected event media upload error message handling.

## V2.8.8
- Minor: Added event image uploads with previews and delete support.

## V2.8.7
- Major: Added production queue with auto-replenish from event sales and one-click move-to-stock.

## V2.8.6
- Major: Removed event stock targets; added event-specific sales view and sale edit/delete actions.

## V2.8.5
- Minor: Split active-event sales into a dedicated page and show recent sales on Events.

## V2.8.4
- Fix: Avoided JSON serialization errors for sales prices in API responses.

## V2.8.3
- Major: Added supplies inventory and expenses ledger with receipt uploads and yearly totals.

## V2.8.2
- Minor: Added printable tally sheets for event inventory.

## V2.8.1
- Minor: Added event totals reporting and stock target print queue.

## V2.8.0
- Major: Added events and in-person sales tracking with Quick Sale flow.

## V2.7.13
- Minor: Added Phase 5 for unit testing coverage.

## V2.7.12
- Fix: Avoided HTML injection in stock table rows.
- Fix: Added rollback for rename operations when DB updates fail.
- Fix: Paused auto-refresh when unsaved changes are pending.

## V2.7.11
- Minor: Reordered TODO into phases and marked completed Phase 0 items.

## V2.7.10
- Fix: Hardened file path handling for uploads, delete, and file token operations.
- Fix: Prevented uploads from overwriting files and enforced size limits.
- Fix: Product page now uses server config for open-folder and respects updated categories.

## V2.7.9
- Minor: Added audit follow-ups to TODO backlog.

## V2.7.8
- Minor: Expanded TODO backlog with supply tracking, expenses, and Square import ideas.

## V2.7.7
- Minor: Updated TODO backlog with order/event tracking improvements and CSV import ideas.

## V2.7.6
- Minor: Show UKCA status as a read-only badge on the main products table.

## V2.7.5
- Minor: Added a UKCA reset script and defaulted UKCA test date to today.

## V2.7.4
- Minor: Added chip-style editing for tags, colors, and sizes on the main products table.
- Minor: Hid cost/sale/postage columns in the main products overview.

## V2.7.3
- Fix: Sync SKU/name edits to disk by renaming folders and SKU-prefixed media on save.

## V2.7.2
- Minor: Stored UKCA document content in Postgres while mirroring to disk.

## V2.7.1
- Fix: Added startup retry loop to wait for Postgres readiness.

## V2.7.0
- Major: Moved structured product/stock/pricing data to Postgres with migration tooling.
- Minor: Added Postgres service and env defaults to Docker Compose.

## V2.6.1
- Minor: Updated agent notes for the Product Manager app.

## V2.6.0
- Minor: Added pricing fields (cost, sale, postage) and size-based pricing on product pages.

## V2.5.2
- Minor: Added product search on stock page and dropdowns for color/size.

## V2.5.1
- Minor: Added initial stock.csv with headers.

## V2.5.0
- Minor: Added stock tracking page with color/size adjustments and CSV storage.

## V2.4.1
- Fix: Added filename to tokenized 3MF URLs for Bambu Studio.

## V2.4.0
- Minor: Added Colors and Sizes variations with de-duplication on product pages.

## V2.3.2
- Fix: Added short-lived file tokens for Bambu Studio open links under auth.

## V2.3.1
- Fix: Passed TOTP secret into Docker container for 2FA enforcement.

## V2.3.0
- Major: Added optional TOTP (authenticator app) support.

## V2.2.0
- Major: Added login and session-based auth for UI and API.

## V2.1.5
- Minor: Auto-refresh main product list periodically and on tab focus.

## V2.1.4
- Minor: Simplified UKCA filter to Yes/No only.

## V2.1.3
- Minor: Added UKCA filter on the main product list.

## V2.1.2
- Minor: Styled action buttons to match dark theme.

## V2.1.1
- Minor: Styled sortable table headers to match dark theme.

## V2.1.0
- Minor: Redesigned UI with dark maker dashboard styling.

## V2.0.1
- Fix: Corrected ProductView template string for Vue build.

## V2.0.0
- Major: Migrated frontend to a Vue SPA (Vite + Vue Router) and added dev proxy.

## V1.5.1
- Minor: Documented Docker and local run commands in workflow notes.

## V1.5.0
- Major: Moved ProductMgmt to repo root and added Docker containerization.

## V1.4.7
- Minor: Excluded UKCA README from printed pack output.

## V1.4.6
- Minor: Added default EN71-1 notes in templates and form helper.

## V1.4.5
- Minor: Added inline EN71-1 form helper and UKCA pack printing.

## V1.4.4
- Minor: UKCA pack files can be expanded and edited inline on the product page.

## V1.4.3
- Minor: Synced product folder moves/renames and status updates.

## V1.4.2
- Minor: Added UKCA pack viewer/editor and dropdown section on product pages.

## V1.4.1
- Fix: Updated upload handling to avoid deprecated `cgi` module on Python 3.13.

## V1.4.0
- Minor: Added UKCA pack workflow on product pages with templates.
- Minor: Added UKCA best-practice guidance in shared UKCA folder.

## V1.3.2
- Minor: Renamed media files to `SKU-###` schema (non-3MF).
- Minor: Media remove action is now an overlay X.

## V1.3.1
- Minor: Added delete-to-_Deleted for media/3MF files and SKU-based upload naming.
- Minor: Removed logo image from the product detail page.

## V1.3.0
- Minor: Added drag-and-drop upload for media and 3MF files.

## V1.2.9
- Minor: Added separate Open (Bambu Studio) and Download actions for 3MFs.

## V1.2.8
- Minor: Renamed 3MF action label to Download.

## V1.2.7
- Minor: Open 3MFs via Bambu Studio URL scheme.

## V1.2.6
- Minor: Open the New Draft Product dialog immediately on Add Product.

## V1.2.5
- Fix: Renaming the product folder in the main table now renames the folder on disk.

## V1.2.4
- Minor: Simplified Add Product to a category/name dialog and auto-open draft details.

## V1.2.2
- Minor: Documented the draft-to-live product workflow.

## V1.2.1
- Fix: Draft readme/media loads (avoid local variable shadowing).

## V1.2.0
- Minor: Draft list items now have View, and draft product pages load their assets.

## V1.1.9
- Minor: Added "To Draft" action for live items.

## V1.1.8
- Minor: Moved View action to the Actions column and removed Open/Rename.

## V1.1.7
- Minor: Moved title/subtitle/version into the header nav and removed the large logo.

## V1.1.6
- Minor: Simplified toolbar to search-only and auto-saves table edits.

## V1.1.5
- Minor: Added a shared top navigation bar across ProductMgmt pages.
- Minor: Removed Open CSV and Add row controls; CSV is now always the master.

## V1.1.4
- Fix: New products start as Draft in `_Draft` and show in Draft tab.
- Fix: Archive updates Status to Archived so items appear in Archived tab only.
- Minor: Added Draft approve action to move items live.

## V1.1.3
- Minor: Added Live/Draft/B2B/Archived tabs plus archived/draft list views.
- Minor: Added B2B category option for product creation and SKU prefix.

## V1.1.2
- Minor: Link version label to the repo changelog.

## V1.1.1
- Minor: Displayed ProductMgmt version in the UI header.

## V1.1.0
- Minor: Documented site context in `AGENTS.md` (link hub, socials/marketplaces, location note, social metadata).
- Minor: Added platform listing context templates in `agents/`.
- Minor: Linked listing context files from `AGENTS.md`.
- Minor: Listed `.3mf` files on product pages with open/copy helpers.
- Minor: Added ProductMgmt README for local setup and endpoints.
- Minor: Serve `.3mf` links via local `/files` to avoid `file://` pop-up blocks.
- Fix: URL-encode `.3mf` links so spaces/symbols open correctly.
- Minor: Archive action now moves items to `_Archive` instead of `_Deleted`.
- Fix: Corrected ProductMgmt README port and API path details.

## V1.0.0
- Major: Product folder restructure (Media/STL/MISC + README templates).
- Major: Product management web app with server-side editing, rename, archive, and per-product detail page.
- Major: SKU scheme reset per category and CSV regeneration.
- Minor: Listings simplified to a single status field with per-platform URLs.
- Minor: README templates and editor improvements.
- Fix: Spelling corrections in select product names.
