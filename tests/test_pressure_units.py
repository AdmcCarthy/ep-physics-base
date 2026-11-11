"""Pressure, specific gravity, overpressure and the datum; fluid-class colours; the three-view pressure-depth figure (docs/pore_pressure.md)."""
from __future__ import annotations


import matplotlib
import numpy as np

matplotlib.use("Agg")

from ep_physics_base import units as pu  # noqa: E402


def test_pressure_and_sg_round_trip_and_the_unit_of_one_sg():
    assert abs(pu.BAR_PER_M_PER_SG - 0.0980665) < 1e-9
    p = pu.pressure_from_sg(1.5, 3000.0)
    assert abs(p - 441.2993) < 1e-3 and abs(float(pu.sg_from_pressure(p, 3000.0)) - 1.5) < 1e-12
    assert np.isnan(pu.sg_from_pressure(10.0, 0.0))


def test_the_datum_changes_the_equivalent_density_of_the_same_pressure():
    gw, rt, z = 0.1005, 25.0, 2000.0
    p = float(pu.hydrostatic_bar(z, gw))
    sg_msl, sg_rt = float(pu.emw_sg(p, z, rt, "MSL")), float(pu.emw_sg(p, z, rt, "RT"))
    assert abs(sg_msl - gw / pu.BAR_PER_M_PER_SG) < 1e-12                                   # 1.025 sg on the water-gradient basis
    assert abs(sg_rt - sg_msl * z / (z + rt)) < 1e-12 and 1.011 < sg_rt < 1.014            # about 1.012 on the rotary-table basis
    assert float(pu.tvd_rt_from_msl(z, rt)) == 2025.0 and float(pu.tvd_msl_from_rt(2025.0, rt)) == 2000.0


def test_overpressure_has_the_hydrostatic_gradient_as_zero_in_bar_and_sg():
    gw = 0.1005
    z = np.array([2000.0, 3000.0])
    p = pu.hydrostatic_bar(z, gw)
    assert np.allclose(pu.overpressure_bar(p, z, gw), 0.0) and np.allclose(pu.overpressure_sg(p, z, gw), 0.0)
    assert np.allclose(pu.overpressure_sg(p + 50.0, z, gw), 50.0 / (pu.BAR_PER_M_PER_SG * z))


def test_ecd_is_esd_plus_the_annular_loss_over_the_depth_and_inverts():
    esd, z, rt = 1.60, 3000.0, 25.0
    loss = 12.0                                                                          # bar
    ecd = float(pu.ecd_sg(esd, loss, z, rt))
    assert abs(ecd - (esd + loss / (pu.BAR_PER_M_PER_SG * 3025.0))) < 1e-12
    assert abs(float(pu.annular_loss_bar(ecd, esd, z, rt)) - loss) < 1e-9
    assert float(pu.ecd_sg(esd, loss, z, rt, back_pressure_bar=5.0)) > ecd
    # a mud column of the ESD has the pressure ESD x g x z_RT
    assert abs(float(pu.mud_pressure_bar(esd, z, rt)) - esd * pu.BAR_PER_M_PER_SG * 3025.0) < 1e-9


def test_iso_sg_lines_are_straight_through_the_datum():
    z = np.array([1000.0, 2000.0])
    a = pu.iso_sg_line(1.4, z, 25.0)
    assert np.allclose(a, 1.4 * pu.BAR_PER_M_PER_SG * (z + 25.0)) and abs((a[1] - a[0]) / 1000.0 - 1.4 * pu.BAR_PER_M_PER_SG) < 1e-12








