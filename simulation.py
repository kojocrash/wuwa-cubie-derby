"""
Wuthering Waves Cubie Derby — race simulator (2026 edition).

Run directly to simulate the first-half race with default settings:
    python simulation.py

Pass -n <count> to change iteration count:
    python simulation.py -n 50000

To simulate with custom starting positions (second-half style), call
simulate() directly from another script:

    from simulation import simulate, print_results
    from cubes.chisa import Chisa
    from cubes.lynae import Lynae

    # First-half (all start at pad 1)
    r = simulate([Chisa, Lynae, ...])

    # Second-half (specific pad positions)
    r = simulate([(Chisa, 5), (Lynae, 10), ...])

    print_results(r)
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from config import PARTICIPANTS
from engine.game import Game


# ---------------------------------------------------------------------------
# Single-run helper
# ---------------------------------------------------------------------------

def _do_race(parsed: list[tuple[type, int | None]]) -> list[str]:
    """Run one race and return the ranking as a list of cube names (best → worst)."""
    participants = [(cls(), pad) for cls, pad in parsed]
    game = Game()
    game.setup(participants)
    return [c.name for c in game.run_game()]


# ---------------------------------------------------------------------------
# Batch simulation
# ---------------------------------------------------------------------------

def simulate(
    participants: list,
    n: int = 2_000,
) -> dict:
    """
    Run *n* races and aggregate results.

    *participants* is a list of cube classes or (cube class, pad) tuples:
      [Chisa, Mornye, ...]                           — first-half (all start at pad 1)
      [(Chisa, 5), (Mornye, 10), ...]                — second-half (specific pads)
      [(Chisa, 5), Mornye, ...]                      — mixed: None pad → pad 1

    Returns a dict with keys:
      'win_pct'    — {name: win_percentage}
      'avg_rank'   — {name: average_finish_rank}
      'n'          — number of simulations run
    """
    parsed = [(p, None) if not isinstance(p, tuple) else p for p in participants]
    names = [cls.CUBE_TYPE for cls, _ in parsed]

    win_counts: dict[str, int] = defaultdict(int)
    rank_totals: dict[str, int] = defaultdict(int)

    for _ in range(n):
        ranking = _do_race(parsed)
        win_counts[ranking[0]] += 1
        for rank_idx, name in enumerate(ranking, start=1):
            rank_totals[name] += rank_idx

    win_pct = {name: win_counts[name] / n * 100 for name in names}
    avg_rank = {name: rank_totals[name] / n for name in names}

    return {"win_pct": win_pct, "avg_rank": avg_rank, "n": n}


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_results(results: dict) -> None:
    n = results["n"]
    win_pct = results["win_pct"]
    avg_rank = results["avg_rank"]

    names_sorted = sorted(win_pct.keys(), key=lambda name: -win_pct[name])

    title = f"Cubie Derby Race Simulation  ({n:,} runs)"
    sep = "─" * 44

    print()
    print(title)
    print(sep)
    print(f"  {'Cube':<14}  {'Win %':>7}    {'Avg Rank':>8}")
    print(f"  {'─'*14}  {'─'*7}    {'─'*8}")
    for name in names_sorted:
        print(f"  {name:<14}  {win_pct[name]:>6.2f}%    {avg_rank[name]:>8.3f}")
    print(sep)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Cubie Derby race simulator")
    parser.add_argument("-n", "--runs", type=int, default=2_000,
                        help="number of simulations to run (default: 2,000)")
    args = parser.parse_args()

    print(f"Running {args.runs:,} simulations…", file=sys.stderr)
    results = simulate(PARTICIPANTS, n=args.runs)
    print_results(results)


if __name__ == "__main__":
    main()
