#!/usr/bin/env python3
import json
import mimetypes
import os
import re
import shutil
import time
import secrets
import hmac
import pyotp
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from email import message_from_bytes
from email.policy import default
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote

import db

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PRODUCTS_DIR = Path(os.environ.get('PRODUCTS_DIR', ROOT_DIR / 'Products')).resolve()
RECORDS_DIR = Path(os.environ.get('RECORDS_DIR', ROOT_DIR / 'Records')).resolve()
EXPENSES_DIR = RECORDS_DIR / 'Expenses'
EVENT_MEDIA_DIR = RECORDS_DIR / 'Events'
UI_DIST_DIR = BASE_DIR / 'ui' / 'dist'
AUTH_USERNAME = os.environ.get('AUTH_USERNAME')
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD')
AUTH_TOTP_SECRET = os.environ.get('AUTH_TOTP_SECRET')
AUTH_COOKIE_SECURE = os.environ.get('AUTH_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes')
SESSION_TTL_SECONDS = int(os.environ.get('SESSION_TTL_SECONDS', '43200'))
SESSIONS = {}
FILE_TOKENS = {}
FILE_TOKEN_TTL_SECONDS = int(os.environ.get('FILE_TOKEN_TTL_SECONDS', '300'))
CATEGORIES_DIR = PRODUCTS_DIR / 'Categories'
ARCHIVE_DIR = CATEGORIES_DIR / '_Archive'
DRAFT_DIR = CATEGORIES_DIR / '_Draft'
UKCA_SHARED_DIR = PRODUCTS_DIR / 'UKCA_Shared'
RUNNING_IN_DOCKER = Path('/.dockerenv').exists() or os.environ.get('RUNNING_IN_DOCKER') == '1'
OPEN_FOLDER_ENABLED = os.environ.get('OPEN_FOLDER_ENABLED')
if OPEN_FOLDER_ENABLED is None:
    OPEN_FOLDER_ENABLED = not RUNNING_IN_DOCKER
else:
    OPEN_FOLDER_ENABLED = OPEN_FOLDER_ENABLED.lower() in ('1', 'true', 'yes')
UPLOAD_MAX_BYTES = int(os.environ.get('UPLOAD_MAX_BYTES', str(100 * 1024 * 1024)))
CATEGORY_PREFIXES = {
    'Automotive': 'GT-AUT',
    'Bookish & Stationery': 'GT-BKS',
    'B2B': 'GT-B2B',
    'Gaming & Tech': 'GT-TCH',
    'Health & Medical': 'GT-HLT',
    'Home & Living': 'GT-HOM',
    'Jewelry & Accessories': 'GT-JWL',
    'Office & Storage': 'GT-OFF',
    'Tools & Workshop': 'GT-TLW',
    'Toys & Games': 'GT-TOY',
    'Uncategorized': 'GT-UNC',
}
EVENT_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def update_stock_refs(old_category: str, old_folder: str, new_category: str, new_folder: str, new_sku: str | None):
    db.update_stock_refs(old_category, old_folder, new_category, new_folder, new_sku)


def is_safe_component(name: str) -> bool:
    if not name:
        return False
    if name in ('.', '..'):
        return False
    if os.path.isabs(name):
        return False
    if re.match(r'^[a-zA-Z]:', name):
        return False
    if '/' in name or '\\' in name:
        return False
    return True


def safe_path_component(name: str) -> str:
    cleaned = (name or '').strip()
    if not is_safe_component(cleaned):
        return ''
    return cleaned


def sanitize_folder_name(name: str) -> str:
    cleaned = name.replace('/', '-').replace('\\', '-').strip()
    return ' '.join(cleaned.split())


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '_', name or '').strip('._')
    return cleaned


def sanitize_upload_filename(name: str) -> str:
    # Keep user-friendly names but strip path separators/control chars.
    cleaned = (name or '').replace('/', '-').replace('\\', '-')
    cleaned = re.sub(r'[\x00-\x1f\x7f]+', '', cleaned).strip()
    return ' '.join(cleaned.split())


def normalize_status(value: str) -> str:
    return db.normalize_status(value)


def normalize_folder_name(value: str, fallback: str) -> str:
    cleaned = sanitize_folder_name(value or '')
    if cleaned and is_safe_component(cleaned):
        return cleaned
    return fallback


def safe_rel_path(value: str) -> Path | None:
    cleaned = (value or '').strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace('\\', '/')
    if cleaned.startswith('/'):
        return None
    if re.match(r'^[a-zA-Z]:', cleaned):
        return None
    parts = cleaned.split('/')
    if any(part in ('', '.', '..') for part in parts):
        return None
    return Path(*parts)


def derive_folder_for_sku(folder_name: str, old_sku: str, new_sku: str) -> tuple[str, bool]:
    if not old_sku or not new_sku or old_sku == new_sku:
        return folder_name, False
    if folder_name.startswith(old_sku):
        return f"{new_sku}{folder_name[len(old_sku):]}", True
    return folder_name, False


def collect_sku_renames(product_path: Path, old_sku: str, new_sku: str) -> tuple[list[tuple[Path, Path]], str | None]:
    if not old_sku or not new_sku or old_sku == new_sku:
        return [], None
    renames = []
    for path in product_path.rglob('*'):
        if not path.is_file():
            continue
        if '_Deleted' in path.parts:
            continue
        name = path.name
        if not name.startswith(old_sku):
            continue
        new_name = f"{new_sku}{name[len(old_sku):]}"
        if new_name == name:
            continue
        renames.append((path, path.with_name(new_name)))
    dests = set()
    for src, dest in renames:
        if dest in dests:
            return [], f"Duplicate target filename {dest.name}"
        if dest.exists():
            return [], f"Target filename already exists: {dest.name}"
        dests.add(dest)
    return renames, None


def apply_sku_renames(product_path: Path, old_sku: str, new_sku: str) -> tuple[bool, str | None, int]:
    renames, error = collect_sku_renames(product_path, old_sku, new_sku)
    if error:
        return False, error, 0
    for src, dest in renames:
        src.rename(dest)
    return True, None, len(renames)


def apply_sku_renames_with_tracking(
    product_path: Path, old_sku: str, new_sku: str
) -> tuple[bool, str | None, list[tuple[Path, Path]]]:
    renames, error = collect_sku_renames(product_path, old_sku, new_sku)
    if error:
        return False, error, []
    for src, dest in renames:
        src.rename(dest)
    return True, None, renames


def rollback_sku_renames(renames: list[tuple[Path, Path]]):
    for src, dest in reversed(renames):
        try:
            if dest.exists() and not src.exists():
                dest.rename(src)
        except OSError:
            continue


def product_base_dir(status: str) -> Path:
    normalized = normalize_status(status)
    if normalized == 'Draft':
        return DRAFT_DIR
    if normalized == 'Archived':
        return ARCHIVE_DIR
    return CATEGORIES_DIR


def product_dir(category: str, folder_name: str, status: str) -> Path:
    return product_base_dir(status) / category / folder_name


def ukca_file_paths(product_path: Path) -> dict:
    return {
        'readme': product_path / 'UKCA' / 'README.md',
        'declaration': product_path / 'UKCA' / 'Declarations' / 'UKCA_Declaration_of_Conformity.md',
        'risk_assessment': product_path / 'UKCA' / 'Risk_Assessment' / 'Risk_Assessment.md',
        'en71': product_path / 'UKCA' / 'EN71-1_Compliance_Pack.md',
    }


