"""Thin Helius API client.

Uses two Helius surfaces:

* Enhanced Transactions API  -> parsed SWAP / TRANSFER events for an address.
* DAS (getAsset)             -> token creators / authorities for the deployer check.

Only read endpoints are touched. No keys, signing, or execution live here.

Set HELIUS_API_KEY in the environment. Free-tier keys work but rate-limit;
the client backs off and retries on 429 / 5xx.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

HELIUS_BASE = "https://api.helius.xyz"
HELIUS_RPC = "https://mainnet.helius-rpc.com"


class HeliusError(RuntimeError):
    pass


class HeliusClient:
    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("HELIUS_API_KEY", "")
        if not self.api_key:
            raise HeliusError(
                "No Helius API key. Set HELIUS_API_KEY or pass --api-key. "
                "Get one free at https://dev.helius.xyz"
            )
        self.timeout = timeout
        self.session = requests.Session()

    # -- low level ----------------------------------------------------------
    def _get(self, url: str, params: dict[str, Any]) -> Any:
        return self._request("GET", url, params=params)

    def _rpc(self, method: str, params: Any) -> Any:
        payload = {"jsonrpc": "2.0", "id": "screener", "method": method, "params": params}
        data = self._request(
            "POST",
            f"{HELIUS_RPC}/?api-key={self.api_key}",
            json=payload,
        )
        if isinstance(data, dict) and data.get("error"):
            raise HeliusError(f"RPC {method} error: {data['error']}")
        return data.get("result") if isinstance(data, dict) else data

    def _request(self, verb: str, url: str, **kwargs: Any) -> Any:
        backoff = 2.0
        last_exc: Exception | None = None
        for attempt in range(5):
            try:
                resp = self.session.request(verb, url, timeout=self.timeout, **kwargs)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise HeliusError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, HeliusError) as exc:
                last_exc = exc
                if attempt == 4:
                    break
                time.sleep(backoff)
                backoff *= 2
        raise HeliusError(f"request to {url} failed after retries: {last_exc}")

    # -- high level ---------------------------------------------------------
    def address_transactions(
        self, address: str, *, limit: int = 3000, tx_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Page the Enhanced Transactions API for an address (newest first)."""
        out: list[dict[str, Any]] = []
        before: str | None = None
        page_size = 100
        while len(out) < limit:
            params: dict[str, Any] = {"api-key": self.api_key, "limit": page_size}
            if before:
                params["before"] = before
            if tx_type:
                params["type"] = tx_type
            batch = self._get(f"{HELIUS_BASE}/v0/addresses/{address}/transactions", params)
            if not batch:
                break
            out.extend(batch)
            before = batch[-1].get("signature")
            if len(batch) < page_size or not before:
                break
        return out[:limit]

    def get_asset(self, mint: str) -> dict[str, Any] | None:
        """DAS getAsset — returns creators/authorities for a mint, or None."""
        try:
            return self._rpc("getAsset", {"id": mint})
        except HeliusError:
            return None
