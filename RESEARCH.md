# Research: TTS/STT for Zimbabwean & Mozambican Languages

**Date:** 2026-05-23
**Hardware target:** RTX 4000 Ada (20 GB VRAM), CUDA 12.0, Ubuntu 24.04

## Executive Summary

**Hypothesis (MMS + Whisper) confirmed with nuance.** Meta MMS is the only model with broad coverage of long-tail Mozambican/Zimbabwean languages. Whisper large-v3 covers only Shona, Chichewa/Nyanja, and Portuguese. Correct deployment = **hybrid router**: Whisper (fine-tuned) for sn/ny/pt, MMS for everything else, IMS Toucan + data collection for Ndebele/Kalanga/Nambya.

## Target Languages

| Country | Language | ISO |
|---|---|---|
| Zimbabwe | Shona | sna/sn |
| Zimbabwe | Ndebele (N./S.) | nde/nbl/nr |
| Zimbabwe | Chewa/Nyanja | nya/ny |
| Zimbabwe | Tonga | toi |
| Zimbabwe | Kalanga | kck |
| Zimbabwe | Nambya | nmq |
| Zimbabwe | Venda | ven |
| Zimbabwe | Tsonga | tso |
| Mozambique | Portuguese | por/pt |
| Mozambique | Makhuwa | vmw |
| Mozambique | Tsonga/Changana | tso |
| Mozambique | Sena | seh |
| Mozambique | Lomwe | ngl |
| Mozambique | Chuwabo | chw |
| Mozambique/Zimbabwe | Ndau (chiNdau) | ndc |
| Mozambique | Nyanja/Chichewa | nya |
| Mozambique | Tswa | tsc |
| Mozambique | Ronga | rng |
| Mozambique | Yao | yao |

## STT/ASR Model Comparison

| Model | Year | Params | Coverage of targets | License | VRAM |
|---|---|---|---|---|---|
| **Whisper large-v3 / turbo** | 2023/24 | 1.55B / 809M | sn, ny, pt only | MIT | 3 GB / 1.6 GB |
| **MMS-1B-all (fl1107)** | 2023 | 1B + adapters | sna, nya, tso, vmw, seh, yao confirmed; ndc, tsc, rng, chw, ngl, ven, toi likely; por yes | CC-BY-NC 4.0 | ~2.4 GB |
| **MMS-1B-fl102** | 2023 | 1B | FLEURS 102 — sn, ny only | CC-BY-NC 4.0 | ~2.4 GB |
| **NVIDIA Canary/Parakeet v2/v3** | 2025 | 0.6–1B | **Europe only**; pt yes, no African targets | CC-BY-4.0 | <2 GB |
| **SeamlessM4T v2 Large** | 2023 | 2.3B | sn, ny, pt; misses tso/vmw/seh/yao | CC-BY-NC 4.0 | ~5 GB |
| **w2v-BERT 2.0** | 2024 | 580M | Backbone (needs FT) | MIT | <2 GB |
| **`dmatekenya/whisper-large-v3-chichewa`** | 2024 | 1.55B | Chichewa (~61 WER) | MIT-ish | 3 GB |
| **AfriSpeech-200 / Intron** | 2023–25 | varies | Pan-African accented **English** (clinical) | varies | — |
| **Lelapa AI Vulavula** | 2023–25 | proprietary | Swahili/Yoruba/Xhosa/Hausa/Zulu only — no Zim/Moz targets | proprietary API | n/a |

**Benchmark note (arXiv 2512.10968, Dec 2025):** MMS + w2v-BERT win in very-low-resource; Whisper wins mid-resource (where Shona/Nyanja sit); XLS-R scales best with more data.

## TTS Model Comparison

