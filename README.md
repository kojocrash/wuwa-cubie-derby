# Wuthering Waves — Cubie Derby Simulator

A Python simulator for the Cubie Derby mini-game from Wuthering Waves (2026 edition).
Models the full race engine including cube skills, stacking mechanics, pad effects, and
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

## Track layout

The track is a loop of 32 pads numbered 0–31. Pad 0 is the finish line — the first cube
to reach it wins. Starting positions vary by race format, and the game handles any edge
cases around the finish line correctly regardless of where cubes begin. Cubes travel forward
(1 → 2 → … → 31 → 0); Abbowser, the chaos wildcard, moves in reverse.

Special pads along the way:

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

## Configuration

Edit **`config.py`** to change who races and where they start.
Both `debug.py` and `simulation.py` read from this file.

```python
PARTICIPANTS: list = [
    (Iuno,      -3),   # 3 pads before the finish line
    (Calcharo,  -2),   # 2 pads before the finish line
    (Jinhsi,    -2),   # 2 pads before the finish line
    (Augusta,   -1),   # 1 pad before the finish line
    (Changli,   -1),   # 1 pad before the finish line
    Phrolova,          # no starting pad — defaults to pad 0
]
```

Each participant is either just a cube class, or a `(cube class, starting pad)` pair.
If none of them have a starting pad explicitly defined, the program treats this as a
first-half race and places everyone at pad 1. Otherwise starting pads are used as given —
negative values wrap naturally around the track (e.g. `-1` is the pad just before the
finish line, `-2` is two pads before it, and so on). Leaving out a starting pad defaults
to pad 0, except in a first-half race where everyone starts at pad 1 instead.

When multiple cubes share a starting pad, list order determines the stack —
first listed ends up at the bottom, last listed at the top.

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

## Cube skills

Each cube's skill is modeled closely to its in-game behavior. The skill descriptions
pulled directly from the game in all supported languages are available at
[kojocrash/wuwa-cubie-info](https://github.com/kojocrash/wuwa-cubie-info/blob/main/output/3.3/skill_desc.json).

---

## Adding a new cube

1. Create `cubes/<name>.py` with a class that extends `CubeBase`.
2. Set `CUBE_TYPE: ClassVar[str] = "<Name>"`.
3. Override `_setup_effects` and register one or more `Effect` subclasses via `self._register(...)`.
4. Add an export line to `cubes/__init__.py`.
5. Add the cube to `PARTICIPANTS` in `config.py`.

---

## Effect system

Every cube skill is an `Effect` subclass. An effect declares which **phase** it listens to,
and the engine calls it automatically at the right moment each turn or round.

### Phases

Phases fire in this order within a turn (round-level phases are noted separately):

| Phase | When |
|---|---|
| `TURN_ORDER` | Once per round, before anyone moves — effects can reorder the turn list |
| `ROLL_POST` | After a cube rolls its dice — effects can modify the roll value |
| `PRE_MOVE` | Before a cube's movement begins — effects can change the number of pads to move |
| `MOVE_PRE` | Before each individual pad step — effects can cancel or redirect a step |
| `MOVE_POST` | After each individual pad step — effects can adjust remaining pads or react to position |
| `FINISH_CHECK` | When a cube crosses pad 0 going forward — effects can suppress the finish |
| `PAD_EFFECT` | When a cube lands on a special pad — effects can modify the push distance or stack order before it executes |
| `TURN_END` | After a cube's full turn including any pad effects |
| `ROUND_END` | After every cube in the round has taken their turn |

### Contexts

Each phase passes a context object to `can_trigger` and `apply`. The context carries
everything the effect needs to read or modify. Mutable fields are what effects are expected
to write to — everything else is read-only.

| Context | Key fields | Mutable |
|---|---|---|
| `TurnOrderContext` | `turn_order` | `turn_order` |
| `RollContext` | `roll` | `roll` |
| `PreMoveContext` | `roll`, `move_count` | `move_count` |
| `MovePreContext` | `pads_remaining`, `stride` | `pads_remaining`, `stride`, `cancelled` |
| `MovePostContext` | `pads_remaining`, `stride`, `is_pad_push` | `pads_remaining` |
| `FinishCheckContext` | `stride` | `finish_suppressed` |
| `PadEffectContext` | `pad_type`, `push_pads`, `new_order` | `push_pads`, `new_order` |
| `TurnEndContext` | `active_cube`, `game` | — |
| `RoundEndContext` | `game` | — |

All contexts also carry `game` (the `Game` instance) and `active_cube` (the cube whose turn
it is, or `None` for round-level phases).

### Writing an effect

```python
from engine.effect_system import Effect, Phase, PreMoveContext

class _MyEffect(Effect):
    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE)   # or any other phase

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return ctx.active_cube is self.owner      # only fire on this cube's own turn

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.move_count += 2                       # write to the mutable field
```

### Priority

The third argument to `super().__init__` is an optional `priority` (default `0`). Higher
values fire first within the same phase. Use this when two effects at the same phase have
an ordering dependency — for example, an effect that needs to read a clean stack before
another effect shuffles it.

---

## Tag system

Tags are lightweight string labels attached to individual cubes. They are the standard way
to implement once-per-match guards, multi-round state, and any other per-cube flags.

```python
cube.add_tag("my_effect.fired")                      # attach a tag (optionally with a context dict)
cube.has_tag("my_effect.fired", exact=True)          # check for it
cube.remove_tags("my_effect.fired", exact=True)      # clear it
```

The `exact` parameter controls name matching. Without it, `has_tag("foo")` also matches tags
named `"foo.bar"`, `"foo.baz"`, etc., which is useful for grouping related tags under a
common prefix.

Tags can also carry a `context` dict of arbitrary data if the effect needs to store more
than a boolean — retrieve them with `cube.get_tags(...)` to access that payload.
