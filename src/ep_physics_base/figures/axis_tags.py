"""Add a bracket after the unit of an axis, colour bar or sheet header that says how the quantity was obtained in this project: measured, derived, modelled or assumed.
"Pressure [bar]" becomes "Pressure [bar] (measured)".  Rules are in config/axis_basis.yaml.  `install_matplotlib()` patches the axis-label setters so every chart made after `setup_notebook()` is covered.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from ep_physics_base.tags import AXIS_TAGS

_UNIT = re.compile(r"\[[^\[\]]+\]")
_DONE = re.compile(r"\((" + "|".join(AXIS_TAGS) + r")[^)]*\)")


@lru_cache(maxsize=1)
def _rules() -> list[tuple[str, re.Pattern]]:
    from ep_physics_base.config import load_yaml

    return [(r["tag"], re.compile(r["pattern"], re.IGNORECASE)) for r in load_yaml("config/axis_basis.yaml")["rules"]]


def tag_for(label: str) -> str:
    for tag, rx in _rules():
        if rx.search(label):
            return tag
    return "derived"


def tag_label(label: Any) -> Any:
    """The label with ' (tag)' after its LAST unit bracket; labels without a unit bracket, or already tagged, are returned unchanged."""
    if not isinstance(label, str) or _DONE.search(label):
        return label
    units = list(_UNIT.finditer(label))
    if not units:
        return label
    end = units[-1].end()
    return f"{label[:end]} ({tag_for(label[:end])}){label[end:]}"


def install_matplotlib() -> None:
    """Patch Axes.set_xlabel / set_ylabel / set_zlabel and Colorbar.set_label (once) so labels are tagged when they are set."""
    from matplotlib.axes import Axes
    from matplotlib.colorbar import Colorbar

    def wrap(fn):
        if getattr(fn, "_axis_tagged", False):
            return fn

        def inner(self, label, *a, **k):
            return fn(self, tag_label(label), *a, **k)

        inner._axis_tagged = True
        inner.__doc__ = fn.__doc__
        return inner

    for name in ("set_xlabel", "set_ylabel"):
        setattr(Axes, name, wrap(getattr(Axes, name)))
    try:
        from mpl_toolkits.mplot3d.axes3d import Axes3D

        Axes3D.set_zlabel = wrap(Axes3D.set_zlabel)
    except Exception:                                              # noqa: BLE001
        pass
    Colorbar.set_label = wrap(Colorbar.set_label)

    def quiet_log(fn):                                              # Few: fewer ticks. On a log axis the minor tick labels (3x10^1, 4x10^1 ...) run into each other: major labels only
        if getattr(fn, "_quiet_log", False):
            return fn

        def inner(self, value, *a, **k):
            res = fn(self, value, *a, **k)
            if value == "log":
                from matplotlib.ticker import NullFormatter

                (self.xaxis if fn.__name__ == "set_xscale" else self.yaxis).set_minor_formatter(NullFormatter())
            return res

        inner._quiet_log = True
        inner.__name__ = fn.__name__
        return inner

    from matplotlib.axes import Axes as _Ax

    _Ax.set_xscale, _Ax.set_yscale = quiet_log(_Ax.set_xscale), quiet_log(_Ax.set_yscale)
    # Few: nothing may run off the figure or hide the data.  (1) titles are wrapped to the width of their axes (or the figure for a suptitle); (2) a legend with a fixed INSIDE position
    # is placed where it covers least ('best'), unless the caller anchored it outside the axes.
    import textwrap

    def wrap_title(fn, kind):
        if getattr(fn, "_wrapped", False):
            return fn

        def inner(self, label, *a, **k):
            try:
                fig = self.figure if kind == "axes" else self
                size = float(k.get("fontsize", 12.0)) if not isinstance(k.get("fontsize"), str) else 12.0
                width_in = (self.get_position().width * fig.get_size_inches()[0]) if kind == "axes" else fig.get_size_inches()[0] * 0.95
                chars = max(int(width_in * 72 / (size * 0.56)), 20)
                if isinstance(label, str) and len(label) > chars and "\n" not in label:
                    label = "\n".join(textwrap.wrap(label, chars))
            except Exception:                                      # noqa: BLE001
                pass
            return fn(self, label, *a, **k)

        inner._wrapped = True
        inner.__doc__ = fn.__doc__
        return inner

    from matplotlib.figure import Figure

    Axes.set_title = wrap_title(Axes.set_title, "axes")
    Figure.suptitle = wrap_title(Figure.suptitle, "figure")

    def legend_best(fn):
        if getattr(fn, "_best", False):
            return fn

        def inner(self, *a, **k):
            inside = {"upper left", "upper right", "lower left", "lower right", "upper center", "lower center", "center left", "center right", "center", 2, 1, 3, 4, 9, 8, 6, 7, 10}
            if "bbox_to_anchor" not in k and k.get("loc") in inside:
                k["loc"] = "best"
            return fn(self, *a, **k)

        inner._best = True
        inner.__doc__ = fn.__doc__
        return inner

    Axes.legend = legend_best(Axes.legend)


def tag_plotly_json(fig_json: str) -> str:
    """Tag every axis title (2D and 3D scenes) of a Plotly figure given as JSON; other text is unchanged."""
    fig = json.loads(fig_json)
    lay = fig.get("layout", {})

    def fix(ax: dict) -> None:
        t = ax.get("title")
        if isinstance(t, dict) and "text" in t:
            t["text"] = tag_label(t["text"])
        elif isinstance(t, str):
            ax["title"] = tag_label(t)

    for k, v in lay.items():
        if re.match(r"[xyz]axis\d*$", k) and isinstance(v, dict):
            fix(v)
        if k.startswith("scene") and isinstance(v, dict):
            for kk, vv in v.items():
                if re.match(r"[xyz]axis$", kk) and isinstance(vv, dict):
                    fix(vv)
    return json.dumps(fig)