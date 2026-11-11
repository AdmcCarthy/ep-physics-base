"""Equinor Design System (EDS) light-theme constants.

Single source of truth for colours used by Excel reports and, later, charts.
Hex values were derived from the oklch values in .cursor/rules/EDS_DESIGN_GUIDE.md.
"""

from __future__ import annotations

from ep_physics_base.figures.hc_colours import hc_colour

# --- Semantic tones (light mode) -------------------------------------------------
NORTH_SEA = "#243746"   # deep slate blue: headers, high-emphasis text
MOSS_GREEN = "#007079"  # accent: brand highlights, secondary series
BLUE = "#0084C4"        # primary data series (water, general fluids)
GREEN = "#3FA13D"       # oil / positive indicators
ORANGE = "#E57E00"      # gas / warnings
RED = "#E20337"         # critical alerts, water-cut peaks

# --- Neutral canvas steps --------------------------------------------------------
CANVAS = "#FFFFFF"       # Step 1  : plot / sheet background
SURFACE = "#F1F4F6"      # Step 2  : zebra stripe (light, cool grey)
SURFACE_ALT = "#EBEBEB"  # Step 3  : card / table container
GRIDLINE = "#DCDCDC"     # Step 4  : subtle gridlines and borders
TEXT_PRIMARY = "#243746" # Step 13 : primary text (North Sea)
TEXT_ON_EMPHASIS = "#FFFFFF"  # Step 15 on Step 9/10 emphasis fills

# Stream colours (fluid conventions from the design guide)
STREAM_COLOURS = {
    "oil": hc_colour("oil"),                 # hydrocarbon type colours: NPD Geostandard 6.12 (config/hc_colours.yaml, Adam 2026-11-04)
    "gas": hc_colour("gas"),
    "oe": NORTH_SEA,
    "water": BLUE,
    "ngl": MOSS_GREEN,
    "condensate": hc_colour("condensate"),
}

# Categorical palette for "one colour per field" charts (distinct, all valid on light canvas)
CATEGORICAL_PALETTE = [
    BLUE, GREEN, ORANGE, MOSS_GREEN, NORTH_SEA, RED,
    "#6FB7DD", "#8CCB89", "#F2B266", "#5BA3A9", "#7A8A99", "#F07A93",
]
OTHER_COLOUR = "#B8BEC4"  # "Other fields" bucket

FONT_NAME = "Calibri"
