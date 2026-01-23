# ProductMgmt

Local product management web app for GeekyThings. It provides a simple browser UI to manage products, edit README templates, and access media/print files.

## What it does
- Lists products from `categories_index.csv` and allows editing core fields.
- Table edits auto-save to the master CSV.
- Opens product folders, renames folders, and writes updates back to the CSV.
- Reads/writes per-product `README.md` content.
- Shows media from each product's `Media` folder.
- Lists `.3mf` files under the product folder with open/copy helpers.

## Run locally
From this folder:

```
python3 server.py
```

Then open `http://localhost:8555` in a browser.

## Data layout
- CSV source: `categories_index.csv` in repo root.
- Products root: `Products/Categories/<Category>/<Product Folder>`.
- Media folder: `Products/Categories/<Category>/<Product Folder>/Media`.
- Files are served via `/files/...` for media and `.3mf` listing.

## Key files
- `index.html`: Product list, search, and table view.
- `product.html`: Product detail view with media and `.3mf` files.
- `add.html`: Create new product flow.
- `server.py`: Local HTTP server and API endpoints.

## API endpoints
- `GET /api/rows`: Returns CSV headers and rows.
- `GET /api/archived`: Lists archived rows (Status = Archived).
- `GET /api/drafts`: Lists draft rows (Status = Draft).
- `GET /api/media?category=...&folder=...`: Lists files in the product `Media` folder.
- `GET /api/3mf?category=...&folder=...`: Lists `.3mf` files under the product folder.
- `POST /api/save`: Save full table to CSV.
- `POST /api/update_row`: Update a single row and optionally move the folder.
- `POST /api/add_product`: Create a new product folder and CSV row.
- `POST /api/rename`: Rename a product folder.
- `POST /api/readme`: Read/write per-product `README.md`.
- `POST /api/approve`: Move a draft product into live categories and mark Status = Live.
- `POST /api/move_to_draft`: Move a live product into drafts and mark Status = Draft.
- `POST /api/upload`: Upload media and 3MF files (category, folder_name, status).

## Notes
- This is a local-only tool. It serves files directly from disk.
- New products are created as Drafts under `Products/Categories/_Draft/<Category>/...`.
- Draft product pages should include `status=draft` in the query string.
- The `.3mf` list is recursive under each product folder.
