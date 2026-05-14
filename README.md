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

## Track layout

The track is a loop of 32 pads numbered 0–31. Pad 0 doubles as both the start and the
finish — normal cubes begin just past it at pad 1, race forward through 2, 3, … 31, and win
by crossing pad 0 again. Abbowser starts at pad 0 and travels the loop in reverse
(0 → 31 → 30 → …).

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
    Phrolova,          # no starting pad specified
]
```

Each participant is either just a cube class, or a `(cube class, starting pad)` pair.
If **none** of the participants have a starting pad, the program treats this as a first-half
race and places everyone at pad 1. Otherwise starting pads are used as given — negative
values wrap naturally around the track (e.g. `-1` is the pad just before the finish line,
`-2` is two pads before it, and so on). A participant without a pad in a mixed list defaults
to pad 0.

When multiple cubes share a starting pad, list order determines the stack —
first listed ends up at the bottom, last listed at the top.

---

## Cube abilities

Skill descriptions for every cube are available in all supported languages in
[kojocrash/wuwa-cubie-info](https://github.com/kojocrash/wuwa-cubie-info/blob/main/output/3.3/skill_desc.json).

---

## Abbowser

Abbowser is placed automatically at pad 0 at the start of every race — he is not listed in
`PARTICIPANTS`. He plays differently from every other cube:

- **Sits out the first two rounds** before joining the race.
- **Travels backward** around the track, rolling 1–6 each turn like everyone else.
- **Always at the bottom.** Whenever he moves onto a pad with other cubes, he sinks to the
  bottom of that stack. Cubes he picks up along the way travel with him until they take
  their own turn and walk off.
- **Sets cubes back.** If he drags cubes backward past the finish line (pad 0), each of
  those cubes owes an extra lap.
- **Warps home.** At the end of any round where he is alone and every other cube has already
  passed his position going forward, he teleports back to pad 0.

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
3. Override `_setup_effects` and register one or more `Effect` subclasses via `self._register(...)`.
4. Add an export line to `cubes/__init__.py`.
5. Add the cube to `PARTICIPANTS` in `config.py`.

---

## Effect system

Every cube ability is an `Effect` subclass. An effect declares which **phase** it listens to,
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

The third argument to `super().__init__` is an optional `priority` (default `0`). Lower
values fire first within the same phase. Use negative numbers to guarantee firing before
other effects at the same phase, or higher numbers to fire after them.

---

## Tag system

Tags are lightweight string labels attached to individual cubes. They are the standard way
to implement once-per-match guards, multi-round state, and any other per-cube flags.

```python
cube.add_tag("my_effect.fired")          # attach a tag (optionally with a context dict)
cube.has_tag("my_effect.fired", exact=True)  # check for it
cube.remove_tags("my_effect.fired", exact=True)  # clear it
```

The `exact` parameter controls name matching. Without it, `has_tag("foo")` also matches tags
named `"foo.bar"`, `"foo.baz"`, etc., which is useful for grouping related tags under a
common prefix.

Tags can also carry a `context` dict of arbitrary data if the effect needs to store more
than a boolean — retrieve them with `cube.get_tags(...)` to access that payload.
