# Wuthering Waves — Cubie Derby Simulator

A Python simulator for the Cubie Derby mini-game from Wuthering Waves (2026 edition).
Models the full race engine including cube abilities, stacking mechanics, pad effects, and
Abbowser's chaos.

---

## Requirements

- Python 3.11+
- No third-party packages — standard library only

---

## Quick start

```bash
# Single verbose race (reads config.py for participants)
python debug.py

# Batch simulation — 2,000 races by default
python simulation.py

# Change iteration count
python simulation.py -n 10000
```

---

## Configuration

Edit **`config.py`** to change who races and where they start.
Both `debug.py` and `simulation.py` read from this file.

```python
PARTICIPANTS: list = [
    (Iuno,     -3),   # pad 29 — 3 pads before the finish
    (Calcharo, -2),   # pad 30
    (Jinhsi,   -2),   # pad 30
    (Augusta,  -1),   # pad 31 — 1 pad before the finish
    (Changli,  -1),   # pad 31
    (Phrolova,  0),   # pad 0  — at the finish/start line
]
```

Each entry is either a **bare cube class** (first-half mode, all start at pad 1) or a
**(cube class, pad)** tuple (second-half mode).

### First-half vs second-half

| Mode | How to specify | `laps_needed` |
|---|---|---|
| First-half | All bare classes: `[Iuno, Changli, ...]` | 1 for everyone |
| Second-half | At least one tuple: `[(Iuno, -3), ...]` | 1 if starting at pad 0, 2 if starting behind (past the first quarter of the track) |

**Negative pad values** wrap correctly around the 32-pad track:
`-1` → pad 31, `-2` → pad 30, `-3` → pad 29, etc.

When multiple cubes share a starting pad, **stacking order follows list order**
(first listed = bottom of stack, last listed = top).

---

## Track layout

The track has **32 pads** numbered 0–31. Normal cubes travel **forward** (1 → 2 → … → 31 → 0).
Pad 0 is the finish line. Abbowser travels **backward** (0 → 31 → 30 → …).

| Pad | Type |
|---|---|
| 3 | Thruster — pushes 1 pad forward |
| 6 | Spatial Rift — randomises stack order |
| 10 | Blocker — pushes 1 pad backward |
| 11 | Thruster |
| 16 | Thruster |
| 20 | Spatial Rift |
| 23 | Thruster |
| 28 | Blocker |

---

## Cube abilities

### Playable cubes

| Cube | Trigger | Effect |
|---|---|---|
| **Augusta** | PRE_MOVE — when at the top of a stack (cube below, none above) | Skips turn; goes last the following round |
| **Calcharo** | PRE_MOVE — when in last place | +3 moves this turn |
| **Changli** | ROUND_END — when at least one cube is stacked below her | 65% chance to go last next round |
| **Iuno** | PRE_MOVE — first time past the midpoint (pad 16), neither first nor last in rankings | Pulls all non-Abbowser cubes to her pad and restacks by ranking (worst → bottom, best → top). Held until the ranking condition is met. Once per match. |
| **Jinhsi** | TURN_END — *another* cube ends its turn on Jinhsi's pad while cubes are above her | 40% chance to float to the top of the stack |
| **Phrolova** | PRE_MOVE — when at the bottom of a stack with at least one cube above | +3 moves this turn |
| **Aemeath** | TURN_END (own turn) — first time past the midpoint | Teleports to the top of the closest stack strictly ahead by adjusted position. Held until someone is ahead. Once per match. |

### Abbowser (automatic)

Abbowser is placed automatically at pad 0. He is not in `PARTICIPANTS`.

| Behaviour | Details |
|---|---|
| Sits out | Does not take a turn in rounds 1 or 2 |
| Moves backward | Rolls 1–6 each turn, moves toward lower pad numbers |
| Sinks to bottom | After every step, teleports to the bottom of whatever stack he joined |
| Backward finish cross | If he steps backward onto pad 0 while carrying cubes, those cubes have `laps_needed += 1` |
| Separation teleport | At round end, if all non-Abbowser cubes are past him and he is alone, teleports back to pad 0 |

---

## Stacking rules

- A moving cube carries **all cubes above it** as a unit.
- When a unit lands on an occupied pad, it is placed **on top** of the existing stack.
- Abbowser always sinks to the **bottom** of any stack he is in.
- Spatial Rift pads **shuffle the entire stack** on landing.

---

## Project structure

```
config.py          Race participants — edit this to change the setup
debug.py           Runs one race with full verbose output
simulation.py      Batch simulation with win % and average rank

cubes/
  __init__.py      Re-exports all cube classes
  abbowser.py      Abbowser's automatic behaviours
  augusta.py       Augusta
  calcharo.py      Calcharo
  changli.py       Changli
  iuno.py          Iuno
  jinhsi.py        Jinhsi
  phrolova.py      Phrolova
  aemeath.py       Aemeath
  *.py             Other cubes (not yet in rotation)

engine/
  game.py          Core race loop, movement, stacking, finish logic
  cube_base.py     Base class for all cubes
  effect_system.py Effect phases, contexts, and priority queue
  tag_system.py    Per-cube tag storage (used for once-per-match guards)
  track.py         Track size, pad types, pad layout
```

---

## Adding a new cube

1. Create `cubes/<name>.py` with a class that extends `CubeBase`.
2. Set `CUBE_TYPE: ClassVar[str] = "<Name>"`.
3. Override `_setup_effects` and register one or more `Effect` subclasses.
4. Add an export line to `cubes/__init__.py`.
5. Add the cube to `PARTICIPANTS` in `config.py`.

Each `Effect` subclass picks a `Phase` (e.g. `Phase.PRE_MOVE`, `Phase.TURN_END`,
`Phase.ROUND_END`) and implements `can_trigger(ctx)` + `apply(ctx)`.
