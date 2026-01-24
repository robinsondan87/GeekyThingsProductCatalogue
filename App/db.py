import json
import os
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / 'schema.sql'

PRODUCT_HEADERS = [
    'id',
    'category',
    'product_folder',
    'sku',
    'UKCA',
    'Listings',
    'tags',
    'Facebook URL',
    'TikTok URL',
    'Ebay URL',
    'Etsy URL',
    'Status',
    'Colors',
    'Sizes',
    'Cost To Make',
    'Sale Price',
    'Postage Price',
]

STOCK_HEADERS = ['category', 'product_folder', 'sku', 'color', 'size', 'quantity']

PRODUCT_SELECT_BASE = """
    SELECT
        id,
        category,
        product_folder,
        sku,
        ukca AS "UKCA",
        listings AS "Listings",
        tags,
        facebook_url AS "Facebook URL",
        tiktok_url AS "TikTok URL",
        ebay_url AS "Ebay URL",
        etsy_url AS "Etsy URL",
        status AS "Status",
        colors AS "Colors",
        sizes AS "Sizes",
        cost_to_make AS "Cost To Make",
        sale_price AS "Sale Price",
        postage_price AS "Postage Price"
    FROM products
"""

PRODUCT_SELECT_SQL = PRODUCT_SELECT_BASE + " ORDER BY category, product_folder"


def _get_database_url() -> str:
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is not set.')
    return database_url


def get_connection():
    return psycopg.connect(_get_database_url())


def ensure_schema():
    schema_sql = SCHEMA_PATH.read_text(encoding='utf-8')
    retries = int(os.environ.get('DB_CONNECT_RETRIES', '30'))
    delay = float(os.environ.get('DB_CONNECT_DELAY_SECONDS', '1'))
    last_error = None
    for _ in range(max(retries, 1)):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            return
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    if last_error:
        raise last_error


def normalize_status(value: str) -> str:
    lowered = (value or '').strip().lower()
    if lowered == 'draft':
        return 'Draft'
    if lowered == 'archived':
        return 'Archived'
    return 'Live'


def _normalize_text(value) -> str:
    if value is None:
        return ''
    return str(value).strip()


def normalize_product_row(row: dict) -> dict:
    return {
        'category': _normalize_text(row.get('category')),
        'product_folder': _normalize_text(row.get('product_folder')),
        'sku': _normalize_text(row.get('sku')),
        'ukca': _normalize_text(row.get('UKCA') or row.get('ukca') or 'No'),
        'listings': _normalize_text(row.get('Listings') or row.get('listings')),
        'tags': _normalize_text(row.get('tags')),
        'facebook_url': _normalize_text(row.get('Facebook URL') or row.get('facebook_url')),
        'tiktok_url': _normalize_text(row.get('TikTok URL') or row.get('tiktok_url')),
        'ebay_url': _normalize_text(row.get('Ebay URL') or row.get('ebay_url')),
        'etsy_url': _normalize_text(row.get('Etsy URL') or row.get('etsy_url')),
        'status': normalize_status(row.get('Status') or row.get('status')),
        'colors': _normalize_text(row.get('Colors') or row.get('colors')),
        'sizes': _normalize_text(row.get('Sizes') or row.get('sizes')),
        'cost_to_make': _normalize_text(row.get('Cost To Make') or row.get('cost_to_make')),
        'sale_price': _normalize_text(row.get('Sale Price') or row.get('sale_price')),
        'postage_price': _normalize_text(row.get('Postage Price') or row.get('postage_price')),
    }


def fetch_products() -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(PRODUCT_SELECT_SQL)
            return cur.fetchall()


def fetch_product(category: str, product_folder: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                PRODUCT_SELECT_BASE + " WHERE category = %s AND product_folder = %s",
                (category, product_folder),
            )
            return cur.fetchone()


