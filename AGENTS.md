# Agent Notes

## Workflow expectation
- After making changes, update `CHANGELOG.md` with a brief summary.
- Exception: product content-only updates (README/tags/colours/sizes/pricing/listing URLs) do not require a changelog entry.
- Then commit and push to git.
- Always bump the app version in `App/ui/src/constants.js` for every push.
- Do not ask for `git add` or `git commit` commands or commit messages; do them automatically.

## Preferred docs
- Keep a separate `TODO.md` for outstanding tasks.

## Site context (geekythings.co.uk)
- Landing page is a simple links hub.
- Social/marketplace links: TikTok (@geekythingsuk), Etsy (GeekyThingsUK), eBay (geekythingsuk), Facebook (GeekyThings), Instagram (@geekythingsuk).
- Facebook page title indicates Stafford (location context).
- Uses `logo.png` as the favicon/avatar image.

## Social profile notes (public metadata)
- Facebook (GeekyThings, Stafford): 49 likes; 28 talking about this; description mentions games, photography, computers, and more.
- Instagram (@geekythingsuk): 33 followers, 23 following, 37 posts; display name "Dan".

## Listing context files
- Read and follow these for listing rules and automation context:
  - `agents/AGENT.etsy.md`
  - `agents/AGENT.ebay.md`
  - `agents/AGENT.tiktokshop.md`

## App context (GeekyThings Product Manager)
- App root: `App/` (backend in `App/server.py`, frontend in `App/ui`).
- Main data source: `Products/categories_index.csv`.
- Drafts: `Products/Categories/_Draft/<Category>/...`.
- Archive: `Products/Categories/_Archive/<Category>/...`.
- Deleted media/3MF: `.../_Deleted` subfolders.
- Stock: `Products/stock.csv`.
- Pricing per product: `Products/Categories/<Category>/<Product Folder>/Pricing.json`.
- UKCA templates: `Products/UKCA_Shared`, per-product packs under `<Product>/UKCA`.
- Media/3MF access uses `/files/...` and tokenized `/files-token/...` URLs.

## App features summary
- Vue SPA with Vue Router (built via Vite).
- Auth: session cookie + optional TOTP (`AUTH_TOTP_SECRET`); removing `.env` disables auth.
- Product page supports: README edit, media uploads, 3MF open/download, UKCA pack, colors/sizes variations, pricing.
- Stock page supports: product search, size/color dropdowns, stock adjustments.

## Run commands
- Docker: `docker compose up --build -d` (serves on `http://localhost:8555`).
- Vite dev: `npm run dev` from `App/ui` (proxy to backend).
