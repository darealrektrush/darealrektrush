# Solana copy-trade wallet screener

A due-diligence pass for the wallets you pull off a Solana leaderboard
(GMGN, Solana Tracker, Photon, Axiom, KOLScan). Leaderboards rank on headline
PnL, which is the worst thing to copy: it's inflated by self-transfers,
unrealized bags, and single lucky trades, and a wallet that topped the board
months ago is usually one whose run already ended.

This tool takes candidate addresses and screens each against **process**, not
rank, using on-chain data. It reads chain data only — **no private keys, no
signing, no execution.** A `PASS` means "worth paper-tracking for two weeks",
never "buy".

## The five filters

| # | Filter | What it catches | Default gate |
|---|--------|-----------------|--------------|
| 1 | **Realized PnL, transfer-filtered** | Inflated leaderboard PnL. We rebuild realized PnL from swaps (SOL in vs SOL out, FIFO), so transfers between a wallet's own addresses and unrealized bags never count. | net realized ≥ 0 SOL |
| 2 | **Concentration** | One lucky bag masquerading as edge. | no single token > 40% of total positive profit |
| 3 | **Consistency** | Lifetime numbers hiding a cold streak. | 30-day win rate ≥ 60% over ≥ 60 closed trades |
| 4 | **Deployer / self-dealing** | You being the exit liquidity. Flags buys in tokens created by the wallet or a funding-linked address. | ≤ 10% of buys in self/linked mints |
| 5 | **Hold time** | Fills you physically can't match when copying. | median hold ≥ 30s |

A wallet gets **FAIL** if any hard gate fails, **FLAG** if only soft/unknown
issues remain (thin sample, missing data), else **PASS**. A composite 0–100
score is reported for ranking within a verdict — it's a convenience, not the gate.

## Setup

```bash
cd tools/wallet-screener
pip install -r requirements.txt
export HELIUS_API_KEY=...        # free key from https://dev.helius.xyz
```

## Usage

```bash
# a few wallets inline
python screener.py 5xoT... 9aBc...

# a candidate list from a file (one address per line, # comments ok)
python screener.py --file wallets.txt --json report.json

# widen the sample / change the window
python screener.py --file wallets.txt --max-tx 5000 --window-days 30
```

Progress goes to stderr; the table and per-wallet reasons go to stdout;
`--json` writes the full metrics (per-mint PnL, linked addresses, deployer
mints) for further analysis.

Example output:

```
WALLET       VERDICT SCORE  PnL(SOL)  CONC  WIN30d TRADES    HOLD DEPLOY
5xoT..a9Kd   PASS    88.0     142.30   28%     67%     93    142s     0%
9aBc..7Qm2   FLAG    61.0      44.10   35%     62%     41     88s     4%
Dz11..k8Ra   FAIL    22.0     310.50   71%     58%    120     11s    22%
```

## How it works

1. Pages the Helius Enhanced Transactions API for each wallet (newest first,
   up to `--max-tx`).
2. Reconstructs SOL-quoted buys/sells from parsed `SWAP` events, attributing
   only transactions the wallet paid for (`feePayer == wallet`). WSOL legs are
   treated as SOL; pure token→token swaps are skipped.
3. FIFO-matches sells against prior buys to get realized PnL, per-token PnL,
   and per-sell hold time.
4. Derives funding-linked addresses from native SOL transfer relationships,
   then checks each bought mint's creators/authorities (Helius DAS `getAsset`)
   against the wallet + linked set for the deployer filter.
5. Applies the thresholds in `config.py` and prints verdicts.

## Tuning

All goalposts live in `config.py` (`Thresholds`, `ScoreWeights`). Edit those
rather than the analysis code.

## Limits (read before trusting a number)

- **Sample depth.** Metrics only see the last `--max-tx` transactions. Very
  high-frequency wallets may need a larger window to get a fair 30-day count.
- **Untracked sells.** If a wallet sold a token it bought before the sampled
  window, that sell has no cost basis in-sample and its PnL is overstated. The
  tool sets an `untracked` warning when this happens — raise `--max-tx`.
- **Not financial advice.** This narrows a candidate list; it does not tell you
  to copy anyone. Paper-track survivors before any real capital moves.

## Tests

Fully offline (synthetic Helius-shaped fixtures, no network):

```bash
python -m unittest test_analysis -v
```