def fetch_products_by_status(status: str) -> list:
    normalized = normalize_status(status)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT category, product_folder
                FROM products
                WHERE status = %s
                ORDER BY category, product_folder
                """,
                (normalized,),
            )
            return cur.fetchall()


def product_exists(category: str, product_folder: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM products WHERE category = %s AND product_folder = %s",
                (category, product_folder),
            )
            return cur.fetchone() is not None


def upsert_products(rows: list[dict]):
    if not rows:
        return
    payloads = [normalize_product_row(row) for row in rows]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO products (
                    category,
                    product_folder,
                    sku,
                    ukca,
                    listings,
                    tags,
                    facebook_url,
                    tiktok_url,
                    ebay_url,
                    etsy_url,
                    status,
                    colors,
                    sizes,
                    cost_to_make,
                    sale_price,
                    postage_price,
                    updated_at
                )
                VALUES (
                    %(category)s,
                    %(product_folder)s,
                    %(sku)s,
                    %(ukca)s,
                    %(listings)s,
                    %(tags)s,
                    %(facebook_url)s,
                    %(tiktok_url)s,
                    %(ebay_url)s,
                    %(etsy_url)s,
                    %(status)s,
                    %(colors)s,
                    %(sizes)s,
                    %(cost_to_make)s,
                    %(sale_price)s,
                    %(postage_price)s,
                    now()
                )
                ON CONFLICT (category, product_folder)
                DO UPDATE SET
                    sku = EXCLUDED.sku,
                    ukca = EXCLUDED.ukca,
                    listings = EXCLUDED.listings,
                    tags = EXCLUDED.tags,
                    facebook_url = EXCLUDED.facebook_url,
                    tiktok_url = EXCLUDED.tiktok_url,
                    ebay_url = EXCLUDED.ebay_url,
                    etsy_url = EXCLUDED.etsy_url,
                    status = EXCLUDED.status,
                    colors = EXCLUDED.colors,
                    sizes = EXCLUDED.sizes,
                    cost_to_make = EXCLUDED.cost_to_make,
                    sale_price = EXCLUDED.sale_price,
                    postage_price = EXCLUDED.postage_price,
                    updated_at = now()
                """,
                payloads,
            )


def update_product(old_category: str, old_product_folder: str, data: dict) -> bool:
    payload = normalize_product_row(data)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET
                    category = %s,
                    product_folder = %s,
                    sku = %s,
                    ukca = %s,
                    listings = %s,
                    tags = %s,
                    facebook_url = %s,
                    tiktok_url = %s,
                    ebay_url = %s,
                    etsy_url = %s,
                    status = %s,
                    colors = %s,
                    sizes = %s,
                    cost_to_make = %s,
                    sale_price = %s,
                    postage_price = %s,
                    updated_at = now()
                WHERE category = %s AND product_folder = %s
                RETURNING id
                """,
                (
                    payload['category'],
                    payload['product_folder'],
                    payload['sku'],
                    payload['ukca'],
                    payload['listings'],
                    payload['tags'],
                    payload['facebook_url'],
                    payload['tiktok_url'],
                    payload['ebay_url'],
                    payload['etsy_url'],
                    payload['status'],
                    payload['colors'],
                    payload['sizes'],
                    payload['cost_to_make'],
                    payload['sale_price'],
                    payload['postage_price'],
                    old_category,
                    old_product_folder,
                ),
            )
            return cur.fetchone() is not None


def rename_product(category: str, old_name: str, new_name: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET product_folder = %s, updated_at = now()
                WHERE category = %s AND product_folder = %s
                RETURNING id
                """,
                (new_name, category, old_name),
            )
            return cur.fetchone() is not None


def set_product_status(category: str, folder_name: str, status: str) -> bool:
    normalized = normalize_status(status)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET status = %s, updated_at = now()
                WHERE category = %s AND product_folder = %s
                RETURNING id
                """,
                (normalized, category, folder_name),
            )
            return cur.fetchone() is not None


def set_product_ukca(category: str, folder_name: str, value: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET ukca = %s, updated_at = now()
                WHERE category = %s AND product_folder = %s
                RETURNING id
                """,
                (value, category, folder_name),
            )
            return cur.fetchone() is not None


