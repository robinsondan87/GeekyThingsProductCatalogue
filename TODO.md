# TODO

## Phase 0 - Stability/Security
- [x] Harden path handling for file APIs (reject absolute paths, use safe relative resolution, validate category list).
- [x] Fix ProductView to update active category after save so media/README/UKCA use the new category.
- [x] Replace hardcoded local folder paths with server-provided base path (or disable open-folder in Docker).
- [x] Add upload size limits/streaming and collision checks to prevent overwrites.
- [x] Remove innerHTML in stock table rows to avoid HTML injection from SKU/product text.
- [x] Make folder/file rename operations atomic or add rollback when DB update fails.
- [x] Prevent auto-refresh from overwriting unsaved table edits (pause refresh or warn).

## Phase 1 - Core Ops
- [x] Add Events feature: event records (name/date/location/fee/notes) and event selector for sales/stock adjustments.
- [x] Add Sales ledger: per-line item records (SKU, qty, unit price, channel, payment method, fees) with event or online order linkage.
- [x] Add Quick Sale mode for craft fairs (search/scan SKU, select variations, adjust stock, record payment).
- [x] Add low-stock alerts and print queue (target qty per event, reserve stock, show deficits).
- [ ] Add WIP/production tracker that moves completed items into stock automatically.
- [x] Add quick-count printable tally sheets for event inventory reconciliation.

## Phase 2 - Imports
- [ ] Add CSV import wizard for marketplace orders (Etsy CSV, eBay Seller Hub reports, TikTok Shop export orders, Square exports), with SKU mapping and order dedupe.
- [ ] Add import history/audit log with raw CSV archived for rollback.

## Phase 3 - Inventory + Finance
- [x] Add supplies/materials inventory (filament, boxes, bags, labels) with reorder points and lead times.
- [x] Add expenses ledger (supplier, invoice, receipt upload, tax category) with yearly totals export.

## Phase 4 - Reporting
- [x] Add per-event totals summary (items, revenue, payment breakdown).
- [ ] Add extended reporting: top SKUs, payout/fee totals.

## Phase 5 - Tests
- [ ] Add unit test coverage for backend paths, renames, and upload handling.
