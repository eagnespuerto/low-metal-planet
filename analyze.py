"""Three tests of the [Fe/H] = -2.83 claim for TIC 219893931 (Gaia DR3 1651056179580039424).

Reads the cached JSON in data/ (run fetch_data.py first) and writes
results.json plus figures/toomre.png.
"""
import json
from pathlib import Path

import astropy.coordinates as coord
import astropy.units as u
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).parent
DATA = ROOT / "data"
N_MC = 20_000
RNG = np.random.default_rng(219893931)

# Schönrich, Binney & Dehnen (2010) solar peculiar motion; Astropy v4.0 frame
# otherwise (R0 = 8.122 kpc, z0 = 20.8 pc).
GC_FRAME = coord.Galactocentric(
    galcen_v_sun=coord.CartesianDifferential([11.1, 12.24 + 233.4, 7.25] * u.km / u.s))
V_LSR = 233.4  # km/s, matches the frame above
# Thick-disk / halo boundaries in the Toomre diagram (Venn et al. 2004,
# Bensby et al. 2014 use ~70 and ~180-200 km/s).
V_THICK, V_HALO = 70.0, 180.0


def load(name):
    return json.loads((DATA / f"{name}.json").read_text())


def kinematics(s):
    """Monte-Carlo UVW and Toomre velocity relative to the LSR."""
    mean = [s["parallax"], s["pmra"], s["pmdec"]]
    e = [s["parallax_error"], s["pmra_error"], s["pmdec_error"]]
    corr = np.array([[1, s["parallax_pmra_corr"], s["parallax_pmdec_corr"]],
                     [s["parallax_pmra_corr"], 1, s["pmra_pmdec_corr"]],
                     [s["parallax_pmdec_corr"], s["pmra_pmdec_corr"], 1]])
    cov = corr * np.outer(e, e)
    plx, pmra, pmdec = RNG.multivariate_normal(mean, cov, N_MC).T
    rv = RNG.normal(s["radial_velocity"], s["radial_velocity_error"], N_MC)

    icrs = coord.SkyCoord(ra=np.full(N_MC, s["ra"]) * u.deg,
                          dec=np.full(N_MC, s["dec"]) * u.deg,
                          distance=(1000 / plx) * u.pc,
                          pm_ra_cosdec=pmra * u.mas / u.yr,
                          pm_dec=pmdec * u.mas / u.yr,
                          radial_velocity=rv * u.km / u.s)
    # Heliocentric Galactic UVW (U toward GC, V rotation, W NGP).
    gal = icrs.galactic
    gal.representation_type = "cartesian"
    gal.differential_type = "cartesian"
    U = gal.velocity.d_x.to_value(u.km / u.s)
    V = gal.velocity.d_y.to_value(u.km / u.s)
    W = gal.velocity.d_z.to_value(u.km / u.s)
    # Relative to the LSR (add solar peculiar motion back in).
    U_lsr, V_lsr, W_lsr = U + 11.1, V + 12.24, W + 7.25
    v_tot = np.sqrt(U_lsr**2 + V_lsr**2 + W_lsr**2)

    gc = icrs.transform_to(GC_FRAME)
    z = gc.z.to_value(u.pc)

    def summ(x):
        lo, med, hi = np.percentile(x, [16, 50, 84])
        return {"median": round(float(med), 2), "minus": round(float(med - lo), 2),
                "plus": round(float(hi - med), 2)}

    v_tan = 4.74047 * np.hypot(pmra, pmdec) / plx
    return {
        "distance_pc": summ(1000 / plx),
        "v_tan_km_s": summ(v_tan),
        "rv_km_s": summ(rv),
        "U_lsr": summ(U_lsr), "V_lsr": summ(V_lsr), "W_lsr": summ(W_lsr),
        "v_total_lsr": summ(v_tot),
        "v_total_heliocentric": summ(np.sqrt(U**2 + V**2 + W**2)),
        "z_pc": summ(z),
        "P(v_lsr > 180 km/s)": float(np.mean(v_tot > V_HALO)),
        "P(v_lsr > 70 km/s)": float(np.mean(v_tot > V_THICK)),
        "_samples": (U_lsr, V_lsr, W_lsr),
    }