def list_folder_entries(base_dir: Path):
    entries = []
    if not base_dir.exists():
        return entries
    for category_dir in sorted(base_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for product_dir in sorted(category_dir.iterdir()):
            if not product_dir.is_dir():
                continue
            entries.append({
                'category': category,
                'product_folder': product_dir.name,
            })
    return entries


def readme_template(title: str, sku: str) -> str:
    return (
        f"# {title}\n\n"
        f"SKU: {sku}\n\n"
        "## Short Description\n\n"
        "## Long Description\n\n"
        "## Features / Bullet Points\n"
        "- \n- \n- \n\n"
        "## Variations / Sizes\n\n"
        "## Colours\n\n"
        "## Materials\n\n"
        "## Print Settings\n\n"
        "## Assembly\n\n"
        "## Packaging\n\n"
        "## Listing Keywords / Tags\n\n"
        "## UKCA Notes\n\n"
        "## Change Log\n- \n"
    )


def next_sku_filename(dest_dir: Path, sku: str, ext: str) -> str:
    if not sku:
        return ''
    pattern = re.compile(rf"^{re.escape(sku)}-(\d{{3}}){re.escape(ext)}$", re.IGNORECASE)
    max_index = 0
    if dest_dir.exists():
        for entry in dest_dir.iterdir():
            if not entry.is_file():
                continue
            match = pattern.match(entry.name)
            if not match:
                continue
            try:
                value = int(match.group(1))
            except ValueError:
                continue
            max_index = max(max_index, value)
    return f"{sku}-{max_index + 1:03d}{ext}"


def unique_filename(dest_dir: Path, name: str) -> str | None:
    if not name:
        return None
    candidate = name
    if not (dest_dir / candidate).exists():
        return candidate
    base, ext = os.path.splitext(name)
    for index in range(1, 1000):
        candidate = f"{base}-{index:03d}{ext}"
        if not (dest_dir / candidate).exists():
            return candidate
    return None


def next_sku_for_category(category: str) -> str:
    prefix = CATEGORY_PREFIXES.get(category)
    if not prefix:
        return ''
    max_num = 0
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT sku FROM products WHERE category = %s", (category,))
            for (sku,) in cur.fetchall():
                if not sku or not sku.startswith(prefix + '-'):
                    continue
                suffix = sku[len(prefix) + 1:]
                digits = ''.join(ch for ch in suffix if ch.isdigit())
                if not digits:
                    continue
                try:
                    num = int(digits)
                except ValueError:
                    continue
                if num > max_num:
                    max_num = num
    return f'{prefix}-{max_num + 1:05d}'


def read_template(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding='utf-8')
    return ''


def apply_replacements(template: str, replacements: dict) -> str:
    content = template
    for key, value in replacements.items():
        content = content.replace(f'{{{{{key}}}}}', value)
    return content


def parse_cookies(header_value: str) -> dict:
    cookies = {}
    if not header_value:
        return cookies
    for part in header_value.split(';'):
        if '=' not in part:
            continue
        name, value = part.split('=', 1)
        cookies[name.strip()] = value.strip()
    return cookies


def create_session(username: str) -> str:
    session_id = secrets.token_hex(24)
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    SESSIONS[session_id] = {'user': username, 'expires_at': expires_at}
    return session_id


def cleanup_sessions():
    now = int(time.time())
    expired = [key for key, value in SESSIONS.items() if value['expires_at'] <= now]
    for key in expired:
        SESSIONS.pop(key, None)


def cleanup_file_tokens():
    now = int(time.time())
    expired = [key for key, value in FILE_TOKENS.items() if value['expires_at'] <= now]
    for key in expired:
        FILE_TOKENS.pop(key, None)


def create_file_token(path: Path) -> str:
    cleanup_file_tokens()
    token = secrets.token_urlsafe(24)
    FILE_TOKENS[token] = {
        'path': str(path),
        'expires_at': int(time.time()) + FILE_TOKEN_TTL_SECONDS,
    }
    return token


def get_session(headers) -> dict | None:
    cleanup_sessions()
    cookies = parse_cookies(headers.get('Cookie'))
    session_id = cookies.get('session_id')
    if not session_id:
        return None
    session = SESSIONS.get(session_id)
    if not session:
        return None
    if session['expires_at'] <= int(time.time()):
        SESSIONS.pop(session_id, None)
        return None
    return session


def check_credentials(username: str, password: str) -> bool:
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        return False
    return hmac.compare_digest(username, AUTH_USERNAME) and hmac.compare_digest(password, AUTH_PASSWORD)


def auth_enabled() -> bool:
    return bool(AUTH_USERNAME and AUTH_PASSWORD)


def open_path_in_os(path: Path) -> tuple[bool, str | None]:
    if not OPEN_FOLDER_ENABLED:
        return False, 'Open folder is disabled in this environment.'
    try:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', str(path)])
        elif sys.platform.startswith('win'):
            os.startfile(str(path))
        else:
            subprocess.Popen(['xdg-open', str(path)])
        return True, None
    except Exception as exc:
        return False, str(exc)


def parse_multipart_form_data(content_type: str, body: bytes) -> tuple[dict, list]:
    if not content_type or 'multipart/form-data' not in content_type:
        return {}, []
    message = message_from_bytes(
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + body,
        policy=default,
    )
    fields = {}
    files = []
    for part in message.iter_parts():
        if part.get_content_disposition() != 'form-data':
            continue
        name = part.get_param('name', header='content-disposition')
        filename = part.get_filename()
        if filename:
            files.append({
                'name': name,
                'filename': filename,
                'content': part.get_payload(decode=True) or b'',
            })
        else:
            value = part.get_content()
            if isinstance(value, bytes):
                value = value.decode(part.get_content_charset() or 'utf-8', errors='replace')
            fields[name] = value
    return fields, files


def parse_price(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def format_money(value) -> str:
    if value is None:
        value = Decimal('0')
    try:
        quantized = value.quantize(Decimal('0.01'))
    except (InvalidOperation, AttributeError):
        quantized = Decimal('0.00')
    return format(quantized, '.2f')


def calculate_event_totals(rows: list[dict]) -> dict:
    total_items = 0
    total_revenue = Decimal('0.00')
    payments: dict[str, Decimal] = {}
    for row in rows:
        try:
            quantity = int(row.get('quantity') or 0)
        except (TypeError, ValueError):
            quantity = 0
        unit_price = parse_price(row.get('unit_price')) or Decimal('0.00')
        override_price = parse_price(row.get('override_price'))
        effective_price = override_price if override_price is not None else unit_price
        line_total = effective_price * quantity
        total_items += quantity
        total_revenue += line_total
        payment_method = row.get('payment_method') or 'Unknown'
        payments[payment_method] = payments.get(payment_method, Decimal('0.00')) + line_total
    return {
        'total_items': total_items,
        'total_revenue': format_money(total_revenue),
        'payments': {name: format_money(value) for name, value in payments.items()},
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status, text):
        data = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_unauthorized(self):
        self._send_json(401, {'error': 'Unauthorized'})

    def _send_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        mime = 'text/plain'
        if path.suffix == '.html':
            mime = 'text/html; charset=utf-8'
        elif path.suffix == '.css':
            mime = 'text/css; charset=utf-8'
        elif path.suffix == '.js':
            mime = 'text/javascript; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_file_dynamic(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            mime = 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        session = get_session(self.headers)
        if auth_enabled():
            if parsed.path.startswith('/api') and parsed.path not in ('/api/session', '/api/login'):
                if not session:
                    self._send_unauthorized()
                    return
            if parsed.path.startswith('/files/') or parsed.path.startswith('/files-records/'):
                if not session:
                    self._send_unauthorized()
                    return

        if parsed.path.startswith('/files-token/'):
            token_part = parsed.path.replace('/files-token/', '', 1)
            token = token_part.split('/', 1)[0]
            cleanup_file_tokens()
            token_data = FILE_TOKENS.get(token)
            if not token_data:
                self.send_error(404)
                return
            file_path = Path(token_data['path'])
            if not file_path.exists():
                self.send_error(404)
                return
            self._send_file_dynamic(file_path)
            return
        if parsed.path == '/api/rows':
            rows = db.fetch_products()
            self._send_json(200, {'headers': db.PRODUCT_HEADERS, 'rows': rows})
            return

        if parsed.path == '/api/session':
            if not auth_enabled():
                self._send_json(200, {'authenticated': True, 'user': 'local', 'auth_disabled': True})
                return
            if session:
                self._send_json(200, {'authenticated': True, 'user': session['user']})
                return
            self._send_json(200, {'authenticated': False})
            return
        if parsed.path == '/api/config':
            self._send_json(
                200,
                {
                    'open_folder_enabled': OPEN_FOLDER_ENABLED,
                    'paths': {
                        'products': str(PRODUCTS_DIR),
                        'categories': str(CATEGORIES_DIR),
                        'drafts': str(DRAFT_DIR),
                        'archived': str(ARCHIVE_DIR),
                    },
                },
            )
            return

        if parsed.path == '/api/archived':
            items = db.fetch_products_by_status('Archived')
            self._send_json(200, {'items': items})
            return

        if parsed.path == '/api/drafts':
            items = db.fetch_products_by_status('Draft')
            self._send_json(200, {'items': items})
            return

        if parsed.path == '/api/stock':
            rows = db.fetch_stock()
            self._send_json(200, {'headers': db.STOCK_HEADERS, 'rows': rows})
            return

        if parsed.path == '/api/events':
            events = db.fetch_events()
            self._send_json(200, {'events': events})
            return

        if parsed.path == '/api/event_media':
            query = parse_qs(parsed.query)
            event_id_raw = query.get('event_id', [''])[0]
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event_id'})
                return
            if not db.fetch_event(event_id):
                self._send_json(404, {'error': 'Event not found'})
                return
            rows = db.fetch_event_media(event_id)
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/sales':
            query = parse_qs(parsed.query)
            event_id_raw = query.get('event_id', [''])[0]
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event_id'})
                return
            rows = db.fetch_sales(event_id)
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/sales_recent':
            query = parse_qs(parsed.query)
            limit_raw = query.get('limit', ['50'])[0]
            try:
                limit = int(limit_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid limit'})
                return
            if limit <= 0:
                self._send_json(400, {'error': 'Invalid limit'})
                return
            limit = min(limit, 200)
            rows = db.fetch_recent_sales(limit)
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/event_totals':
            query = parse_qs(parsed.query)
            event_id_raw = query.get('event_id', [''])[0]
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event_id'})
                return
            if not db.fetch_event(event_id):
                self._send_json(404, {'error': 'Event not found'})
                return
            rows = db.fetch_sales(event_id)
            totals = calculate_event_totals(rows)
            self._send_json(200, {'totals': totals})
            return

        if parsed.path == '/api/event_targets':
            query = parse_qs(parsed.query)
            event_id_raw = query.get('event_id', [''])[0]
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event_id'})
                return
            targets = db.fetch_event_targets(event_id)
            stock_rows = db.fetch_stock()
            stock_map = {
                (row.get('category'), row.get('product_folder'), row.get('color'), row.get('size')): row.get('quantity')
                for row in stock_rows
            }
            enriched = []
            for row in targets:
                key = (row.get('category'), row.get('product_folder'), row.get('color'), row.get('size'))
                current_qty = stock_map.get(key) or 0
                try:
                    current_qty = int(current_qty)
                except (TypeError, ValueError):
                    current_qty = 0
                try:
                    target_qty = int(row.get('target_qty') or 0)
                except (TypeError, ValueError):
                    target_qty = 0
                deficit = max(target_qty - current_qty, 0)
                entry = dict(row)
                entry['current_qty'] = current_qty
                entry['deficit'] = deficit
                enriched.append(entry)
            self._send_json(200, {'rows': enriched})
            return

        if parsed.path == '/api/supplies':
            rows = db.fetch_supplies()
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/expenses':
            rows = db.fetch_expenses()
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/production':
            query = parse_qs(parsed.query)
            status = (query.get('status', [''])[0] or '').strip()
            rows = db.fetch_production_queue(status or None)
            self._send_json(200, {'rows': rows})
            return

        if parsed.path == '/api/media':
            query = parse_qs(parsed.query)
            category = safe_path_component(query.get('category', [''])[0])
            folder_name = safe_path_component(query.get('folder', [''])[0])
            status = query.get('status', [''])[0]
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder'})
                return
            base_path = product_dir(category, folder_name, status)
            media_dir = base_path / 'Media'
            if not media_dir.exists():
                self._send_json(200, {'files': []})
                return
            files = []
            for entry in sorted(media_dir.iterdir()):
                if not entry.is_file():
                    continue
                if entry.name == '_Deleted':
                    continue
                rel = entry.relative_to(CATEGORIES_DIR)
                url = f"/files/{quote(rel.as_posix())}"
                files.append({
                    'name': entry.name,
                    'rel_path': entry.relative_to(base_path).as_posix(),
                    'url': url,
                })
            self._send_json(200, {'files': files})
            return

        if parsed.path == '/api/3mf':
            query = parse_qs(parsed.query)
            category = safe_path_component(query.get('category', [''])[0])
            folder_name = safe_path_component(query.get('folder', [''])[0])
            status = query.get('status', [''])[0]
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder'})
                return
            product_path = product_dir(category, folder_name, status)
            if not product_path.exists():
                self._send_json(200, {'files': []})
                return
            files = []
            for entry in sorted(product_path.rglob('*')):
                if not entry.is_file():
                    continue
                if '_Deleted' in entry.parts:
                    continue
                if entry.suffix.lower() != '.3mf':
                    continue
                rel = entry.relative_to(CATEGORIES_DIR)
                url = f"/files/{quote(rel.as_posix())}"
                files.append({
                    'name': entry.name,
                    'rel_path': entry.relative_to(product_path).as_posix(),
                    'abs_path': str(entry.resolve()),
                    'url': url,
                })
            self._send_json(200, {'files': files})
            return

        if parsed.path == '/api/ukca_pack':
            query = parse_qs(parsed.query)
            category = safe_path_component(query.get('category', [''])[0])
            folder_name = safe_path_component(query.get('folder', [''])[0])
            status = query.get('status', [''])[0]
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder'})
                return
            product_path = product_dir(category, folder_name, status)
            stored_keys = db.list_ukca_doc_keys(category, folder_name)
            files = []
            for key, path in ukca_file_paths(product_path).items():
                files.append({
                    'key': key,
                    'exists': path.exists() or key in stored_keys,
                })
            self._send_json(200, {'files': files})
            return

        if parsed.path.startswith('/files/'):
            rel = unquote(parsed.path.replace('/files/', '', 1))
            rel_path = Path(*[p for p in rel.split('/') if p and p not in ('.', '..')])
            file_path = (CATEGORIES_DIR / rel_path).resolve()
            if not file_path.is_relative_to(CATEGORIES_DIR.resolve()):
                self.send_error(403)
                return
            self._send_file_dynamic(file_path)
            return

        if parsed.path.startswith('/files-records/'):
            rel = unquote(parsed.path.replace('/files-records/', '', 1))
            rel_path = safe_rel_path(rel)
            if not rel_path:
                self.send_error(403)
                return
            file_path = (RECORDS_DIR / rel_path).resolve()
            if not file_path.is_relative_to(RECORDS_DIR.resolve()):
                self.send_error(403)
                return
            self._send_file_dynamic(file_path)
            return

        if UI_DIST_DIR.exists():
            if parsed.path == '/':
                self._send_file(UI_DIST_DIR / 'index.html')
                return
            rel = parsed.path.lstrip('/')
            if rel:
                candidate = UI_DIST_DIR / rel
                if candidate.exists():
                    self._send_file(candidate)
                    return
            self._send_file(UI_DIST_DIR / 'index.html')
            return

        if parsed.path == '/':
            self._send_text(503, 'UI build not found. Run `npm run build` in App/ui or use Vite dev server.')
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        session = get_session(self.headers)
        if auth_enabled():
            if parsed.path != '/api/login' and parsed.path.startswith('/api'):
                if not session:
                    self._send_unauthorized()
                    return
        if parsed.path == '/api/upload':
            content_length = int(self.headers.get('Content-Length', '0'))
            if content_length > UPLOAD_MAX_BYTES:
                self._send_json(413, {'error': 'Upload exceeds size limit'})
                return
            body = self.rfile.read(content_length) if content_length > 0 else b''
            fields, files_field = parse_multipart_form_data(
                self.headers.get('Content-Type', ''),
                body,
            )
            category = safe_path_component(fields.get('category', ''))
            folder_name = safe_path_component(fields.get('folder_name', ''))
            status = fields.get('status', '')
            sku = (fields.get('sku', '') or '').strip()
            use_provided_names = (fields.get('use_provided_names', '') or '').strip() == '1'
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            saved = []
            for item in files_field:
                filename = item.get('filename')
                if not filename:
                    continue
                name = os.path.basename(filename)
                ext = os.path.splitext(name)[1].lower()
                if ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.tiff', '.heic', '.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v'):
                    dest_dir = product_dir(category, folder_name, status) / 'Media'
                elif ext == '.3mf':
                    dest_dir = product_dir(category, folder_name, status) / 'STL'
                else:
                    dest_dir = product_dir(category, folder_name, status) / 'MISC'
                dest_dir.mkdir(parents=True, exist_ok=True)
                if ext == '.3mf' and use_provided_names:
                    candidate_name = sanitize_upload_filename(name)
                    if candidate_name and not candidate_name.lower().endswith(ext):
                        candidate_name = f"{candidate_name}{ext}"
                    new_name = candidate_name or name
                else:
                    new_name = next_sku_filename(dest_dir, sku, ext) or name
                new_name = unique_filename(dest_dir, new_name)
                if not new_name:
                    self._send_json(409, {'error': 'Failed to create unique filename'})
                    return
                dest_path = dest_dir / new_name
                with dest_path.open('wb') as f:
                    f.write(item.get('content') or b'')
                saved.append(str(dest_path))
            self._send_json(200, {'ok': True, 'saved': saved})
            return

        if parsed.path == '/api/expense_upload':
            content_length = int(self.headers.get('Content-Length', '0'))
            if content_length > UPLOAD_MAX_BYTES:
                self._send_json(413, {'error': 'Upload exceeds size limit'})
                return
            body = self.rfile.read(content_length) if content_length > 0 else b''
            _, files_field = parse_multipart_form_data(
                self.headers.get('Content-Type', ''),
                body,
            )
            if not files_field:
                self._send_json(400, {'error': 'Missing receipt file'})
                return
            file_item = files_field[0]
            filename = file_item.get('filename') or ''
            content = file_item.get('content') or b''
            if not filename or not content:
                self._send_json(400, {'error': 'Invalid receipt upload'})
                return
            base_name = os.path.basename(filename)
            name_part, ext = os.path.splitext(base_name)
            safe_name = sanitize_filename(name_part) or 'receipt'
            safe_ext = re.sub(r'[^A-Za-z0-9.]', '', ext.lower())
            timestamp = time.strftime('%Y%m%d-%H%M%S')
            token = secrets.token_hex(4)
            dest_dir = EXPENSES_DIR / time.strftime('%Y')
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_name = f"{timestamp}-{token}-{safe_name}{safe_ext}"
            dest_path = dest_dir / dest_name
            if dest_path.exists():
                dest_name = f"{timestamp}-{token}-{secrets.token_hex(2)}-{safe_name}{safe_ext}"
                dest_path = dest_dir / dest_name
            dest_path.write_bytes(content)
            rel_path = dest_path.relative_to(RECORDS_DIR).as_posix()
            self._send_json(200, {'receipt_path': rel_path})
            return

        if parsed.path == '/api/event_upload':
            content_length = int(self.headers.get('Content-Length', '0'))
            if content_length > UPLOAD_MAX_BYTES:
                self._send_json(413, {'error': 'Upload exceeds size limit'})
                return
            body = self.rfile.read(content_length) if content_length > 0 else b''
            fields, files_field = parse_multipart_form_data(
                self.headers.get('Content-Type', ''),
                body,
            )
            event_id_raw = fields.get('event_id', '')
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event_id'})
                return
            if not db.fetch_event(event_id):
                self._send_json(404, {'error': 'Event not found'})
                return
            if not files_field:
                self._send_json(400, {'error': 'Missing image files'})
                return
            allowed_exts = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
            rows = []
            skipped = []
            for item in files_field:
                filename = item.get('filename') or ''
                content = item.get('content') or b''
                if not filename or not content:
                    skipped.append({'filename': filename or 'unknown', 'reason': 'empty file'})
                    continue
                base_name = os.path.basename(filename)
                name_part, ext = os.path.splitext(base_name)
                ext = ext.lower()
                if ext not in allowed_exts:
                    skipped.append({
                        'filename': base_name or filename or 'unknown',
                        'reason': f"unsupported file type: {ext or 'unknown'}",
                    })
                    continue
                safe_name = sanitize_filename(name_part) or 'event'
                timestamp = time.strftime('%Y%m%d-%H%M%S')
                token = secrets.token_hex(4)
                dest_dir = EVENT_MEDIA_DIR / str(event_id)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_name = f"{timestamp}-{token}-{safe_name}{ext}"
                dest_path = dest_dir / dest_name
                if dest_path.exists():
                    dest_name = f"{timestamp}-{token}-{secrets.token_hex(2)}-{safe_name}{ext}"
                    dest_path = dest_dir / dest_name
                dest_path.write_bytes(content)
                rel_path = dest_path.relative_to(RECORDS_DIR).as_posix()
                row = db.insert_event_media(event_id, rel_path)
                if row:
                    rows.append(row)
                else:
                    try:
                        dest_path.unlink()
                    except OSError:
                        pass
            if not rows:
                self._send_json(400, {'error': 'No valid images to upload', 'skipped': skipped})
                return
            payload = {'rows': rows}
            if skipped:
                payload['skipped'] = skipped
            self._send_json(200, payload)
            return

        if parsed.path == '/api/login':
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length > 0 else b''
            try:
                data = json.loads(body.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                self._send_json(400, {'error': 'Invalid JSON'})
                return
            if not auth_enabled():
                self._send_json(200, {'ok': True})
                return
            username = (data.get('username') or '').strip()
            password = (data.get('password') or '').strip()
            if not check_credentials(username, password):
                self._send_unauthorized()
                return
            if AUTH_TOTP_SECRET:
                totp_code = (data.get('totp') or '').strip()
                totp = pyotp.TOTP(AUTH_TOTP_SECRET)
                if not totp.verify(totp_code, valid_window=1):
                    self._send_unauthorized()
                    return
            session_id = create_session(username)
            self.send_response(200)
            cookie = f"session_id={session_id}; Path=/; Max-Age={SESSION_TTL_SECONDS}; HttpOnly; SameSite=Lax"
            if AUTH_COOKIE_SECURE:
                cookie += "; Secure"
            self.send_header('Set-Cookie', cookie)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
            return

        if parsed.path == '/api/logout':
            if session:
                cookies = parse_cookies(self.headers.get('Cookie'))
                session_id = cookies.get('session_id')
                if session_id:
                    SESSIONS.pop(session_id, None)
            self.send_response(200)
            self.send_header('Set-Cookie', 'session_id=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
            return

        if parsed.path == '/api/file_token':
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length > 0 else b''
            try:
                data = json.loads(body.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                self._send_json(400, {'error': 'Invalid JSON'})
                return
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            rel_path = data.get('rel_path', '')
            if not category or not folder_name or not rel_path:
                self._send_json(400, {'error': 'Missing category/folder_name/rel_path'})
                return
            base_path = product_dir(category, folder_name, status).resolve()
            rel_clean = safe_rel_path(rel_path)
            if not rel_clean:
                self._send_json(403, {'error': 'Invalid path'})
                return
            target_path = (base_path / rel_clean).resolve()
            if not target_path.is_relative_to(base_path):
                self._send_json(403, {'error': 'Invalid path'})
                return
            if not target_path.exists() or not target_path.is_file():
                self._send_json(404, {'error': 'File not found'})
                return
            token = create_file_token(target_path)
            self._send_json(200, {'token': token})
            return
        if parsed.path == '/api/open_path':
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length > 0 else b''
            try:
                data = json.loads(body.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                self._send_json(400, {'error': 'Invalid JSON'})
                return
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            rel_path = data.get('rel_path', '')
            open_parent = bool(data.get('open_parent'))
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            base_path = product_dir(category, folder_name, status).resolve()
            target_path = base_path
            if rel_path:
                rel_clean = safe_rel_path(rel_path)
                if not rel_clean:
                    self._send_json(403, {'error': 'Invalid path'})
                    return
                target_path = (base_path / rel_clean).resolve()
                if not target_path.is_relative_to(base_path):
                    self._send_json(403, {'error': 'Invalid path'})
                    return
            if open_parent:
                target_path = target_path.parent
            if not target_path.exists():
                self._send_json(404, {'error': 'Path not found'})
                return
            ok, error = open_path_in_os(target_path)
            if not ok:
                self._send_json(409, {'error': error or 'Failed to open path'})
                return
            self._send_json(200, {'ok': True})
            return
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length > 0 else b''
        try:
            data = json.loads(body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            self._send_json(400, {'error': 'Invalid JSON'})
            return

        if parsed.path == '/api/delete_file':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            rel_path = data.get('rel_path', '')
            if not category or not folder_name or not rel_path:
                self._send_json(400, {'error': 'Missing category/folder_name/rel_path'})
                return
            base_path = product_dir(category, folder_name, status).resolve()
            rel_clean = safe_rel_path(rel_path)
            if not rel_clean:
                self._send_json(403, {'error': 'Invalid path'})
                return
            target_path = (base_path / rel_clean).resolve()
            if not target_path.is_relative_to(base_path):
                self._send_json(403, {'error': 'Invalid path'})
                return
            if not target_path.exists() or not target_path.is_file():
                self._send_json(404, {'error': 'File not found'})
                return
            deleted_dir = target_path.parent / '_Deleted'
            deleted_dir.mkdir(parents=True, exist_ok=True)
            dest_path = deleted_dir / target_path.name
            if dest_path.exists():
                self._send_json(409, {'error': 'Destination already exists'})
                return
            target_path.rename(dest_path)
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/rename_file':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            rel_path = data.get('rel_path', '')
            new_name = data.get('new_name', '')
            if not category or not folder_name or not rel_path:
                self._send_json(400, {'error': 'Missing category/folder_name/rel_path'})
                return
            base_path = product_dir(category, folder_name, status).resolve()
            rel_clean = safe_rel_path(rel_path)
            if not rel_clean:
                self._send_json(403, {'error': 'Invalid path'})
                return
            target_path = (base_path / rel_clean).resolve()
            if not target_path.is_relative_to(base_path):
                self._send_json(403, {'error': 'Invalid path'})
                return
            if not target_path.exists() or not target_path.is_file():
                self._send_json(404, {'error': 'File not found'})
                return
            if '_Deleted' in target_path.parts:
                self._send_json(409, {'error': 'Cannot rename deleted files'})
                return
            cleaned_name = sanitize_upload_filename(new_name)
            if not cleaned_name:
                self._send_json(400, {'error': 'Invalid filename'})
                return
            ext = target_path.suffix.lower()
            if ext and not cleaned_name.lower().endswith(ext):
                cleaned_name = f"{cleaned_name}{ext}"
            if cleaned_name == target_path.name:
                rel_out = target_path.relative_to(base_path).as_posix()
                self._send_json(200, {'ok': True, 'name': target_path.name, 'rel_path': rel_out})
                return
            unique_name = unique_filename(target_path.parent, cleaned_name)
            if not unique_name:
                self._send_json(409, {'error': 'Failed to create unique filename'})
                return
            dest_path = target_path.parent / unique_name
            target_path.rename(dest_path)
            rel_out = dest_path.relative_to(base_path).as_posix()
            self._send_json(200, {'ok': True, 'name': dest_path.name, 'rel_path': rel_out})
            return

        if parsed.path == '/api/ukca_create':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            product_name = (data.get('product_name', '') or '').strip()
            sku = (data.get('sku', '') or '').strip()
            materials = (data.get('materials', '') or '').strip()
            intended_age = (data.get('intended_age', '') or '').strip()
            manufacturer = (data.get('manufacturer', '') or '').strip()
            address = (data.get('address', '') or '').strip()
            tester = (data.get('tester', '') or '').strip()
            test_date = (data.get('test_date', '') or '').strip()
            notes = (data.get('notes', '') or '').strip()
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return

            product_path = product_dir(category, folder_name, status)
            ukca_dir = product_path / 'UKCA'
            (ukca_dir / 'Declarations').mkdir(parents=True, exist_ok=True)
            (ukca_dir / 'Risk_Assessment').mkdir(parents=True, exist_ok=True)
            (ukca_dir / 'Evidence').mkdir(parents=True, exist_ok=True)
            (ukca_dir / 'Labels').mkdir(parents=True, exist_ok=True)

            replacements = {
                'PRODUCT_NAME': product_name or folder_name,
                'SKU': sku,
                'MATERIALS': materials or 'PLA / PETG',
                'INTENDED_AGE': intended_age or '3+',
                'MANUFACTURER': manufacturer or 'GeekyThingsUK',
                'ADDRESS': address or 'United Kingdom',
                'TESTER': tester or 'Dan Robinson',
                'TEST_DATE': test_date or '',
                'NOTES': notes,
            }

            readme_template_path = UKCA_SHARED_DIR / 'UKCA_README_TEMPLATE.md'
            declaration_template_path = UKCA_SHARED_DIR / 'UKCA_Declaration_TEMPLATE.md'
            risk_template_path = UKCA_SHARED_DIR / 'UKCA_Risk_Assessment_TEMPLATE.md'
            en71_template_path = UKCA_SHARED_DIR / 'EN71-1_Compliance_Pack_TEMPLATE.md'

            ukca_readme = apply_replacements(read_template(readme_template_path), replacements)
            if ukca_readme:
                (ukca_dir / 'README.md').write_text(ukca_readme, encoding='utf-8')
                db.set_ukca_doc(category, folder_name, 'readme', ukca_readme)

            declaration = apply_replacements(read_template(declaration_template_path), replacements)
            if declaration:
                (ukca_dir / 'Declarations' / 'UKCA_Declaration_of_Conformity.md').write_text(
                    declaration, encoding='utf-8'
                )
                db.set_ukca_doc(category, folder_name, 'declaration', declaration)

            risk = apply_replacements(read_template(risk_template_path), replacements)
            if risk:
                (ukca_dir / 'Risk_Assessment' / 'Risk_Assessment.md').write_text(
                    risk, encoding='utf-8'
                )
                db.set_ukca_doc(category, folder_name, 'risk_assessment', risk)

            en71 = read_template(en71_template_path)
            if en71:
                header = (
                    f"# {replacements['PRODUCT_NAME']} (SKU: {replacements['SKU']})\n\n"
                    f"Material: {replacements['MATERIALS']}\n\n"
                    f"Intended age: {replacements['INTENDED_AGE']}\n\n"
                    f"Date tested: {replacements['TEST_DATE']}\n\n"
                    f"Tester: {replacements['TESTER']}\n\n"
                    "---\n\n"
                )
                en71_content = header + en71
                (ukca_dir / 'EN71-1_Compliance_Pack.md').write_text(en71_content, encoding='utf-8')
                db.set_ukca_doc(category, folder_name, 'en71', en71_content)

            db.set_product_ukca(category, folder_name, 'Yes')

            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/ukca_pack':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            status = data.get('status', '')
            action = (data.get('action', '') or '').strip().lower()
            file_key = (data.get('file', '') or '').strip().lower()
            if not category or not folder_name or not action or not file_key:
                self._send_json(400, {'error': 'Missing category/folder/action/file'})
                return
            product_path = product_dir(category, folder_name, status)
            target = ukca_file_paths(product_path).get(file_key)
            if not target:
                self._send_json(400, {'error': 'Unknown UKCA file'})
                return
            if action == 'read':
                stored = db.get_ukca_doc(category, folder_name, file_key)
                if stored is not None:
                    self._send_json(200, {'content': stored})
                    return
                if not target.exists():
                    self._send_json(404, {'error': 'UKCA file not found'})
                    return
                content = target.read_text(encoding='utf-8')
                db.set_ukca_doc(category, folder_name, file_key, content)
                self._send_json(200, {'content': content})
                return
            if action == 'write':
                content = data.get('content', '')
                if not db.set_ukca_doc(category, folder_name, file_key, content):
                    self._send_json(404, {'error': 'Product not found'})
                    return
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
                self._send_json(200, {'ok': True})
                return
            self._send_json(400, {'error': 'Invalid action'})
            return

        if parsed.path == '/api/events':
            action = (data.get('action') or 'create').strip().lower()
            event = data.get('event') or {}
            event_id = data.get('id') or event.get('id')
            if action == 'delete':
                try:
                    event_id = int(event_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid event id'})
                    return
                if not db.delete_event(event_id):
                    self._send_json(404, {'error': 'Event not found'})
                    return
                event_dir = (EVENT_MEDIA_DIR / str(event_id)).resolve()
                try:
                    if event_dir.is_relative_to(EVENT_MEDIA_DIR.resolve()) and event_dir.exists():
                        shutil.rmtree(event_dir)
                except OSError:
                    pass
                self._send_json(200, {'ok': True})
                return

            name = (event.get('name') or '').strip()
            event_date = (event.get('event_date') or '').strip()
            if not name or not event_date:
                self._send_json(400, {'error': 'Missing event name or date'})
                return
            if not EVENT_DATE_RE.match(event_date):
                self._send_json(400, {'error': 'Event date must be YYYY-MM-DD'})
                return
            payload = {
                'name': name,
                'event_date': event_date,
                'location': (event.get('location') or '').strip(),
                'contact_name': (event.get('contact_name') or '').strip(),
                'contact_email': (event.get('contact_email') or '').strip(),
                'notes': (event.get('notes') or '').strip(),
            }
            if action == 'update':
                try:
                    event_id = int(event_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid event id'})
                    return
                if not db.update_event(event_id, payload):
                    self._send_json(404, {'error': 'Event not found'})
                    return
                updated = db.fetch_event(event_id)
                self._send_json(200, {'ok': True, 'event': updated})
                return
            inserted = db.insert_event(payload)
            if not inserted:
                self._send_json(500, {'error': 'Failed to create event'})
                return
            self._send_json(200, {'ok': True, 'event': inserted})
            return

        if parsed.path == '/api/event_media':
            action = (data.get('action') or '').strip().lower()
            if action != 'delete':
                self._send_json(400, {'error': 'Invalid action'})
                return
            media_id = data.get('id')
            try:
                media_id = int(media_id)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid media id'})
                return
            row = db.fetch_event_media_by_id(media_id)
            if not row:
                self._send_json(404, {'error': 'Media not found'})
                return
            rel_path = safe_rel_path(row.get('file_path') or '')
            if rel_path:
                file_path = (RECORDS_DIR / rel_path).resolve()
                if file_path.is_relative_to(RECORDS_DIR.resolve()) and file_path.exists():
                    try:
                        file_path.unlink()
                    except OSError:
                        self._send_json(500, {'error': 'Failed to delete media file'})
                        return
            if not db.delete_event_media(media_id):
                self._send_json(500, {'error': 'Failed to delete media record'})
                return
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/sale':
            event_id_raw = data.get('event_id')
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event id'})
                return
            if not db.fetch_event(event_id):
                self._send_json(404, {'error': 'Event not found'})
                return
            category = safe_path_component(data.get('category', ''))
            product_folder = safe_path_component(data.get('product_folder', ''))
            if not category or not product_folder:
                self._send_json(400, {'error': 'Missing category/product_folder'})
                return
            try:
                quantity = int(data.get('quantity', 1))
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid quantity'})
                return
            if quantity <= 0:
                self._send_json(400, {'error': 'Quantity must be greater than 0'})
                return
            unit_price_raw = (data.get('unit_price') or '').strip()
            try:
                unit_price = Decimal(unit_price_raw)
            except (InvalidOperation, TypeError):
                self._send_json(400, {'error': 'Invalid unit price'})
                return
            if unit_price < 0:
                self._send_json(400, {'error': 'Unit price must be non-negative'})
                return
            unit_price = unit_price.quantize(Decimal('0.01'))
            override_price = (data.get('override_price') or '').strip()
            payment_method = (data.get('payment_method') or '').strip()
            color = (data.get('color') or '').strip()
            size = (data.get('size') or '').strip()

            product = db.fetch_product(category, product_folder)
            sku = (data.get('sku') or '').strip()
            product_id = None
            if product:
                product_id = product.get('id')
                sku = (product.get('sku') or '').strip() or sku

            sale_row = db.insert_sale({
                'event_id': event_id,
                'product_id': product_id,
                'category': category,
                'product_folder': product_folder,
                'sku': sku,
                'color': color,
                'size': size,
                'quantity': quantity,
                'unit_price': unit_price,
                'override_price': override_price,
                'payment_method': payment_method,
            })
            if not sale_row:
                self._send_json(500, {'error': 'Failed to record sale'})
                return

            stock_adjusted = False
            new_qty = None
            existing = db.get_stock_entry(category, product_folder, color, size)
            if existing:
                try:
                    current_qty = int(existing.get('quantity') or 0)
                except (TypeError, ValueError):
                    current_qty = 0
                updated_qty = current_qty - quantity
                if updated_qty <= 0:
                    db.delete_stock_entry(category, product_folder, color, size)
                    new_qty = 0
                else:
                    db.upsert_stock_entry(category, product_folder, sku, color, size, updated_qty)
                    new_qty = updated_qty
                stock_adjusted = True

            db.adjust_production_by_key(
                category,
                product_folder,
                sku,
                color,
                size,
                quantity,
                'Queued',
            )

            self._send_json(
                200,
                {
                    'ok': True,
                    'sale': sale_row,
                    'stock_adjusted': stock_adjusted,
                    'new_quantity': new_qty,
                },
            )
            return

        if parsed.path == '/api/sale_update':
            sale_id_raw = data.get('id')
            try:
                sale_id = int(sale_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid sale id'})
                return
            existing = db.fetch_sale(sale_id)
            if not existing:
                self._send_json(404, {'error': 'Sale not found'})
                return
            event_id_raw = data.get('event_id')
            if event_id_raw is not None:
                try:
                    event_id = int(event_id_raw)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid event id'})
                    return
                if event_id != existing.get('event_id'):
                    self._send_json(400, {'error': 'Event mismatch'})
                    return
            category = safe_path_component(data.get('category', ''))
            product_folder = safe_path_component(data.get('product_folder', ''))
            if not category or not product_folder:
                self._send_json(400, {'error': 'Missing category/product_folder'})
                return
            quantity_raw = data.get('quantity')
            try:
                quantity = int(quantity_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid quantity'})
                return
            if quantity <= 0:
                self._send_json(400, {'error': 'Quantity must be greater than 0'})
                return
            unit_price_raw = (data.get('unit_price') or '').strip()
            try:
                unit_price = Decimal(unit_price_raw)
            except (InvalidOperation, TypeError):
                self._send_json(400, {'error': 'Invalid unit price'})
                return
            if unit_price < 0:
                self._send_json(400, {'error': 'Unit price must be non-negative'})
                return
            unit_price = unit_price.quantize(Decimal('0.01'))
            override_price = (data.get('override_price') or '').strip()
            payment_method = (data.get('payment_method') or '').strip()
            color = (data.get('color') or '').strip()
            size = (data.get('size') or '').strip()

            product = db.fetch_product(category, product_folder)
            if not product:
                self._send_json(404, {'error': 'Product not found'})
                return
            sku = (product.get('sku') or '').strip()
            product_id = product.get('id')

            updated = db.update_sale(
                sale_id,
                {
                    'product_id': product_id,
                    'category': category,
                    'product_folder': product_folder,
                    'sku': sku,
                    'color': color,
                    'size': size,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'override_price': override_price,
                    'payment_method': payment_method,
                },
            )
            if not updated:
                self._send_json(500, {'error': 'Failed to update sale'})
                return

            stock_adjusted = False
            new_qty = None
            old_key = (
                existing.get('category', ''),
                existing.get('product_folder', ''),
                existing.get('color', ''),
                existing.get('size', ''),
            )
            try:
                old_qty = int(existing.get('quantity') or 0)
            except (TypeError, ValueError):
                old_qty = 0
            new_key = (category, product_folder, color, size)
            if old_key == new_key:
                existing_stock = db.get_stock_entry(category, product_folder, color, size)
                if existing_stock:
                    try:
                        current_qty = int(existing_stock.get('quantity') or 0)
                    except (TypeError, ValueError):
                        current_qty = 0
                    delta = quantity - old_qty
                    updated_qty = current_qty - delta
                    if updated_qty <= 0:
                        db.delete_stock_entry(category, product_folder, color, size)
                        new_qty = 0
                    else:
                        db.upsert_stock_entry(category, product_folder, sku, color, size, updated_qty)
                        new_qty = updated_qty
                    stock_adjusted = True
            else:
                old_stock = db.get_stock_entry(*old_key)
                if old_stock:
                    try:
                        current_qty = int(old_stock.get('quantity') or 0)
                    except (TypeError, ValueError):
                        current_qty = 0
                    updated_qty = current_qty + old_qty
                    db.upsert_stock_entry(
                        old_key[0],
                        old_key[1],
                        existing.get('sku') or '',
                        old_key[2],
                        old_key[3],
                        updated_qty,
                    )
                    stock_adjusted = True
                new_stock = db.get_stock_entry(category, product_folder, color, size)
                if new_stock:
                    try:
                        current_qty = int(new_stock.get('quantity') or 0)
                    except (TypeError, ValueError):
                        current_qty = 0
                    updated_qty = current_qty - quantity
                    if updated_qty <= 0:
                        db.delete_stock_entry(category, product_folder, color, size)
                        new_qty = 0
                    else:
                        db.upsert_stock_entry(category, product_folder, sku, color, size, updated_qty)
                        new_qty = updated_qty
                    stock_adjusted = True

            if old_key == new_key:
                db.adjust_production_by_key(
                    category,
                    product_folder,
                    sku,
                    color,
                    size,
                    quantity - old_qty,
                    'Queued',
                )
            else:
                db.adjust_production_by_key(
                    old_key[0],
                    old_key[1],
                    existing.get('sku') or '',
                    old_key[2],
                    old_key[3],
                    -old_qty,
                    'Queued',
                )
                db.adjust_production_by_key(
                    category,
                    product_folder,
                    sku,
                    color,
                    size,
                    quantity,
                    'Queued',
                )

            self._send_json(
                200,
                {
                    'ok': True,
                    'sale': updated,
                    'stock_adjusted': stock_adjusted,
                    'new_quantity': new_qty,
                },
            )
            return

        if parsed.path == '/api/sale_delete':
            sale_id_raw = data.get('id')
            try:
                sale_id = int(sale_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid sale id'})
                return
            existing = db.fetch_sale(sale_id)
            if not existing:
                self._send_json(404, {'error': 'Sale not found'})
                return
            event_id_raw = data.get('event_id')
            if event_id_raw is not None:
                try:
                    event_id = int(event_id_raw)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid event id'})
                    return
                if event_id != existing.get('event_id'):
                    self._send_json(400, {'error': 'Event mismatch'})
                    return
            deleted = db.delete_sale(sale_id)
            if not deleted:
                self._send_json(500, {'error': 'Failed to delete sale'})
                return
            stock_adjusted = False
            new_qty = None
            category = existing.get('category', '')
            product_folder = existing.get('product_folder', '')
            color = existing.get('color', '')
            size = existing.get('size', '')
            try:
                old_qty = int(existing.get('quantity') or 0)
            except (TypeError, ValueError):
                old_qty = 0
            existing_stock = db.get_stock_entry(category, product_folder, color, size)
            if existing_stock:
                try:
                    current_qty = int(existing_stock.get('quantity') or 0)
                except (TypeError, ValueError):
                    current_qty = 0
                updated_qty = current_qty + old_qty
                db.upsert_stock_entry(
                    category,
                    product_folder,
                    existing.get('sku') or '',
                    color,
                    size,
                    updated_qty,
                )
                stock_adjusted = True
                new_qty = updated_qty
            db.adjust_production_by_key(
                category,
                product_folder,
                existing.get('sku') or '',
                color,
                size,
                -old_qty,
                'Queued',
            )
            self._send_json(
                200,
                {
                    'ok': True,
                    'stock_adjusted': stock_adjusted,
                    'new_quantity': new_qty,
                },
            )
            return

        if parsed.path == '/api/event_targets':
            action = (data.get('action') or 'upsert').strip().lower()
            if action == 'delete':
                target_id = data.get('id')
                try:
                    target_id = int(target_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid target id'})
                    return
                if not db.delete_event_target(target_id):
                    self._send_json(404, {'error': 'Target not found'})
                    return
                self._send_json(200, {'ok': True})
                return

            event_id_raw = data.get('event_id')
            try:
                event_id = int(event_id_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid event id'})
                return
            if not db.fetch_event(event_id):
                self._send_json(404, {'error': 'Event not found'})
                return
            category = safe_path_component(data.get('category', ''))
            product_folder = safe_path_component(data.get('product_folder', ''))
            color = (data.get('color') or '').strip()
            size = (data.get('size') or '').strip()
            target_qty_raw = data.get('target_qty', 0)
            try:
                target_qty = int(target_qty_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid target quantity'})
                return
            if target_qty <= 0:
                self._send_json(400, {'error': 'Target quantity must be greater than 0'})
                return
            if not category or not product_folder:
                self._send_json(400, {'error': 'Missing category/product_folder'})
                return
            product = db.fetch_product(category, product_folder)
            if not product:
                self._send_json(404, {'error': 'Product not found'})
                return
            sku = (product.get('sku') or '').strip()
            target = db.upsert_event_target({
                'event_id': event_id,
                'product_id': product.get('id'),
                'category': category,
                'product_folder': product_folder,
                'sku': sku,
                'color': color,
                'size': size,
                'target_qty': target_qty,
            })
            if not target:
                self._send_json(500, {'error': 'Failed to save target'})
                return
            self._send_json(200, {'ok': True, 'target': target})
            return

        if parsed.path == '/api/supplies':
            action = (data.get('action') or '').strip().lower()
            if action == 'create':
                supply = data.get('supply', {})
                if not (supply.get('name') or '').strip():
                    self._send_json(400, {'error': 'Supply name is required'})
                    return
                row = db.insert_supply(supply)
                if not row:
                    self._send_json(500, {'error': 'Failed to save supply'})
                    return
                self._send_json(200, {'row': row})
                return
            if action == 'update':
                supply_id = data.get('id')
                supply = data.get('supply', {})
                try:
                    supply_id = int(supply_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid supply id'})
                    return
                if not (supply.get('name') or '').strip():
                    self._send_json(400, {'error': 'Supply name is required'})
                    return
                if not db.update_supply(supply_id, supply):
                    self._send_json(404, {'error': 'Supply not found'})
                    return
                self._send_json(200, {'ok': True})
                return
            if action == 'delete':
                supply_id = data.get('id')
                try:
                    supply_id = int(supply_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid supply id'})
                    return
                if not db.delete_supply(supply_id):
                    self._send_json(404, {'error': 'Supply not found'})
                    return
                self._send_json(200, {'ok': True})
                return
            self._send_json(400, {'error': 'Invalid action'})
            return

        if parsed.path == '/api/supply_adjust':
            supply_id = data.get('id')
            delta = data.get('delta')
            try:
                supply_id = int(supply_id)
                delta = int(delta)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid supply adjustment'})
                return
            row = db.adjust_supply_quantity(supply_id, delta)
            if not row:
                self._send_json(404, {'error': 'Supply not found'})
                return
            self._send_json(200, {'row': row})
            return

        if parsed.path == '/api/expenses':
            action = (data.get('action') or '').strip().lower()
            if action not in ('create', 'update', 'delete'):
                self._send_json(400, {'error': 'Invalid action'})
                return
            if action == 'delete':
                expense_id = data.get('id')
                try:
                    expense_id = int(expense_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid expense id'})
                    return
                if not db.delete_expense(expense_id):
                    self._send_json(404, {'error': 'Expense not found'})
                    return
                self._send_json(200, {'ok': True})
                return

            expense = data.get('expense', {})
            expense_date = (expense.get('expense_date') or '').strip()
            if not EVENT_DATE_RE.match(expense_date):
                self._send_json(400, {'error': 'Invalid expense date'})
                return
            try:
                amount_value = Decimal(str(expense.get('amount') or ''))
            except (InvalidOperation, TypeError):
                self._send_json(400, {'error': 'Invalid expense amount'})
                return
            if amount_value < 0:
                self._send_json(400, {'error': 'Expense amount must be positive'})
                return
            receipt_path = (expense.get('receipt_path') or '').strip()
            if receipt_path:
                rel_clean = safe_rel_path(receipt_path)
                if not rel_clean:
                    self._send_json(400, {'error': 'Invalid receipt path'})
                    return
            expense['expense_date'] = expense_date
            expense['amount'] = f"{amount_value:.2f}"
            if action == 'create':
                row = db.insert_expense(expense)
                if not row:
                    self._send_json(500, {'error': 'Failed to save expense'})
                    return
                self._send_json(200, {'row': row})
                return
            expense_id = data.get('id')
            try:
                expense_id = int(expense_id)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid expense id'})
                return
            if not db.update_expense(expense_id, expense):
                self._send_json(404, {'error': 'Expense not found'})
                return
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/production':
            action = (data.get('action') or '').strip().lower()
            if action not in ('create', 'update', 'delete'):
                self._send_json(400, {'error': 'Invalid action'})
                return
            if action == 'delete':
                item_id = data.get('id')
                try:
                    item_id = int(item_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid production id'})
                    return
                if not db.delete_production_item(item_id):
                    self._send_json(404, {'error': 'Production item not found'})
                    return
                self._send_json(200, {'ok': True})
                return
            if action == 'update':
                item_id = data.get('id')
                status = (data.get('status') or '').strip() or 'Queued'
                if status not in ('Queued', 'Printing'):
                    self._send_json(400, {'error': 'Invalid status'})
                    return
                try:
                    item_id = int(item_id)
                except (TypeError, ValueError):
                    self._send_json(400, {'error': 'Invalid production id'})
                    return
                if not db.update_production_status(item_id, status):
                    self._send_json(404, {'error': 'Production item not found'})
                    return
                self._send_json(200, {'ok': True})
                return

            category = safe_path_component(data.get('category', ''))
            product_folder = safe_path_component(data.get('product_folder', ''))
            if not category or not product_folder:
                self._send_json(400, {'error': 'Missing category/product_folder'})
                return
            quantity_raw = data.get('quantity')
            try:
                quantity = int(quantity_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid quantity'})
                return
            if quantity <= 0:
                self._send_json(400, {'error': 'Quantity must be greater than 0'})
                return
            status = (data.get('status') or '').strip() or 'Queued'
            if status not in ('Queued', 'Printing'):
                self._send_json(400, {'error': 'Invalid status'})
                return
            color = (data.get('color') or '').strip()
            size = (data.get('size') or '').strip()
            product = db.fetch_product(category, product_folder)
            if not product:
                self._send_json(404, {'error': 'Product not found'})
                return
            sku = (product.get('sku') or '').strip()
            row = db.insert_production_item(
                {
                    'category': category,
                    'product_folder': product_folder,
                    'sku': sku,
                    'color': color,
                    'size': size,
                    'quantity': quantity,
                    'status': status,
                }
            )
            if not row:
                self._send_json(500, {'error': 'Failed to save production item'})
                return
            self._send_json(200, {'row': row})
            return

        if parsed.path == '/api/production_adjust':
            item_id = data.get('id')
            delta = data.get('delta')
            try:
                item_id = int(item_id)
                delta = int(delta)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid production adjustment'})
                return
            existing = db.fetch_production_item(item_id)
            if not existing:
                self._send_json(404, {'error': 'Production item not found'})
                return
            row = db.adjust_production_quantity(item_id, delta)
            if not row:
                self._send_json(200, {'ok': True, 'deleted': True})
                return
            self._send_json(200, {'row': row})
            return

        if parsed.path == '/api/production_complete':
            item_id = data.get('id')
            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid production id'})
                return
            item = db.fetch_production_item(item_id)
            if not item:
                self._send_json(404, {'error': 'Production item not found'})
                return
            try:
                quantity = int(item.get('quantity') or 0)
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                db.delete_production_item(item_id)
                self._send_json(200, {'ok': True, 'stock_adjusted': False})
                return
            category = item.get('category', '')
            product_folder = item.get('product_folder', '')
            color = item.get('color', '')
            size = item.get('size', '')
            sku = item.get('sku', '')
            existing_stock = db.get_stock_entry(category, product_folder, color, size)
            if existing_stock:
                try:
                    current_qty = int(existing_stock.get('quantity') or 0)
                except (TypeError, ValueError):
                    current_qty = 0
            else:
                current_qty = 0
            new_qty = current_qty + quantity
            db.upsert_stock_entry(category, product_folder, sku, color, size, new_qty)
            db.delete_production_item(item_id)
            self._send_json(200, {'ok': True, 'stock_adjusted': True, 'new_quantity': new_qty})
            return

        if parsed.path == '/api/save':
            rows = data.get('rows') or []
            if not isinstance(rows, list):
                self._send_json(400, {'error': 'Invalid rows payload'})
                return
            for row in rows:
                if not (row.get('category') or '').strip() or not (row.get('product_folder') or '').strip():
                    self._send_json(400, {'error': 'Row missing category or product_folder'})
                    return
            existing_rows = db.fetch_products()
            existing_by_id = {
                str(row.get('id')): row
                for row in existing_rows
                if row.get('id') is not None
            }
            existing_by_key = {
                (row.get('category', ''), row.get('product_folder', '')): row
                for row in existing_rows
            }
            refresh_needed = False
            for row in rows:
                row_id = row.get('id')
                existing = None
                if row_id is not None:
                    existing = existing_by_id.get(str(row_id))
                if not existing:
                    existing = existing_by_key.get((row.get('category', ''), row.get('product_folder', '')))
                if not existing:
                    continue
                if 'Status' not in row and 'status' not in row:
                    row['Status'] = existing.get('Status')
                old_category = existing.get('category', '')
                old_folder = existing.get('product_folder', '')
                old_status = existing.get('Status') or 'Live'
                old_sku = (existing.get('sku') or '').strip()
                new_category = safe_path_component(row.get('category', '')) or old_category
                new_folder = normalize_folder_name(row.get('product_folder', ''), old_folder)
                new_sku = (row.get('sku') or '').strip() or None
                if new_sku and old_sku and new_folder == old_folder:
                    new_folder, auto_renamed = derive_folder_for_sku(new_folder, old_sku, new_sku)
                    if auto_renamed:
                        row['product_folder'] = new_folder
                        refresh_needed = True
                conflict = existing_by_key.get((new_category, new_folder))
                if conflict and conflict.get('id') != existing.get('id'):
                    self._send_json(409, {'error': 'Destination already exists'})
                    return
                row['category'] = new_category
                row['product_folder'] = new_folder
                old_path = product_dir(old_category, old_folder, old_status)
                new_path = product_dir(new_category, new_folder, old_status)
                renamed_folder = False
                sku_renames = []
                if new_category != old_category or new_folder != old_folder:
                    if not old_path.exists():
                        self._send_json(404, {'error': 'Source folder not found'})
                        return
                    if new_path.exists():
                        self._send_json(409, {'error': 'Destination already exists'})
                        return
                    old_path.rename(new_path)
                    renamed_folder = True
                    refresh_needed = True
                target_path = new_path if renamed_folder else old_path
                if new_sku and old_sku and new_sku != old_sku:
                    ok, error, sku_renames = apply_sku_renames_with_tracking(target_path, old_sku, new_sku)
                    if not ok:
                        if renamed_folder:
                            new_path.rename(old_path)
                        self._send_json(409, {'error': error or 'Failed to rename files'})
                        return
                    if sku_renames:
                        refresh_needed = True
                if not db.update_product(old_category, old_folder, row):
                    if sku_renames:
                        rollback_sku_renames(sku_renames)
                    if renamed_folder:
                        new_path.rename(old_path)
                    self._send_json(404, {'error': 'Row not found'})
                    return
                if new_category != old_category or new_folder != old_folder or new_sku:
                    update_stock_refs(old_category, old_folder, new_category, new_folder, new_sku)
                if renamed_folder:
                    existing_by_key.pop((old_category, old_folder), None)
                    existing_by_key[(new_category, new_folder)] = row
                    if row_id is not None:
                        existing_by_id[str(row_id)] = row
            db.upsert_products(rows)
            self._send_json(200, {'ok': True, 'refresh': refresh_needed})
            return

        if parsed.path == '/api/rename':
            category = safe_path_component(data.get('category', ''))
            old_name = safe_path_component(data.get('old_name', ''))
            new_name = sanitize_folder_name(data.get('new_name', ''))
            status = data.get('status', '')
            if not category or not old_name or not new_name:
                self._send_json(400, {'error': 'Missing category/old_name/new_name'})
                return
            if not is_safe_component(new_name):
                self._send_json(400, {'error': 'Invalid folder name'})
                return
            if not db.product_exists(category, old_name):
                self._send_json(404, {'error': 'Row not found'})
                return
            if db.product_exists(category, new_name):
                self._send_json(409, {'error': 'Destination already exists'})
                return
            old_path = product_dir(category, old_name, status)
            new_path = product_dir(category, new_name, status)
            if not old_path.exists():
                self._send_json(404, {'error': 'Source folder not found'})
                return
            if new_path.exists():
                self._send_json(409, {'error': 'Destination already exists'})
                return
            old_path.rename(new_path)
            if not db.rename_product(category, old_name, new_name):
                new_path.rename(old_path)
                self._send_json(404, {'error': 'Row not found'})
                return
            new_sku = None
            existing = db.fetch_product(category, new_name)
            if existing:
                new_sku = (existing.get('sku') or '').strip() or None
            update_stock_refs(category, old_name, category, new_name, new_sku)
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/update_row':
            old_category = safe_path_component(data.get('old_category', ''))
            old_product_folder = safe_path_component(data.get('old_product_folder', ''))
            row = data.get('row') or {}
            if not old_category or not old_product_folder:
                self._send_json(400, {'error': 'Missing old_category/old_product_folder'})
                return
            existing = db.fetch_product(old_category, old_product_folder)
            if not existing:
                self._send_json(404, {'error': 'Row not found'})
                return
            old_status = existing.get('Status') or 'Live'
            old_sku = (existing.get('sku') or '').strip()
            new_category = safe_path_component(row.get('category', '')) or old_category
            new_folder = normalize_folder_name(row.get('product_folder', ''), old_product_folder)
            new_sku = (row.get('sku') or '').strip() or None
            if new_sku and old_sku and new_folder == old_product_folder:
                new_folder, _ = derive_folder_for_sku(new_folder, old_sku, new_sku)
                row['product_folder'] = new_folder
            if (
                (new_category != old_category or new_folder != old_product_folder)
                and db.product_exists(new_category, new_folder)
            ):
                self._send_json(409, {'error': 'Destination already exists'})
                return
            if 'Status' not in row and 'status' not in row:
                row['Status'] = existing.get('Status')
            if 'Completed' not in row and 'completed' not in row:
                row['Completed'] = existing.get('Completed', '')
            row['category'] = new_category
            row['product_folder'] = new_folder
            old_path = product_dir(old_category, old_product_folder, old_status)
            new_path = product_dir(new_category, new_folder, old_status)
            renamed_folder = False
            sku_renames = []
            if (new_category != old_category or new_folder != old_product_folder):
                if not old_path.exists():
                    self._send_json(404, {'error': 'Source folder not found'})
                    return
                if new_path.exists():
                    self._send_json(409, {'error': 'Destination already exists'})
                    return
                old_path.rename(new_path)
                renamed_folder = True
            target_path = new_path if renamed_folder else old_path
            if new_sku and old_sku and new_sku != old_sku:
                ok, error, sku_renames = apply_sku_renames_with_tracking(target_path, old_sku, new_sku)
                if not ok:
                    if renamed_folder:
                        new_path.rename(old_path)
                    self._send_json(409, {'error': error or 'Failed to rename files'})
                    return
            if not db.update_product(old_category, old_product_folder, row):
                if sku_renames:
                    rollback_sku_renames(sku_renames)
                if renamed_folder:
                    new_path.rename(old_path)
                self._send_json(404, {'error': 'Row not found'})
                return
            if new_category != old_category or new_folder != old_product_folder or new_sku:
                update_stock_refs(old_category, old_product_folder, new_category, new_folder, new_sku)
            self._send_json(200, {'ok': True, 'row': row})
            return

        if parsed.path == '/api/stock_adjust':
            category = safe_path_component(data.get('category', ''))
            product_folder = safe_path_component(data.get('product_folder', ''))
            sku = (data.get('sku', '') or '').strip()
            color = (data.get('color', '') or '').strip()
            size = (data.get('size', '') or '').strip()
            delta_raw = data.get('delta', 0)
            try:
                delta = int(delta_raw)
            except (TypeError, ValueError):
                self._send_json(400, {'error': 'Invalid delta'})
                return
            if not category or not product_folder:
                self._send_json(400, {'error': 'Missing category/product_folder'})
                return
            if delta == 0:
                self._send_json(400, {'error': 'Delta must be non-zero'})
                return
            if not sku:
                existing = db.fetch_product(category, product_folder)
                if existing:
                    sku = (existing.get('sku') or '').strip()
            matched = db.get_stock_entry(category, product_folder, color, size)
            if matched:
                try:
                    current_qty = int(matched.get('quantity') or 0)
                except (TypeError, ValueError):
                    current_qty = 0
                new_qty = current_qty + delta
                if new_qty <= 0:
                    db.delete_stock_entry(category, product_folder, color, size)
                    self._send_json(200, {'ok': True, 'quantity': 0, 'removed': True})
                    return
                db.upsert_stock_entry(category, product_folder, sku, color, size, new_qty)
                self._send_json(200, {'ok': True, 'quantity': new_qty})
                return
            if delta < 0:
                self._send_json(400, {'error': 'No existing stock entry to decrement'})
                return
            db.upsert_stock_entry(category, product_folder, sku, color, size, delta)
            self._send_json(200, {'ok': True, 'quantity': delta})
            return

        if parsed.path == '/api/readme':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            action = data.get('action')
            status = data.get('status', '')
            if not category or not folder_name or action not in ('read', 'write'):
                self._send_json(400, {'error': 'Missing category/folder_name/action'})
                return
            readme_path = product_dir(category, folder_name, status) / 'README.md'
            if action == 'read':
                content = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''
                self._send_json(200, {'ok': True, 'content': content})
                return
            content = data.get('content', '')
            readme_path.write_text(content, encoding='utf-8')
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/product_meta':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            existing = db.fetch_product(category, folder_name)
            if not existing:
                self._send_json(404, {'error': 'Product not found'})
                return

            def normalize_field(value) -> str:
                if value is None:
                    return ''
                if isinstance(value, list):
                    return ', '.join([str(item).strip() for item in value if str(item).strip()])
                return str(value).strip()

            updated = dict(existing)
            if 'tags' in data:
                updated['tags'] = normalize_field(data.get('tags'))
            if 'colors' in data or 'Colors' in data:
                updated['Colors'] = normalize_field(data.get('colors', data.get('Colors')))
            if 'sizes' in data or 'Sizes' in data:
                updated['Sizes'] = normalize_field(data.get('sizes', data.get('Sizes')))

            if not db.update_product(category, folder_name, updated):
                self._send_json(404, {'error': 'Product not found'})
                return

            readme_content = data.get('readme')
            if readme_content is not None:
                status = data.get('status', existing.get('Status') or 'Live')
                readme_path = product_dir(category, folder_name, status) / 'README.md'
                readme_path.write_text(str(readme_content), encoding='utf-8')

            refreshed = db.fetch_product(category, folder_name)
            self._send_json(200, {'ok': True, 'row': refreshed or updated})
            return

        if parsed.path == '/api/pricing':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            action = (data.get('action') or '').strip().lower()
            if not category or not folder_name or action not in ('read', 'write'):
                self._send_json(400, {'error': 'Missing category/folder_name/action'})
                return
            if action == 'read':
                pricing_data = db.get_pricing(category, folder_name)
                if pricing_data is None:
                    self._send_json(404, {'error': 'Product not found'})
                    return
                self._send_json(200, {'ok': True, 'pricing': pricing_data or {'base': {}, 'sizes': []}})
                return
            pricing_data = data.get('pricing') or {}
            if not isinstance(pricing_data, dict):
                self._send_json(400, {'error': 'Invalid pricing payload'})
                return
            if not db.set_pricing(category, folder_name, pricing_data):
                self._send_json(404, {'error': 'Product not found'})
                return
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/add_product':
            category = safe_path_component(data.get('category', ''))
            description = sanitize_folder_name(data.get('description', ''))
            tags = (data.get('tags') or '').strip()
            requires_ukca = bool(data.get('requires_ukca'))
            notes = (data.get('notes') or '').strip()
            if not category or not description:
                self._send_json(400, {'error': 'Missing category/description'})
                return
            if category not in CATEGORY_PREFIXES:
                self._send_json(400, {'error': 'Unknown category'})
                return
            sku = next_sku_for_category(category)
            if not sku:
                self._send_json(500, {'error': 'Failed to create SKU'})
                return
            product_folder = f'{sku} - {description}'
            product_path = DRAFT_DIR / category / product_folder
            if product_path.exists():
                self._send_json(409, {'error': 'Folder already exists'})
                return
            if db.product_exists(category, product_folder):
                self._send_json(409, {'error': 'Row already exists'})
                return
            product_path.mkdir(parents=True, exist_ok=True)
            (product_path / 'Media').mkdir(exist_ok=True)
            (product_path / 'STL').mkdir(exist_ok=True)
            (product_path / 'MISC').mkdir(exist_ok=True)
            if requires_ukca:
                (product_path / 'UKCA').mkdir(exist_ok=True)
            readme_path = product_path / 'README.md'
            if not readme_path.exists():
                content = readme_template(description, sku)
                if notes:
                    content = f"{content}\n## Notes\n{notes}\n"
                readme_path.write_text(content, encoding='utf-8')

            row = {
                'category': category,
                'product_folder': product_folder,
                'sku': sku,
                'UKCA': 'No' if requires_ukca else 'N/A',
                'Listings': '',
                'tags': tags,
                'Colors': '',
                'Sizes': '',
                'Cost To Make': '',
                'Sale Price': '',
                'Postage Price': '',
                'Completed': '',
                'Status': 'Draft',
                'Facebook URL': '',
                'TikTok URL': '',
                'Ebay URL': '',
                'Etsy URL': '',
            }
            inserted = db.insert_product(row)
            if inserted and 'id' in inserted:
                row['id'] = inserted['id']
            self._send_json(200, {'ok': True, 'headers': db.PRODUCT_HEADERS, 'row': row})
            return

        if parsed.path == '/api/archive':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            src_path = CATEGORIES_DIR / category / folder_name
            if not src_path.exists():
                self._send_json(404, {'error': 'Source folder not found'})
                return
            dest_dir = ARCHIVE_DIR / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / folder_name
            if dest_path.exists():
                self._send_json(409, {'error': 'Destination already exists'})
                return
            src_path.rename(dest_path)
            db.set_product_status(category, folder_name, 'Archived')
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/approve':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            src_path = DRAFT_DIR / category / folder_name
            if not src_path.exists():
                self._send_json(404, {'error': 'Source folder not found'})
                return
            dest_dir = CATEGORIES_DIR / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / folder_name
            if dest_path.exists():
                self._send_json(409, {'error': 'Destination already exists'})
                return
            src_path.rename(dest_path)
            db.set_product_status(category, folder_name, 'Live')
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/move_to_draft':
            category = safe_path_component(data.get('category', ''))
            folder_name = safe_path_component(data.get('folder_name', ''))
            if not category or not folder_name:
                self._send_json(400, {'error': 'Missing category/folder_name'})
                return
            src_path = CATEGORIES_DIR / category / folder_name
            if not src_path.exists():
                self._send_json(404, {'error': 'Source folder not found'})
                return
            dest_dir = DRAFT_DIR / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / folder_name
            if dest_path.exists():
                self._send_json(409, {'error': 'Destination already exists'})
                return
            src_path.rename(dest_path)
            db.set_product_status(category, folder_name, 'Draft')
            self._send_json(200, {'ok': True})
            return

        self.send_error(404)


def main():
    db.ensure_schema()
    port = int(os.environ.get('CSV_EDITOR_PORT', '8555'))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'Serving product manager at: http://localhost:{port}/')
    server.serve_forever()


if __name__ == '__main__':
    main()
