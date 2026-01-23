# Workflow

Quick checklist for changes:

- Make changes.
- Update `CHANGELOG.md` with a brief summary and version bump.
- Verify status: `git status -sb`.
- Stage and commit: `git add .` then `git commit -m "Describe change"`.
- Push: `git push`.

## Add a new product workflow
1. Go to **Add Product** and create the item.
2. The new item is created as **Draft** under `Products/Categories/_Draft/<Category>/...`.
3. Use the **Draft** tab and click **View** to edit details, README, media, and files.
4. When ready, click **Approve** to move it live into the category folder.
5. If needed, use **To Draft** on a live item to send it back to Draft.

## App
- Run locally:

```
python3 App/server.py
```

Then open `http://localhost:8555`.

- Run with Docker:

```
docker compose up --build
```

Then open `http://localhost:8555`.