def toomre_plot(kin, out):
    U, V, W = kin["_samples"]
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    x = V
    y = np.hypot(U, W)
    for r, ls, lab in [(V_THICK, "--", "70 km/s (thin/thick)"),
                       (V_HALO, "-", "180 km/s (thick/halo)"),
                       (V_LSR, ":", "non-rotating (V = -233 km/s)")]:
        if lab.startswith("non"):
            ax.axvline(-V_LSR, color="0.4", ls=ls, lw=1, label=lab)
            continue
        th = np.linspace(0, np.pi, 300)
        ax.plot(r * np.cos(th), r * np.sin(th), color="0.3", ls=ls, lw=1, label=lab)
    ax.scatter(x[::20], y[::20], s=2, alpha=0.2, color="#c0392b", lw=0)
    ax.errorbar(np.median(x), np.median(y), fmt="*", ms=14, color="#c0392b",
                mec="k", label="TIC 219893931 (Gaia DR3)")
    ax.set_xlim(-400, 150)
    ax.set_ylim(0, 350)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$V_{\rm LSR}$ [km s$^{-1}$]")
    ax.set_ylabel(r"$\sqrt{U_{\rm LSR}^2 + W_{\rm LSR}^2}$ [km s$^{-1}$]")
    ax.set_title("Toomre diagram")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(out)


def metallicity(gaia, lamost, vizier, nea):
    s = gaia["source"]
    flags = s["flags_gspspec"] or ""
    return {
        "claimed": {"value": nea[0]["st_met"], "err": nea[0]["st_meterr1"],
                    "ref": "Hotnisky et al. 2026 (ApJS 286, 42) via NASA Exoplanet Archive",
                    "claimed_mass_msun": nea[0]["st_mass"]},
        "gaia_mh_gspspec": {"value": s["mh_gspspec"], "lower": s["mh_gspspec_lower"],
                            "upper": s["mh_gspspec_upper"], "teff": s["teff_gspspec"],
                            "logg": s["logg_gspspec"], "flags": flags},
        "gaia_mh_gspphot": {"value": s["mh_gspphot"], "lower": s["mh_gspphot_lower"],
                            "upper": s["mh_gspphot_upper"]},
        "gaia_mh_msc": s["mh_msc"],
        "gaia_rv_template_fe_h": s["rv_template_fe_h"],
        "independent_catalogues": {k: v["value"] for k, v in vizier.items()},
        "lamost_spectra": {rel: len(rows) for rel, rows in lamost.items()},
    }


def binarity(gaia):
    s = gaia["source"]
    return {
        "ruwe": s["ruwe"],
        "ruwe_ok": s["ruwe"] < 1.4,
        "non_single_star": s["non_single_star"],
        "nss_table_matches": gaia["nss_table_matches"],
        "ipd_frac_multi_peak": s["ipd_frac_multi_peak"],
        "ipd_gof_harmonic_amplitude": s["ipd_gof_harmonic_amplitude"],
        "duplicated_source": s["duplicated_source"],
        "rv_nb_transits": s["rv_nb_transits"],
        "rv_chisq_pvalue": s["rv_chisq_pvalue"],
        "rv_renormalised_gof": s["rv_renormalised_gof"],
        "rv_amplitude_robust": s["rv_amplitude_robust"],
        "dsc_prob_binary": s["classprob_dsc_combmod_binarystar"],
        "phot_bp_rp_excess_factor": s["phot_bp_rp_excess_factor"],
    }


def main():
    gaia, lamost = load("gaia_dr3"), load("lamost")
    vizier, nea = load("vizier_metallicity"), load("exoplanet_archive")

    kin = kinematics(gaia["source"])
    (ROOT / "figures").mkdir(exist_ok=True)
    toomre_plot(kin, ROOT / "figures" / "toomre.png")
    kin.pop("_samples")

    results = {"kinematics": kin,
               "metallicity": metallicity(gaia, lamost, vizier, nea),
               "binarity": binarity(gaia)}
    (ROOT / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