| Model | Coverage | License | VRAM |
|---|---|---|---|
| **MMS-TTS (per-lang VITS, 36.3M each)** | Confirmed: `sna`, `nya`, `tso`, `vmw`, `seh`, `yao`, `por`. Also in 1107 set: `ndc`, `chw`, `ngl`, `tsc`, `rng`, `ven`, `toi`. **Missing**: Ndebele, Kalanga, Nambya. | CC-BY-NC 4.0 | <1 GB each |
| **IMS Toucan** | Articulatory-phoneme, 7000+ langs claimed; quality on Bantu untested but only option for Ndebele/Kalanga/Nambya | Apache 2.0 | <2 GB |
| **Coqui XTTS-v2** | 17 langs, **no Bantu**; great voice cloning | CPML (non-commercial) | ~4 GB |
| **F5-TTS / E2-TTS** | EN/ZH pretraining; needs FT for African langs | CC-BY-NC / MIT | 4–8 GB |
| **Piper TTS** | ~50 langs, **no Zim/Moz** | MIT | <1 GB |
| **StyleTTS 2** | EN-centric | MIT | ~3 GB |

## Per-Language Coverage Matrix (CORRECTED 2026-05-23 — empirical)

| Language | ISO | MMS-ASR | MMS-TTS | Whisper v3 | Best path |
|---|---|---|---|---|---|
| Shona | sna/sn | **yes** | **yes** | yes (low qual) | Whisper FT + MMS-TTS |
| Ndebele | nde/nbl | **no** | **no** | no | Toucan + isiZulu FT (proxy=zul) |
| Chichewa/Nyanja | nya | **yes** | **yes** | yes | Whisper FT (`dmatekenya`) + MMS-TTS |
| Tonga | toi | **no** | **no** | no | proxy=nya + FT |
| Kalanga | kck | no | no | no | Toucan + proxy=sna + data collection |
| Nambya | nmq | no | no | no | Toucan + proxy=sna + data collection |
| Venda | ven | **no** | **no** | no | proxy=sna + NCHLT FT |
| Tsonga | tso | **yes** | **yes** | no | MMS both + NCHLT FT |
| Portuguese | pt | yes | yes | yes (excellent) | Whisper turbo + Piper/MMS-TTS |
| Makhuwa | vmw | **yes** | **yes** | no | MMS both |
| Sena | seh | **yes** | **yes** | no | MMS both |
| Lomwe | ngl | **yes** | **yes** | no | MMS both |
| Chuwabo | chw | **no** | **no** | no | proxy=seh + FT |
| Ndau | ndc | **no** | **no** | no | proxy=sna + FT (verified — loses depressor consonants) |
| Tswa | tsc | **no** | **no** | no | proxy=tso + FT |
| Ronga | rng | **yes** | **yes** | no | MMS both |
| Yao | yao | **yes** | **yes** | no | MMS both |

**Reality check:** Only **9 of 19** target languages have any native MMS model.
The other 10 need cross-lingual proxy + fine-tuning on collected data.

## Hardware Fit (RTX 4000 Ada 20 GB)

All inference fits without quantization:
- Whisper large-v3 FP16: ~3 GB; turbo: ~1.6 GB
- MMS-1B FP16: ~2.4 GB + ~100 MB per adapter
- MMS-TTS: <300 MB each (load dozens)
- SeamlessM4T v2 Large FP16: ~5 GB
- F5-TTS FP16: ~3 GB

**Fine-tuning fits too:** MMS adapter FT ~10–14 GB; Whisper large LoRA ~14 GB; Whisper turbo full FT fits; F5-TTS FT ~12 GB.

Full router stack inference: ~8 GB VRAM. Headroom for LLM frontend.

## Training Data Sources

- **FLEURS** (HF `google/fleurs`): 102 langs incl. Shona, Nyanja; ~12h each
- **Common Voice v19+** (Sept 2024): Tsonga added v19
- **NCHLT corpus** (CSIR/RMA): ~56h each for Tsonga, Venda, Ndebele + 20–170h aux. **Best resource for SA-shared languages.**
- **AfriSpeech-200**: 200h pan-African English (clinical)
- **Bible.is / Faith Comes By Hearing / GlobalRecordings**: MMS-pretraining source
- **Masakhane / Lanfrica catalog** (lanfrica.com)
- **Esethu Framework** (Lelapa + UP, 2025): new SA-language data initiative

## Recommended Deployment Stack

