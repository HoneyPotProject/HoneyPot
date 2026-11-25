# Sends harmless test payloads to your local honeypot only, so you can demo and test.

from __future__ import annotations

import argparse
import socket
import time


PAYLOADS = [
    b'GET /login HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b"GET /search?q=1'+OR+1%3D1 HTTP/1.1\r\nHost: localhost\r\n\r\n",
    b'GET /q?x=%3Cscript%3Ealert(1)%3C/script%3E HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'GET /static/..%2f..%2fetc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'GET /run?cmd=%3Bid%3Bcat+/etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'GET /.env HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'GET /wp-admin HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'GET /phpmyadmin HTTP/1.1\r\nHost: localhost\r\n\r\n',
    b'POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 29\r\n\r\nusername=admin&password=test',
    b'POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 29\r\n\r\nusername=admin&password=test',
    b'POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 29\r\n\r\nusername=admin&password=test',
    b'POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 29\r\n\r\nusername=admin&password=test',
    b'POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 29\r\n\r\nusername=admin&password=test',
    b'TRACE / HTTP/1.1\r\nHost: localhost\r\n\r\n',
]


def send(host: str, port: int, payload: bytes) -> None:
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.sendall(payload)
        sock.settimeout(2)
        try:
            sock.recv(1024)
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description='Send harmless local honeypot probes')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    for payload in PAYLOADS:
        send(args.host, args.port, payload)
        time.sleep(0.05)
        print(f'sent {payload.split(b" ")[0].decode()} {payload.split(b" ")[1].decode()}')


if __name__ == '__main__':
    main()
