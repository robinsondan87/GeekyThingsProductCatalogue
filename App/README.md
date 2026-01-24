# App

Local product management web app for GeekyThings. It provides a simple browser UI to manage products, edit README templates, and access media/print files.

## What it does
- Lists products from Postgres and allows editing core fields.
- Table edits auto-save to the database.
- Opens product folders, renames folders, and writes updates back to the database.
- Reads/writes per-product `README.md` content.
- Shows media from each product's `Media` folder.
- Lists `.3mf` files under the product folder with open/copy helpers.
- Tracks simple stock counts by product, color, and size.
- Stores pricing fields and optional size-based pricing per product.

## Run locally (backend)
From this folder:

```
export DATABASE_URL=postgresql://user:pass@localhost:5432/geekythings
python3 server.py
```

Then open `http://localhost:8555` in a browser.

## Data layout
- Database: Postgres via `DATABASE_URL` (schema in `App/schema.sql`).
- CSV source: `Products/categories_index.csv` (used for migration only).
- Stock source: `Products/stock.csv` (used for migration only).
- Products root: `Products/Categories/<Category>/<Product Folder>`.
- Pricing file: `Products/Categories/<Category>/<Product Folder>/Pricing.json` (legacy; migrated into DB).
- Media folder: `Products/Categories/<Category>/<Product Folder>/Media`.
- Files are served via `/files/...` for media and `.3mf` listing.

## Key files
- `ui/`: Vite + Vue frontend (SPA).
- `ui/src/views/IndexView.vue`: Product list, search, and table view.
- `ui/src/views/ProductView.vue`: Product detail view with media and `.3mf` files.
- `ui/src/views/AddView.vue`: Create new product flow.
- `server.py`: Local HTTP server and API endpoints.

## API endpoints
- `GET /api/rows`: Returns product headers and rows.
- `GET /api/archived`: Lists archived rows (Status = Archived).
- `GET /api/drafts`: Lists draft rows (Status = Draft).
- `GET /api/media?category=...&folder=...`: Lists files in the product `Media` folder.
- `GET /api/3mf?category=...&folder=...`: Lists `.3mf` files under the product folder.
- `GET /api/stock`: Returns stock rows.
- `POST /api/pricing`: Read/write pricing JSON for a product.
- `POST /api/save`: Save full table to the database.
- `POST /api/update_row`: Update a single row and optionally move the folder.
- `POST /api/add_product`: Create a new product folder and database row.
- `POST /api/rename`: Rename a product folder.
- `POST /api/readme`: Read/write per-product `README.md`.
- `POST /api/approve`: Move a draft product into live categories and mark Status = Live.
- `POST /api/move_to_draft`: Move a live product into drafts and mark Status = Draft.
- `POST /api/upload`: Upload media and 3MF files (category, folder_name, status).
- `POST /api/delete_file`: Move a file into a `_Deleted` subfolder (category, folder_name, status, rel_path).
- `POST /api/ukca_create`: Create a per-product UKCA pack from templates and set UKCA = Yes.
- `GET /api/ukca_pack`: List available UKCA files for a product.
- `POST /api/ukca_pack`: Read/write UKCA pack files.
- `POST /api/stock_adjust`: Add or subtract stock rows.

## Notes
- This is a local-only tool. It serves files directly from disk.
- New products are created as Drafts under `Products/Categories/_Draft/<Category>/...`.
- Draft product pages should include `status=draft` in the query string.
- Uploaded files are named `SKU-###` when SKU is provided.
- The `.3mf` list is recursive under each product folder.
- UKCA templates live in `Products/UKCA_Shared` and are copied into `<Product>/UKCA`.
- Set `PRODUCTS_DIR` if the Products folder is mounted elsewhere.

## Run the frontend (Vite)
From `App/ui`:

```
npm install
npm run dev
```

Then open `http://localhost:5173` in a browser. The dev server proxies `/api` and `/files` to the backend on port 8555.

## Run with Docker
From the repo root:

```
docker compose up --build
```

Then open `http://localhost:8555` in a browser.

## Migrate CSV/JSON into Postgres
With `DATABASE_URL` set (or via Docker Compose):

```
python3 App/migrate_to_db.py
```

## Auth setup
Set environment variables before running the server or Docker:

- `AUTH_USERNAME`
- `AUTH_PASSWORD`
- `AUTH_TOTP_SECRET` (optional, base32 secret for 6-digit authenticator codes)
- `SESSION_TTL_SECONDS` (optional, defaults to 12 hours)
- `AUTH_COOKIE_SECURE` (set to `1` when running behind HTTPS)

For Docker, copy `.env.example` to `.env` and set the values.
