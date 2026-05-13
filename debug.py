"""
Single-game debug trace.

Edit PARTICIPANTS below, then run:
    python debug.py

Each entry is either a cube class (first-half, starts at pad 1) or a
(cube class, pad) tuple (second-half, specific starting pad; None = pad 0).
Mix and match — if any pad is given, all None entries default to pad 0.
"""

from cubes import Augusta, Iuno, Phrolova, Changli, Jinhsi, Calcharo
from engine.game import Game

# ── Edit this list to change who races and where they start ──────────────────
PARTICIPANTS = [
    Augusta,
    Iuno,
    Phrolova,
    Changli,
    Jinhsi,
    Calcharo,
]
# ─────────────────────────────────────────────────────────────────────────────

parsed = [(p, None) if not isinstance(p, tuple) else p for p in PARTICIPANTS]
participants = [(cls(), pad) for cls, pad in parsed]

game = Game(verbose=True)
game.setup(participants)
ranking = game.run_game()

print("\n" + "═" * 52)
print("  FINAL RANKING")
print("═" * 52)
for i, cube in enumerate(ranking, 1):
    print(f"  {i}. {cube.name}")
print()
