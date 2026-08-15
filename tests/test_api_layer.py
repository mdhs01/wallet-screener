import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.wallet_screener.api_client import ApiClient
from src.wallet_screener.gmgn_adapter import GMGNAdapter, GmgnEndpointMap
from src.wallet_screener.api_config import ProviderConfig


class Handler(BaseHTTPRequestHandler):
    calls = 0

    def do_GET(self):
        Handler.calls += 1
        payload = {"data": {"items": [{"address": "wallet-1"}]}}
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def test_api_client_get_and_cache():
    Handler.calls = 0
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = ApiClient(base_url=f"http://127.0.0.1:{server.server_port}", requests_per_second=1000, cache_ttl_seconds=30)
        assert client.get("/items").data["data"]["items"][0]["address"] == "wallet-1"
        assert client.get("/items").from_cache is True
        assert Handler.calls == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_gmgn_adapter_does_not_assume_endpoints():
    config = ProviderConfig(name="gmgn", base_url="http://127.0.0.1:1")
    adapter = GMGNAdapter(config, GmgnEndpointMap())
    try:
        adapter.discover_wallets()
    except Exception as exc:
        assert "endpoint for discovery is not configured" in str(exc)
    else:
        raise AssertionError("Expected missing endpoint configuration error")
