"""Fetch every input for the TIC 219893931 checks and cache it in data/.

Sources: MAST TIC v8.2, Gaia DR3 (gaia_source, astrophysical_parameters,
NSS tables), LAMOST DR8-DR11 cone searches, NASA Exoplanet Archive and a
VizieR cone search for independent metallicity estimates.
"""
import io
import json
from pathlib import Path

import requests
from astropy.io.votable import parse_single_table

TIC_ID = 219893931
GAIA_ID = 1651056179580039424
RA, DEC = 262.56212549988214, 71.84294849488633  # Gaia DR3, epoch 2016.0
DATA = Path(__file__).parent / "data"

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
NEA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
LAMOST_RELEASES = ["dr11/v1.0", "dr10/v2.0", "dr9/v2.0", "dr8/v2.0"]

GAIA_QUERY = f"""
SELECT g.source_id, g.ra, g.dec, g.parallax, g.parallax_error,
       g.pmra, g.pmra_error, g.pmdec, g.pmdec_error, g.pmra_pmdec_corr,
       g.parallax_pmra_corr, g.parallax_pmdec_corr,
       g.radial_velocity, g.radial_velocity_error, g.rv_nb_transits,
       g.rv_chisq_pvalue, g.rv_renormalised_gof, g.rv_amplitude_robust,
       g.rv_template_teff, g.rv_template_fe_h,
       g.ruwe, g.non_single_star, g.ipd_frac_multi_peak,
       g.ipd_gof_harmonic_amplitude, g.duplicated_source,
       g.phot_g_mean_mag, g.bp_rp, g.phot_bp_rp_excess_factor, g.has_rvs,
       g.teff_gspphot, g.logg_gspphot, g.mh_gspphot,
       a.mh_gspphot_lower, a.mh_gspphot_upper,
       a.mh_gspspec, a.mh_gspspec_lower, a.mh_gspspec_upper,
       a.teff_gspspec, a.logg_gspspec, a.flags_gspspec,
       a.mh_msc, a.classprob_dsc_combmod_star,
       a.classprob_dsc_combmod_binarystar
FROM gaiadr3.gaia_source AS g
LEFT JOIN gaiadr3.astrophysical_parameters AS a USING (source_id)
WHERE g.source_id = {GAIA_ID}
"""
NSS_TABLES = ["nss_two_body_orbit", "nss_acceleration_astro",
              "nss_non_linear_spectro", "nss_vim_fl"]


def tap_json(url, query):
    r = requests.get(url, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                  "FORMAT": "json", "QUERY": query}, timeout=300)
    r.raise_for_status()
    return r.json()


def gaia_rows(query):
    js = tap_json(GAIA_TAP, query)
    names = [m["name"] for m in js["metadata"]]
    return [dict(zip(names, row)) for row in js["data"]]


def fetch_gaia():
    star = gaia_rows(GAIA_QUERY)[0]
    nss = {t: len(gaia_rows(f"SELECT source_id FROM gaiadr3.{t} "
                            f"WHERE source_id = {GAIA_ID}"))
           for t in NSS_TABLES}
    return {"source": star, "nss_table_matches": nss}


def fetch_lamost(radius_deg=0.01):
    """LAMOST LRS cone searches; radius 36 arcsec to be generous."""
    out = {}
    for release in LAMOST_RELEASES:
        r = requests.get(f"https://www.lamost.org/{release}/voservice/conesearch",
                         params={"ra": RA, "dec": DEC, "sr": radius_deg}, timeout=300)
        r.raise_for_status()
        table = parse_single_table(io.BytesIO(r.content)).to_table()
        out[release] = [{k: str(row[k]) for k in table.colnames} for row in table]
    return out


def fetch_exoplanet_archive():
    r = requests.get(NEA_TAP, params={
        "query": "select pl_name, default_flag, pl_orbper, pl_rade, pl_radeerr1, "
                 "st_teff, st_tefferr1, st_logg, st_met, st_meterr1, st_metratio, "
                 "st_rad, st_mass, sy_dist, pl_refname, disc_facility, soltype "
                 f"from ps where tic_id = 'TIC {TIC_ID}'",
        "format": "json"}, timeout=300)
    r.raise_for_status()
    return r.json()


def fetch_tic():
    from astroquery.mast import Catalogs
    t = Catalogs.query_criteria(catalog="Tic", ID=TIC_ID)
    cols = ["ID", "GAIA", "Tmag", "Teff", "logg", "MH", "plx", "d", "lumclass"]
    return {c: (None if hasattr(t[c][0], "mask") else t[c][0].item()
                if hasattr(t[c][0], "item") else t[c][0]) for c in cols}


# Independent photometric / spectroscopic metallicities found by a 3" VizieR
# cone search. Keys: catalogue -> metallicity column.
VIZIER_METALLICITY = {
    "I/355/paramsup": "[M/H]-Phx",           # Gaia DR3 GSP-Phot, PHOENIX library
    "I/354/starhorse2021": "met50",          # StarHorse EDR3 (Anders+ 2022)
    "J/MNRAS/524/1855/xpparams": "[Fe/H]",   # Gaia XP, Zhang, Green & Rix 2023
    "J/A+A/692/A115/pristine_gaia": "[Fe/H]ph",  # Pristine synthetic CaHK (Martin+ 2024)
    "J/A+A/692/A150/allskytg": "[Fe/H]",     # PLATO all-sky target list
    "J/ApJ/984/58/table1": "[Fe/H]",
    "J/A+A/685/A59/catalog": "[Fe/H]",
    "J/MNRAS/551/G1593/table1": "[M/H]",
}


def fetch_vizier():
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.vizier import Vizier
    coord = SkyCoord(RA, DEC, unit="deg")
    out = {}
    for cat, col in VIZIER_METALLICITY.items():
        res = Vizier(columns=["**"], row_limit=5).query_region(
            coord, radius=3 * u.arcsec, catalog=cat)
        val = res[0][col][0] if len(res) and len(res[0]) else None
        out[cat] = {"column": col,
                    "value": None if val is None or hasattr(val, "mask") and val.mask
                    else float(val)}
    return out


def main():
    DATA.mkdir(exist_ok=True)
    for name, fn in [("tic", fetch_tic), ("gaia_dr3", fetch_gaia),
                     ("lamost", fetch_lamost), ("exoplanet_archive", fetch_exoplanet_archive),
                     ("vizier_metallicity", fetch_vizier)]:
        print(f"fetching {name} ...")
        (DATA / f"{name}.json").write_text(json.dumps(fn(), indent=2, default=str))


if __name__ == "__main__":
    main()
