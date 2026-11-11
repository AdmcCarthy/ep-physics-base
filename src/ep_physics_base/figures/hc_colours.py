"""Hydrocarbon type colours from the NPD Geostandard (config/hc_colours.yaml, docs/geostandard.md).

    hc_colour("gas")               # "#FF0000": fill for areas, bars, pies and markers
    hc_line_colour("condensate")   # a darker shade of the same hue with >= 3:1 contrast on white: for lines and text
    hc_colour("GAS/CONDENSATE")    # Sodir wording is accepted; a combination returns its first colour, `hc_pair` both

Never hard-code an oil, gas or condensate colour: use this module (the theme's STREAM_COLOURS and the network, region and Excel charts do).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILE = Path(__file__).resolve().parents[2] / "config" / "hc_colours.yaml"


@lru_cache(maxsize=1)
def load_hc_colours() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))


def _key(name: str) -> str:
    cfg = load_hc_colours()
    raw = str(name).strip()
    return cfg["aliases"].get(raw.upper(), raw.lower())


def hc_pair(name: str) -> tuple[str, str]:
    """(first, second) colour of a type; a single type returns the same colour twice."""
    cfg = load_hc_colours()
    k = _key(name)
    if k in cfg["combinations"]:
        a, b = cfg["combinations"][k]
        return cfg["colours"][a]["fill"], cfg["colours"][b]["fill"]
    fill = cfg["colours"].get(k, cfg["colours"]["unknown"])["fill"]
    return fill, fill


def hc_colour(name: str) -> str:
    """Fill colour of a hydrocarbon type (the first colour of a combination; `unknown` for names the standard does not list)."""
    return hc_pair(name)[0]


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _contrast_on_white(h: str) -> float:
    r, g, b = (int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    lum = 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    return 1.05 / (lum + 0.05)


def hc_line_colour(name: str, min_contrast: float = 3.0) -> str:
    """The type's hue darkened until it has `min_contrast` on white: for lines, thin markers and text."""
    h = hc_colour(name).lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = 1.0
    while f > 0.2:
        cand = "#%02X%02X%02X" % (int(r * f), int(g * f), int(b * f))
        if _contrast_on_white(cand) >= min_contrast:
            return cand
        f -= 0.04
    return "#333333"


def show_colour(name: str) -> str:
    """Colour of a show class (`proven oil zone`, `gas shows` ...)."""
    return load_hc_colours()["shows"][name.lower()]


__all__ = ["hc_colour", "hc_pair", "hc_line_colour", "show_colour", "load_hc_colours"]
