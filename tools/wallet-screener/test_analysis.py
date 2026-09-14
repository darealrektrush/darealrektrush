"""Offline unit tests for swap reconstruction and metrics.

No network. Feeds synthetic Helius-shaped transactions through the same code
paths analyze_wallet uses, so the FIFO PnL, concentration, win rate, hold
time, deployer, and verdict logic are all exercised deterministically.

Run:  python -m unittest test_analysis    (or: python test_analysis.py)
"""

from __future__ import annotations

import time
import unittest

from analysis import (
    LAMPORTS,
    WSOL,
    WalletMetrics,
    _fifo_close,
    reconstruct_swaps,
)
from config import Thresholds
from screener import composite_score, evaluate
from config import DEFAULT_WEIGHTS

WALLET = "Wa11etAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TOK = "Toknaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TOK2 = "Tokn2bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def swap_tx(sig, ts, *, sol_in=0.0, sol_out=0.0, tok_in=None, tok_out=None,
            fee_payer=WALLET):
    """Build a minimal enhanced-tx SWAP for the wallet."""
    def tok_entry(mint, amount):
        return {"userAccount": WALLET, "mint": mint,
                "rawTokenAmount": {"tokenAmount": str(int(amount * 1e6)), "decimals": 6}}
    ev = {
        "nativeInput": {"account": WALLET, "amount": str(int(sol_in * LAMPORTS))},
        "nativeOutput": {"account": WALLET, "amount": str(int(sol_out * LAMPORTS))},
        "tokenInputs": [tok_entry(*tok_in)] if tok_in else [],
        "tokenOutputs": [tok_entry(*tok_out)] if tok_out else [],
    }
    return {"type": "SWAP", "feePayer": fee_payer, "timestamp": ts,
            "signature": sig, "events": {"swap": ev}}


class TestReconstruction(unittest.TestCase):
    def test_buy_and_sell(self):
        t0 = 1_700_000_000
        txns = [
            swap_tx("s1", t0, sol_in=2.0, tok_out=(TOK, 1000)),        # buy 1000 @ 2 SOL
            swap_tx("s2", t0 + 60, tok_in=(TOK, 1000), sol_out=3.0),   # sell 1000 -> 3 SOL
        ]
        swaps = reconstruct_swaps(txns, WALLET)
        self.assertEqual([s.side for s in swaps], ["buy", "sell"])
        self.assertAlmostEqual(swaps[0].sol_amount, 2.0)
        self.assertAlmostEqual(swaps[1].sol_amount, 3.0)

    def test_wsol_leg_counts_as_sol(self):
        t0 = 1_700_000_000
        txns = [swap_tx("s1", t0, tok_in=(WSOL, 2.0), tok_out=(TOK, 500))]
        swaps = reconstruct_swaps(txns, WALLET)
        self.assertEqual(len(swaps), 1)
        self.assertEqual(swaps[0].side, "buy")
        self.assertAlmostEqual(swaps[0].sol_amount, 2.0)

    def test_ignores_other_fee_payer(self):
        txns = [swap_tx("s1", 1, sol_in=1.0, tok_out=(TOK, 10), fee_payer="someoneelse")]
        self.assertEqual(reconstruct_swaps(txns, WALLET), [])


class TestFifoPnl(unittest.TestCase):
    def test_realized_pnl_and_hold(self):
        from analysis import Swap
        t0 = 1_700_000_000
        swaps = [
            Swap("b", t0, TOK, "buy", 1000, 2.0),
            Swap("s", t0 + 90, TOK, "sell", 1000, 3.0),
        ]
        closed, untracked = _fifo_close(swaps)
        self.assertFalse(untracked)
        self.assertEqual(len(closed), 1)
        self.assertAlmostEqual(closed[0].realized_sol, 1.0)     # 3 - 2
        self.assertAlmostEqual(closed[0].hold_seconds, 90)

    def test_partial_fifo(self):
        from analysis import Swap
        t0 = 1_700_000_000
        swaps = [
            Swap("b1", t0, TOK, "buy", 500, 1.0),      # unit cost 0.002
            Swap("b2", t0 + 10, TOK, "buy", 500, 2.0), # unit cost 0.004
            Swap("s1", t0 + 20, TOK, "sell", 500, 2.0),# sells first lot: cost 1.0 -> +1.0
        ]
        closed, _ = _fifo_close(swaps)
        self.assertAlmostEqual(closed[0].realized_sol, 1.0)

    def test_untracked_sell(self):
        from analysis import Swap
        swaps = [Swap("s", 1, TOK, "sell", 100, 5.0)]  # no prior buy
        closed, untracked = _fifo_close(swaps)
        self.assertTrue(untracked)
        self.assertAlmostEqual(closed[0].realized_sol, 5.0)  # zero cost basis


class TestVerdict(unittest.TestCase):
    def _clean_metrics(self) -> WalletMetrics:
        return WalletMetrics(
            wallet=WALLET, total_swaps=200, buys=100, sells=100,
            realized_pnl_sol=40.0,
            per_mint_pnl={TOK: 20.0, TOK2: 20.0},
            max_single_token_profit_share=0.5,  # overwritten per test
            window_trades=80, window_win_rate=0.7,
            median_hold_seconds=120,
            deployer_buys=0, unique_mints_bought=50, deployer_buy_share=0.0,
        )

    def test_pass(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.3
        verdict, fails, warns = evaluate(m, Thresholds())
        self.assertEqual(verdict, "PASS", (fails, warns))

    def test_concentration_fail(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.8
        verdict, fails, _ = evaluate(m, Thresholds())
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("luck" in f for f in fails))

    def test_deployer_fail(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.3
        m.deployer_buys, m.deployer_buy_share = 20, 0.4
        verdict, fails, _ = evaluate(m, Thresholds())
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("exit-liquidity" in f for f in fails))

    def test_hold_fail(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.3
        m.median_hold_seconds = 5
        verdict, fails, _ = evaluate(m, Thresholds())
        self.assertEqual(verdict, "FAIL")

    def test_thin_sample_flags(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.3
        m.window_trades = 10
        verdict, fails, warns = evaluate(m, Thresholds())
        self.assertEqual(verdict, "FLAG")
        self.assertFalse(fails)

    def test_score_range(self):
        m = self._clean_metrics()
        m.max_single_token_profit_share = 0.2
        s = composite_score(m, Thresholds(), DEFAULT_WEIGHTS)
        self.assertTrue(0 <= s <= 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
