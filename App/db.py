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


def normalize_event_row(row: dict) -> dict:
    return {
        'name': _normalize_text(row.get('name')),
        'event_date': _normalize_text(row.get('event_date')),
        'location': _normalize_text(row.get('location')),
        'contact_name': _normalize_text(row.get('contact_name')),
        'contact_email': _normalize_text(row.get('contact_email')),
        'notes': _normalize_text(row.get('notes')),
    }


def fetch_events() -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id,
                       name,
                       event_date::text AS event_date,
                       location,
                       contact_name,
                       contact_email,
                       notes,
                       created_at::text AS created_at,
                       updated_at::text AS updated_at
                FROM events
                ORDER BY event_date DESC, name
                """
            )
            return cur.fetchall()


def fetch_event(event_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id,
                       name,
                       event_date::text AS event_date,
                       location,
                       contact_name,
                       contact_email,
                       notes,
                       created_at::text AS created_at,
                       updated_at::text AS updated_at
                FROM events
                WHERE id = %s
                """,
                (event_id,),
            )
            return cur.fetchone()


def insert_event(data: dict) -> dict | None:
    payload = normalize_event_row(data)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO events (name, event_date, location, contact_name, contact_email, notes, updated_at)
                VALUES (%s, %s::date, %s, %s, %s, %s, now())
                RETURNING id,
                          name,
                          event_date::text AS event_date,
                          location,
                          contact_name,
                          contact_email,
                          notes,
                          created_at::text AS created_at,
                          updated_at::text AS updated_at
                """,
                (
                    payload['name'],
                    payload['event_date'],
                    payload['location'],
                    payload['contact_name'],
                    payload['contact_email'],
                    payload['notes'],
                ),
            )
            return cur.fetchone()


def update_event(event_id: int, data: dict) -> bool:
    payload = normalize_event_row(data)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE events
                SET name = %s,
                    event_date = %s::date,
                    location = %s,
                    contact_name = %s,
                    contact_email = %s,
                    notes = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (
                    payload['name'],
                    payload['event_date'],
                    payload['location'],
                    payload['contact_name'],
                    payload['contact_email'],
                    payload['notes'],
                    event_id,
                ),
            )
            return cur.fetchone() is not None


def delete_event(event_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id = %s RETURNING id", (event_id,))
            return cur.fetchone() is not None


def insert_sale(data: dict) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO sales (
                    event_id,
                    product_id,
                    category,
                    product_folder,
                    sku,
                    color,
                    size,
                    quantity,
                    unit_price,
                    override_price,
                    payment_method
                )
                VALUES (
                    %(event_id)s,
                    %(product_id)s,
                    %(category)s,
                    %(product_folder)s,
                    %(sku)s,
                    %(color)s,
                    %(size)s,
                    %(quantity)s,
                    %(unit_price)s,
                    %(override_price)s,
                    %(payment_method)s
                )
                RETURNING id, event_id, product_id, category, product_folder, sku, color, size,
                          quantity, unit_price::text AS unit_price, override_price,
                          payment_method, sold_at::text AS sold_at
                """,
                data,
            )
            return cur.fetchone()


def fetch_sales(event_id: int) -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, event_id, product_id, category, product_folder, sku, color, size,
                       quantity, unit_price::text AS unit_price, override_price,
                       payment_method, sold_at::text AS sold_at
                FROM sales
                WHERE event_id = %s
                ORDER BY sold_at DESC, id DESC
                """,
                (event_id,),
            )
            return cur.fetchall()


def normalize_production_row(row: dict) -> dict:
    return {
        'category': _normalize_text(row.get('category')),
        'product_folder': _normalize_text(row.get('product_folder')),
        'sku': _normalize_text(row.get('sku')),
        'color': _normalize_text(row.get('color')),
        'size': _normalize_text(row.get('size')),
        'status': _normalize_text(row.get('status')) or 'Queued',
        'quantity': row.get('quantity', 0),
    }


def fetch_production_queue(status: str | None = None) -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if status:
                cur.execute(
                    """
                    SELECT id, category, product_folder, sku, color, size, quantity,
                           status, created_at::text AS created_at, updated_at::text AS updated_at
                    FROM production_queue
                    WHERE status = %s
                    ORDER BY updated_at DESC, id DESC
                    """,
                    (status,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, category, product_folder, sku, color, size, quantity,
                           status, created_at::text AS created_at, updated_at::text AS updated_at
                    FROM production_queue
                    ORDER BY updated_at DESC, id DESC
                    """
                )
            return cur.fetchall()


