#!/usr/bin/env python3
import csv
import json
import os
from pathlib import Path

import db

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PRODUCTS_DIR = Path(os.environ.get('PRODUCTS_DIR', ROOT_DIR / 'Products')).resolve()
CSV_PATH = PRODUCTS_DIR / 'categories_index.csv'
STOCK_PATH = PRODUCTS_DIR / 'stock.csv'
CATEGORIES_DIR = PRODUCTS_DIR / 'Categories'
ARCHIVE_DIR = CATEGORIES_DIR / '_Archive'
DRAFT_DIR = CATEGORIES_DIR / '_Draft'


def pricing_path(category: str, folder_name: str, status: str) -> Path:
    normalized = db.normalize_status(status)
    if normalized == 'Draft':
        base_dir = DRAFT_DIR
    elif normalized == 'Archived':
        base_dir = ARCHIVE_DIR
    else:
        base_dir = CATEGORIES_DIR
    return base_dir / category / folder_name / 'Pricing.json'


def load_products() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    rows = []
    with CSV_PATH.open(newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = {header: row.get(header, '') for header in db.PRODUCT_HEADERS}
            normalized['Status'] = db.normalize_status(row.get('Status'))
            rows.append(normalized)
    return rows


def load_stock():
    if not STOCK_PATH.exists():
        return []
    rows = []
    with STOCK_PATH.open(newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            quantity_raw = row.get('quantity', '')
            try:
                quantity = int(quantity_raw)
            except (TypeError, ValueError):
                quantity = 0
            rows.append({
                'category': (row.get('category') or '').strip(),
                'product_folder': (row.get('product_folder') or '').strip(),
                'sku': (row.get('sku') or '').strip(),
                'color': (row.get('color') or '').strip(),
                'size': (row.get('size') or '').strip(),
                'quantity': quantity,
            })
    return rows


def load_pricing(rows: list[dict]) -> int:
    count = 0
    for row in rows:
        category = (row.get('category') or '').strip()
        folder_name = (row.get('product_folder') or '').strip()
        status = row.get('Status') or 'Live'
        if not category or not folder_name:
            continue
        path = pricing_path(category, folder_name, status)
        if not path.exists():
            continue
        try:
            pricing_data = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        if db.set_pricing(category, folder_name, pricing_data):
            count += 1
    return count


def main():
    db.ensure_schema()
    product_rows = load_products()
    if product_rows:
        db.upsert_products(product_rows)
    stock_rows = load_stock()
    for row in stock_rows:
        if not row['category'] or not row['product_folder']:
            continue
        db.upsert_stock_entry(
            row['category'],
            row['product_folder'],
            row['sku'],
            row['color'],
            row['size'],
            row['quantity'],
        )
    pricing_count = load_pricing(product_rows)
    print(f'Imported {len(product_rows)} products, {len(stock_rows)} stock rows, {pricing_count} pricing files.')


if __name__ == '__main__':
    main()
