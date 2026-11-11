"""Figure style after Stephen Few, *Show Me the Numbers*: legible text, little non-data ink, labels on the data instead of legends where possible, and the notable points named.

    readable_defaults()           rcParams with a readable floor for every text (called by setup_notebook)
    annotate_points(ax, x, y, labels, max_labels=25)
                                   names points directly; when there are too many, only the most extreme ones (furthest from the middle of the cloud) are named and the rest stay unnamed,
                                   and a label is skipped rather than drawn over another one
    direct_labels(ax)              replaces a line legend by a label at the end of each line
    legibility_issues(fig)         what a reader would trip over: text smaller than the floor, overlapping text, crowded tick labels (used by savefig to log every figure)
Rules (Few): the data are the darkest ink; gridlines are faint; one emphasis colour; text horizontal; label units on axes; annotate what the reader should notice.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

MIN_FONT_PT = 8.0          # smallest text a reader can take in on a laptop screen at the saved size (ASSUMPTION, style choice)


def readable_defaults() -> dict[str, Any]:
    return {"font.size": 10.0, "axes.labelsize": 10.5, "axes.titlesize": 12.0, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "legend.fontsize": 9.0,
            "legend.title_fontsize": 9.5, "figure.titlesize": 13.0, "grid.alpha": 0.6, "lines.linewidth": 1.8}


def _extremes(x: np.ndarray, y: np.ndarray, k: int) -> np.ndarray:
    """Indices of the k points furthest from the median of the cloud, in units of each axis' spread."""
    def z(v):
        s = np.nanpercentile(v, 75) - np.nanpercentile(v, 25)
        return (v - np.nanmedian(v)) / (s if s > 0 else (np.nanstd(v) or 1.0))
    d = np.hypot(z(x), z(y))
    d = np.where(np.isfinite(d), d, -1)
    return np.argsort(-d)[:k]


