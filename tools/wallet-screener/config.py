"""Screening thresholds and tunables.

Every number here maps to one of the five filters described in the README.
Edit these instead of the analysis code when you want to move a goalpost.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Thresholds:
    # --- Filter 3: consistency ---------------------------------------------
    # 30-day window, judged on realized round-trips only.
    consistency_window_days: int = 30
    min_trades_in_window: int = 60          # fewer than this = not enough sample
    min_win_rate: float = 0.60              # 60% winning closed trades

    # --- Filter 2: concentration -------------------------------------------
    # If a single token accounts for more than this share of total positive
    # realized profit, the "edge" is one lucky bag, not a repeatable process.
    max_single_token_profit_share: float = 0.40

    # --- Filter 5: hold time -----------------------------------------------
    # Median hold below this and you physically cannot match their fills when
    # copying, so their P&L is not reproducible for you.
    min_median_hold_seconds: float = 30.0

    # --- Filter 1: realized PnL --------------------------------------------
    # A wallet must actually be net-positive on transfer-filtered realized PnL.
    min_realized_pnl_sol: float = 0.0

    # --- Filter 4: deployer / self-dealing ---------------------------------
    # Share of buys (by count) that are in tokens created by the wallet or a
    # funding-linked address. Above this and you are the exit liquidity.
    max_deployer_buy_share: float = 0.10

    # --- Linked-address detection -----------------------------------------
    # A counterparty is treated as "linked" if it sent/received at least this
    # much native SOL to/from the wallet across the sampled history.
    linked_min_sol_flow: float = 1.0

    # --- Sampling limits ---------------------------------------------------
    max_transactions: int = 3000            # how deep to page per wallet


@dataclass
class ScoreWeights:
    """Weights used only for the informational 0-100 composite score.

    The PASS / FLAG / FAIL verdict is driven by the hard thresholds above;
    this composite is a convenience ranking, not the gate.
    """

    realized_pnl: float = 20.0
    concentration: float = 20.0
    consistency: float = 25.0
    deployer: float = 25.0
    hold_time: float = 10.0


DEFAULT_THRESHOLDS = Thresholds()
DEFAULT_WEIGHTS = ScoreWeights()
