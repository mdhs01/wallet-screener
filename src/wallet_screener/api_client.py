from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    """Raised when an API request cannot be completed successfully."""


@dataclass(slots=True)
class ApiResponse:
    status_code: int
    data: Any
    headers: dict[str, str]
    from_cache: bool = False


class TokenBucket:
    """Small thread-safe rate limiter used by API adapters."""

    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        self.interval = 1.0 / requests_per_second
        self._lock = Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_for = max(0.0, self._next_at - now)
            self._next_at = max(now, self._next_at) + self.interval
        if wait_for:
            time.sleep(wait_for)


class TTLCache:
    def __init__(self, max_items: int = 256) -> None:
        self.max_items = max_items
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str, ttl: float) -> Any | None:
        now = time.monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            created, value = item
            if now - created > ttl:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._items[key] = (time.monotonic(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)


class ApiClient:
    """Provider-neutral JSON HTTP client.

    Endpoint paths, auth headers and API keys are deliberately supplied by
    adapters/configuration later. This class owns common transport concerns.
    """

    def __init__(
        self,
        *,
        base_url: str,
        headers: dict[str, str] | None = None,
        timeout_seconds: float = 15.0,
        retries: int = 2,
        retry_backoff_seconds: float = 0.5,
        requests_per_second: float = 5.0,
        cache_ttl_seconds: float = 5.0,
        cache_items: int = 256,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = dict(headers or {})
        self.timeout_seconds = timeout_seconds
        self.retries = max(0, retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.limiter = TokenBucket(requests_per_second)
        self.cache_ttl_seconds = max(0.0, cache_ttl_seconds)
        self.cache = TTLCache(cache_items)

    def _url(self, path: str, params: dict[str, Any] | None) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            query = urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
            if query:
                url = f"{url}?{query}"
        return url

    @staticmethod
    def _cache_key(method: str, url: str) -> str:
        return f"{method.upper()} {url}"

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, headers: dict[str, str] | None = None) -> ApiResponse:
        method = method.upper()
        url = self._url(path, params)
        cache_key = self._cache_key(method, url)
        if method == "GET" and self.cache_ttl_seconds:
            cached = self.cache.get(cache_key, self.cache_ttl_seconds)
            if cached is not None:
                return ApiResponse(200, cached, {}, True)

        body = None
        request_headers = dict(self.headers)
        request_headers.update(headers or {})
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request_headers.setdefault("Accept", "application/json")

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self.limiter.wait()
            request = Request(url, data=body, headers=request_headers, method=method)
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                    data = json.loads(raw) if raw else None
                    headers_out = {k.lower(): v for k, v in response.headers.items()}
                    if method == "GET" and self.cache_ttl_seconds:
                        self.cache.set(cache_key, data)
                    return ApiResponse(response.status, data, headers_out)
            except HTTPError as exc:
                last_error = exc
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt >= self.retries:
                    detail = exc.read().decode("utf-8", errors="replace")
                    raise ApiError(f"HTTP {exc.code} for {url}: {detail[:500]}") from exc
            except (URLError, TimeoutError, ValueError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise ApiError(f"Request failed for {url}: {exc}") from exc
            time.sleep(self.retry_backoff_seconds * (2**attempt))

        raise ApiError(f"Request failed for {url}: {last_error}")

    def get(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> ApiResponse:
        return self.request("GET", path, params=params, headers=headers)