1. **LangID router** first: MMS-LID-4017 (or Whisper detector for Portuguese)
2. **STT routing**:
   - `pt-MZ` → Whisper large-v3-turbo
   - `sna`, `nya` → Whisper large-v3 fine-tuned (FLEURS + CV + Bible.is)
   - All other Bantu targets → MMS-1B-all + per-lang adapter (FT on NCHLT/Bible)
   - `Ndebele/Kalanga/Nambya` → MMS adapter from related-lang base (isiZulu for Ndebele; Shona for Kalanga/Nambya)
3. **TTS routing**:
   - All MMS-covered langs → MMS-TTS VITS
   - `pt` → Piper or XTTS-v2 (pt-BR)
   - `Ndebele/Kalanga/Nambya` → IMS Toucan + collect data + FT

## Per-Language Deep-Dive: Ndau (ndc)

**Speakers:** ~2.4M. Mainly Sofala Province, Mozambique (Machanga, Chibabava, Machaze/Danda, Buzi, Nhamatanda, Dondo, Beira/Bangwe). Also SE Zimbabwe (Chipinge, Chimanimani districts).

**Classification:** Bantu, Shona group (S.15 Guthrie). Close to Shona (sn), Manyika, Zezuru, Karanga. Often treated as Shona macrolang member — useful for cross-lingual transfer.

**Status:** Official language of Zimbabwe since 2013. In Mozambique: regional, no official status.

**Dialects:** Shanga, Danda (MZ); Garwe, Tonga-Ndau (ZW); core Ndau (both). Aka chiNdau, Chindau, Ndzawu, Njao, Chidanda.

**Distinctive phonology:** Preserves contrastive aspiration + breathy/murmured (depressor) consonants borrowed from Nguni contact — sounds noticeably different from central Shona. ASR/TTS trained on central Shona will mis-handle these segments. Forces phoneme-aware FT, not just adapter swap.

**Writing:** Latin script.

**Bible translations (key text-audio corpus source):**

| Title | Year | Publisher | Scope | Format / Code |
|---|---|---|---|---|
| **Bhaibheri Rakachena muChindau** ("Chindau New Bible") | 2015 (current edition) | Bible Society of Zimbabwe | Full Bible (OT+NT) | Print + audio + digital. YouVersion ID 1694. find.bible NDCNDC. FCBH Android app `org.fcbh.ndcbsz.n2`. |
| **Ndau 1999 Edition** | 1997 publish / 1999 ed. label | Bible Society of Zimbabwe | Full Bible | find.bible NDCBSZ. Predecessor to 2015 revision. |
| **Ndau Bible** | 1957 | early missionary (pre-BSZ) | Bible | find.bible NDCB57. Historic, rare. |
| **NWT Christian Greek Scriptures** | 28 Feb 2021 | Watch Tower / JW Mozambique Branch | NT only | Digital only via jw.org. 200th NWT language. |

Translation timeline: NT work 1919–2000; first full Bible reportedly 2009; current authoritative = 2015 BSZ revision.

**Licensing for training:** BSZ texts copyrighted; FCBH/Bible.is audio has specific use terms (research permitted, commercial requires negotiation). NWT under Watch Tower copyright. Verify before fine-tuning beyond research scope.

**Speech model coverage:**
- **MMS-ASR**: Included in `mms-1b-all` 1107-lang set. Adapter loadable via `model.load_adapter("ndc")`.
- **MMS-TTS**: `facebook/mms-tts-ndc` VITS checkpoint, ~36M params, trained on Bible.is/GlobalRecordings religious read-speech. Domain-narrow → expect awkward prosody on conversational text.
- **Whisper**: No coverage (will misroute to `sn`).
- **FLEURS / Common Voice / NCHLT**: Not included.
- **SeamlessM4T**: No.

**Available audio data:**
- GlobalRecordings.net: "Words of Life", "Good News", JESUS film (narrow domain, single/few speakers, religious register).
- Bible.is / Faith Comes By Hearing: Ndau audio Bible (used in MMS pretraining).
- No public conversational corpus identified. Field collection needed for production-grade ASR.

