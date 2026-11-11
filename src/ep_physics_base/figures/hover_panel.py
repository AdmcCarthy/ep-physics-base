"""Tooltips that do not hide the data (Plotly dashboards).

Problems this solves: a hover box with ten lines covers the point being hovered and its neighbours.  Rule (Few: details on demand, never over the data):
  * the hover box next to the point keeps at most TWO lines (what it is, the one number that matters);
  * the rest of the text appears in a DETAIL PANEL fixed in a corner of the window, on the side AWAY from the cursor, and never takes mouse events;
  * the hover box is small (11 px), left aligned, slightly transparent.

`hover_panel.js` is one script shared by every page (assets/hover_panel.js).  It wraps `Plotly.react` / `Plotly.newPlot`: a trace whose hover text (`text` or `hovertext`) has more than
`MAX_LINES` lines is cut to the first two lines and the full text is kept in `trace.meta.full`.  A page can register `window.HP_DETAIL = (trace, point) => html | null` for traces whose
tooltip is built from a template and `customdata` (the PVT dashboards).  Nothing else in a page has to change.
"""
from __future__ import annotations

from pathlib import Path

MAX_LINES = 3
SCRIPT_TAG = '<script src="assets/hover_panel.js"></script>'

JS = r"""
(function () {
  const MAX_LINES = __MAX__;
  const css = document.createElement('style');
  css.textContent = '#hp{position:fixed;z-index:9999;bottom:14px;max-width:360px;max-height:70vh;overflow:auto;background:rgba(255,255,255,.97);border:1px solid #B8BEC4;border-left:4px solid #0083CF;'
    + 'border-radius:6px;padding:8px 11px;font:12px/1.4 "Segoe UI",Arial,sans-serif;color:#243746;box-shadow:0 2px 10px rgba(0,0,0,.18);pointer-events:none;display:none}'
    + '#hp b{color:#007079}';
  document.head.appendChild(css);
  const panel = document.createElement('div'); panel.id = 'hp'; document.addEventListener('DOMContentLoaded', () => document.body.appendChild(panel));
  if (document.body) document.body.appendChild(panel);
  function show(html, ev) {
    panel.innerHTML = html; panel.style.display = 'block';
    const x = ev && ev.event ? ev.event.clientX : 0, right = x < window.innerWidth / 2;      // the side away from the cursor
    panel.style.right = right ? '14px' : 'auto'; panel.style.left = right ? 'auto' : '14px';
  }
  function hide() { panel.style.display = 'none'; }
  const textKey = tr => Array.isArray(tr.hovertext) ? 'hovertext' : (Array.isArray(tr.text) && (tr.hoverinfo === 'text' || String(tr.hovertemplate || '').indexOf('%{text}') >= 0) ? 'text' : null);
  function compact(tr) {
    const key = textKey(tr);
    if (!key || !tr[key].some(s => typeof s === 'string' && s.split('<br>').length > MAX_LINES)) return tr;
    const full = tr[key].slice(), short = full.map(s => typeof s === 'string' ? s.split('<br>').slice(0, 2).join('<br>') : s);
    return Object.assign({}, tr, {[key]: short, meta: Object.assign({}, tr.meta || {}, {full: full})});
  }
  const lay = l => Object.assign({}, l, {hoverlabel: Object.assign({bgcolor: 'rgba(255,255,255,.95)', bordercolor: '#B8BEC4', font: {size: 11}, align: 'left', namelength: -1}, (l || {}).hoverlabel || {})});
  const wired = new WeakSet();
  function wire(gd) {
    if (!gd || !gd.on || wired.has(gd)) return; wired.add(gd);
    gd.on('plotly_hover', ev => {
      const p = ev.points && ev.points[0]; if (!p) return;
      const tr = gd.data[p.curveNumber] || p.data || {};
      let html = window.HP_DETAIL ? window.HP_DETAIL(tr, p) : null;
      if (!html && tr.meta && tr.meta.full && tr.meta.full[p.pointNumber]) html = tr.meta.full[p.pointNumber];
      if (html) show(html, ev);
    });
    gd.on('plotly_unhover', hide);
  }
  ['react', 'newPlot'].forEach(fn => {
    const orig = Plotly[fn].bind(Plotly);
    Plotly[fn] = function (gd, data, layout, config) {
      const el = typeof gd === 'string' ? document.getElementById(gd) : gd;
      return orig(gd, (data || []).map(compact), lay(layout), config).then(r => { wire(el); return r; });
    };
  });
})();
""".replace("__MAX__", str(MAX_LINES))


def write_assets(out_dir: Path) -> Path:
    """Write assets/hover_panel.js next to the plotly bundle; returns the path."""
    p = Path(out_dir) / "assets" / "hover_panel.js"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(JS, encoding="utf-8")
    return p
