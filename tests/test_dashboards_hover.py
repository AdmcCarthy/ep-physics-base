"""Dashboard tooltips: two lines next to the point, details in a fixed panel on the far side."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from ep_physics_base.figures import hover_panel as hp

DASH = Path(__file__).resolve().parents[1] / "reports" / "dashboards"


def test_the_shared_script_is_written_and_keeps_the_rules(tmp_path):
    p = hp.write_assets(tmp_path)
    js = p.read_text(encoding="utf-8")
    assert p.name == "hover_panel.js" and "pointer-events:none" in js and "plotly_hover" in js and "MAX_LINES = 3" in js
    assert "slice(0, 2)" in js and "window.innerWidth / 2" in js                       # two lines in the box; panel on the side away from the cursor


@pytest.mark.skipif(not (DASH / "pvt_glr_pressure.html").exists(), reason="dashboards not built")
@pytest.mark.parametrize("name", ["pvt_glr_pressure", "pvt_3d", "network_map", "company_family_tree", "unconformity_delta_story"])
def test_every_dashboard_loads_the_hover_panel(name):
    html = (DASH / f"{name}.html").read_text(encoding="utf-8")
    assert hp.SCRIPT_TAG in html and html.index("plotly.min.js") < html.index("hover_panel.js")      # after Plotly, before the page script
    assert (DASH / "assets" / "hover_panel.js").exists()


@pytest.mark.skipif(not (DASH / "pvt_glr_pressure.html").exists(), reason="dashboards not built")
def test_the_pvt_tooltip_has_at_most_two_lines_and_the_detail_is_in_the_panel():
    html = (DASH / "pvt_glr_pressure.html").read_text(encoding="utf-8")
    m = re.search(r"const HOVER = '([^']*)'", html)
    assert m and m.group(1).count("<br>") <= 1
    assert "window.HP_DETAIL" in html and "envelope basis" in html.split("window.HP_DETAIL")[1]