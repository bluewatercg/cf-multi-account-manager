#!/usr/bin/env python3
"""Copy local accounts to the deployed Pages Functions API without printing tokens."""
import argparse, base64, getpass, hashlib, json, os, sqlite3, sys, urllib.error, urllib.request, http.cookiejar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'cloudflare-manager.db'
SECRET = ROOT / 'data' / '.local_secret'

def stream(key: bytes, size: int) -> bytes:
    out, i = b'', 0
    while len(out) < size:
        out += hashlib.sha256(key + i.to_bytes(8, 'big')).digest(); i += 1
    return out[:size]

def decrypt(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    return bytes(a ^ b for a, b in zip(raw, stream(SECRET.read_bytes(), len(raw)))).decode()

def request(opener, url, method='GET', payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'application/json', 'Origin': url.split('/api/', 1)[0],
    })
    with opener.open(req, timeout=30) as response:
        return json.loads(response.read().decode() or '{}')

def main():
    parser = argparse.ArgumentParser(description='同步本地 SQLite 账号到 Cloudflare Pages')
    parser.add_argument('--url', default='https://cf-multi-account-manager.pages.dev', help='Pages 根地址')
    parser.add_argument('--all', action='store_true', help='同时同步已停用账号')
    args = parser.parse_args()
    if not DB.exists() or not SECRET.exists(): raise SystemExit('找不到本地数据库或密钥文件')
    base = args.url.rstrip('/')
    password = getpass.getpass('Pages ADMIN 密码（不会显示）：')
    jar = http.cookiejar.CookieJar(); opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try: request(opener, base + '/api/auth/login', 'POST', {'password': password})
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors='replace')[:500]
        raise SystemExit(f'Pages 登录失败：HTTP {e.code} {detail}')
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        query = 'SELECT alias,account_id,token_encrypted,daily_quota,enabled,notes,email_hint FROM accounts'
        if not args.all: query += ' WHERE enabled=1'
        local = conn.execute(query).fetchall()
    existing = {row.get('account_id') for row in request(opener, base + '/api/accounts') if isinstance(row, dict)}
    created = skipped = failed = 0
    for row in local:
        if row['account_id'] in existing:
            skipped += 1; continue
        payload = {'alias': row['alias'], 'account_id': row['account_id'], 'token': decrypt(row['token_encrypted']), 'daily_quota': row['daily_quota'], 'enabled': bool(row['enabled']), 'notes': row['notes'] or '', 'email_hint': row['email_hint'] or ''}
        try:
            result = request(opener, base + '/api/accounts', 'POST', payload)
            if result.get('ok'): created += 1; existing.add(row['account_id'])
            else: failed += 1; print(f"失败：{row['alias']}：{result.get('error', '未知错误')}")
        except Exception as exc:
            failed += 1; print(f'失败：{row["alias"]}：{exc}')
    remote = request(opener, base + '/api/accounts')
    print(f'同步完成：新增 {created}，跳过 {skipped}，失败 {failed}，共读取 {len(local)} 个账号；Pages 当前返回 {len(remote)} 个账号')

if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print('\n已取消'); sys.exit(130)