def fetch_production_item(item_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, category, product_folder, sku, color, size, quantity,
                       status, created_at::text AS created_at, updated_at::text AS updated_at
                FROM production_queue
                WHERE id = %s
                """,
                (item_id,),
            )
            return cur.fetchone()


def insert_production_item(data: dict) -> dict | None:
    payload = normalize_production_row(data)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO production_queue (
                    category,
                    product_folder,
                    sku,
                    color,
                    size,
                    quantity,
                    status,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (category, product_folder, color, size, status)
                DO UPDATE SET
                    quantity = production_queue.quantity + EXCLUDED.quantity,
                    sku = EXCLUDED.sku,
                    updated_at = now()
                RETURNING id, category, product_folder, sku, color, size, quantity,
                          status, created_at::text AS created_at, updated_at::text AS updated_at
                """,
                (
                    payload['category'],
                    payload['product_folder'],
                    payload['sku'],
                    payload['color'],
                    payload['size'],
                    payload['quantity'],
                    payload['status'],
                ),
            )
            return cur.fetchone()


def update_production_status(item_id: int, status: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE production_queue
                SET status = %s, updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (status, item_id),
            )
            return cur.fetchone() is not None


def delete_production_item(item_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM production_queue WHERE id = %s RETURNING id", (item_id,))
            return cur.fetchone() is not None


def adjust_production_quantity(item_id: int, delta: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE production_queue
                SET quantity = quantity + %s, updated_at = now()
                WHERE id = %s
                RETURNING id, category, product_folder, sku, color, size, quantity,
                          status, created_at::text AS created_at, updated_at::text AS updated_at
                """,
                (delta, item_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            if row['quantity'] <= 0:
                cur.execute("DELETE FROM production_queue WHERE id = %s", (item_id,))
                return None
            return row


def adjust_production_by_key(
    category: str,
    product_folder: str,
    sku: str,
    color: str,
    size: str,
    delta: int,
    status: str = 'Queued',
) -> dict | None:
    if delta == 0:
        return None
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if delta > 0:
                cur.execute(
                    """
                    INSERT INTO production_queue (
                        category,
                        product_folder,
                        sku,
                        color,
                        size,
                        quantity,
                        status,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                    ON CONFLICT (category, product_folder, color, size, status)
                    DO UPDATE SET
                        quantity = production_queue.quantity + EXCLUDED.quantity,
                        sku = EXCLUDED.sku,
                        updated_at = now()
                    RETURNING id, category, product_folder, sku, color, size, quantity,
                              status, created_at::text AS created_at, updated_at::text AS updated_at
                    """,
                    (category, product_folder, sku, color, size, delta, status),
                )
                return cur.fetchone()
            cur.execute(
                """
                UPDATE production_queue
                SET quantity = quantity + %s, updated_at = now()
                WHERE category = %s
                  AND product_folder = %s
                  AND color = %s
                  AND size = %s
                  AND status = %s
                RETURNING id, quantity
                """,
                (delta, category, product_folder, color, size, status),
            )
            row = cur.fetchone()
            if not row:
                return None
            if row['quantity'] <= 0:
                cur.execute("DELETE FROM production_queue WHERE id = %s", (row['id'],))
                return None
            cur.execute(
                """
                SELECT id, category, product_folder, sku, color, size, quantity,
                       status, created_at::text AS created_at, updated_at::text AS updated_at
                FROM production_queue
                WHERE id = %s
                """,
                (row['id'],),
            )
            return cur.fetchone()


def fetch_event_media(event_id: int) -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, event_id, file_path, uploaded_at::text AS uploaded_at
                FROM event_media
                WHERE event_id = %s
                ORDER BY uploaded_at DESC, id DESC
                """,
                (event_id,),
            )
            return cur.fetchall()


def insert_event_media(event_id: int, file_path: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO event_media (event_id, file_path)
                VALUES (%s, %s)
                RETURNING id, event_id, file_path, uploaded_at::text AS uploaded_at
                """,
                (event_id, file_path),
            )
            return cur.fetchone()


def delete_event_media(media_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                DELETE FROM event_media
                WHERE id = %s
                RETURNING id, event_id, file_path, uploaded_at::text AS uploaded_at
                """,
                (media_id,),
            )
            return cur.fetchone()


def fetch_sale(sale_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, event_id, product_id, category, product_folder, sku, color, size,
                       quantity, unit_price::text AS unit_price, override_price,
                       payment_method, sold_at::text AS sold_at
                FROM sales
                WHERE id = %s
                """,
                (sale_id,),
            )
            return cur.fetchone()


def update_sale(sale_id: int, data: dict) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE sales
                SET product_id = %(product_id)s,
                    category = %(category)s,
                    product_folder = %(product_folder)s,
                    sku = %(sku)s,
                    color = %(color)s,
                    size = %(size)s,
                    quantity = %(quantity)s,
                    unit_price = %(unit_price)s,
                    override_price = %(override_price)s,
                    payment_method = %(payment_method)s
                WHERE id = %(sale_id)s
                RETURNING id, event_id, product_id, category, product_folder, sku, color, size,
                          quantity, unit_price::text AS unit_price, override_price,
                          payment_method, sold_at::text AS sold_at
                """,
                {
                    'sale_id': sale_id,
                    **data,
                },
            )
            return cur.fetchone()


def delete_sale(sale_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                DELETE FROM sales
                WHERE id = %s
                RETURNING id, event_id, product_id, category, product_folder, sku, color, size,
                          quantity, unit_price::text AS unit_price, override_price,
                          payment_method, sold_at::text AS sold_at
                """,
                (sale_id,),
            )
            return cur.fetchone()


def fetch_recent_sales(limit: int) -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT s.id,
                       s.event_id,
                       e.name AS event_name,
                       s.product_id,
                       s.category,
                       s.product_folder,
                       s.sku,
                       s.color,
                       s.size,
                       s.quantity,
                       s.unit_price::text AS unit_price,
                       s.override_price,
                       s.payment_method,
                       s.sold_at::text AS sold_at
                FROM sales AS s
                JOIN events AS e ON e.id = s.event_id
                ORDER BY s.sold_at DESC, s.id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()


def fetch_event_targets(event_id: int) -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, event_id, product_id, category, product_folder, sku, color, size, target_qty,
                       created_at::text AS created_at, updated_at::text AS updated_at
                FROM event_targets
                WHERE event_id = %s
                ORDER BY category, product_folder, color, size
                """,
                (event_id,),
            )
            return cur.fetchall()


def upsert_event_target(data: dict) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO event_targets (
                    event_id,
                    product_id,
                    category,
                    product_folder,
                    sku,
                    color,
                    size,
                    target_qty,
                    updated_at
                )
                VALUES (
                    %(event_id)s,
                    %(product_id)s,
                    %(category)s,
                    %(product_folder)s,
                    %(sku)s,
                    %(color)s,
                    %(size)s,
                    %(target_qty)s,
                    now()
                )
                ON CONFLICT (event_id, category, product_folder, color, size)
                DO UPDATE SET
                    product_id = EXCLUDED.product_id,
                    sku = EXCLUDED.sku,
                    target_qty = EXCLUDED.target_qty,
                    updated_at = now()
                RETURNING id, event_id, product_id, category, product_folder, sku, color, size, target_qty,
                          created_at::text AS created_at, updated_at::text AS updated_at
                """,
                data,
            )
            return cur.fetchone()


def delete_event_target(target_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM event_targets WHERE id = %s RETURNING id", (target_id,))
            return cur.fetchone() is not None


def fetch_event_totals(event_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(quantity), 0)::int AS total_items,
                       COALESCE(SUM(quantity * unit_price), 0)::numeric(10, 2)::text AS total_revenue
                FROM sales
                WHERE event_id = %s
                """,
                (event_id,),
            )
            totals = cur.fetchone() or {'total_items': 0, 'total_revenue': '0.00'}
            cur.execute(
                """
                SELECT payment_method,
                       COALESCE(SUM(quantity * unit_price), 0)::numeric(10, 2)::text AS total
                FROM sales
                WHERE event_id = %s
                GROUP BY payment_method
                ORDER BY payment_method
                """,
                (event_id,),
            )
            payments = {row['payment_method'] or 'Unknown': row['total'] for row in cur.fetchall()}
    return {
        'total_items': totals.get('total_items', 0),
        'total_revenue': totals.get('total_revenue', '0.00'),
        'payments': payments,
    }


def normalize_supply_row(row: dict) -> dict:
    return {
        'name': _normalize_text(row.get('name')),
        'category': _normalize_text(row.get('category')),
        'unit': _normalize_text(row.get('unit')),
        'vendor': _normalize_text(row.get('vendor')),
        'location': _normalize_text(row.get('location')),
        'notes': _normalize_text(row.get('notes')),
        'quantity': row.get('quantity', 0),
        'reorder_point': row.get('reorder_point', 0),
        'lead_time_days': row.get('lead_time_days', 0),
    }


def fetch_supplies() -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, name, category, unit, quantity, reorder_point, vendor,
                       lead_time_days, location, notes, created_at::text AS created_at,
                       updated_at::text AS updated_at
                FROM supplies
                ORDER BY name
                """
            )
            return cur.fetchall()


def insert_supply(data: dict) -> dict | None:
    payload = normalize_supply_row(data)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO supplies (
                    name,
                    category,
                    unit,
                    quantity,
                    reorder_point,
                    vendor,
                    lead_time_days,
                    location,
                    notes,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                RETURNING id, name, category, unit, quantity, reorder_point, vendor,
                          lead_time_days, location, notes, created_at::text AS created_at,
                          updated_at::text AS updated_at
                """,
                (
                    payload['name'],
                    payload['category'],
                    payload['unit'],
                    payload['quantity'],
                    payload['reorder_point'],
                    payload['vendor'],
                    payload['lead_time_days'],
                    payload['location'],
                    payload['notes'],
                ),
            )
            return cur.fetchone()


