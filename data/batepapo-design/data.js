/* Language data + mock content for the Language Server prototype.
   Coverage flags are illustrative — real production data lives in the FastAPI backend.
   Status: native | proxy | missing
*/

window.LANGUAGES = [
  { iso: "sna", name: "Shona",            country: "ZW",    whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
  { iso: "nde", name: "Ndebele (N.)",     country: "ZW",    whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native", note: "Northern Ndebele, Zimbabwe" },
  { iso: "ndc", name: "Ndau",             country: "ZW/MZ", whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: "sna", status: "proxy"  },
  { iso: "kck", name: "Kalanga",          country: "ZW",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: "nde", status: "proxy" },
  { iso: "nmq", name: "Nambya",           country: "ZW",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: null,  status: "missing" },
  { iso: "toi", name: "Tonga",            country: "ZW",    whisper: true,  mmsAsr: true,  mmsTts: false, nllb: true,  proxy: null,  status: "native" },
  { iso: "ven", name: "Venda",            country: "ZW",    whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
  { iso: "nbl", name: "Ndebele (S.)",     country: "ZW",    whisper: false, mmsAsr: true,  mmsTts: false, nllb: true,  proxy: null,  status: "native", note: "Southern Ndebele" },
  { iso: "nya", name: "Chichewa / Nyanja", country: "MZ",   whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
  { iso: "seh", name: "Sena",             country: "MZ",    whisper: false, mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
  { iso: "vmw", name: "Makhuwa",          country: "MZ",    whisper: false, mmsAsr: true,  mmsTts: true,  nllb: false, proxy: null,  status: "native" },
  { iso: "ngl", name: "Lomwe",            country: "MZ",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: "vmw", status: "proxy" },
  { iso: "chw", name: "Chuwabo",          country: "MZ",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: null,  status: "missing" },
  { iso: "yao", name: "Yao",              country: "MZ",    whisper: false, mmsAsr: true,  mmsTts: true,  nllb: false, proxy: null,  status: "native" },
  { iso: "tso", name: "Tsonga / Changana", country: "MZ",   whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
  { iso: "tsc", name: "Tswa",             country: "MZ",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: "tso", status: "proxy" },
  { iso: "rng", name: "Ronga",            country: "MZ",    whisper: false, mmsAsr: false, mmsTts: false, nllb: false, proxy: "tso", status: "proxy" },
  { iso: "por", name: "Portuguese",       country: "MZ",    whisper: true,  mmsAsr: true,  mmsTts: true,  nllb: true,  proxy: null,  status: "native" },
];

window.PAGES = [
  { id: "live",      label: "Live Transcribe", short: "Live" },
  { id: "file",      label: "Transcribe File", short: "File" },
  { id: "tts",       label: "TTS",             short: "TTS" },
  { id: "resources", label: "Resources",       short: "Refs" },
  { id: "upload",    label: "Upload",          short: "Upload" },
  { id: "inventory", label: "Components",      short: "Kit", devOnly: true },
];

window.MOCK_TRANSCRIPT_LINES_SNA = [
  "Mhoroi, ndinotenda zvikuru kuti mauya kuno nhasi.",
  "Tichakurukura nezve mabhuku matsva atinoshanda nawo.",
  "Pano pane vana vatatu vanoda kudzidza mutauro wedu.",
  "Tinokumbira kuti uvape mukana wekutaura nemumwe nemumwe.",
  "Ndinotenda. Tinosangana zvakare svondo rinotevera.",
];
window.MOCK_TRANSCRIPT_LINES_NDC = [
  "Makadii vakuru? Tati tichagamuchira basa idzva.",
  "Vana vehurevhi vari kuda kudzidza chiNdau zviri sei?",
  "Tine mabhuku matatu okutanga nawo svondo rinotevera.",
  "Hatisati taringa zvinodikanwa zvose, asi tichaedza.",
];
window.MOCK_TRANSLATION_LINES_EN = [
  "Hello, thank you very much for coming here today.",
  "We will discuss the new books we are working with.",
  "There are three children here who want to learn our language.",
  "We ask that you give each of them a chance to speak.",
  "Thank you. We will meet again next week.",
];
window.MOCK_TRANSLATION_LINES_PT = [
  "Olá, muito obrigado por terem vindo cá hoje.",
  "Vamos falar sobre os novos livros com que estamos a trabalhar.",
  "Há três crianças aqui que querem aprender a nossa língua.",
  "Pedimos que dêem a cada uma a oportunidade de falar.",
  "Obrigado. Voltamos a encontrar-nos na próxima semana.",
];

window.MOCK_BIBLE_CATALOG = {
  sna: [
    { id: "BSZ", title: "Bible Society of Zimbabwe — Union Shona",   vern: "Bhaibheri Magwaro Matsvene", year: 1949, country: "ZW" },
    { id: "BSC", title: "Contemporary Shona Bible",                  vern: "Bhaibheri Idzva muChiShona",  year: 2002, country: "ZW" },
    { id: "SDA", title: "Shona Common-Language NT",                  vern: "Testamende Itsva",             year: 1989, country: "ZW" },
  ],
  ndc: [],
  seh: [
    { id: "SEH-NT", title: "Sena New Testament",                     vern: "Testamento Yatsopa",           year: 2014, country: "MZ" },
  ],
};
window.MOCK_BIBLE_AUDIO = {
  sna: [
    { id: "SNAWBT", name: "Wycliffe Shona Audio Bible", scope: "Full",  filesets: [
      { id: "snawbt-nondrama", label: "Non-drama, 16 kHz", status: "downloaded", chapters: 1189, size: "1.4 GB" },
      { id: "snawbt-drama",    label: "Drama, 22 kHz",     status: "not-downloaded", chapters: 1189, size: "2.1 GB" },
    ]},
    { id: "SNAOBT", name: "Oral Bible — Shona NT",        scope: "NT",   filesets: [
      { id: "snaobt-oral",     label: "Oral retelling",    status: "partial", chapters: 264, totalChapters: 416, size: "780 MB" },
    ]},
  ],
  ndc: [],
  seh: [
    { id: "SEHWBT", name: "Sena Audio NT", scope: "NT", filesets: [
      { id: "sehwbt-nd", label: "Non-drama, 16 kHz", status: "not-downloaded", chapters: 416, size: "520 MB" },
    ]},
  ],
};

window.MOCK_UPLOADED_CORPUS = {
  sna: [
    { id: "a1f2", filename: "harare_radio_2024-08-12.wav", speaker: "MM-014", dialect: "Karanga",  register: "news",          license: "CC-BY-NC", uploaded: "2024-08-12", duration: "12:04" },
    { id: "b3c4", filename: "church_recording_seke.wav",   speaker: "VL-009", dialect: "Zezuru",   register: "religious",     license: "CC-BY",    uploaded: "2024-08-09", duration: "47:21" },
    { id: "d5e6", filename: "kitchen_chat.m4a",            speaker: "RN-021", dialect: "Manyika",  register: "conversational",license: "CC-BY",    uploaded: "2024-07-28", duration: "08:42" },
    { id: "f7g8", filename: "schoolbook_ch1.wav",          speaker: "MM-014", dialect: "Karanga",  register: "read",          license: "CC0",      uploaded: "2024-07-21", duration: "06:11" },
  ],
  ndc: [
    { id: "n1d2", filename: "chimanimani_interview.wav",   speaker: "TH-003", dialect: "Ndau-Hlanganu", register: "conversational", license: "CC-BY", uploaded: "2024-08-02", duration: "23:08" },
  ],
  seh: [],
};

window.MOCK_DIALECT_SUGGESTIONS = {
  sna: ["Karanga", "Zezuru", "Manyika", "Korekore", "Kalanga"],
  ndc: ["Ndau-Hlanganu", "Ndau-Danda", "Garwe", "Tonga-Ndau"],
  seh: ["Bangwe", "Caia", "Gorongosa", "Podzo", "Cuabo-Sena"],
  nya: ["Nyanja", "Chewa", "Manganja"],
  vmw: ["Emakhuwa", "Esaaka", "Elomwe-Makhuwa"],
};

window.MOCK_RESEARCH_MD = {
  sna: `## Overview

Shona (chiShona; ISO 639-3 \`sna\`) is a Bantu language of the **Southern Bantu, Shona (S.10)** group spoken primarily in Zimbabwe by approximately 13 million native speakers. It functions as the principal language of communication in central, eastern, and northern Zimbabwe, and serves as a national language alongside Ndebele and English.[^1]

The language is best understood as a cluster: a **standardised written form** based largely on Zezuru, and a continuum of mutually-intelligible spoken dialects. Doke's 1931 unification effort (the "Doke Report") established the orthographic basis still in use today.[^2]

## Dialect groupings

| Dialect | Region | Approx. speakers | Notes |
|---|---|---|---|
| Zezuru   | Harare, Mashonaland | 5.3 M | Basis of standard written form |
| Karanga  | Masvingo, Midlands  | 4.1 M | Southern; ⟨ɓ⟩ allophone preserved |
| Manyika  | Manicaland          | 1.8 M | Strong influence from Ndau |
| Korekore | Mash. Central / North | 1.2 M | Tonal pattern differs |
| Ndau     | SE Zimbabwe / W. Moz | 1.4 M | Often treated as separate language (\`ndc\`) |

> Ndau is variably classified as a Shona dialect or a separate language. Equip's policy is to treat it as a separate ISO entry but **proxy ASR/TTS to Shona** until native models are available.

## Phonology notes

The Shona consonant inventory is famously dense, with both **whistled fricatives** and **labialised velars**. Standard orthography uses digraphs that ASR tokenisers should be configured to handle as single units:

- \`sv\` (whistled /s̩/), \`zv\` (whistled /z̩/), \`tsv\`, \`dzv\`
- \`bw\`, \`pw\` (rounded labials)
- \`ng'\` (velar nasal, distinct from \`ng\`)

Whisper's BPE tokenisation handles most of these acceptably, though \`ng'\` is consistently rendered as \`ng\` and must be post-corrected.

### Tone

Shona is a **two-tone (H/L)** language with limited grammatical tone marking in writing. ASR systems do not currently encode tone; downstream MT systems should not be expected to resolve tonal minimal pairs (e.g. *báda* "rib" vs *bàdá* "be wicked").

## ASR coverage

OpenAI Whisper supports Shona officially since v3 (Sep 2023). MMS-ASR provides word-level alignment via the Meta MMS-1B checkpoint. **Empirically**, on the Equip evaluation set:

- Whisper-large-v3: 14.2% WER on read speech, 28.1% on conversational
- MMS-1B-all: 19.7% WER on read, 31.4% on conversational
- Whisper performs better on EN/SN code-switched audio (common in urban Harare)

## TTS coverage

MMS-TTS Shona is supported. Voice is **female, neutral register**, somewhat formal. Field workers have reported acceptable intelligibility for read text but noticeable artefacts on long compound words.

## Translation

NLLB-200 supports the \`sna_Latn\` direction. Quality varies dramatically by domain — religious and news domains perform well (BLEU > 22 against the FLORES devtest), while conversational and code-switched input degrades sharply.

## Footnotes

[^1]: Ethnologue (27th ed., 2024). *Shona*.
[^2]: Doke, C.M. (1931). *Report on the unification of the Shona dialects*. Government Stationery Office.`,
  ndc: `## Overview

Ndau (chiNdau; ISO 639-3 \`ndc\`) is a Bantu language spoken in **southeastern Zimbabwe (Chipinge, Chimanimani, parts of Buhera)** and across the border in **Mozambique (Manica, Sofala)**. Estimated speakers: 1.4 million.

It is often classified as a dialect of Shona, but native speakers and Mozambican government policy treat it as a distinct language. Equip Mozambique follows the latter convention.

## Proxying strategy

Because **no native ASR or TTS** models exist for Ndau, the Language Server proxies to **Shona (\`sna\`)** for both ASR transcription and TTS synthesis. This works tolerably for read speech but degrades for:

- Lexical items unique to Ndau (esp. Portuguese loans in Mozambican Ndau)
- Conversational fast speech, where vowel devoicing differs
- Code-switching with Portuguese (very common in Mozambique)

> Field workers should manually correct transcripts produced via the proxy, especially proper nouns and place names.

## Dialects

- **Ndau-Hlanganu** — central Chipinge
- **Ndau-Danda** — Buhera border
- **Garwe** — northern, transitional to Manyika
- **Tonga-Ndau** — Sofala lowlands, heavy Portuguese influence

## Open work

1. Collect 100 h of conversational Ndau for an MMS-style fine-tune.
2. Pilot a transliteration step before passing audio to Shona ASR.
3. Document Portuguese loan inventory for code-switch handling.`,
  seh: `## Overview

Sena (ciSena; ISO 639-3 \`seh\`) is spoken along the **Zambezi valley in central Mozambique** (Sofala, Tete, Manica, Zambezia provinces). Speakers: ~1.6 million.

It is part of the **N.40 Senga–Sena** group, closely related to Nyungwe, Cuabo, and Manganja.

## Dialects

| Dialect | Region | Notes |
|---|---|---|
| Bangwe   | Sofala lowlands | Coastal influence |
| Caia     | Caia district   | Central, often treated as standard |
| Gorongosa | Gorongosa massif | Tone system differs |
| Podzo    | Zambezi delta   | Strong Portuguese contact |
| Cuabo-Sena | Northern transition | Heavy lexical mixing |

## ASR / TTS status

MMS-ASR and MMS-TTS both support Sena natively. Whisper does **not** support Sena directly; we attempt EN-target translation via Whisper-large-v3 in \`translate\` mode, but accuracy is poor — recommended fallback is MMS-ASR + NLLB.`,
  default: `## Overview

Research notes for this language are still being compiled. The page will populate as field researchers contribute findings.

If you have notes, please attach them to a JIRA ticket and tag \`equipmoz-linguistics\`.`,
};

window.MOCK_RESEARCH_TOC = {
  sna: ["Overview", "Dialect groupings", "Phonology notes", "ASR coverage", "TTS coverage", "Translation", "Footnotes"],
  ndc: ["Overview", "Proxying strategy", "Dialects", "Open work"],
  seh: ["Overview", "Dialects", "ASR / TTS status"],
  default: ["Overview"],
};

window.MOCK_TTS_SAMPLES = [
  { id: "t1", text: "Mhoroi, ndinotenda kuti mauya nhasi.", lang: "sna", duration: "0:04", at: "2 min ago" },
  { id: "t2", text: "Tinosangana zvakare svondo rinotevera.", lang: "sna", duration: "0:03", at: "8 min ago" },
  { id: "t3", text: "Vana vehurevhi vari kudzidza zvakanaka.", lang: "sna", duration: "0:05", at: "1 hr ago" },
];

window.MOCK_SPEAKER_IDS = {
  sna: ["MM-014", "VL-009", "RN-021", "AB-007", "TC-018"],
  ndc: ["TH-003", "MK-001"],
  seh: ["JS-002", "AP-005"],
};

// Helper
window.getLang = (iso) => window.LANGUAGES.find(l => l.iso === iso);
window.getResearch = (iso) => window.MOCK_RESEARCH_MD[iso] || window.MOCK_RESEARCH_MD.default;
window.getResearchToc = (iso) => window.MOCK_RESEARCH_TOC[iso] || window.MOCK_RESEARCH_TOC.default;
