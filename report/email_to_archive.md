# Draft: report to the NASA Exoplanet Archive

**To:** NASA Exoplanet Archive Helpdesk (https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Helpdesk/nph-genTicketForm)
**From:** Ella Agnes Puerto, Independent researcher, eagnespuerto@gmail.com
**Subject:** Likely erroneous host metallicity for TIC 219893931 b ([Fe/H] = −2.83, Hotnisky et al. 2026)

---

Dear Exoplanet Archive team,

The Planetary Systems table lists TIC 219893931 b (Hotnisky et al. 2026, ApJS 286, 42; arXiv:2606.13789) with a host-star metallicity of st_met = −2.83 ± 0.233 [Fe/H]. If correct, that would make the host one of the most metal-poor planet hosts known. I believe the value is wrong. Every independent check I ran puts the star near solar metallicity:

1. Spectroscopy: Gaia DR3 GSP-Spec, from the RVS spectrum covering the Ca II triplet, gives [M/H] = +0.28 (+0.21/+0.41). Its fluxNoise flag is 1, so the value is noisy, but it cannot be reconciled with −2.8. The star's Gaia XP spectrum lacks the strong blue excess that very metal-poor dwarfs show: it is ~20–25% fainter in 380–450 nm than HD 84937, HD 74000 and BD−13 3442 at the same red colour, and sits with the solar-metallicity benchmarks.
2. Photometric metallicities: Gaia GSP-Phot gives −0.29 and Gaia MSC +0.08. Gaia XP (Zhang, Green & Rix 2023) gives −0.02 ± 0.04, Pristine synthetic CaHK (Martin et al. 2024) −0.20, and StarHorse −0.40. No catalogue I found is below −0.5.
3. Kinematics: Gaia DR3 astrometry and RV give a space velocity of 70 km/s relative to the LSR. The star co-rotates with the disk (V_LSR = −32 km/s), with no sign of halo membership.
4. Binarity: RUWE is 1.06, non_single_star = 0, there are no Gaia NSS solutions, and the RV is constant (p = 0.46). Nothing suggests blended light corrupting the colours.
5. Internal consistency: The archive entry itself lists M★ = 1.14 M☉ and R★ = 1.28 R☉ at T_eff = 5956 K. That fits a roughly solar-metallicity late-F dwarf, not a [Fe/H] = −2.8 turn-off star of ~0.8 M☉. The 2MASS photometry is clean (Qflg AAA, J − Ks = 0.35).

The paper derives [Fe/H] with a random-forest regression on Gaia/2MASS colours trained on LAMOST DR11 labels (Section 2.2), with a uniform ±0.233 dex uncertainty. The archive's error bar matches that. A random forest cannot predict below the lowest metallicity in its training labels, and stars near −2.8 are extremely rare in LAMOST. A value of −2.83 therefore points to a problem in that star's row of the machine-readable Table 1, or in how the archive ingested it, rather than to a real measurement. The paper's own Table 2 does not print [Fe/H], so I could not tell which of the two it is.

Could you check the ingested value against the published table?  The analysis code, cached query results and figures are public: https://github.com/eagnespuerto/low-metal-planet

Thank you for maintaining the archive.

Best regards,
Ella Agnes Puerto
Independent researcher
eagnespuerto@gmail.com
