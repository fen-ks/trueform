import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from trueform.web.server import TrueformHandler


def _with_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), TrueformHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{port}"


def _post(url: str, payload: dict) -> dict:
    req = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def test_web_serves_index():
    httpd, base = _with_server()
    try:
        with urlopen(f"{base}/", timeout=5) as resp:
            html = resp.read().decode()
        assert "trueform" in html.lower()
    finally:
        httpd.shutdown()


def test_api_score_returns_json():
    httpd, base = _with_server()
    try:
        data = _post(
            f"{base}/api/score",
            {"text": "Furthermore, it is important to note that we utilize this."},
        )
        assert "score" in data
        assert data["score"]["overall"] < 80
    finally:
        httpd.shutdown()


def test_api_humanize_with_mock():
    httpd, base = _with_server()
    try:
        data = _post(
            f"{base}/api/humanize",
            {
                "text": "Furthermore, we utilize it.",
                "provider": "mock",
            },
        )
        assert "text" in data
        assert data["scores"]["after"]["overall"] >= data["scores"]["before"]["overall"]
    finally:
        httpd.shutdown()
