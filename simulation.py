"""
Wuthering Waves Cubie Derby — race simulator (2026 edition).

Run directly to simulate the first-half race with default settings:
    python simulation.py

Pass -n <count> to change iteration count:
    python simulation.py -n 50000

To simulate with custom starting positions (second-half style), call
simulate() directly from another script and pass positions/stacks.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from cubes.abbowser import AbbowserCube
from cubes.aemeath import Aemeath
from cubes.carlotta import Carlotta
from cubes.chisa import Chisa
from cubes.lynae import Lynae
from cubes.mornye import Mornye
from cubes.shorekeeper import Shorekeeper
from engine.game_engine import GameEngine


# ---------------------------------------------------------------------------
# Cube factory
# ---------------------------------------------------------------------------

_CUBE_CLASSES = {
    "Chisa": Chisa,
    "Mornye": Mornye,
    "Lynae": Lynae,
    "Aemeath": Aemeath,
    "Shorekeeper": Shorekeeper,
    "Carlotta": Carlotta,
}

_REGULAR_NAMES = list(_CUBE_CLASSES)


def _make_cubes() -> tuple[list, AbbowserCube]:
    """Instantiate one fresh set of cubes for a single simulation run."""
    regular = [cls(name) for name, cls in _CUBE_CLASSES.items()]
    ab = AbbowserCube("Abbowser")
    return regular, ab


# ---------------------------------------------------------------------------
# Single-run helper
# ---------------------------------------------------------------------------

def _run_once(
    positions: dict[str, int] | None = None,
    stacks: list[list[str]] | None = None,
) -> list[str]:
    """
    Run one race and return the ranking as a list of cube names (best → worst).
    If *positions* is None, a first-half race is used (all start at pad 1).
    """
    regular, ab = _make_cubes()
    engine = GameEngine()

    if positions is None:
        engine.setup_first_half(regular, abbowser=ab)
    else:
        engine.setup_custom(regular, positions, stacks=stacks, abbowser=ab)

    ranking = engine.run_game()
    return [c.name for c in ranking]


# ---------------------------------------------------------------------------
# Batch simulation
# ---------------------------------------------------------------------------

def simulate(
    n: int = 10_000,
    positions: dict[str, int] | None = None,
    stacks: list[list[str]] | None = None,
) -> dict:
    """
    Run *n* races and aggregate results.

    Returns a dict with keys:
      'win_pct'    — {name: win_percentage}
      'avg_rank'   — {name: average_finish_rank}
      'n'          — number of simulations run
    """
    win_counts: dict[str, int] = defaultdict(int)
    rank_totals: dict[str, int] = defaultdict(int)

    for _ in range(n):
        ranking = _run_once(positions, stacks)
        win_counts[ranking[0]] += 1
        for rank_idx, name in enumerate(ranking, start=1):
            rank_totals[name] += rank_idx

    win_pct = {name: win_counts[name] / n * 100 for name in _REGULAR_NAMES}
    avg_rank = {name: rank_totals[name] / n for name in _REGULAR_NAMES}

    return {"win_pct": win_pct, "avg_rank": avg_rank, "n": n}


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_results(results: dict) -> None:
    n = results["n"]
    win_pct = results["win_pct"]
    avg_rank = results["avg_rank"]

    # Sort by win percentage descending
    names_sorted = sorted(_REGULAR_NAMES, key=lambda name: -win_pct[name])

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
    parser.add_argument("-n", "--runs", type=int, default=10_000,
                        help="number of simulations to run (default: 10,000)")
    args = parser.parse_args()

    print(f"Running {args.runs:,} simulations…", file=sys.stderr)
    results = simulate(n=args.runs)
    print_results(results)


if __name__ == "__main__":
    main()