def update_supply(supply_id: int, data: dict) -> bool:
    payload = normalize_supply_row(data)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE supplies
                SET name = %s,
                    category = %s,
                    unit = %s,
                    quantity = %s,
                    reorder_point = %s,
                    vendor = %s,
                    lead_time_days = %s,
                    location = %s,
                    notes = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (
                    payload['name'],
                    payload['category'],
                    payload['unit'],
                    payload['quantity'],
                    payload['reorder_point'],
                    payload['vendor'],
                    payload['lead_time_days'],
                    payload['location'],
                    payload['notes'],
                    supply_id,
                ),
            )
            return cur.fetchone() is not None


def delete_supply(supply_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM supplies WHERE id = %s RETURNING id", (supply_id,))
            return cur.fetchone() is not None


def adjust_supply_quantity(supply_id: int, delta: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE supplies
                SET quantity = quantity + %s, updated_at = now()
                WHERE id = %s
                RETURNING id, name, category, unit, quantity, reorder_point, vendor,
                          lead_time_days, location, notes, created_at::text AS created_at,
                          updated_at::text AS updated_at
                """,
                (delta, supply_id),
            )
            return cur.fetchone()


def normalize_expense_row(row: dict) -> dict:
    return {
        'expense_date': _normalize_text(row.get('expense_date')),
        'vendor': _normalize_text(row.get('vendor')),
        'description': _normalize_text(row.get('description')),
        'category': _normalize_text(row.get('category')),
        'amount': _normalize_text(row.get('amount')),
        'payment_method': _normalize_text(row.get('payment_method')),
        'reference': _normalize_text(row.get('reference')),
        'receipt_path': _normalize_text(row.get('receipt_path')),
    }


def fetch_expenses() -> list:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id,
                       expense_date::text AS expense_date,
                       vendor,
                       description,
                       category,
                       amount::text AS amount,
                       payment_method,
                       reference,
                       receipt_path,
                       created_at::text AS created_at,
                       updated_at::text AS updated_at
                FROM expenses
                ORDER BY expense_date DESC, id DESC
                """
            )
            return cur.fetchall()


def insert_expense(data: dict) -> dict | None:
    payload = normalize_expense_row(data)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO expenses (
                    expense_date,
                    vendor,
                    description,
                    category,
                    amount,
                    payment_method,
                    reference,
                    receipt_path,
                    updated_at
                )
                VALUES (%s::date, %s, %s, %s, %s::numeric, %s, %s, %s, now())
                RETURNING id,
                          expense_date::text AS expense_date,
                          vendor,
                          description,
                          category,
                          amount::text AS amount,
                          payment_method,
                          reference,
                          receipt_path,
                          created_at::text AS created_at,
                          updated_at::text AS updated_at
                """,
                (
                    payload['expense_date'],
                    payload['vendor'],
                    payload['description'],
                    payload['category'],
                    payload['amount'] or '0',
                    payload['payment_method'],
                    payload['reference'],
                    payload['receipt_path'],
                ),
            )
            return cur.fetchone()


def update_expense(expense_id: int, data: dict) -> bool:
    payload = normalize_expense_row(data)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE expenses
                SET expense_date = %s::date,
                    vendor = %s,
                    description = %s,
                    category = %s,
                    amount = %s::numeric,
                    payment_method = %s,
                    reference = %s,
                    receipt_path = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (
                    payload['expense_date'],
                    payload['vendor'],
                    payload['description'],
                    payload['category'],
                    payload['amount'] or '0',
                    payload['payment_method'],
                    payload['reference'],
                    payload['receipt_path'],
                    expense_id,
                ),
            )
            return cur.fetchone() is not None


def delete_expense(expense_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id = %s RETURNING id", (expense_id,))
            return cur.fetchone() is not None