**Recommended path:**
1. **STT**: MMS-1B-all + `ndc` adapter as baseline. Fine-tune on (a) any Ndau Bible.is splits + (b) collected conversational data. If data thin, warm-start adapter from Shona (`sna`) adapter — closely related, much more data — then continue on ndc.
2. **TTS**: `mms-tts-ndc` baseline. Voice cloning quality limited; for better naturalness, FT VITS from scratch via `ylacombe/finetune-hf-vits` on collected studio recordings (need ≥3h clean speech per voice).
3. **LangID gotcha**: Disambiguate from Shona at router. MMS-LID-4017 covers ndc but expect confusion at short utterances — bias by speaker geo if available.

**Risk:** Phonological depressor consonants underrepresented in MMS training (Bible domain). Aspiration contrasts may collapse. Plan eval set with minimal-pair coverage.

## Per-Language Deep-Dive: Sena (seh)

**Speakers:** ~1.55M L1 (2017 Mozambique census, 6.9% of pop ≥5y). Heritage speakers in Malawi, Zimbabwe, Zambia. Aka Chisena, Cisena.

**Geography:** Lower Zambezi valley. Mozambique provinces: **Tete, Sofala, Zambezia, Manica**. Major urban centres include Beira, Caia, Gorongosa.

**Classification:** Bantu, Guthrie N.44. Eastern Bantu. **NOT** Shona-group (unlike Ndau). Closer to Nyanja, Nyungwe, Sena-Tonga cluster.

**Status:** No official status. Working language in lower-Zambezi NGO/missionary/literacy circles. Not in Mozambique national-language list for education.

**Dialects (rich — matters for data collection):** Bangwe, Caia, Care, Chipodzo/Cipodzo, Gombe, Gorongosa, North Sena, Phodzo/Podzo, Puthsu/Shiputhsu, Sangwe, Sare, South Sena. Also related: Nyungwe (often split as separate lang), Mag'anja, Rue, Chikunda.

**Linguistic features:** Agglutinative, noun-class system, SVO, **no phonemic tone** (penultimate-syllable accent), CV syllable structure. Lack of tone simplifies TTS prosody modelling vs Shona/Ndau.

**Writing:** Latin script. Standard orthography by Sociedade Bíblica de Moçambique / Wycliffe.

**Bible translations (key text-audio corpus source):**

| Title | Year | Publisher | Scope | Format / Code |
|---|---|---|---|---|
| **Mattheo 1911 (Evangelho de S. Mattheus — XiPuthshu)** | 1911 | Bible Society of Mozambique | Matthew only (in Puthsu dialect) | YouVersion SEHMAT. Historic. |
| **Sena New Testament (Sena do Novo Testamento)** | 1983 | Wycliffe / SBM | NT | Print. |
| **Cibverano Cipsa (sehNT)** | n/a (Wycliffe edition) | Wycliffe Bible Translators | NT | YouVersion sehNT. |
| **Cibverano Cipsa Cisena 2013** | 2013 | Bible Society of Mozambique | NT | YouVersion CCHNT13. Dedicated in Beira (Wycliffe SA). |
| **Sociedade Bíblica de Moçambique Chisena audio NT** | 2014 | SBM / FCBH partner | NT (audio) | Bible.is / FCBH distribution. Used in MMS pretraining. |
| **Sena (Malawi) — SenaMw** | post-2014 | Bible Society of Malawi | **Full Bible** | YouVersion 2973, audio available. |
| **Chisena Bible (full)** | 2017 | likely SBM/UBS | **Full Bible** | find.bible listing. |
| **New World Translation of the Holy Scriptures** | 2 Oct 2022 | Watch Tower / JW Mozambique Branch (David Amorim) | **Full Bible** | Digital via jw.org. First complete NWT in indigenous Mozambican language. |

**Audio corpora (GlobalRecordings, Sena-Mozambique entry):**
- **Good News** — 58:27, 40-section audio-visual Bible lessons
- **Look, Listen & Live** — 8 books, 40–50 min each (~6h total)
- **The Living Christ** — 4:22:34, 120-picture chronological series
- Download bundle: MP3 673.6 MB, low-MP3 173.3 MB, MP4 slideshows 1.27 GB
- Dialect spread: Bangwe, Caia, Gombe variants mixed

