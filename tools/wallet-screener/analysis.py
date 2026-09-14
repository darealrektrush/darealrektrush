"""Swap reconstruction and the five screening metrics.

Everything here is derived from on-chain swaps, not from a leaderboard's
headline number. That is the whole point: a leaderboard's PnL is inflated by
self-transfers, unrealized bags, and single outliers. We rebuild realized,
transfer-filtered PnL from the swaps themselves and judge process, not luck.
"""

from __future__ import annotations

import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from config import Thresholds
from helius_client import HeliusClient

WSOL = "So11111111111111111111111111111111111111112"
LAMPORTS = 1_000_000_000
SECONDS_PER_DAY = 86_400


# --------------------------------------------------------------------------- #
# Swap reconstruction
# --------------------------------------------------------------------------- #
@dataclass
class Swap:
    signature: str
    timestamp: int
    mint: str
    side: str          # "buy" or "sell"
    token_amount: float
    sol_amount: float  # SOL spent (buy) or received (sell), always positive


def _raw_amount(entry: dict[str, Any]) -> float:
    raw = entry.get("rawTokenAmount")
    if raw and raw.get("tokenAmount") is not None:
        try:
            return int(raw["tokenAmount"]) / (10 ** int(raw.get("decimals", 0)))
        except (ValueError, TypeError):
            return 0.0
    return float(entry.get("tokenAmount") or 0.0)


def reconstruct_swaps(txns: list[dict[str, Any]], wallet: str) -> list[Swap]:
    """Turn Helius enhanced transactions into SOL-quoted buys/sells for `wallet`.

    Only transactions the wallet paid for (feePayer == wallet) are attributed,
    so passthrough / MEV-adjacent inclusions don't get counted as its trades.
    Pure token->token swaps (no SOL leg) are skipped.
    """
    swaps: list[Swap] = []
    for tx in txns:
        if tx.get("type") != "SWAP" or tx.get("feePayer") != wallet:
            continue
        ev = (tx.get("events") or {}).get("swap")
        if not ev:
            continue
        ts = int(tx.get("timestamp") or 0)
        sig = tx.get("signature", "")

        spent_sol = int((ev.get("nativeInput") or {}).get("amount") or 0) / LAMPORTS
        recv_sol = int((ev.get("nativeOutput") or {}).get("amount") or 0) / LAMPORTS

        # per-mint signed token movement for the wallet (received - sent)
        token_delta: dict[str, float] = defaultdict(float)
        for entry in ev.get("tokenInputs") or []:
            if entry.get("userAccount") not in (wallet, None):
                continue
            mint = entry.get("mint")
            amt = _raw_amount(entry)
            if mint == WSOL:
                spent_sol += amt
            elif mint:
                token_delta[mint] -= amt
        for entry in ev.get("tokenOutputs") or []:
            if entry.get("userAccount") not in (wallet, None):
                continue
            mint = entry.get("mint")
            amt = _raw_amount(entry)
            if mint == WSOL:
                recv_sol += amt
            elif mint:
                token_delta[mint] += amt

        if not token_delta:
            continue
        # primary traded token = largest absolute movement
        mint = max(token_delta, key=lambda m: abs(token_delta[m]))
        delta = token_delta[mint]
        if delta > 0 and spent_sol > recv_sol:
            swaps.append(Swap(sig, ts, mint, "buy", delta, spent_sol - recv_sol))
        elif delta < 0 and recv_sol > spent_sol:
            swaps.append(Swap(sig, ts, mint, "sell", -delta, recv_sol - spent_sol))
    swaps.sort(key=lambda s: s.timestamp)
    return swaps


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
@dataclass
class ClosedTrade:
    mint: str
    sell_ts: int
    realized_sol: float
    hold_seconds: float


@dataclass
class WalletMetrics:
    wallet: str
    total_swaps: int = 0
    buys: int = 0
    sells: int = 0

    realized_pnl_sol: float = 0.0            # full sample, FIFO, transfer-filtered
    per_mint_pnl: dict[str, float] = field(default_factory=dict)
    max_single_token_profit_share: float | None = None

    window_trades: int = 0
    window_win_rate: float | None = None

    median_hold_seconds: float | None = None

    deployer_buys: int = 0
    unique_mints_bought: int = 0
    deployer_buy_share: float | None = None
    deployer_mints: list[str] = field(default_factory=list)

    linked_addresses: list[str] = field(default_factory=list)
    untracked_sell_flag: bool = False        # sells with no matching buy in sample
    notes: list[str] = field(default_factory=list)


