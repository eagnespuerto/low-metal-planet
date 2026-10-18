"""Gaia DR3 XP low-resolution spectrum of TIC 219893931 against benchmark stars.

Metal lines blanket the blue/near-UV (< 450 nm), so at fixed temperature a
metal-poor dwarf is brighter in the blue than a solar-metallicity one. We
compare the target's XP spectrum with stars whose metallicities come from
high-resolution spectroscopy, using
  * a temperature index  T_idx = F(560-620 nm) / F(780-880 nm)  (red, few metal lines)
  * a blanketing index   B_idx = F(380-450 nm) / F(500-560 nm)
and fit B_idx = a + b*T_idx + c*[Fe/H] over the benchmarks to invert for the
target's [Fe/H].

Writes data/xp_sampled.csv (cache), figures/xp_spectrum.png and
results_xp.json.
"""
import io
import json
import zipfile
from pathlib import Path

import matplotlib
import numpy as np
import requests

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "xp_sampled.csv"
TARGET = 1651056179580039424
EBV_TARGET = 0.0287  # Schlafly & Finkbeiner (2011) via IRSA; benchmarks assumed unreddened

# Approximate literature values from high-resolution spectroscopy
# (Gaia FGK benchmarks / PASTEL-style compilations). Precision ~0.1 dex, ~100 K.
BENCHMARKS = {
    "HD 209458": (1779546757669063552, 6065, 0.00),
    "HIP 56948": (1061266013453102080, 5790, 0.02),
    "HD 45184": (2898239468873596800, 5870, 0.04),
    "HD 98618": (856774374153131008, 5840, 0.05),
    "HD 22879": (3250489115709122560, 5860, -0.85),
    "HD 201891": (1787990525934491776, 5900, -1.05),
    "HD 194598": (1752459532807704704, 6020, -1.10),
    "BD+17 4708": (1776289248313154688, 6100, -1.60),
    "HD 19445": (112440873718983680, 6050, -2.00),
    "HD 74000": (5709390701922940416, 6200, -2.00),
    "HD 84937": (615943806835727872, 6360, -2.03),
    "HD 140283": (6268770373590148224, 5790, -2.40),
    "BD-13 3442": (3572742676591656832, 6400, -2.70),
    "G 64-12": (3662741860852094208, 6450, -3.20),
}
BLUE, GREEN, RED, NIR = (380, 450), (500, 560), (560, 620), (780, 880)


def fetch():
    ids = [TARGET] + [v[0] for v in BENCHMARKS.values()]
    r = requests.get("https://gea.esac.esa.int/data-server/data", params={
        "RETRIEVAL_TYPE": "XP_SAMPLED", "ID": ",".join(map(str, ids)),
        "DATA_STRUCTURE": "DATAMODEL_STANDARD", "FORMAT": "csv",
        "RELEASE": "Gaia DR3", "VALID_DATA": "false"}, timeout=300)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    header, rows = None, []
    for name in z.namelist():
        lines = z.read(name).decode().strip().splitlines()
        header = lines[0]
        rows += lines[1:]
    CACHE.write_text("\n".join([header] + rows) + "\n")


def load():
    d = np.genfromtxt(CACHE, delimiter=",", names=True, dtype=None, encoding=None)
    out = {}
    for sid in np.unique(d["source_id"]):
        m = d["source_id"] == sid
        out[int(sid)] = (d["wavelength"][m], d["flux"][m], d["flux_error"][m])
    return out


def ccm89_alambda_over_av(wl_nm, rv=3.1):
    """Cardelli, Clayton & Mathis (1989) optical/NIR extinction curve."""
    x = 1000.0 / wl_nm  # inverse microns
    a, b = np.zeros_like(x), np.zeros_like(x)
    ir = x < 1.1
    a[ir], b[ir] = 0.574 * x[ir] ** 1.61, -0.527 * x[ir] ** 1.61
    op = ~ir
    y = x[op] - 1.82
    a[op] = (1 + 0.17699 * y - 0.50447 * y**2 - 0.02427 * y**3 + 0.72085 * y**4
             + 0.01979 * y**5 - 0.77530 * y**6 + 0.32999 * y**7)
    b[op] = (1.41338 * y + 2.28305 * y**2 + 1.07233 * y**3 - 5.38434 * y**4
             - 0.62251 * y**5 + 5.30260 * y**6 - 2.09002 * y**7)
    return a + b / rv


def band(wl, f, lo_hi):
    m = (wl >= lo_hi[0]) & (wl <= lo_hi[1])
    return f[m].mean()


def indices(wl, f):
    return band(wl, f, RED) / band(wl, f, NIR), band(wl, f, BLUE) / band(wl, f, GREEN)