def annotate_points(ax, x: Sequence[float], y: Sequence[float], labels: Sequence[str], max_labels: int = 25, fontsize: float = 8.5, colour: str = "#243746",
                    only: Sequence[int] | None = None, unique: bool = True, priority: Sequence[float] | None = None,
                    box: bool = False) -> dict[str, int]:
    """Name points without covering each other.  Returns {'named': n, 'skipped': n, 'unnamed': n}.  `only` = indices to consider (e.g. the points a key finding mentions)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    labels = [str(s) for s in labels]
    idx = np.arange(len(x)) if only is None else np.asarray(only)
    idx = idx[np.isfinite(x[idx]) & np.isfinite(y[idx])]
    pri = None if priority is None else np.asarray(priority, dtype=float)

    def ranked(ii):                                                          # most important first: the given priority (e.g. production on a map), else the most extreme points
        return ii[np.argsort(-np.nan_to_num(pri[ii], nan=-np.inf))] if pri is not None else ii[_extremes(x[ii], y[ii], len(ii))]

    if unique and len(idx):                                                  # one label per name (several tests in one well): keep its most extreme point
        order = ranked(idx)
        seen, keep = set(), []
        for i in order:
            if labels[i] not in seen:
                seen.add(labels[i]); keep.append(i)
        idx = np.asarray(keep)
    idx = ranked(idx)[:max_labels] if len(idx) else idx
    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    axbox = ax.get_window_extent(r)
    allpts = ax.transData.transform(np.column_stack([np.nan_to_num(x), np.nan_to_num(y)]))
    placed = [t.get_window_extent(r) for t in ax.texts if t.get_visible()]          # text already on the axes (finding notes, line labels)
    offsets = [(6, 4), (6, -11), (-6, 4), (-6, -11), (0, 9), (0, -15), (12, 0), (-12, 0), (14, 12), (-14, -16), (20, -4), (-20, 4)]
    named = skipped = 0
    for i in idx:
        best = None
        for dx, dy in offsets:
            ann = ax.annotate(labels[i], (x[i], y[i]), xytext=(dx, dy), textcoords="offset points", fontsize=fontsize, color=colour, ha="right" if dx < 0 else "left", va="bottom", zorder=8,
                              bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8) if box else None,
                              arrowprops=dict(arrowstyle="-", color="#9AA5AE", lw=0.5, shrinkA=0, shrinkB=2) if abs(dx) > 10 or abs(dy) > 12 else None)
            bb = ann.get_window_extent(r)
            inside = axbox.x0 <= bb.x0 and bb.x1 <= axbox.x1 and axbox.y0 <= bb.y0 and bb.y1 <= axbox.y1
            hits = sum(1 for p in placed if bb.overlaps(p))
            covered = int(np.sum((allpts[:, 0] > bb.x0) & (allpts[:, 0] < bb.x1) & (allpts[:, 1] > bb.y0) & (allpts[:, 1] < bb.y1)))
            score = (0 if inside else 100) + hits * 10 + covered
            if best is None or score < best[0]:
                if best is not None:
                    best[1].remove()
                best = (score, ann, bb)
            else:
                ann.remove()
            if score == 0:
                break
        if best is None or best[0] >= 10:
            if best is not None:
                best[1].remove()
            skipped += 1
            continue
        placed.append(best[2])
        named += 1
    return {"named": named, "skipped": skipped, "unnamed": int(len(x) - named)}


def direct_labels(ax, fontsize: float = 9.0, remove_legend: bool = True) -> int:
    """Put each line's label at its right end, in the line's colour (Few: label the data, not a legend)."""
    n = 0
    for line in ax.get_lines():
        lab = line.get_label()
        if not lab or lab.startswith("_"):
            continue
        xd, yd = np.asarray(line.get_xdata(), dtype=float), np.asarray(line.get_ydata(), dtype=float)
        ok = np.isfinite(xd) & np.isfinite(yd)
        if not ok.any():
            continue
        j = np.flatnonzero(ok)[-1]
        ax.annotate(lab, (xd[j], yd[j]), xytext=(4, 0), textcoords="offset points", fontsize=fontsize, color=line.get_color(), va="center")
        n += 1
    if remove_legend and ax.get_legend() is not None and n:
        ax.get_legend().remove()
    return n


def legibility_issues(fig, min_font: float = MIN_FONT_PT, max_texts: int = 400) -> dict[str, Any]:
    """Count what a reader would trip over: text below `min_font` points, overlapping texts (more than a fifth of the smaller box), and the worst examples."""
    from matplotlib.text import Text

    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    texts = [t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip() and t.get_alpha() != 0
             and (t.axes is None or (t.axes.get_visible() and (t.axes.axison or t in t.axes.texts)))]   # hidden helper axes draw nothing
    small = [t.get_text()[:40] for t in texts if t.get_fontsize() < min_font]
    ticks = {}
    for a in fig.axes:
        for d, axis in (("x", a.xaxis), ("y", a.yaxis)):
            for tl in axis.get_ticklabels():
                ticks[id(tl)] = (id(a), d)
    boxes = []
    for t in texts[:max_texts]:
        try:
            b = t.get_window_extent(r)
        except Exception:                                                  # noqa: BLE001
            continue
        if b.width > 0 and b.height > 0:
            boxes.append((b.x0, b.y0, b.x1, b.y1, t.get_text()[:30], ticks.get(id(t))))
    over, crowd = [], 0
    for i in range(len(boxes)):
        a = boxes[i]
        for j in range(i + 1, len(boxes)):
            b = boxes[j]
            if a[5] and b[5] and a[5] != b[5]:
                continue                                                   # an x and a y tick label meeting at a corner: matplotlib layout, not a reading problem
            w = min(a[2], b[2]) - max(a[0], b[0])
            h = min(a[3], b[3]) - max(a[1], b[1])
            if w > 0 and h > 0:
                inter = w * h
                smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if smaller > 0 and inter / smaller > 0.2:
                    if a[5] and b[5]:
                        crowd += 1                                         # tick labels of one axis running into each other
                    else:
                        over.append(f"'{a[4]}' / '{b[4]}'")
    out = {"texts": len(texts), "small_text": len(small), "small_examples": small[:5], "overlaps": len(over), "overlap_examples": over[:5], "tick_crowding": crowd}
    out.update(placement_issues(fig))
    return out


def _data_points_px(ax, max_per_artist: int = 400, lines: bool = True) -> np.ndarray:
    """Display-space positions (pixels) of the data an axes draws: scatter offsets and line vertices (sampled), only those inside the visible axes."""
    pts = []
    for col in ax.collections:
        try:
            off = np.asarray(col.get_offsets(), dtype=float)
            if off.ndim == 2 and len(off):
                tr = col.get_offset_transform() if hasattr(col, "get_offset_transform") else ax.transData
                pts.append(tr.transform(off[np.isfinite(off).all(axis=1)][:: max(1, len(off) // max_per_artist)]))
        except Exception:                                                  # noqa: BLE001
            continue
    for ln in (ax.get_lines() if lines else []):
        try:
            xy = np.column_stack([np.asarray(ln.get_xdata(), dtype=float), np.asarray(ln.get_ydata(), dtype=float)])
            if len(xy) > 1 and ln.get_visible():
                pts.append(ln.get_transform().transform(xy[np.isfinite(xy).all(axis=1)][:: max(1, len(xy) // max_per_artist)]))
        except Exception:                                                  # noqa: BLE001
            continue
    if not pts:
        return np.empty((0, 2))
    p = np.vstack(pts)
    bb = ax.get_window_extent()
    return p[(p[:, 0] >= bb.x0) & (p[:, 0] <= bb.x1) & (p[:, 1] >= bb.y0) & (p[:, 1] <= bb.y1)]


def _inside(points: np.ndarray, bb) -> np.ndarray:
    return (points[:, 0] >= bb.x0) & (points[:, 0] <= bb.x1) & (points[:, 1] >= bb.y0) & (points[:, 1] <= bb.y1)


def placement_issues(fig, allow_labelled_points: int = 1) -> dict[str, Any]:
    """Where things sit, which a reader trips over even when no two texts overlap:
      legend_over_data   data points hidden behind a legend box (move the legend outside the axes: `legend_below`)
      labels_over_data   an annotation that covers more than its own point
      intrusions         text of one axes (tick labels, axis title) running into the area of another axes
      clipped            text running off the figure edge
    Pure inspection of a drawn figure; returns counts and short examples."""
    from matplotlib.text import Annotation

    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = {"legend_over_data": 0, "labels_over_data": 0, "intrusions": 0, "clipped": 0, "placement_examples": []}
    axes = [a for a in fig.axes if a.get_visible() and a.axison and a.get_window_extent().width > 30 and a.get_window_extent().height > 30]
    for a in axes:
        pts = _data_points_px(a)
        marks = _data_points_px(a, lines=False)                             # markers only: a label crossing a line or an outline is normal, covering markers is not
        lg = a.get_legend()
        if lg is not None and lg.get_visible() and len(pts):
            n = int(_inside(pts, lg.get_window_extent(r)).sum())
            if n > 2:
                out["legend_over_data"] += 1
                out["placement_examples"].append(f"legend covers {n} data points")
        for t in a.texts:
            if not t.get_visible() or not t.get_text().strip() or not len(marks):
                continue
            bb = t.get_window_extent(r)
            hit = _inside(marks, bb)
            if isinstance(t, Annotation):
                own = np.asarray(a.transData.transform(t.xy)) if t.xycoords == "data" else None
                if own is not None:
                    hit &= np.hypot(marks[:, 0] - own[0], marks[:, 1] - own[1]) > 8.0       # its own point may sit next to the label
            if int(hit.sum()) > allow_labelled_points:
                out["labels_over_data"] += 1
                out["placement_examples"].append(f"'{t.get_text()[:25]}' covers {int(hit.sum())} points")
    for a in axes:
        mine = list(a.get_xticklabels()) + list(a.get_yticklabels()) + [a.xaxis.label, a.yaxis.label]
        for b in axes:
            if b is a or b.get_shared_x_axes().joined(a, b) and b.get_shared_y_axes().joined(a, b):
                continue
            bb = b.get_window_extent()
            for t in mine:
                if t.get_visible() and t.get_text().strip():
                    tb = t.get_window_extent(r)
                    w = min(tb.x1, bb.x1 - 2) - max(tb.x0, bb.x0 + 2)
                    h = min(tb.y1, bb.y1 - 2) - max(tb.y0, bb.y0 + 2)
                    if w > 3 and h > 3 and tb.width > 0:
                        out["intrusions"] += 1
                        out["placement_examples"].append(f"'{t.get_text()[:20]}' of one axes lies inside another axes")
    fb = fig.bbox
    tick_ids = {id(tl) for a in fig.axes for tl in list(a.get_xticklabels()) + list(a.get_yticklabels())}      # tick labels outside the view limits are not drawn
    legend_ids = {id(tx) for lg in fig.findobj(__import__("matplotlib").legend.Legend) for tx in lg.get_texts() + [lg.get_title()]}       # legends set outside the figure are kept by bbox_inches="tight"
    for t in fig.findobj(__import__("matplotlib").text.Text):
        if t.get_visible() and t.get_text().strip() and id(t) not in tick_ids and id(t) not in legend_ids:
            try:
                tb = t.get_window_extent(r)
            except Exception:                                                  # noqa: BLE001
                continue
            if tb.width > 0 and (tb.x0 < fb.x0 - 3 or tb.x1 > fb.x1 + 3 or tb.y0 < fb.y0 - 3 or tb.y1 > fb.y1 + 3):
                out["clipped"] += 1
                out["placement_examples"].append(f"'{t.get_text()[:25]}' runs off the figure")
    out["placement_examples"] = out["placement_examples"][:5]
    return out


def legend_below(ax, handles=None, labels=None, ncol: int = 4, fontsize: float = 8.5, gap: float = 0.03):
    """A legend under the axes, in one or two rows, so it never covers data (Few: keep the plot area for the data)."""
    kw = dict(loc="upper center", bbox_to_anchor=(0.5, -gap), ncol=ncol, fontsize=fontsize, frameon=False, borderaxespad=0.0)
    return ax.legend(handles=handles, labels=labels, **kw) if handles is not None else ax.legend(**kw)

def install_legibility_log(path: str | None = None) -> None:
    """Log the legibility of EVERY figure that is rendered (inline display or file), with the notebook name from the environment variable NB_NAME, to reports/figures/legibility.jsonl."""
    import json
    import os

    from matplotlib.backend_bases import FigureCanvasBase

    from ep_physics_base.config import PROJECT_ROOT

    if getattr(FigureCanvasBase.print_figure, "_legibility", False):
        return
    orig = FigureCanvasBase.print_figure
    log = PROJECT_ROOT / (path or "reports/figures/legibility.jsonl")

    def wrapped(self, *a, **k):
        try:
            fig = self.figure
            titles = [ax.get_title() for ax in fig.axes if ax.get_title()]
            rec = {"notebook": os.environ.get("NB_NAME", "?"), "run": os.environ.get("NB_RUN", ""), "title": (fig._suptitle.get_text() if fig._suptitle else (titles[0] if titles else ""))[:80], **legibility_issues(fig)}
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except Exception:                                                  # noqa: BLE001
            pass
        return orig(self, *a, **k)

    wrapped._legibility = True
    FigureCanvasBase.print_figure = wrapped