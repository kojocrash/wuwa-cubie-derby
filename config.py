"""
Race configuration — edit here to change who races and where they start.

Each entry is either a cube class (first-half, all start at pad 1) or a
(cube class, pad) tuple (second-half).  Negative pad values wrap correctly:
  -1 → pad 31 (one pad before the finish)
  -2 → pad 30
  -3 → pad 29
   0 → pad 0  (finish/start line; shares a stack with Abbowser)

Mix of tuple and bare-class entries is allowed; if ANY pad is specified the
whole race runs in second-half mode and bare classes default to pad 0.
"""

from cubes import *

PARTICIPANTS: list = [
    (Iuno,      -3),
    (Calcharo,  -2),
    (Jinhsi,    -2),
    (Augusta,   -1),
    (Changli,   -1),
    Phrolova,          # no starting pad — defaults to pad 0
]
