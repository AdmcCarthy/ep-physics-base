"""Figure style (Few): point labels that do not collide, the legibility check, the readable defaults."""
from __future__ import annotations

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from ep_physics_base.figures import figure_style as fs  # noqa: E402


def test_annotate_points_names_extremes_only_when_crowded_and_never_overlaps():
    rng = np.random.default_rng(1)
    x, y = rng.normal(size=300), rng.normal(size=300)
    x[0], y[0] = 8.0, 8.0                                                    # an obvious outlier must be named
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(x, y)
    res = fs.annotate_points(ax, x, y, [f"W{i}" for i in range(300)], max_labels=10)
    assert res["named"] <= 10 and res["named"] >= 5
    assert any(t.get_text() == "W0" for t in ax.texts)
    issues = fs.legibility_issues(fig)
    assert issues["overlaps"] == 0
    plt.close(fig)


def test_legibility_flags_small_and_overlapping_text():
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.text(0.5, 0.5, "tiny", fontsize=5)
    ax.text(0.5, 0.5, "same place", fontsize=10)
    ax.text(0.5, 0.5, "same place too", fontsize=10)
    issues = fs.legibility_issues(fig)
    assert issues["small_text"] >= 1 and issues["overlaps"] >= 1
    plt.close(fig)


def test_readable_defaults_keep_every_size_above_the_floor():
    d = fs.readable_defaults()
    assert all(v >= fs.MIN_FONT_PT for k, v in d.items() if k.endswith("size"))


def test_direct_labels_replace_the_legend():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="oil"); ax.plot([0, 1], [1, 2], label="gas"); ax.legend()
    assert fs.direct_labels(ax) == 2 and ax.get_legend() is None
    plt.close(fig)


def test_placement_checks_find_a_legend_over_data_a_label_over_points_and_one_axes_in_another():
    rng = np.random.default_rng(3)
    x, y = rng.uniform(0, 1, 80), rng.uniform(0, 1, 80)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(x, y, label="a legend with a long first entry"); ax.plot([0, 1], [0, 1], label="second entry"); ax.plot([0, 1], [1, 0], label="third entry"); ax.legend(loc="center", fontsize=14)
    bad = fs.placement_issues(fig)
    assert bad["legend_over_data"] == 1
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(x, y, label="points"); fs.legend_below(ax)
    assert fs.placement_issues(fig)["legend_over_data"] == 0
    ax.annotate("a long label that lies over many of the points", (0.5, 0.5), xytext=(-60, 0), textcoords="offset points", fontsize=12)
    assert fs.placement_issues(fig)["labels_over_data"] == 1
    plt.close(fig)
    fig = plt.figure(figsize=(6, 3))
    a1 = fig.add_axes([0.1, 0.15, 0.5, 0.7]); a2 = fig.add_axes([0.5, 0.15, 0.45, 0.7])          # the second axes starts under the first one's right half
    a1.set_xlabel("A label that is long"); a2.set_yticks([0.2, 0.5]); a2.set_yticklabels(["a very long tick label"] * 2, fontsize=10)
    assert fs.placement_issues(fig)["intrusions"] >= 1
    plt.close(fig)


def test_annotate_points_leaves_no_label_over_other_points_or_labels():
    rng = np.random.default_rng(5)
    x, y = rng.normal(size=120), rng.normal(size=120)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(x, y)
    fs.annotate_points(ax, x, y, [f"W{i}" for i in range(120)], max_labels=15)
    issues = fs.legibility_issues(fig)
    assert issues["overlaps"] == 0 and issues["labels_over_data"] == 0 and issues["clipped"] == 0
    plt.close(fig)