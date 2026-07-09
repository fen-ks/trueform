"""Minimal local web UI for trueform (stdlib only).

Run with: trueform serve
Then open http://127.0.0.1:8765 in your browser.
"""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from trueform.config import HumanizeConfig, Strength, Tone
from trueform.pipeline.humanizer import Humanizer
from trueform.pipeline.scoring import score_text
from trueform.providers import ProviderError

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765


class TrueformHandler(BaseHTTPRequestHandler):
    server_version = "trueform/0.5"

    def log_message(self, fmt: str, *args) -> None:
        # Quieter logs — only errors go to stderr via default handler on failure.
        if args and str(args[1]).startswith("5"):
            super().log_message(fmt, *args)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._serve_file(_STATIC_DIR / "index.html")
        if path.startswith("/static/"):
            return self._serve_file(_STATIC_DIR / path.removeprefix("/static/"))
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_json()
        except ValueError as exc:
            return self._send_json(400, {"error": str(exc)})

        if path == "/api/score":
            return self._api_score(body)
        if path == "/api/humanize":
            return self._api_humanize(body)
        self._send_json(404, {"error": "Not found"})

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _api_score(self, body: dict) -> None:
        text = str(body.get("text", "")).strip()
        if not text:
            return self._send_json(400, {"error": "text is required"})
        score = score_text(text)
        self._send_json(200, {"score": score.to_dict()})

    def _api_humanize(self, body: dict) -> None:
        text = str(body.get("text", "")).strip()
        if not text:
            return self._send_json(400, {"error": "text is required"})

        provider = body.get("provider") or "mock"
        try:
            tone = Tone(str(body.get("tone", Tone.NATURAL.value)))
            strength = Strength(str(body.get("strength", Strength.MEDIUM.value)))
        except ValueError:
            return self._send_json(400, {"error": "invalid tone or strength"})

        config = HumanizeConfig(
            provider=provider,
            model=body.get("model"),
            tone=tone,
            strength=strength,
            target_score=float(body.get("target_score", 70.0)),
            max_passes=int(body.get("max_passes", 3)),
        )

        try:
            result = Humanizer(config).run(text)
        except ProviderError as exc:
            return self._send_json(502, {"error": str(exc)})
        except ValueError as exc:
            return self._send_json(400, {"error": str(exc)})

        self._send_json(
            200,
            {
                "text": result.text,
                "scores": result.scores,
                "notes": result.notes,
            },
        )

    def _serve_file(self, path: Path) -> None:
        if not path.is_file():
            return self._send_json(404, {"error": "Not found"})
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> None:
    """Start the local web UI (blocks until Ctrl+C)."""
    httpd = ThreadingHTTPServer((host, port), TrueformHandler)
    url = f"http://{host}:{port}"
    print(f"trueform web UI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
