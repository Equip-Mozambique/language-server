# Training Language Models for Low-Resource Languages
## A practical guide for Equip Mozambique's audio + text AI program

**Audience:** board members + programmers
**Last updated:** 2026-05-24
**Project:** BatePapo / ai-server (18 Bantu target languages of Zimbabwe & Mozambique)

---

## TL;DR (1 page)

We are building three kinds of AI models for low-resource Bantu languages:

| Model | What it does | What it needs |
|---|---|---|
| **ASR** (speech → text) | Listens to a person speaking, types what they said | Hours of audio paired with text |
| **TTS** (text → speech) | Reads text out loud in the target language | Clean audio recordings (less than ASR) |
| **LM / MT** (language model, translation) | Understands / generates text in the language | Lots of written text |

**Key insight:** Modern multilingual base models (Meta's MMS, OpenAI's Whisper, Meta's NLLB-200) already include some of our target languages. **We don't train from scratch — we fine-tune.** Fine-tuning needs **10-100x less data** than training from scratch.

**Minimum useful data (per language):**

- **ASR:** ~1 hour of paired audio + text (gets a "marginal" model). 10 hours for "usable" (WER < 20%). 50+ hours for "production". [^MMS][^Whisper]
- **TTS:** ~15 minutes of clean audio gets an intelligible voice. 1-3 hours for natural-sounding. [^MMS-TTS][^XTTS]
- **LM:** A complete New Testament (~200k words) is enough to **fine-tune** a multilingual base, but **not enough to train from scratch**. From-scratch needs ≥100M tokens. [^NLLB][^InkubaLM]

**Biggest risk for our project:** Bible audio is **one speaker, slow, formal, religious**. Models trained only on Bible audio fail on real-world conversational speech — typically 2-4× worse word error rate.[^BibleTTS] We need to collect non-Bible speech (news, conversation, sermons) as soon as possible.

**Where we are today (per `aiserver.readiness`):**
- 12 of 18 target languages are in "ADAPTER" tier — can fine-tune existing models
- 4 are in "BOOTSTRAP" or "BIBLELESS" tier — need data collection first
- 0 are in "PRODUCTION" or "MATURE" tier — none ready to deploy without more work

---

## 1. What is a "language model" really?

A model is just a big set of learned numbers (weights) that maps inputs to outputs. For our three model types:

- **ASR** maps audio frames → letters/words.
- **TTS** maps letters/words → audio frames.
- **LM** maps a sequence of words → the most-likely next word.

The numbers are learned by showing the model **examples** (millions or billions of them) and updating the numbers so its guess on each example gets better. This is called **training**.

For **low-resource languages** we don't have millions of examples — often only thousands. So we use **transfer learning**:

1. Start with a model trained on dozens or hundreds of high-resource languages (this is the "base" or "pretrained" model).
2. Continue training on our target language's small dataset. This is **fine-tuning** (a.k.a. "adapter training" for the lightest version).
3. The base provides the language-general knowledge; our small dataset teaches it the specifics.

This is why the choice of base model matters enormously. The best bases for African Bantu languages today:

| Type | Best base model | Languages covered | License |
|---|---|---|---|
| ASR | **Meta MMS-1B-all** | 1,162 langs (≥9 of our 18) | CC-BY-NC 4.0[^MMS] |
| ASR | OpenAI Whisper large-v3 / turbo | ~100 langs (Shona, Chichewa, Portuguese of ours) | MIT[^Whisper] |
| TTS | **Meta MMS-TTS** | ~1,100 separate VITS checkpoints | CC-BY-NC 4.0[^MMS] |
| LM/MT | **Meta NLLB-200** | 200 langs (some of ours) | CC-BY-NC 4.0[^NLLB] |
| LM | Lelapa AI InkubaLM-0.4B | 5 African langs (none of ours) | CC-BY-NC 4.0[^InkubaLM] |
| **LM** | **UBC Serengeti-E250 (encoder) + Cheetah-1.2B (generation)** | **517 African langs — 17 of our 18 covered directly** | Apache-2.0 / research[^Serengeti][^Cheetah] |

---

## 2. ASR (Speech → Text)

### What data we need

**Paired data:** audio file + the exact text of what's said in it. The pairing can be at the level of:
- **Verse** — "this 25-second audio clip = these 2 lines of Bible text" (what we have from Bible.com + DBP)
- **Word** — "at second 3.4 the word `mukororo` starts" (better, requires forced alignment)
- **Phoneme** — finest-grained (rarely worth doing for our targets)

### How much data?

Anchored to empirical results from the MMS paper, Whisper paper, and 2024-25 fine-tuning studies:

| Recipe | Minimum useful (WER < 30%) | "Good" (WER < 20%) | "Production" (WER < 10%) | Source |
|---|---|---|---|---|
| **MMS adapter fine-tune** | ~1 hour paired | 4-10 hours | 20-50 hours | [^MMS][^MMS-adapters] |
| **Whisper large-v3 full fine-tune** | 5-10 hours | 25-50 hours | 100-500 hours | [^Whisper][^Whisper-LoRA] |
| **Whisper LoRA fine-tune** | 5-10 hours | 25-50 hours | 100-200 hours (~5× cheaper compute) | [^Whisper-LoRA-Optuna] |
| **wav2vec2 / XLS-R fine-tune** | 10-20 hours | 40-80 hours | 100-300 hours | [^XLS-R] |
| **Hard floor (any recipe)** | ~1 hour | — | — | [^MMS][^XLS-R] |

> **WER** = Word Error Rate. Lower = better. 30% means roughly 1 in 3 words wrong; 10% is "good for many uses"; under 5% is human-level on clean speech.

### Three rules of thumb the literature is very clear about

1. **More speakers > more hours per speaker.** A 10-hour dataset with 30 different voices beats a 30-hour dataset with 1 voice. The 1-voice model overfits — it works only for that one person.[^Speaker-Count] Bible audio is usually 1 speaker per language — this is a known problem we have to mitigate.

2. **Domain matters as much as volume.** A model trained only on Bible audio will work badly on conversational speech, code-switching, and noisy phone audio. The drop is well documented — see §5.

3. **Forced alignment is cheap and high-value.** If you only have audio + a transcript at the chapter level, run a forced-alignment tool (MMS CTC, aeneas) to get word-level timing first. It typically improves training quality 1.5-2× for free.[^MMS-Aligner]

### What our project has today

- **DBP / FCBH NT audio** for 14 languages: ~25 hours each, single reader, studio-clean
- **StoryRunners "The Promise"** for 13 languages: ~1.7 hours each, professional reader, parallel across languages
- **ScriptureEarth Makonde** NT + Genesis (~143 MB), with verse-aligned text
- **JESUS Film** for 17 languages, ~2 hours each (audio extractable from mp4)

Total fine-tuning material for ASR per language: typically **20-30 hours of Bible-domain audio + 7,957 verses of Bible text**. This puts us in the **ADAPTER** tier for most of our 18 languages — enough to fine-tune MMS adapters or Whisper LoRA, but **not** to deploy as production speech recognition for general conversational use.

---

## 3. TTS (Text → Speech)

### What data we need

Clean studio recordings of one or more speakers reading text, paired with that text. **Quality matters more than quantity for TTS** — 30 min of professionally-recorded studio audio beats 5 hours of phone-quality audio.

### How much data?

| Recipe | Minimum intelligible | "Natural" (MOS ≥ 3.5) | Source |
|---|---|---|---|
| **MMS-TTS VITS (Meta's default)** | **~13 min** of clean Bible audio | 30-60 min | [^MMS][^MMS-TTS] |
| VITS from scratch (single speaker) | 2-5 hours | 10-24 hours (LJSpeech ≈ 23.5h is the reference) | [^Mizo-TTS] |
| Coqui VITS fine-tune on top of MMS | 15-30 min | 1-3 hours | Coqui docs |
| **XTTS-v2 zero-shot voice clone** | **3-8 seconds** of reference audio | 30-60 seconds | [^XTTS] |
| XTTS-v2 fine-tune for new speaker | ~10 minutes | 30 min - 1 hour | [^XTTS-FT] |
| **StyleTTS 2** speaker fine-tune | 21-30 min | ~4 hours | [^StyleTTS2] |

> **MOS** = Mean Opinion Score (1=bad, 5=excellent). 3.5+ is "good enough for most uses".

### Why TTS is the easiest of the three

Modern TTS bases like XTTS-v2 and StyleTTS 2 dramatically reduced the data floor. **XTTS-v2 can clone a voice from 3 seconds.** For us, a 20-hour single-speaker Bible NT recording is **massively over-budget for TTS** — the limit on TTS quality for our languages is not data volume but speaker diversity (only 1 voice) and register diversity (only Bible reading, no conversational prosody).

### What our project has today

For 9 of our 18 target languages, Meta's MMS-TTS already has a published VITS checkpoint. We can run those right now without any training. For the other 9, we have audio that's plenty to fine-tune one of: XTTS-v2, Coqui VITS, or IMS Toucan. **TTS is not the bottleneck.**

---

## 4. LM / MT (Text generation + Translation)

### What data we need

Lots of written text in the target language. For **MT** specifically, **parallel sentences** (e.g. English ↔ Shona) are gold.

### How much data?

| Resource / task | Minimum useful | "High-resource" threshold | Source |
|---|---|---|---|
| **Train a SentencePiece tokenizer** | ~100k tokens (≈ a full NT) | 1-5M tokens | [^SentencePiece] |
| **MT from scratch** | ~10k parallel sentences (barely usable) | 50-100k for coherent output | [^MAFAND][^Masakhane] |
| **MT fine-tuning on NLLB-200** | ~1,000 parallel sentences | 5-20k for measurable gain | [^NLLB] |
| **NLLB-200 "high-resource" classification** | ≥1M aligned sentences vs another language | — | [^NLLB] |
| **Train a small LM from scratch (0.4B params)** | ≥1B tokens (InkubaLM ratio) | not viable below ~100M tokens | [^InkubaLM] |

### The hard truth about Bible-only text

A complete Bible New Testament is ~180k English words (~250-400k Bantu characters depending on the language's morphology[^Bible-Stats]). This is:

- **Enough** to train a tokenizer
- **Enough** to fine-tune a multilingual base like NLLB-200
- **Enough** for adapter-style fine-tuning of a multilingual LLM
- **NOT enough** to train any standalone language model from scratch
- **NOT enough** for high-quality MT — NLLB's own threshold is 1M sentences[^NLLB]

Whole Bible (NT + OT) gives ~3.4× the raw text and **substantially more genre diversity** (poetry, law, narrative, prophecy, wisdom literature). Treat whole-Bible as worth ~5-7× NT in practical corpus value, not just 3.4×.[^Bible-Stats]

### What our project has today

- **Bible.com NT text** scraped for 16 of 18 languages (~7,900 verses each)
- **Total: ~111K verses across 16 languages**
- **Missing entirely:** Chuwabo, Makhuwa (need alternate ISO sources)

This puts us in the **BOOTSTRAP** tier for the LM axis on most languages — enough to fine-tune NLLB-200 for basic MT, not enough for a standalone language model. **Collecting non-religious text (news, social media, conversations) is the single highest-leverage investment for the LM axis.**

### Recommended LM base: UBC Serengeti / Cheetah (Adebara et al., ACL 2023-2024)

The single most important LM finding of this project: **UBC NLP's Serengeti / Cheetah / Toucan family covers 17 of our 18 target languages directly** in its 517-African-language pretraining set.[^Serengeti][^Cheetah][^Toucan]

| Coverage | Our targets |
|---|---|
| ✅ Native pretraining | sna, nde, nbl, nya, toi, kck, ven, tso, vmw, ngl, chw, ndc, tsc, rng, yao (15) |
| ✅ Via close sibling `swk` | seh (Sena-Malawi as proxy) |
| ✅ Via "10 world languages" Wikipedia | por |
| ❌ Not covered | nmq (Nambya) only |

**Recommended LM workflow:**

1. **Encoder tasks** (named-entity recognition, classification, intent, search/RAG embeddings) → fine-tune `UBC-NLP/serengeti-E250` (~277M params, ELECTRA architecture, fits a single 24 GB GPU)
2. **Generation tasks** (summarisation, paraphrase, RAG answer rewriting) → fine-tune `UBC-NLP/cheetah-1.2B` (T5/mT5 seq2seq, same 517-lang coverage)
3. **MT tasks** (translation pairs) → fine-tune `facebook/nllb-200-1.3B` or `-3.3B`, register a new lang code for unseen langs, initialise embeddings from a sibling[^NLLB-FT]
4. **For Nambya specifically** — pivot via Kalanga/Shona using NLLB + Serengeti continued pretraining

**Practical recipe for an NT-only Bantu language:**

```
Step 1: Continued MLM pretraining on target NT text (5-15 epochs, lr=5e-5, batch=16)
Step 2: Augment with related-language NTs from eBible corpus (5-10× more tokens, free)
        - Ndau → add Shona
        - Tswa → add Tsonga + Ronga
        - Lomwe → add Makhuwa
        - Chuwabo → add Makhuwa + Lomwe
        - Nambya → add Kalanga + Shona
Step 3: Fine-tune downstream head on whatever labeled data exists
Step 4: Evaluate on held-out NT pericopes + cross-language transfer baseline
```

Reference notebook: https://github.com/UBC-NLP/serengeti/blob/main/Serengeti_notebook.ipynb

**License nuance:** Repository is Apache-2.0; individual model cards say "research only." For our non-commercial NGO use this is fine; confirm with authors for commercial deployment.

### Other LM bases worth knowing

| Model | Our-target coverage | When to use |
|---|---|---|
| **NLLB-200** (Meta) | 5/18 (sna, nya, ven, tso, por) | Translation; pivoting through major Bantu langs |
| **AfroXLMR-76L** (Davlan) | 6/18 (sna, nya, toi, ven, tso, por) | Strong off-the-shelf NER heads for token-classification tasks[^AfroXLMR] |
| **MADLAD-400** (Google) | 8/18 monolingual data + MT models 3B/7B/10B | Data augmentation; ready MT models[^MADLAD] |
| **InkubaLM-0.4B** (Lelapa AI) | 0/18 directly (Swahili/Yoruba/Xhosa/Hausa/Zulu) | Donor for Ndebele via isiZulu cluster transfer |
| **Aya-101 / Aya-23** (Cohere) | 3/18 (sna, nya, por) | Larger multilingual base; weak on minor Bantu |
| **Gemma 3 / Llama 3.1** | Portuguese only realistically | Use for `por` exclusively — wrong tool for Bantu |

### Hosted alternative — SIL Alpha2 (added 2026-05-25)

Before fine-tuning our own MT or TTS model for a given language, it is worth checking whether SIL's hosted **Alpha2** service already covers it. Alpha2 is a pay-per-use API offering machine translation + text-to-speech across **200+ languages out-of-the-box** and **1,200+ via on-request fine-tuning**, built on top of SIL's open-source **Serval** platform (NLLB-200 backend + minority-language fine-tuning).[^Alpha2][^Serval]

**Pricing (2026-05):** Professional tier $0.002/word (first 1M), $0.001/word thereafter; Custom tier (on-request fine-tunes) $0.01/word (first 1M), $0.005/word thereafter; TTS $0.14–$1.14/minute. Free monthly allocation: 5,000 words MT + 5 minutes TTS. Licensing mixed — most commercial-OK, some non-commercial-only; verify per language before deploy.

**Why it's relevant to this project.**

| Capability | In-house plan in this doc | Alpha2 alternative |
|---|---|---|
| MT for our 18 Bantu targets | Fine-tune NLLB-200 + Serengeti per §4 | Hit API (custom tier if lang not in 200-default) |
| TTS for langs without `mms-tts-<iso>` (nde, nbl, kck, nmq, chw, tsc, toi, ven) | IMS Toucan + collected studio audio | API call, per minute |
| TTS for langs with MMS-TTS (sna, nya, tso, vmw, seh, ngl, rng, ndc, yao, por) | MMS-TTS direct, free + on-server | Redundant — keep MMS-TTS |
| ASR | MMS adapter / Whisper FT (this doc, §2) | **Not in scope — Alpha2 has no STT** |
| Phone / offline deployment | Distilled on-device stack (§7–§8) | Not applicable — hosted only |

**Recommended use in this project's roadmap.**

1. Use the free monthly allocation as a **baseline benchmark** when evaluating our own fine-tuned models — Alpha2 quality is a fair upper-bound for the SIL parallel-data ceiling.
2. Use as **stop-gap TTS** for the 8 languages where no `mms-tts-<iso>` checkpoint exists, while we collect studio audio for proper VITS / Toucan fine-tunes.
3. Watch the [**Serval GitHub repo**](https://github.com/sillsdev/serval) (Apache-2.0) — if hosted API access proves limiting, we can self-host the MT half on ai-server.
4. Coverage of our 18 targets is not publicly enumerated — **submit a contact request to ai@sil.org listing all 18 ISO codes** to get a confirmed coverage + license matrix before committing to API integration.

**What Alpha2 does NOT change in this doc:** ASR is still ours to build (MMS / Whisper FT, §2); the phone / offline / distilled-model story (§7–§8) is unchanged; the Bible-domain bias risk (§5) applies equally to Alpha2 outputs since SIL's training data has the same provenance.

---

## 5. The Bible-text problem (domain bias)

This is the single most important risk to understand. Our entire dataset is derived from Bible translations and audio. That data is:

- **Single-speaker** (one reader per language)
- **Single-register** (formal religious narrative)
- **Single-domain** (no news, sports, cooking, conversation, sermons, social)
- **Studio-recorded** (clean, no background noise)
- **Slow + careful** (Bible readers read deliberately, not at conversational speed)

The **BibleTTS** paper quantified this gap directly. They trained TTS on 33-86 hours of high-quality Bible audio in Yoruba and Hausa, then tested it on:[^BibleTTS]

| Language | In-domain MOS | Out-of-domain MOS | Drop |
|---|---|---|---|
| Yoruba | 4.06 (≈ "natural") | 2.93 (≈ "below acceptable") | **−1.13** |
| Hausa | 3.42 ("good") | 2.34 ("poor") | **−1.08** |

ASR shows the same pattern: Bible-trained models typically degrade **2-4× worse WER** on conversational speech.

**Practical implication for our project:** every per-language readiness report in `aiserver.readiness` raises a `BIBLE_ONLY_DOMAIN_RISK` flag when the corpus is Bible-only. **The first non-Bible audio recording we collect per language is worth more than any additional Bible audio.**

---

## 6. Per-language tier recipes

The project's `readiness.py` module assigns each language to one of six tiers based on a 0-100 score. Recommended recipe per tier:

| Tier | Score | Recipe | Realistic deliverable |
|---|---|---|---|
| **BIBLELESS** | 0-15 | No ML. Document orthography first. | None |
| **BOOTSTRAP** | 15-35 | Tokenizer training. MMS adapter fine-tune attempt. MMS-TTS-style ~13-min VITS. | Proof of concept; low expectations. |
| **EMERGING** | 35-55 | Reliable MMS-TTS voice. MMS-adapter ASR with WER 15-25% in-domain. NLLB-200 fine-tune for MT. | Pilot models, Bible-domain use cases. |
| **ADAPTER** | 55-75 | Whisper LoRA fine-tune. Multi-speaker TTS. **Collect non-religious data.** | Solid in-domain ASR (WER < 15%); usable MT. |
| **PRODUCTION** | 75-90 | Whisper full fine-tune competitive. Real-user deploy with monitoring. | Conversational-grade speech recognition. |
| **MATURE** | 90-100 | Frontier-grade per-language systems. | (No Bantu Bible-driven workflow reaches this.) |

Our 18 target languages distribute (as of 2026-05-24):

| Tier (overall) | Languages |
|---|---|
| ADAPTER (55-75) | (none yet — best is Tonga/Kalanga/Ndau/Tswa at overall=62, ASR adapter tier) |
| EMERGING (35-55) | nde, nya, tso, sna, por, seh, ngl, rng, vmw, ndc, toi, kck, tsc, yao (14) |
| BOOTSTRAP (15-35) | ven, nmq, chw (3) |
| BIBLELESS (0-15) | nbl (1) |

The "fleet status" is visible in real-time at http://eu-ai1:8000/resources (per-language) or via `python scripts/readiness_report.py`.

---

## 7. Building a smaller, Bantu-only model (specialise + shrink)

The full Serengeti-E250 covers 517 African languages. We only need 18. Three options to specialise + shrink:

### Option A — Vocabulary pruning (cheapest, biggest single win)
Serengeti-E250 has a 250k-token vocab. ~70% of its 277M params sit in the embedding matrix. Pruning the tokenizer to only tokens that fire on our 18 languages reduces vocab to ~30-50k → **model drops from 277M to ~110M params** with **zero quality loss** on covered languages.

Tools: `transformers-tokenizer-shrink`, custom script over `tokenizer.train_new_from_iterator()`. ~1-2 days of work.

### Option B — Knowledge distillation (best quality at small size)
Train a smaller "student" model (4-6 transformer layers, 384-dim hidden) to mimic Serengeti-E250's predictions on a corpus of our 18 languages. Standard DistilBERT recipe.[^DistilBERT]

- Student size: **~40-60M params** (~5-7× smaller)
- Quality retention: typically **95-98%** of teacher on covered tasks
- Cost: 1-3 days on RTX 4000 Ada
- Inference: **5-10× faster**

### Option C — Continued pretraining only (specialise, don't shrink)
Keep Serengeti-E250 at 277M but continue MLM pretraining only on our 18 languages. After ~10 epochs the model reallocates weights to our targets and forgets weights for other African languages. Same size, **higher per-language quality**.

### Recommended pipeline (all three combined)
1. **Continued MLM pretraining** on 18-lang NT corpus + eBible siblings (~6-12 hr on server)
2. **Vocab prune** to ~50k tokens (~1 hr, ~110M params)
3. **Distill** to 40-50M student (~2-3 days)

End state: **40-50M-param Bantu-specialised model** with quality matching or exceeding full Serengeti-E250 on our 18 languages. Ships in ~50-150 MB.

### What NOT to do
Train a 50M model **from scratch** on our 18-lang Bible-only corpus (~5M tokens total). Far below the ~100M-token floor for any from-scratch LM.[^InkubaLM] Result would be much worse than fine-tuned Serengeti.

---

## 8. Deploying to phones

Once distilled, the LM, ASR, and TTS models all fit on a phone.

### Size landscape after distillation + INT8 quantization

| Model | Params | FP16 disk | **INT8 disk** | Phone-ready? |
|---|---|---|---|---|
| **TTS** | | | | |
| MMS-TTS per-lang (out of the box) | 36M | ~75 MB | **~40 MB** | ✅ ships now |
| Piper TTS per voice | 5-30M | 10-60 MB | **5-30 MB** | ✅ designed for edge |
| Coqui XTTS-v2 (distilled) | ~80M | 160 MB | **80 MB** | ✅ post-distill |
| **ASR** | | | | |
| Whisper-tiny (English-multilingual) | 39M | 75 MB | **40 MB** | ✅ ships natively on iOS 18 |
| Distil-Whisper FT on Bantu | ~80M | 160 MB | **80 MB** | ✅ comfortable |
| MMS-1B + per-lang adapter | 1B + 2.5M | base too big | base too big | ⚠ adapter only on-device, base on server |
| **LM** | | | | |
| Serengeti-E250 (raw) | 277M | 550 MB | 280 MB | ⚠ borderline; INT4 fits |
| Distilled Bantu-only LM | 40-50M | 100 MB | **50 MB** | ✅ comfortable |
| INT4-quantized distilled LM | 40-50M | — | **~25-30 MB** | ✅ aggressive but workable |

### Phone deployment stack

| Capability | iOS | Android |
|---|---|---|
| LM | CoreML (`.mlpackage`) or MLX-Swift | TFLite / ONNX Runtime Mobile / MLC LLM |
| ASR | `SpeechAnalyzer` (iOS 18+ has Whisper-tiny built-in) + CoreML for our FT | TFLite + AudioRecord (Android speech APIs are weak on Bantu) |
| TTS | CoreML / AVSpeechSynthesizer-compatible engines | TFLite + Oboe (low-latency audio output) |

### Speed expectations on phone

| Hardware | Whisper-tiny INT8 (ASR) | MMS-TTS INT8 | Distilled 50M LM INT8 |
|---|---|---|---|
| iPhone 16 Pro (Neural Engine) | ~7× real-time | ~5× real-time | 200-400 tok/s |
| iPhone 12 (CPU) | ~3× real-time | ~2× real-time | 60-120 tok/s |
| Pixel 9 Pro | ~4× real-time | ~2.5× real-time | 100-250 tok/s |
| Mid-range Android (Snapdragon 7-gen) | ~1.5× real-time | ~1× real-time | 30-80 tok/s |
| Budget Android (~$100) | ~1× real-time | ~0.8× real-time | 15-30 tok/s |

For comparison: human reading ≈ 5 tok/s. Even budget Androids run our distilled LM **3-5× faster than reading speed**.

### Full BatePapo mobile-app bundle estimate

For 6 priority langs (sna, nya, tso, ven, por, ndc):

| Component | Approx size |
|---|---|
| App shell | 30 MB |
| Distilled Bantu LM (50M INT8) | 50 MB |
| Distilled multilingual Whisper-tiny FT | 80 MB |
| 6× MMS-TTS voices INT8 | 240 MB (or stream from server) |
| Bible text (UTF-8 compressed × 6 langs) | 30 MB |
| Audio NT per lang (OPUS-coded, opt-in download) | ~50 MB/lang |
| **Base offline app (6 langs)** | **~430 MB** + optional audio downloads |

Comparable: Google Translate offline pack ~500 MB / 5 langs; Microsoft Translator ~200 MB per lang.

### Mobile use cases this unlocks

✅ **Phone-suitable:**
- Offline Bible audio + sync-highlight verse (TTS + text alignment)
- Voice-search the Bible ("read me Mateu chapter 5") — ASR + LM
- Real-time sentence translation EN ↔ Bantu offline
- Pastor sermon dictation in target language
- Voice-driven Bible memorization games for children
- Field oral-storytelling collection (record + auto-transcribe in remote villages)
- Named-entity highlighting in Bible apps (places, people)
- On-device semantic search ("find the verse that talks about...")

❌ **Stay on server:**
- Long-form sermon transcription
- Multi-speaker diarization
- Long-context chat / RAG over corpora

### Hybrid pattern (recommended for production)
Phone runs on-device for simple tasks + offline use; falls back to **ai-server over network** for hard tasks. This is how Bible.is, YouVersion, and most modern translation apps work.

### Existing reference projects to study
- **Bible.is mobile** — ships per-language audio + text offline
- **YouVersion** — built-in TTS for major langs, cloud-based
- **whisper.cpp** — Whisper-tiny on phone, 2-5× real-time
- **Piper TTS Android** — Piper VITS voices via TFLite[^Piper]
- **MLC LLM** — Phi-3 / Gemma 2B on phones already works
- **Apple Foundation Models** (WWDC 2024) — on-device LM framework

### Realistic project staging

| Phase | Deliverable | Time estimate |
|---|---|---|
| 0 | Server-only BatePapo (current state) | done |
| 1 | Distill 1 language (Shona) end-to-end + iOS + Android reference apps | ~1 month |
| 2 | Add 5 priority langs (nya, tso, ven, por, ndc), field-test w/ local pastors | ~2 months |
| 3 | Add remaining 12 langs, optimize for budget Androids | ~3-6 months |
| 4 | Open-source distillation pipeline for other Bantu groups | ongoing |

---

## 9. Concrete next steps (ranked by impact-per-hour)

1. **Run `scripts/extract_video_audio.py`** — adds ~34 hours of dramatic-narration audio across 17 languages from JESUS Film files we already have. One ffmpeg run.
2. **Forced-align existing DBP NT audio** with Bible.com text using MMS CTC aligner — converts our chapter-level pairs into word-level training material. Big quality multiplier, ~1 day of work.
3. **Collect non-Bible audio for 2-3 priority languages** — even 1 hour per language of news / conversation / sermons breaks the domain-bias ceiling. Target: Shona, Chichewa, Portuguese first (well-supported by Whisper, can use it as a forced transcription source).
4. **Pull SADILaR NCHLT corpus** for Venda + South Ndebele (~200 hours each, CC-BY licensed) — solves our two biggest data gaps in one step.
5. **Run a first MMS adapter fine-tune** on Shona (best-resourced) to measure actual WER on held-out Bible audio. Establishes our project's baseline.
6. **Submit data request to progress.bible** (already done by Jon on 2026-05-24) for detailed per-language translation status data.

---

## 10. What success looks like

- Each of the 18 languages reaches at least the **ADAPTER** tier (currently 0 do).
- For 5-6 priority languages, we reach **PRODUCTION** tier with measurable WER on held-out conversational evaluation sets.
- Our published models are usable by missionaries, churches, educators, and government services. Licensing: weights released under CC-BY-NC matching the source data (non-commercial, mission/research use).
- The project becomes a reference for other Bantu-language groups (Lelapa AI, Masakhane, SADILaR collaborations).

---

## Sources

[^MMS]: Pratap et al. (2023). *Scaling Speech Technology to 1,000+ Languages*. arXiv:2305.13516. https://arxiv.org/pdf/2305.13516
[^MMS-adapters]: Hugging Face. *Fine-Tune MMS Adapter Models for low-resource ASR*. https://huggingface.co/blog/mms_adapters
[^Whisper]: Radford et al. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision*. OpenAI. https://cdn.openai.com/papers/whisper.pdf
[^Whisper-LoRA]: *Fine-tuning Whisper on Low-Resource Languages*. arXiv:2412.15726. https://arxiv.org/html/2412.15726v3
[^Whisper-LoRA-Optuna]: *Low-Resource Speech Recognition by FT Whisper with Optuna-LoRA*. MDPI Applied Sciences 2025. https://www.mdpi.com/2076-3417/15/24/13090
[^XLS-R]: Conneau et al. *XLS-R: Self-supervised Cross-lingual Speech Representation*. Hugging Face fine-tuning blog: https://huggingface.co/blog/fine-tune-xlsr-wav2vec2
[^Speaker-Count]: *Effects of Speaker Count, Duration, and Accent Diversity*. arXiv:2506.04364. https://arxiv.org/abs/2506.04364
[^MMS-TTS]: Pratap et al. (2023). MMS paper §TTS — VITS per-language with ~13 min Bible audio. https://arxiv.org/pdf/2305.13516
[^MMS-Aligner]: Meta MMS forced aligner. Companion to MMS paper. https://github.com/facebookresearch/fairseq/tree/main/examples/mms
[^XTTS]: Casanova et al. (2024). *XTTS: A Massively Multilingual Zero-Shot Text-to-Speech Model*. arXiv:2406.04904. https://arxiv.org/abs/2406.04904
[^XTTS-FT]: Hugging Face norwooodsystems. *Multilingual Voice Cloning with XTTS-v2*. https://huggingface.co/blog/norwooodsystems/multilingual-voice-cloning-with-xtts-v2
[^StyleTTS2]: Li et al. StyleTTS 2. Fine-tuning docs at https://deepwiki.com/yl4579/StyleTTS2/4.3-fine-tuning and DagsHub overview at https://dagshub.com/blog/styletts2/
[^Mizo-TTS]: *Low-Resource VITS — Mizo TTS*. arXiv:2601.02073. https://arxiv.org/pdf/2601.02073
[^BibleTTS]: Meyer et al. (2022). *BibleTTS: a large, high-fidelity, multilingual, and uniquely African speech corpus*. Interspeech 2022. arXiv:2207.03546. https://arxiv.org/abs/2207.03546
[^NLLB]: Costa-jussà et al. (2024). *Scaling Neural Machine Translation to 200 Languages*. Nature. https://www.nature.com/articles/s41586-024-07335-x
[^SentencePiece]: Kudo & Richardson (2018) + 2025 application study to low-resource Dzongkha. arXiv:2509.15255. https://arxiv.org/pdf/2509.15255
[^MAFAND]: Adelani et al. (2022). *MAFAND-MT*. NAACL 2022. https://www.lsv.uni-saarland.de/wp-content/uploads/2022/06/naacl2022_mafand.pdf
[^Masakhane]: Nekoto et al. *Participatory Research for Low-resourced Machine Translation*. arXiv:2010.02353. https://arxiv.org/pdf/2010.02353
[^InkubaLM]: Tonja et al. (2024). *InkubaLM: A small language model for low-resource African languages*. Lelapa AI. arXiv:2408.17024. https://arxiv.org/html/2408.17024v1
[^Serengeti]: Adebara, Elmadany, Abdul-Mageed et al. (2023). *SERENGETI: Massively Multilingual Language Models for Africa*. Findings of ACL 2023. https://arxiv.org/abs/2212.10785 · ACL: https://aclanthology.org/2023.findings-acl.97 · Checkpoints: https://huggingface.co/UBC-NLP/serengeti-E250 · Code + 517-lang list: https://github.com/UBC-NLP/serengeti
[^Cheetah]: Adebara et al. (2024). *Cheetah: Natural Language Generation for 517 African Languages*. ACL 2024. https://arxiv.org/abs/2401.01053 · Checkpoint: https://huggingface.co/UBC-NLP/cheetah-1.2B
[^Toucan]: UBC-NLP. *Toucan: Afrocentric Machine Translation*. https://huggingface.co/UBC-NLP/toucan-1.2B · https://github.com/UBC-NLP/Toucan
[^NLLB-FT]: David Dale. *How to fine-tune a NLLB-200 model for translating a new language*. https://cointegrated.medium.com/how-to-fine-tune-a-nllb-200-model-for-translating-a-new-language-a37fc706b865
[^AfroXLMR]: Alabi et al. *AfroXLMR-76L* (Davlan). https://huggingface.co/Davlan/afro-xlmr-large-76L
[^MADLAD]: Kudugunta et al. (2023). *MADLAD-400: A Multilingual And Document-Level Large Audited Dataset*. arXiv:2309.04662 · https://huggingface.co/datasets/allenai/MADLAD-400 · MT models: `google/madlad400-3b-mt`, `-7b-mt`, `-10b-mt`
[^DistilBERT]: Sanh et al. (2019). *DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter*. arXiv:1910.01108 · HF: https://huggingface.co/docs/transformers/model_doc/distilbert
[^Piper]: Piper TTS — neural text-to-speech designed for Raspberry Pi 4 / Android edge: https://github.com/rhasspy/piper
[^Bible-Stats]: Catholic Resources. *NT statistics (Greek)*. https://catholic-resources.org/Bible/NT-Statistics-Greek.htm · biblememorygoal Bible word counts. https://www.biblememorygoal.com/bible-books-word-count/
[^Alpha2]: SIL Global. *Alpha2 — AI translation + TTS for 1,200+ languages.* https://ai.sil.org/projects/alpha2 · SIL AI projects index https://ai.sil.org/projects · March 2025 announcement https://www.internationalmediaservices.org/imnarchives/march-2025-offerings-from-sil-global-ai
[^Serval]: SIL Global. *Serval — open-source REST API for NLP.* https://ai.sil.org/projects/serval · Source: https://github.com/sillsdev/serval (Apache-2.0). NLLB-200 backend with minority-language fine-tuning + incremental SMT.

### Additional reading

- Joshi et al. (2020). *The State and Fate of Linguistic Diversity*. ACL. — origin of the now-standard "6-class resource taxonomy" (class 0 = no resources … class 5 = English).
- Conneau et al. *Common Voice* (Mozilla) — gold standard for crowd-sourced multilingual ASR data.
- AfriSpeech-200 (Intron Health, 2023). https://arxiv.org/pdf/2310.00274
- DSFSI ZA-African-Next-Voices (2025). https://huggingface.co/datasets/dsfsi-anv/za-african-next-voices — 250-500 hours per language for Venda / Ndebele / Tsonga (CC-BY 4.0; ASR-only license).
- NCHLT Speech Corpus (CSIR / SADILaR). https://repo.sadilar.org/ — ~200 hours each for Venda, S. Ndebele, Tsonga (CC-BY 3.0).

---

## Glossary

- **ASR** (Automatic Speech Recognition) — speech-to-text
- **TTS** (Text-to-Speech) — text-to-speech synthesis
- **LM** (Language Model) — model that understands and generates text
- **MT** (Machine Translation) — translates between languages
- **WER** (Word Error Rate) — fraction of words wrong in a transcript; lower is better
- **MOS** (Mean Opinion Score) — human-rated naturalness, 1-5 scale; higher is better
- **NT / OT** — New Testament / Old Testament
- **Fine-tuning** — continuing training of a pre-existing model on new data
- **LoRA** (Low-Rank Adaptation) — lightweight fine-tuning that updates only a small fraction of weights, ~5× cheaper compute than full fine-tuning
- **Forced alignment** — automatically determining word/syllable timing in an audio file given a transcript
- **MMS** (Massively Multilingual Speech) — Meta's 1,000+ language speech model family
- **NLLB** (No Language Left Behind) — Meta's 200-language MT model
- **XTTS** — Coqui's multilingual zero-shot voice-cloning TTS model
- **CC-BY-NC** — Creative Commons license: free for non-commercial use only
- **VITS** — common TTS model architecture (Variational Inference Text-to-Speech)
- **CTC** (Connectionist Temporal Classification) — alignment loss used in many speech models
