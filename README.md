# ep-physics-base: The shared foundation of the domain libraries: units, events, configuration, statistics, and one figure standard

Units, the `(result, events)` event helper, configuration with packaged defaults, the bootstrap and decision statistics, the tag vocabulary, name keys, and the shared figure layer (the EDS light theme, the figure legibility rules, axis tags, the hydrocarbon colour standard).

**Status: public (2026-11-11).** The library follows the rules of a public one (no host-repository imports, no data, no private paths, an automated publication gate in `scripts/publication_gate.py`); the gate runs in CI and must stay at zero blockers. Licence: MIT with acknowledgement (`LICENSE`).

## Install

```
uv add git+https://github.com/AdmcCarthy/ep-physics-base
```

Depends on: none. Optional extras:

* `figures`: matplotlib, cycler

## What is in it

| Module | What it does |
| :--- | :--- |
| `units` | Pressure, specific gravity (equivalent density), overpressure and the depth datum: one place for the conversions.  Pure functions. |
| `events` | Audit-log and data-quality (DQ) helpers. |
| `config` | Configuration for the domain libraries: a project file wins, the packaged defaults of the installed libraries come next. |
| `stats` | Statistics shared by the hypothesis tests of the knowledge store and by analyses that need the same decision language (pure): a cluster bootstrap over |
| `tags` | The four words that say how a quantity was obtained (shown after the unit on every axis and sheet header).  Neutral on purpose: the style code and the |
| `figures.theme` | Equinor Design System (EDS) light-theme constants. |
| `figures.figure_style` | Figure style after Stephen Few, *Show Me the Numbers*: legible text, little non-data ink, labels on the data instead of legends where possible, and th |
| `figures.axis_tags` | Add a bracket after the unit of an axis, colour bar or sheet header that says how the quantity was obtained in this project: measured, derived, modell |
| `figures.hc_colours` | Hydrocarbon type colours from the NPD Geostandard (defaults/hc_colours.yaml). |
| `figures.hover_panel` | Tooltips that do not hide the data (Plotly dashboards). |
| `names` | Name keys: a name reduced for matching (pure string functions shared by the domain libraries). |

Functions are pure: they take frames and parameters and return `(result, events)` where they change or flag data; nothing reads or writes files except the configuration loader.

## Settings and assumptions

Every setting has a packaged default in `src/ep_physics_base/defaults/`. A project can override a file by providing `config/<same name>` in its working directory; the project file wins. A default is an assumption unless it says otherwise: its level (`placeholder`, `inferred`, `published`, `official`, `exact`) and a one-line basis travel with it, and a citation (author and year) is given where one exists. Libraries never import a knowledge store: a host that has one passes its values in as an overlay.

## Develop

```
uv sync --all-extras
uv run pytest            # 3 test files
uv run ruff check .
uv run python scripts/publication_gate.py
```

Tests use small synthetic data generated on the fly. No network, no real data.
