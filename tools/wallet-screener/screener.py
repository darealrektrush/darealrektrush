#!/usr/bin/env python3
"""Solana copy-trade wallet screener.

Point it at a list of candidate wallet addresses (the ones you pulled off a
GMGN / Solana Tracker / Axiom leaderboard) and it screens each against five
process filters using on-chain data, so you keep the survivors instead of the
headline PnL ranks:

  1. Realized PnL only, transfer-filtered   (raw leaderboard PnL is inflated)
  2. Concentration                          (one bag > 40% of profit = luck)
  3. Consistency                            (30d win rate + trade count)
  4. Deployer / self-dealing                (buying your own mints = exit liq)
  5. Hold time                              (median < 30s = uncopyable fills)

This is a research / due-diligence tool. It reads chain data only: no keys,
no signing, no execution. A PASS is "worth paper-tracking", never "buy".

Usage:
    export HELIUS_API_KEY=...            # free key from https://dev.helius.xyz
    python screener.py WALLET [WALLET ...]
    python screener.py --file wallets.txt --json report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from analysis import WalletMetrics, analyze_wallet
from config import DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS, ScoreWeights, Thresholds
from helius_client import HeliusClient, HeliusError


def evaluate(m: WalletMetrics, t: Thresholds) -> tuple[str, list[str], list[str]]:
    """Return (verdict, failing_reasons, warning_reasons).

    verdict is FAIL if any hard filter fails, FLAG if only soft/unknown issues,
    else PASS.
    """
    fails: list[str] = []
    warns: list[str] = []

    # 1. realized PnL
    if m.realized_pnl_sol < t.min_realized_pnl_sol:
        fails.append(f"realized PnL {m.realized_pnl_sol:.2f} SOL below "
                     f"{t.min_realized_pnl_sol:.2f}")

    # 2. concentration
    if m.max_single_token_profit_share is None:
        warns.append("no positive realized profit to assess concentration")
    elif m.max_single_token_profit_share > t.max_single_token_profit_share:
        fails.append(f"one token = {m.max_single_token_profit_share:.0%} of profit "
                     f"(> {t.max_single_token_profit_share:.0%}): likely luck")

    # 3. consistency
    if m.window_trades < t.min_trades_in_window:
        warns.append(f"only {m.window_trades} closed trades in "
                     f"{t.consistency_window_days}d (< {t.min_trades_in_window}): thin sample")
    if m.window_win_rate is None:
        warns.append("no closed trades in window to compute win rate")
    elif m.window_win_rate < t.min_win_rate:
        fails.append(f"{t.consistency_window_days}d win rate {m.window_win_rate:.0%} "
                     f"(< {t.min_win_rate:.0%})")

    # 4. deployer / self-dealing
    if m.deployer_buy_share is None:
        warns.append("no buys sampled to assess deployer self-dealing")
    elif m.deployer_buy_share > t.max_deployer_buy_share:
        fails.append(f"{m.deployer_buy_share:.0%} of buys are self-created/linked "
                     f"mints (> {t.max_deployer_buy_share:.0%}): exit-liquidity pattern")

    # 5. hold time
    if m.median_hold_seconds is None:
        warns.append("no hold-time data")
    elif m.median_hold_seconds < t.min_median_hold_seconds:
        fails.append(f"median hold {m.median_hold_seconds:.0f}s "
                     f"(< {t.min_median_hold_seconds:.0f}s): fills not copyable")

    if m.untracked_sell_flag:
        warns.append("sells without matching buys in sample (PnL may be overstated)")

    verdict = "FAIL" if fails else ("FLAG" if warns else "PASS")
    return verdict, fails, warns


def composite_score(m: WalletMetrics, t: Thresholds, w: ScoreWeights) -> float:
    """Informational 0-100 ranking (not the gate). Higher = cleaner."""
    score = 0.0
    # realized pnl: positive gets full weight
    if m.realized_pnl_sol >= t.min_realized_pnl_sol:
        score += w.realized_pnl
    # concentration: linear credit for being under the cap
    if m.max_single_token_profit_share is not None:
        frac = max(0.0, 1 - m.max_single_token_profit_share / max(t.max_single_token_profit_share, 1e-9))
        score += w.concentration * min(frac, 1.0)
    # consistency: scale win rate over threshold, gated on trade count
    if m.window_win_rate is not None and m.window_trades >= t.min_trades_in_window:
        frac = (m.window_win_rate - t.min_win_rate) / max(1 - t.min_win_rate, 1e-9)
        score += w.consistency * max(0.0, min(frac, 1.0))
    # deployer: full credit at zero, zero credit at the cap
    if m.deployer_buy_share is not None:
        frac = 1 - m.deployer_buy_share / max(t.max_deployer_buy_share, 1e-9)
        score += w.deployer * max(0.0, min(frac, 1.0))
    # hold time: full credit at/above threshold
    if m.median_hold_seconds is not None:
        frac = m.median_hold_seconds / max(t.min_median_hold_seconds, 1e-9)
        score += w.hold_time * min(frac, 1.0)
    return round(score, 1)


def _fmt(value, spec: str, dash: str = "—") -> str:
    return format(value, spec) if value is not None else dash


def print_report(rows: list[dict]) -> None:
    order = {"PASS": 0, "FLAG": 1, "FAIL": 2}
    rows = sorted(rows, key=lambda r: (order.get(r["verdict"], 3), -r["score"]))
    header = (
        f"{'WALLET':<12} {'VERDICT':<7} {'SCORE':>5} {'PnL(SOL)':>9} "
        f"{'CONC':>5} {'WIN30d':>7} {'TRADES':>6} {'HOLD':>7} {'DEPLOY':>6}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        m = r["metrics"]
        short = f"{r['wallet'][:4]}..{r['wallet'][-4:]}"
        conc = _fmt(m["max_single_token_profit_share"], ".0%")
        win = _fmt(m["window_win_rate"], ".0%")
        hold = (f"{m['median_hold_seconds']:.0f}s"
                if m["median_hold_seconds"] is not None else "—")
        dep = _fmt(m["deployer_buy_share"], ".0%")
        print(f"{short:<12} {r['verdict']:<7} {r['score']:>5} "
              f"{m['realized_pnl_sol']:>9.2f} {conc:>5} {win:>7} "
              f"{m['window_trades']:>6} {hold:>7} {dep:>6}")
    print()
    for r in rows:
        if r["fails"] or r["warns"]:
            print(f"{r['wallet']}  [{r['verdict']}]  score={r['score']}")
            for f in r["fails"]:
                print(f"    ✗ {f}")
            for wn in r["warns"]:
                print(f"    · {wn}")
            print()


def load_wallets(args: argparse.Namespace) -> list[str]:
    wallets: list[str] = list(args.wallets)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    wallets.append(line)
    # de-dupe, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for w in wallets:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("wallets", nargs="*", help="wallet addresses to screen")
    p.add_argument("--file", "-f", help="file with one wallet per line (# comments ok)")
    p.add_argument("--api-key", help="Helius API key (else $HELIUS_API_KEY)")
    p.add_argument("--json", help="write full JSON report to this path")
    p.add_argument("--max-tx", type=int, default=DEFAULT_THRESHOLDS.max_transactions,
                   help="max transactions to sample per wallet")
    p.add_argument("--window-days", type=int,
                   default=DEFAULT_THRESHOLDS.consistency_window_days,
                   help="consistency window in days")
    args = p.parse_args(argv)

    wallets = load_wallets(args)
    if not wallets:
        p.error("no wallets given (pass addresses or --file)")

    thresholds = Thresholds(
        max_transactions=args.max_tx,
        consistency_window_days=args.window_days,
    )
    try:
        client = HeliusClient(api_key=args.api_key)
    except HeliusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rows: list[dict] = []
    for i, wallet in enumerate(wallets, 1):
        print(f"[{i}/{len(wallets)}] screening {wallet} ...", file=sys.stderr)
        try:
            m = analyze_wallet(client, wallet, thresholds)
        except HeliusError as exc:
            print(f"    error: {exc}", file=sys.stderr)
            continue
        verdict, fails, warns = evaluate(m, thresholds)
        rows.append({
            "wallet": wallet,
            "verdict": verdict,
            "score": composite_score(m, thresholds, DEFAULT_WEIGHTS),
            "fails": fails,
            "warns": warns,
            "metrics": asdict(m),
        })

    print(file=sys.stderr)
    if not rows:
        print("no wallets could be screened", file=sys.stderr)
        return 1
    print_report(rows)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2)
        print(f"full report written to {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
