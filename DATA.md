# Training Data Inventory

Discovered via DBP API + prior research. Updated 2026-05-23.

## DBP Audio Bible Coverage (empirical scan)

Live results from Faith Comes By Hearing Digital Bible Platform v4.

| ISO | Lang | # bibles | Top audio fileset | Scope | Est. hours |
|---|---|---|---|---|---|
| sna | Shona | 5 | SHDBSZN1DA-opus16 | NT | ~25 |
| nde | Ndebele (N. / ZW) | 2 | NDEBSZN2DA | NT | ~25 |
| **nbl** | **Ndebele (S. / ZA)** | **0** | — | — | NCHLT only |
| nya | Chichewa/Nyanja | 5 | NYATWFP1DA | NT portions | ~20 |
| toi | Tonga (ZW) | 1 | TOIBSZN2DA | NT | ~25 |
| kck | Kalanga | 1 | KCKBSBN2SA | NT (stream) | ~25 |
| **nmq** | **Nambya** | **0** | — | — | GRN portions only |
| **ven** | **Venda** | **0** | — | — | NCHLT only |
| tso | Tsonga/Changana | 1 | TS1BSMN2DA | NT | ~25 |
| por | Portuguese | 14 | PORALMO1DA | **OT + NT full** | ~80 |
| vmw | Makhuwa | 1 | VMWBSMN1SA | NT | ~25 |
| seh | Sena | 1 | SEHBSMN1DA-opus16 | NT | ~25 |
| ngl | Lomwe | 2 | NGLBSSN2DA | NT | ~25 |
| **chw** | **Chuwabo** | **0** | — | — | GRN only |
| ndc | Ndau | 1 | NDCBSZN2DA-opus16 | NT | ~25 |
| tsc | Tswa | 1 | TSCBSMN2DA | NT | ~25 |
| rng | Ronga | 1 | RNGSBMN2DA-opus16 | NT | ~25 |
| yao | Yao | 4 | YAOBSMN2DA-opus16 | NT | ~25 |

**DBP totals:** 15 of 19 target langs covered. ~480 hours of read-Bible audio downloadable.

## DBP gaps → alternate sources

| Lang | Alt source | Hours | License |
|---|---|---|---|
| ven (Venda) | NCHLT main + aux (handles `12185/276`, `12185/516`) | ~200 | CC-BY 3.0 |
| ven (Venda) | DSFSI ZA-African-Next-Voices (HF `dsfsi-anv/za-african-next-voices`) | 250 | CC-BY 4.0 (no TTS) |
| nbl (S.Ndebele) | NCHLT-aux (`12185/513`), Lwazi (`12185/457`) | ~200 | CC-BY 3.0 |
| nbl (S.Ndebele) | DSFSI ZA-African-Next-Voices | 250 | CC-BY 4.0 (no TTS) |
| chw (Chuwabo) | GlobalRecordings.net `globalrecordings.net/en/language/chw` | ~2-6 | Free non-commercial |
| nmq (Nambya) | GlobalRecordings.net + TBS portions | ~1-3 | Free non-commercial |

## Bonus DBP discoveries

DBP search also returned audio Bibles for **adjacent** languages we don't target
but could be useful for cross-lingual transfer learning:

- **NYUWYI** — Nyungwe (Mozambique, related to Nyanja/Sena) — 2019 WBT
- **TKEWBT** — Takwane (MZ)
- **KDNBSZ** — Kunda (ZW/Zambia)
- **EKOWBT** — Koti (MZ)
- **MGHWBT** — Makhuwa-Meetto (MZ — close to vmw)
- **CCEFUL** — Chopi (MZ)
- **SWHSUV / SWHBTK** — Swahili (cross-lingual base)
- **WMWWYI** — Coastal Makhuwa variant
- **NYJBIB / NYJNNT** — Nyanja variants

## License & redistribution

DBP/FCBH content: **free for non-commercial research/mission use**. Audio is
copyright FCBH or partner Bible Societies; downloads via DBP API are licensed
for the consumer app or research project specified at key registration.

Cannot legally redistribute the audio files themselves, but **transcripts** are
public domain (Bible text) and **derived models** (fine-tuned ASR weights) are
generally OK as long as the original audio is not redistributed. Confirm w/ FCBH
licensing if intent is commercial deployment.

## Download priorities (next step)

1. **Phase 1** (cheap, fast, no license review): all 15 DBP NT downloads — gets us audio for 15 of 19 targets, ~480h. Run via `scripts/dbp_download.py <iso>`.
2. **Phase 2**: NCHLT for ven + nbl (~400h paired, CC-BY 3.0)
3. **Phase 3**: DSFSI ZA-African-Next-Voices for ven, nbl, tso (~750h, no TTS)
4. **Phase 4**: GlobalRecordings.net scraping for chw, nmq (~5h each)
5. **Phase 5**: Common Voice v20+ for nbl (~few hours, CC-0)

## Storage planning

- 1.7 TB root, 1.4 TB free on server
- ~480h NT mp3 @ 64kbps ≈ 14 GB; @ 16kHz wav ≈ 55 GB
- NCHLT raw ≈ ~40 GB total
- DSFSI Next-Voices ≈ ~100 GB (48kHz wav in parquet)
- Total Phase 1-3 ≈ ~200 GB → fits comfortably
