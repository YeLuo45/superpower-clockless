from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def load_config(path: Path) -> dict[str, str]:
    data = {"host": "127.0.0.1", "port": "8000"}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("host") and "=" in stripped:
            data["host"] = stripped.split("=", 1)[1].strip().strip('"')
        elif stripped.startswith("port") and "=" in stripped:
            data["port"] = stripped.split("=", 1)[1].strip().strip('"')
    return data


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._json(200, {"ok": True, "service": "ai-superpower", "mode": "starter"})
            return
        self._json(404, {"ok": False, "error": "starter scaffold exposes /health only"})

    def log_message(self, format: str, *args: object) -> None:
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bundled ai-superpower starter server")
    parser.add_argument("--config", default="config.toml")
    args = parser.parse_args(argv)
    cfg = load_config(Path(args.config))
    server = ThreadingHTTPServer((cfg["host"], int(cfg["port"])), Handler)
    print(f"ai-superpower starter listening on http://{cfg['host']}:{cfg['port']}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
