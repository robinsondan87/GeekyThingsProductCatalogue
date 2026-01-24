#!/usr/bin/env python3
import csv
import json
import mimetypes
import os
import re
import shutil
import time
import secrets
import hmac
import pyotp
from email import message_from_bytes
from email.policy import default
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PRODUCTS_DIR = Path(os.environ.get('PRODUCTS_DIR', ROOT_DIR / 'Products')).resolve()
UI_DIST_DIR = BASE_DIR / 'ui' / 'dist'
STOCK_PATH = PRODUCTS_DIR / 'stock.csv'
AUTH_USERNAME = os.environ.get('AUTH_USERNAME')
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD')
AUTH_TOTP_SECRET = os.environ.get('AUTH_TOTP_SECRET')
AUTH_COOKIE_SECURE = os.environ.get('AUTH_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes')
SESSION_TTL_SECONDS = int(os.environ.get('SESSION_TTL_SECONDS', '43200'))
SESSIONS = {}
FILE_TOKENS = {}
FILE_TOKEN_TTL_SECONDS = int(os.environ.get('FILE_TOKEN_TTL_SECONDS', '300'))
CSV_PATH = PRODUCTS_DIR / 'categories_index.csv'
CATEGORIES_DIR = PRODUCTS_DIR / 'Categories'
ARCHIVE_DIR = CATEGORIES_DIR / '_Archive'
DRAFT_DIR = CATEGORIES_DIR / '_Draft'
UKCA_SHARED_DIR = PRODUCTS_DIR / 'UKCA_Shared'
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


