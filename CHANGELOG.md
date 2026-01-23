# Changelog

## Unreleased

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
