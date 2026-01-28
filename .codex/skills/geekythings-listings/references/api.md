# GeekyThings Product Manager API (Listing Workflows)

Base URL: `http://localhost:8555`

## Authentication
- `GET /api/session` to check auth state.
- `POST /api/login` with JSON `{ "username": "...", "password": "...", "totp": "123456" }`.
  - On success, the response sets a `session_id` cookie. Reuse that cookie for all subsequent requests.

## Locate products
- `GET /api/rows` -> `{ headers, rows }` (use to find by SKU/title).
- `GET /api/drafts` -> `{ items }`
- `GET /api/archived` -> `{ items }`

## Create a product (Draft)
- `POST /api/add_product`
  - Body:
    - `category` (required)
    - `description` (required; becomes product title)
    - `tags` (optional; comma string)
    - `requires_ukca` (optional boolean)
    - `notes` (optional; appended to README)
  - Response: `{ ok, headers, row }` where `row` includes `sku`, `product_folder`, `category`, and `id` (if inserted).

## Update tags/colours/sizes/readme
- `POST /api/product_meta`
  - Body:
    - `category` (required)
    - `folder_name` (required)
    - `tags` (optional, list or comma string)
    - `colors` or `Colors` (optional, list or comma string)
    - `sizes` or `Sizes` (optional, list or comma string)
    - `readme` (optional; full README content)
    - `status` (optional; Draft/Archived/Live)
  - Notes:
    - Lists are normalized to comma-separated strings.
    - `status` controls which folder receives the README; omit for Live.

## Read/write README
- `POST /api/readme`
  - Body: `category`, `folder_name`, `action` (`read` or `write`), `status`, `content` (for write).

## Pricing
- `POST /api/pricing`
  - Body: `category`, `folder_name`, `action` (`read` or `write`), `pricing`.
  - On read, returns `{ pricing }`. On write, expects `{ base: {...}, sizes: [...] }`.

## Upload media / 3MF
- `POST /api/upload` (multipart/form-data)
  - Fields: `category`, `folder_name`, `status`, `sku`, `use_provided_names` (`1` or `0`)
  - Files:
    - Images/videos -> `Media/`
    - `.3mf` -> `STL/`
    - Other -> `MISC/`
  - Naming:
    - Default uses SKU-prefixed naming.
    - Set `use_provided_names=1` to keep provided filenames (sanitized).

## List media
- `GET /api/media?category=...&folder=...&status=...`
- `GET /api/3mf?category=...&folder=...&status=...`

## Rename/delete files
- `POST /api/rename_file` with `category`, `folder_name`, `status`, `rel_path`, `new_name`.
- `POST /api/delete_file` with `category`, `folder_name`, `status`, `rel_path`.

## State transitions
- `POST /api/approve` with `category`, `folder_name` (Draft -> Live).
- `POST /api/archive` with `category`, `folder_name` (Live -> Archived).
- `POST /api/move_to_draft` with `category`, `folder_name` (Live -> Draft).
