#!/usr/bin/env python3
import argparse
import os
import shutil
from pathlib import Path

import db

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PRODUCTS_DIR = Path(os.environ.get('PRODUCTS_DIR', ROOT_DIR / 'Products')).resolve()
CATEGORIES_DIR = PRODUCTS_DIR / 'Categories'
ARCHIVE_DIR = CATEGORIES_DIR / '_Archive'
DRAFT_DIR = CATEGORIES_DIR / '_Draft'


def find_product_dirs(base_dir: Path):
    if not base_dir.exists():
        return []
    product_dirs = []
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
        for product_dir in category_dir.iterdir():
            if product_dir.is_dir():
                product_dirs.append(product_dir)
    return product_dirs


def delete_ukca_dirs(base_dir: Path, dry_run: bool) -> int:
    deleted = 0
    for product_dir in find_product_dirs(base_dir):
        ukca_dir = product_dir / 'UKCA'
        if not ukca_dir.exists():
            continue
        if dry_run:
            print(f"[dry-run] Would remove {ukca_dir}")
            deleted += 1
            continue
        shutil.rmtree(ukca_dir)
        deleted += 1
    return deleted


def reset_db():
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE products SET ukca = 'No', updated_at = now()")
            cur.execute("DELETE FROM ukca_documents")


def main():
    parser = argparse.ArgumentParser(description="Reset UKCA status and packs.")
    parser.add_argument(
        "--delete-files",
        action="store_true",
        help="Delete UKCA folders from disk (Products/Categories).",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the reset.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print("Dry run: no changes will be made without --confirm.")
        print("Database: would set all UKCA statuses to No and clear ukca_documents.")
        if args.delete_files:
            delete_ukca_dirs(CATEGORIES_DIR, dry_run=True)
            delete_ukca_dirs(DRAFT_DIR, dry_run=True)
            delete_ukca_dirs(ARCHIVE_DIR, dry_run=True)
        return

    db.ensure_schema()
    reset_db()
    deleted = 0
    if args.delete_files:
        deleted += delete_ukca_dirs(CATEGORIES_DIR, dry_run=False)
        deleted += delete_ukca_dirs(DRAFT_DIR, dry_run=False)
        deleted += delete_ukca_dirs(ARCHIVE_DIR, dry_run=False)
    print(f"UKCA reset complete. Deleted {deleted} UKCA folders.")


if __name__ == "__main__":
    main()
