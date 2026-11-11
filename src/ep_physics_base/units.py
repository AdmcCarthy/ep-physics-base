"""Pressure, specific gravity (equivalent density), overpressure and the depth datum: one place for the conversions.  Pure functions.

Three views of the same pressure at a depth:
    * pressure  p [bar]                                         the physical quantity (formation pressure, mud pressure, leak-off pressure)
    * equivalent density  EMW = p / (g z) [sg = g/cm3]         what drilling uses (mud weight, pore pressure and fracture gradient in sg)
    * overpressure  p - p_hydrostatic [bar] (or in sg)          the departure from the water gradient, with the hydrostatic gradient as the vertical line at zero

THE DATUM MATTERS.  Formation pressures and the water column are referenced to MEAN SEA LEVEL (a seawater column from MSL down to the depth: p_hyd = gradient x z_MSL), while the mud column of a
well stands from the ROTARY TABLE (RT, RKB) down and leak-off tests and mud weights are quoted as equivalent densities at the true vertical depth below RT.  With the RT at `rt_elev_m` above MSL,
z_RT = z_MSL + rt_elev_m, so the same pressure has two equivalent densities:
    EMW_RT  = p / (g z_RT)      the drilling basis (mud weight, LOT / FIT, ECD, ESD)
    EMW_MSL = p / (g z_MSL)     the sea-level basis of the water gradient (the pore pressure plots and `pressure_ratio` use MSL)
and a column of seawater of 1.025 sg reads 1.025 sg on the MSL basis and only 1.025 x z_MSL / z_RT (about 1.012 at 2000 m with a 25 m RT) on the RT basis.  The difference is about
rt_elev / z (1.2 % at 2000 m, 0.6 % at 4000 m): small, but it is the size of the margins that a narrow drilling window is judged by, so every figure states its datum.

Equivalent static density (ESD) is the density of a uniform mud column that gives the static pressure the real column gives (the surface mud weight corrected for the compressibility and thermal
expansion of the mud with depth); equivalent circulating density (ECD) adds the annular friction pressure loss (and any surface back pressure) while the mud circulates:
    ECD = ESD + (annular friction loss + back pressure) / (g z_RT)        (API RP 59 and IADC Lexicon: the sum of pressures over depth of interest; knowledge entries `iadc-ecd`)
"""
from __future__ import annotations

import numpy as np

G = 9.80665
BAR_PER_M_PER_SG = G / 100.0                       # 0.0980665 bar per metre for 1.0 sg (1000 kg/m3 x g = 9806.65 Pa/m)


def tvd_rt_from_msl(z_msl_m, rt_elev_m):
    """Depth below the rotary table [m] of a point at `z_msl_m` below sea level; the RT stands `rt_elev_m` above MSL."""
    return np.asarray(z_msl_m, dtype=float) + np.asarray(rt_elev_m, dtype=float)


def tvd_msl_from_rt(z_rt_m, rt_elev_m):
    return np.asarray(z_rt_m, dtype=float) - np.asarray(rt_elev_m, dtype=float)


def pressure_from_sg(sg, depth_m):
    """Pressure [bar] of a column of density `sg` over `depth_m` (depth from the datum the sg is quoted on)."""
    return np.asarray(sg, dtype=float) * BAR_PER_M_PER_SG * np.asarray(depth_m, dtype=float)


def sg_from_pressure(p_bar, depth_m):
    """Equivalent density [sg] of a pressure at a depth below the datum of the density (NaN at depth 0)."""
    d = np.asarray(depth_m, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(d > 0, np.asarray(p_bar, dtype=float) / (BAR_PER_M_PER_SG * d), np.nan)


def emw_sg(p_bar, z_msl_m, rt_elev_m, datum: str = "RT"):
    """Equivalent density of a pressure at `z_msl_m` below sea level on the `datum` basis: `RT` (mud and leak-off convention) or `MSL` (water-gradient convention)."""
    if datum.upper() == "RT":
        return sg_from_pressure(p_bar, tvd_rt_from_msl(z_msl_m, rt_elev_m))
    if datum.upper() == "MSL":
        return sg_from_pressure(p_bar, z_msl_m)
    raise ValueError("datum must be 'RT' or 'MSL'")


def hydrostatic_bar(z_msl_m, gradient_bar_per_m: float):
    """Hydrostatic (water) pressure at a depth below sea level: the water column stands on mean sea level, not on the rotary table."""
    return np.asarray(z_msl_m, dtype=float) * gradient_bar_per_m


def overpressure_bar(p_bar, z_msl_m, gradient_bar_per_m: float):
    return np.asarray(p_bar, dtype=float) - hydrostatic_bar(z_msl_m, gradient_bar_per_m)


def overpressure_sg(p_bar, z_msl_m, gradient_bar_per_m: float):
    """Overpressure as an equivalent density on the MSL basis: (p - p_hydrostatic) / (g z_MSL)."""
    return sg_from_pressure(overpressure_bar(p_bar, z_msl_m, gradient_bar_per_m), z_msl_m)


def mud_pressure_bar(mud_weight_sg, z_msl_m, rt_elev_m):
    """Static pressure at the bit of a uniform mud column from the rotary table: sg x g x z_RT."""
    return pressure_from_sg(mud_weight_sg, tvd_rt_from_msl(z_msl_m, rt_elev_m))


def ecd_sg(esd_sg, annular_loss_bar, z_msl_m, rt_elev_m, back_pressure_bar: float = 0.0):
    """ECD [sg, RT basis] = ESD + (annular friction pressure loss + surface back pressure) / (g z_RT)."""
    return np.asarray(esd_sg, dtype=float) + sg_from_pressure(np.asarray(annular_loss_bar, dtype=float) + back_pressure_bar, tvd_rt_from_msl(z_msl_m, rt_elev_m))


def annular_loss_bar(ecd_sg_value, esd_sg_value, z_msl_m, rt_elev_m):
    """The annular friction pressure loss [bar] that an ECD above the ESD implies."""
    return (np.asarray(ecd_sg_value, dtype=float) - np.asarray(esd_sg_value, dtype=float)) * BAR_PER_M_PER_SG * tvd_rt_from_msl(z_msl_m, rt_elev_m)


def iso_sg_line(sg, z_m, datum_offset_m: float = 0.0):
    """Pressure [bar] along a line of constant equivalent density `sg` for depths `z_m` below sea level (`datum_offset_m` = RT elevation for the RT basis): the fan of lines of a pressure-depth plot."""
    return pressure_from_sg(sg, np.asarray(z_m, dtype=float) + datum_offset_m)