def _fifo_close(swaps: list[Swap]) -> tuple[list[ClosedTrade], bool]:
    """FIFO-match sells against prior buys per mint -> realized closed trades."""
    lots: dict[str, deque[list[float]]] = defaultdict(deque)  # [amount, sol_cost, ts]
    closed: list[ClosedTrade] = []
    untracked = False
    for s in swaps:
        if s.side == "buy":
            lots[s.mint].append([s.token_amount, s.sol_amount, s.timestamp])
            continue
        # sell
        remaining = s.token_amount
        unit_proceeds = s.sol_amount / s.token_amount if s.token_amount else 0.0
        cost_basis = 0.0
        weighted_hold = 0.0
        matched = 0.0
        book = lots[s.mint]
        while remaining > 1e-12 and book:
            lot = book[0]
            take = min(remaining, lot[0])
            unit_cost = lot[1] / lot[0] if lot[0] else 0.0
            cost_basis += take * unit_cost
            weighted_hold += take * max(0, s.timestamp - lot[2])
            matched += take
            lot[0] -= take
            lot[1] -= take * unit_cost
            remaining -= take
            if lot[0] <= 1e-12:
                book.popleft()
        if remaining > 1e-12:
            untracked = True  # sold more than we saw bought (history predates sample)
        proceeds = unit_proceeds * s.token_amount
        realized = proceeds - cost_basis
        hold = (weighted_hold / matched) if matched > 1e-12 else 0.0
        closed.append(ClosedTrade(s.mint, s.timestamp, realized, hold))
    return closed, untracked


def analyze_wallet(
    client: HeliusClient, wallet: str, thresholds: Thresholds
) -> WalletMetrics:
    txns = client.address_transactions(wallet, limit=thresholds.max_transactions)
    m = WalletMetrics(wallet=wallet)

    # linked addresses via native SOL funding relationships
    flow: dict[str, float] = defaultdict(float)
    for tx in txns:
        for nt in tx.get("nativeTransfers") or []:
            amt = int(nt.get("amount") or 0) / LAMPORTS
            if nt.get("fromUserAccount") == wallet and nt.get("toUserAccount"):
                flow[nt["toUserAccount"]] += amt
            elif nt.get("toUserAccount") == wallet and nt.get("fromUserAccount"):
                flow[nt["fromUserAccount"]] += amt
    m.linked_addresses = sorted(
        a for a, f in flow.items() if f >= thresholds.linked_min_sol_flow
    )
    linked_set = set(m.linked_addresses) | {wallet}

    swaps = reconstruct_swaps(txns, wallet)
    m.total_swaps = len(swaps)
    m.buys = sum(1 for s in swaps if s.side == "buy")
    m.sells = sum(1 for s in swaps if s.side == "sell")
    if not swaps:
        m.notes.append("no SOL-quoted swaps found in sample")
        return m

    # --- Filter 1: realized, transfer-filtered PnL (FIFO, full sample) ------
    closed, untracked = _fifo_close(swaps)
    m.untracked_sell_flag = untracked
    if untracked:
        m.notes.append("some sells had no matching buy in sample; PnL may be overstated")
    m.realized_pnl_sol = sum(c.realized_sol for c in closed)

    # --- Filter 2: concentration ------------------------------------------
    per_mint: dict[str, float] = defaultdict(float)
    for c in closed:
        per_mint[c.mint] += c.realized_sol
    m.per_mint_pnl = dict(per_mint)
    positive_total = sum(v for v in per_mint.values() if v > 0)
    if positive_total > 0:
        m.max_single_token_profit_share = max(
            (v for v in per_mint.values() if v > 0), default=0.0
        ) / positive_total

    # --- Filter 5: hold time (full sample) ---------------------------------
    holds = [c.hold_seconds for c in closed if c.hold_seconds > 0]
    if holds:
        m.median_hold_seconds = statistics.median(holds)

    # --- Filter 3: consistency (rolling window) ----------------------------
    cutoff = time.time() - thresholds.consistency_window_days * SECONDS_PER_DAY
    window = [c for c in closed if c.sell_ts >= cutoff]
    m.window_trades = len(window)
    if window:
        wins = sum(1 for c in window if c.realized_sol > 0)
        m.window_win_rate = wins / len(window)

    # --- Filter 4: deployer / self-dealing ---------------------------------
    bought_mints = sorted({s.mint for s in swaps if s.side == "buy"})
    m.unique_mints_bought = len(bought_mints)
    for mint in bought_mints:
        asset = client.get_asset(mint)
        if not asset:
            continue
        related = set()
        for cr in asset.get("creators") or []:
            if cr.get("address"):
                related.add(cr["address"])
        auth = asset.get("authorities") or []
        for a in auth:
            if a.get("address"):
                related.add(a["address"])
        if related & linked_set:
            m.deployer_buys += 1
            m.deployer_mints.append(mint)
    if m.unique_mints_bought:
        m.deployer_buy_share = m.deployer_buys / m.unique_mints_bought

    return m