def main():
    if not CACHE.exists():
        fetch()
    spec = load()

    wl, f, fe = spec[TARGET]
    f = f * 10 ** (0.4 * 3.1 * EBV_TARGET * ccm89_alambda_over_av(wl))
    spec[TARGET] = (wl, f, fe)

    # BD+17 4708, HD 19445 and HD 140283 have no published XP_SAMPLED spectrum.
    names = [n for n in BENCHMARKS if BENCHMARKS[n][0] in spec]
    T = np.array([indices(*spec[BENCHMARKS[n][0]][:2])[0] for n in names])
    B = np.array([indices(*spec[BENCHMARKS[n][0]][:2])[1] for n in names])
    feh = np.array([BENCHMARKS[n][2] for n in names])
    t0, b0 = indices(wl, f)

    # Fit B = a + b*T + c*[Fe/H]; invert for the target, bootstrap over benchmarks.
    def fit(idx):
        A = np.c_[np.ones(len(idx)), T[idx], feh[idx]]
        coef, *_ = np.linalg.lstsq(A, B[idx], rcond=None)
        return coef

    coef = fit(np.arange(len(names)))
    resid = B - np.c_[np.ones(len(names)), T, feh] @ coef
    rng = np.random.default_rng(1)
    boots = []
    for _ in range(5000):
        c = fit(rng.integers(0, len(names), len(names)))
        if abs(c[2]) > 1e-4:
            boots.append((b0 - c[0] - c[1] * t0) / c[2])
    feh_target = (b0 - coef[0] - coef[1] * t0) / coef[2]
    lo, hi = np.percentile(boots, [16, 84])
    # Blanketing index a -2.83 star at the target's T_idx would have:
    b_vmp = coef[0] + coef[1] * t0 + coef[2] * -2.83
    b_sol = coef[0] + coef[1] * t0

    res = {"target_T_idx": t0, "target_B_idx": b0,
           "fit_coefficients(a,b,c)": coef.tolist(),
           "fit_rms_B_idx": float(np.std(resid)),
           "feh_from_xp": float(feh_target),
           "feh_from_xp_16_84": [float(lo), float(hi)],
           "B_idx_expected_at_feh_-2.83": float(b_vmp),
           "B_idx_expected_at_feh_0": float(b_sol),
           "benchmarks": {n: {"T_idx": float(T[i]), "B_idx": float(B[i]),
                              "feh_lit": float(feh[i]), "teff_lit": BENCHMARKS[n][1]}
                          for i, n in enumerate(names)},
           "benchmarks_without_xp": [n for n in BENCHMARKS if n not in names]}
    (ROOT / "results_xp.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if not k.startswith("benchmarks")}, indent=2))

    # Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150)
    norm = lambda w, fl: fl / band(w, fl, (540, 660))  # noqa: E731
    for n, col, ls in [("HD 209458", "#2c7fb8", "-"), ("HD 74000", "#7b3294", "-"),
                       ("BD-13 3442", "#7b3294", ":")]:
        w2, f2, _ = spec[BENCHMARKS[n][0]]
        ax1.plot(w2, norm(w2, f2), color=col, ls=ls, lw=1.3,
                 label=f"{n}  [Fe/H] = {BENCHMARKS[n][2]:+.2f}, {BENCHMARKS[n][1]} K")
    ax1.plot(wl, norm(wl, f), color="#c0392b", lw=2.2,
             label="TIC 219893931 (dereddened)")
    ax1.axvspan(*BLUE, color="0.85", zorder=0)
    ax1.set_xlim(336, 1020)
    ax1.set_xlabel("wavelength [nm]")
    ax1.set_ylabel(r"$F_\lambda$ / F(540–660 nm)")
    ax1.set_title("Gaia DR3 XP spectra (shaded: metal-line blanketing band)")
    ax1.legend(fontsize=7)

    sc = ax2.scatter(T, B, c=feh, cmap="viridis", vmin=-3.2, vmax=0.1, s=45, edgecolor="k")
    for i, n in enumerate(names):
        ax2.annotate(n, (T[i], B[i]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    tt = np.linspace(T.min() - 0.02, T.max() + 0.02, 10)
    for fv, ls in [(0, "-"), (-1, "--"), (-2, "-."), (-2.83, ":")]:
        ax2.plot(tt, coef[0] + coef[1] * tt + coef[2] * fv, color="0.4", ls=ls, lw=0.9,
                 label=f"fit, [Fe/H] = {fv}")
    ax2.plot(t0, b0, marker="*", ms=18, color="#c0392b", mec="k", ls="none",
             label=f"TIC 219893931 → [Fe/H] ≈ {feh_target:+.1f}")
    ax2.set_xlabel(r"T index  F(560–620) / F(780–880)")
    ax2.set_ylabel(r"blanketing index  F(380–450) / F(500–560)")
    ax2.legend(fontsize=7, loc="upper left")
    fig.colorbar(sc, ax=ax2, label="[Fe/H] (literature)")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "xp_spectrum.png")


if __name__ == "__main__":
    main()