def read_csv():
    if not CSV_PATH.exists():
        return [], []
    with CSV_PATH.open(newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    if 'tags' not in headers:
        headers.append('tags')
    if 'Listings' not in headers:
        headers.append('Listings')
    if 'Status' not in headers:
        headers.append('Status')
    if 'Colors' not in headers:
        headers.append('Colors')
    if 'Sizes' not in headers:
        headers.append('Sizes')
    for row in rows:
        row.setdefault('tags', '')
        row.setdefault('Listings', '')
        row.setdefault('Colors', '')
        row.setdefault('Sizes', '')
        row['Status'] = normalize_status(row.get('Status'))
    return headers, rows


def write_csv(headers, rows):
    if 'tags' not in headers:
        headers.append('tags')
    if 'Listings' not in headers:
        headers.append('Listings')
    if 'Status' not in headers:
        headers.append('Status')
    if 'Colors' not in headers:
        headers.append('Colors')
    if 'Sizes' not in headers:
        headers.append('Sizes')
    with CSV_PATH.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            row.setdefault('tags', '')
            row.setdefault('Listings', '')
            row.setdefault('Colors', '')
            row.setdefault('Sizes', '')
            row['Status'] = normalize_status(row.get('Status'))
            writer.writerow(row)


def read_stock():
    if not STOCK_PATH.exists():
        headers = ['category', 'product_folder', 'sku', 'color', 'size', 'quantity']
        return headers, []
    with STOCK_PATH.open(newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    required = ['category', 'product_folder', 'sku', 'color', 'size', 'quantity']
    for field in required:
        if field not in headers:
            headers.append(field)
    for row in rows:
        for field in required:
            row.setdefault(field, '')
    return headers, rows


def write_stock(headers, rows):
    required = ['category', 'product_folder', 'sku', 'color', 'size', 'quantity']
    for field in required:
        if field not in headers:
            headers.append(field)
    with STOCK_PATH.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            for field in required:
                row.setdefault(field, '')
            writer.writerow(row)


def update_stock_refs(old_category: str, old_folder: str, new_category: str, new_folder: str, new_sku: str | None):
    headers, rows = read_stock()
    updated = False
    for row in rows:
        if row.get('category') == old_category and row.get('product_folder') == old_folder:
            row['category'] = new_category
            row['product_folder'] = new_folder
            if new_sku:
                row['sku'] = new_sku
            updated = True
    if updated:
        write_stock(headers, rows)


def safe_path_component(name: str) -> str:
    # Prevent path traversal by normalizing
    return name.replace('..', '').strip()


def sanitize_folder_name(name: str) -> str:
    cleaned = name.replace('/', '-').replace('\\', '-').strip()
    return ' '.join(cleaned.split())


def normalize_status(value: str) -> str:
    lowered = (value or '').strip().lower()
    if lowered == 'draft':
        return 'Draft'
    if lowered == 'archived':
        return 'Archived'
    return 'Live'


def product_base_dir(status: str) -> Path:
    if normalize_status(status) == 'Draft':
        return DRAFT_DIR
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


def next_sku_for_category(category: str) -> str:
    prefix = CATEGORY_PREFIXES.get(category)
    if not prefix:
        return ''
    cat_dir = CATEGORIES_DIR / category
    if not cat_dir.exists():
        return f'{prefix}-00001'
    max_num = 0
    for entry in cat_dir.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if not name.startswith(prefix + '-'):
            continue
        parts = name.split(' - ', 1)[0]
        try:
            num = int(parts.replace(prefix + '-', ''))
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
            if parsed.path.startswith('/files/'):
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
            headers, rows = read_csv()
            self._send_json(200, {'headers': headers, 'rows': rows})
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

        if parsed.path == '/api/archived':
            headers, rows = read_csv()
            items = [
                {
                    'category': row.get('category', ''),
                    'product_folder': row.get('product_folder', ''),
                }
                for row in rows
                if normalize_status(row.get('Status')) == 'Archived'
            ]
            self._send_json(200, {'items': items})
            return

        if parsed.path == '/api/drafts':
            headers, rows = read_csv()
            items = [
                {
                    'category': row.get('category', ''),
                    'product_folder': row.get('product_folder', ''),
                }
                for row in rows
                if normalize_status(row.get('Status')) == 'Draft'
            ]
            self._send_json(200, {'items': items})
            return

        if parsed.path == '/api/stock':
            headers, rows = read_stock()
            self._send_json(200, {'headers': headers, 'rows': rows})
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
            files = []
            for key, path in ukca_file_paths(product_path).items():
                files.append({
                    'key': key,
                    'exists': path.exists(),
                })
            self._send_json(200, {'files': files})
            return

        if parsed.path.startswith('/files/'):
            rel = unquote(parsed.path.replace('/files/', '', 1))
            rel_path = Path(*[p for p in rel.split('/') if p and p not in ('.', '..')])
            file_path = (CATEGORIES_DIR / rel_path).resolve()
            if not str(file_path).startswith(str(CATEGORIES_DIR.resolve())):
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
            body = self.rfile.read(content_length) if content_length > 0 else b''
            fields, files_field = parse_multipart_form_data(
                self.headers.get('Content-Type', ''),
                body,
            )
            category = safe_path_component(fields.get('category', ''))
            folder_name = safe_path_component(fields.get('folder_name', ''))
            status = fields.get('status', '')
            sku = (fields.get('sku', '') or '').strip()
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
                new_name = next_sku_filename(dest_dir, sku, ext) or name
                dest_path = dest_dir / new_name
                with dest_path.open('wb') as f:
                    f.write(item.get('content') or b'')
                saved.append(str(dest_path))
            self._send_json(200, {'ok': True, 'saved': saved})
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
            rel_clean = Path(*[p for p in rel_path.split('/') if p and p not in ('.', '..')])
            target_path = (base_path / rel_clean).resolve()
            if not str(target_path).startswith(str(base_path)):
                self._send_json(403, {'error': 'Invalid path'})
                return
            if not target_path.exists() or not target_path.is_file():
                self._send_json(404, {'error': 'File not found'})
                return
            token = create_file_token(target_path)
            self._send_json(200, {'token': token})
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
            target_path = (base_path / rel_path).resolve()
            if not str(target_path).startswith(str(base_path)):
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

            declaration = apply_replacements(read_template(declaration_template_path), replacements)
            if declaration:
                (ukca_dir / 'Declarations' / 'UKCA_Declaration_of_Conformity.md').write_text(
                    declaration, encoding='utf-8'
                )

            risk = apply_replacements(read_template(risk_template_path), replacements)
            if risk:
                (ukca_dir / 'Risk_Assessment' / 'Risk_Assessment.md').write_text(
                    risk, encoding='utf-8'
                )

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
                (ukca_dir / 'EN71-1_Compliance_Pack.md').write_text(header + en71, encoding='utf-8')

            headers, rows = read_csv()
            updated = False
            for existing in rows:
                if existing.get('category') == category and existing.get('product_folder') == folder_name:
                    existing['UKCA'] = 'Yes'
                    updated = True
                    break
            if updated:
                write_csv(headers, rows)

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
                if not target.exists():
                    self._send_json(404, {'error': 'UKCA file not found'})
                    return
                self._send_json(200, {'content': target.read_text(encoding='utf-8')})
                return
            if action == 'write':
                if not target.exists():
                    self._send_json(404, {'error': 'UKCA file not found'})
                    return
                content = data.get('content', '')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
                self._send_json(200, {'ok': True})
                return
            self._send_json(400, {'error': 'Invalid action'})
            return

        if parsed.path == '/api/save':
            headers = data.get('headers') or []
            rows = data.get('rows') or []
            write_csv(headers, rows)
            self._send_json(200, {'ok': True})
            return

        if parsed.path == '/api/rename':
            category = safe_path_component(data.get('category', ''))
            old_name = safe_path_component(data.get('old_name', ''))
            new_name = sanitize_folder_name(data.get('new_name', ''))
            status = data.get('status', '')
            if not category or not old_name or not new_name:
                self._send_json(400, {'error': 'Missing category/old_name/new_name'})
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
            headers, rows = read_csv()
            updated = False
            new_sku = None
            for existing in rows:
                if existing.get('category') == category and existing.get('product_folder') == old_name:
                    existing['product_folder'] = new_name
                    new_sku = existing.get('sku') or None
                    updated = True
                    break
            if updated:
                write_csv(headers, rows)
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
            new_category = safe_path_component(row.get('category', '')) or old_category
            new_folder = safe_path_component(row.get('product_folder', '')) or old_product_folder
            new_sku = (row.get('sku') or '').strip() or None
            headers, rows = read_csv()
            updated = False
            for existing in rows:
                if existing.get('category') == old_category and existing.get('product_folder') == old_product_folder:
                    existing.update(row)
                    updated = True
                    break
            if not updated:
                self._send_json(404, {'error': 'Row not found'})
                return
            write_csv(headers, rows)
            if new_category != old_category or new_folder != old_product_folder or new_sku:
                update_stock_refs(old_category, old_product_folder, new_category, new_folder, new_sku)
            self._send_json(200, {'ok': True})
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
                _, rows_csv = read_csv()
                for existing in rows_csv:
                    if existing.get('category') == category and existing.get('product_folder') == product_folder:
                        sku = (existing.get('sku') or '').strip()
                        break
            headers, rows = read_stock()
            matched = None
            for stock_row in rows:
                if (
                    stock_row.get('category') == category
                    and stock_row.get('product_folder') == product_folder
                    and (stock_row.get('color') or '').strip() == color
                    and (stock_row.get('size') or '').strip() == size
                ):
                    matched = stock_row
                    break
            if matched:
                try:
                    current_qty = int(matched.get('quantity') or 0)
                except ValueError:
                    current_qty = 0
                new_qty = current_qty + delta
                if new_qty <= 0:
                    rows.remove(matched)
                    write_stock(headers, rows)
                    self._send_json(200, {'ok': True, 'quantity': 0, 'removed': True})
                    return
                matched['quantity'] = str(new_qty)
                if sku:
                    matched['sku'] = sku
                write_stock(headers, rows)
                self._send_json(200, {'ok': True, 'quantity': new_qty})
                return
            if delta < 0:
                self._send_json(400, {'error': 'No existing stock entry to decrement'})
                return
            rows.append({
                'category': category,
                'product_folder': product_folder,
                'sku': sku,
                'color': color,
                'size': size,
                'quantity': str(delta),
            })
            write_stock(headers, rows)
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

            headers, rows = read_csv()
            if 'tags' not in headers:
                headers.append('tags')
            row = {
                'category': category,
                'product_folder': product_folder,
                'sku': sku,
                'UKCA': 'No' if requires_ukca else 'N/A',
                'Listings': '',
                'tags': tags,
                'Colors': '',
                'Sizes': '',
                'Status': 'Draft',
                'Facebook URL': '',
                'TikTok URL': '',
                'Ebay URL': '',
                'Etsy URL': '',
            }
            rows.append(row)
            write_csv(headers, rows)
            self._send_json(200, {'ok': True, 'headers': headers, 'row': row})
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
            headers, rows = read_csv()
            updated = False
            for existing in rows:
                if existing.get('category') == category and existing.get('product_folder') == folder_name:
                    existing['Status'] = 'Archived'
                    updated = True
                    break
            if updated:
                write_csv(headers, rows)
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
            headers, rows = read_csv()
            updated = False
            for existing in rows:
                if existing.get('category') == category and existing.get('product_folder') == folder_name:
                    existing['Status'] = 'Live'
                    updated = True
                    break
            if updated:
                write_csv(headers, rows)
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
            headers, rows = read_csv()
            updated = False
            for existing in rows:
                if existing.get('category') == category and existing.get('product_folder') == folder_name:
                    existing['Status'] = 'Draft'
                    updated = True
                    break
            if updated:
                write_csv(headers, rows)
            self._send_json(200, {'ok': True})
            return

        self.send_error(404)


def main():
    port = int(os.environ.get('CSV_EDITOR_PORT', '8555'))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'Serving CSV editor at: http://localhost:{port}/')
    server.serve_forever()


if __name__ == '__main__':
    main()