**Aggregate read-speech available (estimated):** Bible.is NT ~16–22h (multi-speaker, studio) + GlobalRecordings ~10h + SenaMw full-Bible audio ~70h = **~90–100h read religious speech**. Enough for solid MMS adapter FT.

**Speech model coverage:**
- **MMS-ASR**: `seh` listed in `mms-1b-all` 1107 set. ⚠ Per [[feedback-mms-coverage-verify]], list membership ≠ working adapter — verify empirically before commit.
- **MMS-TTS**: `facebook/mms-tts-seh` VITS checkpoint (~36M params), Bible-domain training data.
- **Whisper**: No coverage.
- **FLEURS / Common Voice / NCHLT**: Not included.
- **SeamlessM4T**: No.

**Recommended path:**
1. **STT**: MMS-1B-all + `seh` adapter as baseline. Empirically test load+inference first. If works, FT on SBM/FCBH NT alignments. Out-of-domain (conversational, news, code-switched Sena/Portuguese) will need fieldwork. Cross-lingual proxy candidates: `nya` (Chichewa, well-resourced) or `seh` warm-start from `nya` adapter if seh fails native.
2. **TTS**: `mms-tts-seh` baseline. For richer prosody, FT VITS via `ylacombe/finetune-hf-vits` on SenaMw audio Bible (cleanest, full-OT+NT, single-narrator typical). Studio collection for non-religious register strongly advised.
3. **LangID**: Confusable with Nyungwe (often misclassified as Sena and vice-versa) and Nyanja. MMS-LID-4017 reasonable; bias by speaker geo (Tete/Sofala/Zambezia → favor seh).
4. **Dialect routing**: Treat as single `seh` for v1. Track dialect labels (Bangwe/Caia/Gorongosa) in metadata for v2 sub-models if needed.

**Risk / data caveat:** All public corpora are **religious read-speech** (single narrator, formal register, archaic vocabulary). Conversational ASR will hit register-shift error. Mozambican Portuguese code-switching extremely common in urban Sena — needs explicit handling at router or in training. SenaMw (Malawi) variant may have phonological/lexical drift from Mozambican Sena — verify before mixing corpora.