def insert_product(data: dict):
    payload = normalize_product_row(data)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO products (
                    category,
                    product_folder,
                    sku,
                    ukca,
                    listings,
                    tags,
                    facebook_url,
                    tiktok_url,
                    ebay_url,
                    etsy_url,
                    status,
                    colors,
                    sizes,
                    cost_to_make,
                    sale_price,
                    postage_price,
                    updated_at
                )
                VALUES (
                    %(category)s,
                    %(product_folder)s,
                    %(sku)s,
                    %(ukca)s,
                    %(listings)s,
                    %(tags)s,
                    %(facebook_url)s,
                    %(tiktok_url)s,
                    %(ebay_url)s,
                    %(etsy_url)s,
                    %(status)s,
                    %(colors)s,
                    %(sizes)s,
                    %(cost_to_make)s,
                    %(sale_price)s,
                    %(postage_price)s,
                    now()
                )
                RETURNING id
                """,
                payload,
            )
            return cur.fetchone()


def get_product_id(category: str, folder_name: str) -> int | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM products WHERE category = %s AND product_folder = %s",
                (category, folder_name),
            )
            result = cur.fetchone()
            if not result:
                return None
            return result[0]


def get_pricing(category: str, folder_name: str) -> dict | None:
    product_id = get_product_id(category, folder_name)
    if not product_id:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pricing FROM product_pricing WHERE product_id = %s",
                (product_id,),
            )
            result = cur.fetchone()
            if not result:
                return {}
            value = result[0]
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {}
    return value or {}


def set_pricing(category: str, folder_name: str, pricing: dict) -> bool:
    product_id = get_product_id(category, folder_name)
    if not product_id:
        return False
    payload = json.dumps(pricing or {})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO product_pricing (product_id, pricing)
                VALUES (%s, %s::jsonb)
                ON CONFLICT (product_id)
                DO UPDATE SET pricing = EXCLUDED.pricing
                """,
                (product_id, payload),
            )
            return True


def normalize_ukca_key(value: str) -> str:
    return _normalize_text(value).lower()


def list_ukca_doc_keys(category: str, folder_name: str) -> set[str]:
    product_id = get_product_id(category, folder_name)
    if not product_id:
        return set()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT file_key FROM ukca_documents WHERE product_id = %s",
                (product_id,),
            )
            return {row[0] for row in cur.fetchall() if row[0]}


def get_ukca_doc(category: str, folder_name: str, file_key: str) -> str | None:
    product_id = get_product_id(category, folder_name)
    if not product_id:
        return None
    key = normalize_ukca_key(file_key)
    if not key:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM ukca_documents WHERE product_id = %s AND file_key = %s",
                (product_id, key),
            )
            result = cur.fetchone()
            if not result:
                return None
            return result[0] or ''


def set_ukca_doc(category: str, folder_name: str, file_key: str, content: str) -> bool:
    product_id = get_product_id(category, folder_name)
    if not product_id:
        return False
    key = normalize_ukca_key(file_key)
    if not key:
        return False
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ukca_documents (product_id, file_key, content, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (product_id, file_key)
                DO UPDATE SET content = EXCLUDED.content, updated_at = now()
                """,
                (product_id, key, content or ''),
            )
            return True


def fetch_stock() -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT category, product_folder, sku, color, size, quantity
                FROM stock
                ORDER BY category, product_folder, color, size
                """
            )
            return cur.fetchall()


def get_stock_entry(category: str, product_folder: str, color: str, size: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, quantity, sku
                FROM stock
                WHERE category = %s AND product_folder = %s AND color = %s AND size = %s
                """,
                (category, product_folder, color, size),
            )
            return cur.fetchone()


def upsert_stock_entry(category: str, product_folder: str, sku: str, color: str, size: str, quantity: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock (category, product_folder, sku, color, size, quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (category, product_folder, color, size)
                DO UPDATE SET sku = EXCLUDED.sku, quantity = EXCLUDED.quantity
                """,
                (category, product_folder, sku, color, size, quantity),
            )


def delete_stock_entry(category: str, product_folder: str, color: str, size: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM stock
                WHERE category = %s AND product_folder = %s AND color = %s AND size = %s
                """,
                (category, product_folder, color, size),
            )


def update_stock_refs(old_category: str, old_folder: str, new_category: str, new_folder: str, new_sku: str | None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if new_sku:
                cur.execute(
                    """
                    UPDATE stock
                    SET category = %s, product_folder = %s, sku = %s
                    WHERE category = %s AND product_folder = %s
                    """,
                    (new_category, new_folder, new_sku, old_category, old_folder),
                )
            else:
                cur.execute(
                    """
                    UPDATE stock
                    SET category = %s, product_folder = %s
                    WHERE category = %s AND product_folder = %s
                    """,
                    (new_category, new_folder, old_category, old_folder),
                )
