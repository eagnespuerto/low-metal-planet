# low-metal-planet

[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![made with](https://img.shields.io/badge/made%20with-Python-3776AB?logo=python&logoColor=white)](https://github.com/eagnespuerto/low-metal-planet)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-support%20me-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/eagnespuerto)
[![Linktree](https://img.shields.io/badge/Linktree-soitsagnes-43E55E?logo=linktree&logoColor=white)](https://linktr.ee/soitsagnes)

Is TIC 219893931 really an extremely metal-poor planet host?

The NASA Exoplanet Archive lists **TIC 219893931 b** (TESS, P = 6.41 d,
R = 2.9 R⊕) with a host metallicity of **[Fe/H] = −2.83 ± 0.23**, from
Hotnisky et al. 2026 (ApJS 286, 42). That would make it one of the most
metal-poor planet hosts known. This repo checks that number against public
data for the host, Gaia DR3 1651056179580039424, in four ways: kinematics,
catalogue metallicities, the Gaia XP spectrum, and binarity.

**Verdict: the −2.83 value is almost certainly wrong.** Every check points
to an ordinary, single, near-solar-metallicity F/G dwarf
([M/H] ≈ −0.4 to +0.3) with disk kinematics.

## Where −2.83 comes from

Section 2.2 of the paper (arXiv:2606.13789) derives [Fe/H] for all 383,718
northern-CVZ stars with a random-forest regression. It is trained on Gaia and
2MASS colours, extinction-corrected with Bayestar19, plus 2MASS absolute
magnitudes, with labels from 9,043 LAMOST DR11 stars. Every star in their
Table 1 carries the same ±0.233 dex error, which matches the archive entry.
The paper's Table 2 does not print [Fe/H], so the number comes from the
machine-readable Table 1.

That method should not be able to produce −2.83 for this star:

- A random forest predicts averages of training labels, so it cannot go
  below the lowest label it saw. Stars near −2.8 are extremely rare among
  9,043 LAMOST stars.
- The inputs are clean. 2MASS has quality flags AAA and J − Ks = 0.35,
  normal for a ~6000 K dwarf, and SFD/S&F reddening is only
  E(B−V) = 0.03.
- The paper's own M★ = 1.14 M☉ and R★ = 1.28 R☉ for this star come from
  T_eff and L, not [Fe/H], so they were not affected. Those values describe a
  roughly solar-metallicity dwarf.

The most likely explanation is a bad row in the machine-readable table, or a
mistake when the archive ingested it. A sign or column slip is possible. A
draft report to the archive is in
[`report/email_to_archive.md`](report/email_to_archive.md).

![Toomre diagram](figures/toomre.png)

## 1. Kinematics (Gaia DR3 astrometry + RVS radial velocity)

| quantity | value |
|---|---|
| parallax | 2.472 ± 0.011 mas → d = 404.6 ± 1.8 pc |
| proper motion | (16.33, 2.54) mas/yr → v_tan = 31.7 km/s |
| radial velocity | −72.9 ± 0.7 km/s (21 transits) |
| (U, V, W)_LSR | (+21.8, −31.6, −58.3) km/s |
| total space velocity vs LSR | **69.8 ± 0.7 km/s** (79.5 km/s heliocentric) |
| height above plane | z = +235 pc |
| P(v_LSR > 180 km/s) | 0 of 20 000 Monte Carlo draws |

The star sits right on the 70 km/s thin/thick-disk boundary of the Toomre
diagram and is co-rotating with the disk (V_LSR = −32 km/s, against −233 km/s
for a non-rotating halo star). Published orbit integrations agree: z_max ≈
1.2–1.4 kpc (Gaia DR3 orbit catalogues in VizieR I/348 and J/A+A/669/A104).
That is a kinematically warm disk star, not a halo star. On its own this is
suggestive rather than decisive, because a minority of stars below
[Fe/H] = −2.5 are on prograde, disk-like orbits (Sestito et al. 2019). The
spectroscopy settles it.

## 2. Metallicity: Gaia GSP-Spec and LAMOST

| source | [M/H] or [Fe/H] |
|---|---|
| **claimed** (Hotnisky et al. 2026) | **−2.83 ± 0.23** |
| Gaia DR3 GSP-Spec `mh_gspspec` (RVS spectrum) | **+0.28** (+0.21 … +0.41) |
| Gaia DR3 GSP-Phot `mh_gspphot` (XP, MARCS) | −0.29 |
| Gaia DR3 GSP-Phot, PHOENIX library | −0.37 |
| Gaia DR3 MSC `mh_msc` | +0.08 |
| Gaia XP (Zhang, Green & Rix 2023) | −0.02 ± 0.04 |
| Pristine synthetic CaHK from XP (Martin et al. 2024) | −0.20 |
| StarHorse EDR3 (Anders et al. 2022) | −0.40 |
| PLATO all-sky target list (XGBoost) | −0.09 |
| other VizieR catalogues (J/ApJ/984/58, J/A+A/685/A59, J/MNRAS/551/G1593) | −0.20, +0.08, +0.25 |
| LAMOST DR8–DR11 low-res spectra within 36″ | **none** |

GSP-Spec does return a value for this star: [M/H] = +0.28. Its quality flag
`flags_gspspec` has `fluxNoise = 1` (moderate noise, as expected at
G = 12.0), and its T_eff of 6371 K is ~400 K hotter than the photometric
values, so +0.28 should not be taken at face value. But the RVS window is the
Ca II triplet, whose lines in a −2.8 dwarf are a small fraction of their
solar strength. GSP-Spec could not fit that spectrum with super-solar
metallicity. Every photometric estimate, including the metallicity-sensitive
CaHK-band synthesis, also lands between −0.4 and +0.1.

LAMOST has not observed the star. The cone searches return nothing in
DR8–DR11, although a control field in the Kepler region returns 48 spectra
from the same service. Section 3 uses the Gaia XP spectrum instead.

There is also an internal consistency problem: the same archive entry gives
M★ = 1.14 M☉ and R★ = 1.28 R☉ at T_eff = 5956 K. A star with [Fe/H] = −2.8 at
that temperature is an old turn-off star of ~0.8 M☉. The quoted mass and
radius fit a roughly solar-metallicity F8–G0 dwarf. See
[Where −2.83 comes from](#where-283-comes-from) above.

## 3. The spectrum: Gaia DR3 XP

LAMOST has no spectrum, but Gaia DR3 does have a low-resolution BP/RP (XP)
spectrum of the star, covering 336–1020 nm. Metal lines blanket the blue, so
at a fixed temperature a very metal-poor dwarf is markedly brighter below
450 nm. `xp_spectrum.py` compares the dereddened target spectrum with XP
spectra of benchmark stars whose metallicities come from high-resolution
spectroscopy, from solar twins down to G 64-12 at [Fe/H] ≈ −3.2.

![XP spectrum comparison](figures/xp_spectrum.png)

- The very metal-poor benchmarks (HD 84937, HD 74000, BD−13 3442, G 64-12)
  have the same red-colour temperature index as the target. They need no
  extrapolation, and all sit at blanketing index 1.18–1.22. The target sits
  at **0.92**, below even HD 209458 ([Fe/H] = 0.00).
- A linear fit (blanketing ∝ T index + [Fe/H]) over the 11 benchmarks
  predicts 1.24 for a [Fe/H] = −2.83 star at the target's temperature. The
  target is 0.31 below that, **6.5× the benchmark scatter** (rms 0.048).
- Inverting the fit gives [Fe/H] ≈ +0.5 (−0.2 to +1.1). The point estimate
  is crude: the solar benchmarks are cooler, so solar metallicity is
  extrapolated. It is consistent with solar and firmly excludes the
  metal-poor regime.

Three planned benchmarks (BD+17 4708, HD 19445, HD 140283) have no published
XP sampled spectrum and are skipped. The benchmark [Fe/H] and T_eff values
are approximate literature values, good to ~0.1 dex and ~100 K.

## 4. Binarity (Gaia RUWE and non-single-star flags)

| diagnostic | value | reading |
|---|---|---|
| RUWE | 1.059 | well below 1.4; good single-star astrometric fit |
| `non_single_star` | 0 | no NSS solution |
| NSS tables (two-body orbit, acceleration, SB, VIM) | no entries | |
| `ipd_frac_multi_peak` | 1 % | no resolved companion in the scans |
| `ipd_gof_harmonic_amplitude` | 0.015 | no sign of a close double |
| `duplicated_source` | False | |
| RV variability: `rv_chisq_pvalue` / `rv_renormalised_gof` | 0.46 / 0.13 | RV constant within errors |
| DSC binary-star probability | 0.0003 | |

There is no sign of binarity. Unresolved light from a companion cannot be
what is corrupting a photometric metallicity here. In any case the Gaia
photometric metallicities are not the problem, since they are near solar.

## Reproducing

```bash
pip install -r requirements.txt
python fetch_data.py   # queries MAST, Gaia archive, LAMOST, NASA Exoplanet Archive, VizieR
python analyze.py      # writes results.json and figures/toomre.png
python xp_spectrum.py  # writes results_xp.json and figures/xp_spectrum.png
```

The cached query results are committed in `data/`, so both analysis scripts run offline.
Kinematics use the Gaia astrometric covariance and RV error (20 000 Monte Carlo
draws), solar motion (11.1, 12.24, 7.25) km/s (Schönrich et al. 2010) and
V_LSR = 233.4 km/s.

## Suggested next step

Send the report in [`report/`](report/email_to_archive.md) to the NASA
Exoplanet Archive helpdesk. A ground-based
spectrum of the Ca II H&K and Mg b regions would add a high-resolution
confirmation, but the existing Gaia data already rule out −2.83.
