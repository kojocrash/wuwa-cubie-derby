"""
Single-game debug trace.

Edit config.py to change who races and where they start, then run:
    python debug.py
"""

from config import PARTICIPANTS
from engine.game import Game

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
