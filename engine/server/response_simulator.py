# Returns fake responses: a fake login page, fake 403/404, and a fake /admin.
# It never reads host files or runs input.

from __future__ import annotations

from engine.core.context import RequestContext

_LOGIN_HTML = (
    b'<!doctype html><html><head><title>Sign in</title></head>'
    b'<body><h1>Account Login</h1>'
    b'<form method="post" action="/login">'
    b'<input name="username"/><input type="password" name="password"/>'
    b'<button type="submit">Login</button></form></body></html>'
)

_ADMIN_HTML = (
    b'<!doctype html><html><head><title>Admin</title></head>'
    b'<body><h1>Administration</h1><p>Access restricted.</p></body></html>'
)

_NOT_FOUND = b'<!doctype html><html><body><h1>404 Not Found</h1></body></html>'
_FORBIDDEN = b'<!doctype html><html><body><h1>403 Forbidden</h1></body></html>'
_OK = b'<!doctype html><html><body><h1>Welcome</h1></body></html>'


def simulate(ctx: RequestContext) -> tuple[int, bytes, str]:
    """Return (status_code, body, content_type) for a decoy response."""
    path = (ctx.path or '/').lower()
    if path in {'/login', '/wp-login.php', '/signin', '/user/login', '/admin/login'}:
        return 200, _LOGIN_HTML, 'text/html; charset=utf-8'
    if path.startswith('/admin') or path.startswith('/wp-admin'):
        return 403, _ADMIN_HTML if path == '/admin' else _FORBIDDEN, 'text/html; charset=utf-8'
    if path in {'/.env', '/.git/config', '/backup.zip', '/id_rsa'}:
        return 403, _FORBIDDEN, 'text/html; charset=utf-8'
    if path in {'/', '/index.html', '/home'}:
        return 200, _OK, 'text/html; charset=utf-8'
    return 404, _NOT_FOUND, 'text/html; charset=utf-8'


def encode_http(status: int, body: bytes, content_type: str) -> bytes:
    reason = {200: 'OK', 403: 'Forbidden', 404: 'Not Found'}.get(status, 'OK')
    headers = (
        f'HTTP/1.1 {status} {reason}\r\n'
        f'Content-Type: {content_type}\r\n'
        f'Content-Length: {len(body)}\r\n'
        'Connection: close\r\n'
        'Server: Apache/2.4.52 (Ubuntu)\r\n'
        'X-Powered-By: PHP/8.1.2\r\n'
        '\r\n'
    )
    return headers.encode('ascii') + body