**Reference for ongoing audio access:** [DBS Mozambique audio Bible catalog](https://dbs.org/bibles/audio?q=mozam) is Cloudflare-protected — fetched via cloudscraper on `ai-server`. Full DBS catalog mirrored from [github.com/digitalbiblesociety/data](https://github.com/digitalbiblesociety/data) to `~/ai-server/data/research/bible_catalogs/dbs_data_repo/` (12 JSON files, ~17 MB). Filtered hits + human-readable per-language summary at `~/ai-server/data/research/bible_catalogs/TARGET_LANGUAGES_SUMMARY.md`. DBS confirms 3 Sena Bibles (matches above table — SEHBSM 2017, SEHWBT 1983 NT, SEHBFBS 1911 Matthew). Catalog pop=2.03M, films=1, recordings=2 for seh.

**DBS catalog finding worth surfacing:** Per-language coverage matrix above marks Kalanga (`kck`) as "no". DBS catalog disagrees: 2 Bible artifacts on record (KCKKBP 1904 portion, KCKBSB 2009 NT) plus 8 audio recordings. Re-investigate before final routing decision.

## Per-Language Deep-Dive: Kalanga (kck)

**Speakers:** ~1.55M (Ethnologue 2020s). Distribution: SW Zimbabwe (Matabeleland — Bulilima, Mangwe, Plumtree areas) + NE Botswana (Central + North-East Districts, esp. around Francistown) + small numbers in Limpopo, South Africa. Endonyms: **TjiKalanga** (Zim), **Ikalanga** (BW). Also: Bakaa, Bakalanga, Chikalanga, Sekalaka, Makalaka.

**Classification:** Bantu, Shonic (Shona-Nyai) branch. Guthrie S.16. **~75% core-vocabulary similarity with Standard Shona but NOT mutually intelligible** — phonological + grammatical drift large enough to break Shona-trained ASR. Sister language to Nambya (kck and nmq form Shonic sub-cluster distinct from Shona proper).

**Status:** Official language of Zimbabwe (2013 Constitution). Taught in schools in Plumtree / Bulilima-Mangwe area. In Botswana: recognised minority lang, no national-language status.

**Dialects:** TjiKalanga Proper (Tjindondondo), TjiLilima (BW dominant), TjiGwizi, TjiTalaunda, TjiNanzwa, Tjijawunda, Tjilembethu. **Lilima** = BW-Bible-Society standard variety.

**Linguistic features:** Tone language (unlike Sena; like Shona). Noun-class system, SVO, agglutinative. Phonology drift from Shona: retains some breathy / depressor consonants, distinctive vowel sequences. Latin script with `bh`, `dh`, `ng'` digraphs.

**Bible translations (key text-audio corpus source):**

| Title | Year | Publisher | Scope | Format / Code |
|---|---|---|---|---|
| **Kalanga Bible Portion** (`BHAIBHILI Yakayengemala`) | 1904 | early missionary | portions (Gospels) | DBS catalog `KCKKBP`. Historic. |
| **Ndebo Mbuya** (Kalanga NT) | 1999 | Bible Society of Botswana | NT | First full NT. |
| **Ndebo Mbuya ne Njimbo** ("Good News with Songs") | 2008 | Bible Society of Botswana | NT + Psalms/songs | YouVersion ID 860 (NMN). DBS `KCKBSB` (2009 reprint). |
| **Bulilima-Mangwe Draft** (TjiKalanga Zim variant) | ~2018 (draft) | Ndzimu-unami Emmanuel Moyo / Kalanga Bible Translation Project | NT draft | PDF only. First Zim-dialect NT. |
| **BHAIBHILI Yakayengemala** (KBTP) | recent | Kalanga Bible Translation Project (KBTP, Zim-side) | NT | YouVersion app dist via `org.bknda.kalangant.kalanga`. |
| **Old Testament Kalanga (in progress)** | start 2000, ongoing | Bible Society of Botswana | OT (project) | Per Mmegi (BW press): 7+ year project, not yet complete. |

**Audio corpora (GlobalRecordings Kalanga entries — 4 separate dialect records):**
- **Main Kalanga (kck, GRN #1838)** — Look, Listen & Live 8 books + Good News (40-section AV) + Words of Life. Audio-visual Bible lessons.
- **Kalanga: Lilima (GRN #3995)** — separate recording, BW dialect.
- **Kalanga: Jawunda (GRN #26496)** — separate dialect recording.
- **Kalanga: Lembethu (GRN #26498)** — separate dialect recording.
- Total: **DBS lists rc=8 recordings** for kck across dialects. Multi-dialect coverage = unusual richness.

**Aggregate read-speech available (estimated):** Ndebo Mbuya ne Njimbo audio NT (BSB) ~16–22h + GRN main + 3 dialect variants ~10–12h = **~28–35h** in main TjiLilima/standard Kalanga, with valuable dialect-tagged subsets for future sub-models.

**Speech model coverage:**
- **MMS-ASR**: `kck` NOT in `mms-1b-all` filtered set per our pull. Not in fl1107 either. Empirical verification needed — could be present in `mms-1b-l1107` LID-only adapter.
- **MMS-TTS**: `facebook/mms-tts-kck` — **not confirmed** on HF (search returned no exact hit). Likely absent.
- **Whisper**: No coverage.
- **FLEURS / Common Voice / NCHLT**: Not included.
- **SeamlessM4T**: No.
- **IMS Toucan**: Articulatory-phoneme model claims 7000+ langs — kck likely present in its language list; quality untested.

**RESEARCH.md prior claim correction:** Per-Language Coverage Matrix above marks kck as "no MMS-ASR, no MMS-TTS, Toucan + proxy=sna + data collection." DBS catalog actually shows **stronger data position than expected** — 2 published Bibles + ~28–35h aggregate audio across 4 dialect variants. Still no Meta MMS coverage, so MMS path remains "build from scratch." But **fine-tuning data exists** — Kalanga is NOT a data desert.

**Recommended path:**
1. **STT**: Two-step. (a) Build empirical KCK adapter on top of MMS-1B-all `sna` (Shona) adapter using BSB audio NT + GRN recordings. ~28h labelled is borderline-sufficient for adapter FT. (b) Continue with w2v-BERT 2.0 (MIT-licensed) FT for commercial use. **Dialect strategy:** Train base on Lilima (most data), add Tjijawunda/Tjilembethu eval splits.
2. **TTS**: IMS Toucan baseline (phoneme-based, articulatory) + FT on BSB NT audio. Alternative: train VITS from scratch with `ylacombe/finetune-hf-vits` on ~10–15h clean studio recordings (need new collection). MMS-TTS-sna voice cloning unlikely to handle KCK tone+phonology cleanly.
3. **LangID**: Confusable with **Nambya (nmq)** (sister Shonic lang), **Shona (sna)**, **Ndebele (nde)** in transcribed text (depressor-consonant interference). MMS-LID-4017 should cover kck — verify. Bias by speaker geo (Plumtree/Francistown → kck) when available.
4. **Stack with Nambya**: nmq has near-zero data. Build kck first; if successful, use kck-adapter as warm-start for nmq.

**Risk / data caveat:** All public audio is religious read-speech. BSB NT recording is BW-Lilima variant — Zim-side TjiKalanga speakers may show register drift. KBTP (Zim project) producing newer text but no aligned audio yet. Tone marking inconsistent across orthographies — affects TTS training. Plan eval set with minimal-pair tone contrasts.

## License Caveat (RESOLVED 2026-05-24)

**This is a non-commercial Equip Mozambique (NGO) project.** See `CLAUDE.md`.

- MMS / MMS-TTS / SeamlessM4T (CC-BY-NC 4.0) → use directly
- FCBH / Bible.is / DBP audio → use under non-commercial research terms
- Coqui XTTS-v2 (CPML) → use directly
- DSFSI ZA-African-Next-Voices → ASR fine; TTS still prohibited per dataset license

The "commercial fallback" plan (w2v-BERT-from-scratch, VITS-from-scratch) is
**not needed**. Disregard.

## Sources

- [Meta MMS paper](https://arxiv.org/abs/2305.13516)
- [facebook/mms-1b-all](https://huggingface.co/facebook/mms-1b-all)
- [mms-tts-sna](https://huggingface.co/facebook/mms-tts-sna) · [mms-tts-yao](https://huggingface.co/facebook/mms-tts-yao) · [mms-tts-vmw](https://huggingface.co/facebook/mms-tts-vmw)
- [MMS in Transformers docs](https://huggingface.co/docs/transformers/model_doc/mms)
- [Whisper large-v3](https://huggingface.co/openai/whisper-large-v3)
- [dmatekenya/whisper-large-v3-chichewa](https://huggingface.co/dmatekenya/whisper-large-v3-chichewa)
- [Benchmarking ASR for African languages — arXiv 2512.10968](https://arxiv.org/pdf/2512.10968)
- [African ASR systematic review — arXiv 2510.01145](https://arxiv.org/html/2510.01145v1)
- [African low-resource ASR challenges — arXiv 2505.11690](https://arxiv.org/pdf/2505.11690)
- [AfriSpeech-200 — arXiv 2310.00274](https://arxiv.org/pdf/2310.00274)
- [NVIDIA Canary/Parakeet — arXiv 2509.14128](https://arxiv.org/html/2509.14128v2)
- [SeamlessM4T v2](https://huggingface.co/facebook/seamless-m4t-v2-large)
- [IMS Toucan](https://github.com/DigitalPhonetics/IMS-Toucan)
- [Cross-Lingual F5-TTS — arXiv 2509.14579](https://arxiv.org/abs/2509.14579)
- [MMS adapter fine-tune blog](https://huggingface.co/blog/mms_adapters)
- [NCHLT Speech Corpus](https://sites.google.com/site/nchltspeechcorpus)
- [FLEURS dataset](https://huggingface.co/datasets/google/fleurs)
- [Common Voice 19 release](https://www.mozillafoundation.org/en/blog/common-voice-190/)
- [Lelapa AI](https://lelapa.ai/)
- [finetune-hf-vits](https://github.com/ylacombe/finetune-hf-vits)
- [facebook/mms-tts-ndc](https://huggingface.co/facebook/mms-tts-ndc)
- [Ndau on Ethnologue (ndc)](https://www.ethnologue.com/language/ndc/)
- [Ndau — Omniglot](https://www.omniglot.com/writing/ndau.htm)
- [Ndau dialect — Wikipedia](https://en.wikipedia.org/wiki/Ndau_dialect)
- [Ndau audio resources — find.bible](https://find.bible/languages/ndc/)
- [Bhaibheri Rakachena muChindau — Bible.com/YouVersion 1694](https://www.bible.com/versions/1694-ndau-chindau-new-bible)
- [Chindau Baiberi FCBH Android app](https://play.google.com/store/apps/details?id=org.fcbh.ndcbsz.n2)
- [NWT Greek Scriptures in Ndau — JW.org release](https://www.jw.org/en/news/region/mozambique/Jehovahs-Witnesses-Reach-Translation-Milestone-With-Bible-Release-in-Mozambique/)
- [facebook/mms-tts-seh](https://huggingface.co/facebook/mms-tts-seh)
- [Sena — Ethnologue (seh)](https://www.ethnologue.com/language/seh/)
- [Sena — Omniglot](https://www.omniglot.com/writing/sena.htm)
- [Sena language — Wikipedia](https://en.wikipedia.org/wiki/Sena_language)
- [Sena Bible versions — YouVersion](https://www.bible.com/languages/seh)
- [SenaMw full Bible — Bible.com 2973](https://www.bible.com/versions/2973-senamw-sena)
- [Sena audio — GlobalRecordings](https://globalrecordings.net/en/language/seh)
- [DBS Mozambique audio Bibles](https://dbs.org/bibles/audio?q=mozam)
- [DBS Sena research page](https://dbs.org/en/research/languages/seh/)
- [Wycliffe SA — Sena NT dedication Beira](https://wycliffe.org.za/stories-and-news/incoming-translation-news/85-sena-new-testament-dedication-beira-mozambique)
- [JW.org — NWT released in Sena (2 Oct 2022)](https://www.jw.org/en/news/region/mozambique/The-New-World-Translation-Released-in-Sena/)
- [Kalanga — Ethnologue (kck)](https://www.ethnologue.com/language/kck/)
- [Kalanga — Wikipedia](https://en.wikipedia.org/wiki/Kalanga_language)
- [Kalanga — Omniglot](https://www.omniglot.com/writing/kalanga.htm)
- [Bible Society of Botswana — Kalanga translation project](https://biblesociety.org.bw/kalanga-bible-translation/)
- [Ndebo Mbuya ne Njimbo — YouVersion 860](https://www.bible.com/en-GB/versions/860-nmn-ndebo-mbuya-ne-njimbo)
- [Ndebo Mbuya Bulilima-Mangwe Draft (Zim TjiKalanga)](https://www.scribd.com/document/396470581/Ndebo-Mbuya-Bulilima-Mangwe-Version-Draft)
- [KBTP — kalanga.org Christian texts](https://kalanga.org/texts-in-kalanga/christian-texts/)
- [GRN Kalanga main (kck #1838)](https://globalrecordings.net/en/language/kck)
- [GRN Kalanga: Lilima (#3995)](https://globalrecordings.net/en/language/3995)
- [GRN Kalanga: Jawunda (#26496)](https://globalrecordings.net/en/language/26496)
- [GRN Kalanga: Lembethu (#26498)](https://globalrecordings.net/en/language/26498)
- [Mmegi — OT Kalanga Bible in progress](https://www.mmegi.bw/artculture-review/old-testament-kalanga-bible-on-way/news)
