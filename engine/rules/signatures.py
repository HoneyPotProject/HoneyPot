# All compiled regexes and path lists, grouped by category. Detectors import
# from here, so you can tune rules without touching detector logic.

import re

SQL_PATTERNS = [
    re.compile(r'(?i)\bunion\b\s+\bselect\b'),
    re.compile(r"(?i)('\s*or\s+'?1'?\s*=\s*'?1)|(\bor\s+1\s*=\s*1\b)"),
    re.compile(r'(?i)\b(sleep|benchmark)\s*\('),
    re.compile(r'(?i);\s*(drop|insert|update|delete|alter)\b'),
    re.compile(r'(?i)/\*|\*/|--\s'),
    re.compile(r'(?i)\binformation_schema\b'),
    re.compile(r"(?i)'\s*;\s*--"),
    re.compile(r'(?i)\bselect\b.+\bfrom\b'),
]

XSS_PATTERNS = [
    re.compile(r'(?i)<\s*script\b'),
    re.compile(r'(?i)javascript\s*:'),
    re.compile(r'(?i)\bon(error|load|click|mouseover|focus|submit)\s*='),
    re.compile(r'(?i)<\s*iframe\b'),
    re.compile(r'(?i)<\s*svg\b[^>]*onload'),
    re.compile(r'(?i)document\s*\.\s*(cookie|location)'),
]

PATH_TRAVERSAL_PATTERNS = [
    re.compile(r'(?i)(\.\./|\.\.\\)'),
    re.compile(r'(?i)(%2e%2e%2f|%2e%2e/|\.\.%2f|%2e%2e\\)'),
    re.compile(r'(?i)(%252e%252e%252f)'),
    re.compile(r'(?i)(\.\.%c0%af|\.\.%c1%9c)'),
    re.compile(r'(?i)(etc/passwd|windows[/\\]win\.ini|boot\.ini)'),
]

COMMAND_SEPARATORS = re.compile(r'(;|&&|\|\||`|\$\(|\|)')
COMMAND_WORDS = re.compile(
    r'(?i)\b(cat|ls|id|whoami|uname|wget|curl|nc|bash|sh|powershell|cmd|python|perl|chmod|rm)\b'
)

SENSITIVE_PATHS = (
    '/.env',
    '/.git/config',
    '/.git/HEAD',
    '/wp-admin',
    '/wp-login.php',
    '/phpmyadmin',
    '/admin',
    '/administrator',
    '/backup.zip',
    '/backup.sql',
    '/config.php',
    '/server-status',
    '/.aws/credentials',
    '/id_rsa',
    '/web.config',
    '/xmlrpc.php',
)

SENSITIVE_PATH_PREFIXES = (
    '/.git/',
    '/wp-admin/',
    '/phpmyadmin/',
    '/administrator/',
)

UNUSUAL_METHODS = frozenset({
    'TRACE', 'TRACK', 'CONNECT', 'DEBUG', 'PROPFIND', 'MOVE', 'COPY',
})
STANDARD_METHODS = frozenset({
    'GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'PATCH',
})
