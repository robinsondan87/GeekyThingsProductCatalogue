import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402


def test_safe_rel_path_rejects_absolute_and_parent():
    assert server.safe_rel_path('/etc/passwd') is None
    assert server.safe_rel_path('..') is None
    assert server.safe_rel_path('../secrets') is None
    assert server.safe_rel_path('C:\\Windows') is None


def test_safe_rel_path_allows_nested():
    result = server.safe_rel_path('Media/poster.png')
    assert result is not None
    assert result.as_posix() == 'Media/poster.png'


def test_unique_filename_increments(tmp_path):
    (tmp_path / 'file.txt').write_text('one', encoding='utf-8')
    (tmp_path / 'file-001.txt').write_text('two', encoding='utf-8')
    name = server.unique_filename(tmp_path, 'file.txt')
    assert name == 'file-002.txt'


def test_collect_sku_renames_skips_deleted(tmp_path):
    sku_old = 'GT-OLD-0001'
    sku_new = 'GT-NEW-0002'
    (tmp_path / 'GT-OLD-0001-model.3mf').write_text('data', encoding='utf-8')
    deleted_dir = tmp_path / '_Deleted'
    deleted_dir.mkdir()
    (deleted_dir / 'GT-OLD-0001-old.3mf').write_text('old', encoding='utf-8')

    renames, error = server.collect_sku_renames(tmp_path, sku_old, sku_new)
    assert error is None
    assert len(renames) == 1
    src, dest = renames[0]
    assert src.name == 'GT-OLD-0001-model.3mf'
    assert dest.name == 'GT-NEW-0002-model.3mf'


def test_collect_sku_renames_detects_conflict(tmp_path):
    sku_old = 'GT-OLD-0001'
    sku_new = 'GT-NEW-0002'
    (tmp_path / 'GT-OLD-0001-model.3mf').write_text('data', encoding='utf-8')
    (tmp_path / 'GT-NEW-0002-model.3mf').write_text('existing', encoding='utf-8')

    renames, error = server.collect_sku_renames(tmp_path, sku_old, sku_new)
    assert renames == []
    assert error is not None


def test_parse_multipart_form_data_extracts_file():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    content_type = f'multipart/form-data; boundary={boundary}'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="event_id"\r\n\r\n'
        '123\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="file"; filename="poster.png"\r\n'
        'Content-Type: image/png\r\n\r\n'
        'PNGDATA\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')

    fields, files = server.parse_multipart_form_data(content_type, body)
    assert fields['event_id'] == '123'
    assert len(files) == 1
    assert files[0]['filename'] == 'poster.png'
    assert files[0]['content'] == b'PNGDATA'
