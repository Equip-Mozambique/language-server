# MMS-ASR Fine-tune Recipe (Language-Agnostic)

Reusable playbook for fine-tuning Meta MMS-1B speech-to-text on any of the 18 Equip Mozambique target Bantu languages. Substitute `<ISO>` (e.g. `sna`, `nde`, `tsn`) and source-specific paths throughout.

License: CC-BY-NC 4.0 (MMS base). Project use is non-commercial (Equip Mozambique NGO) so this is fine — see `CLAUDE.md`.

---

## 0. Pre-flight: empirical MMS coverage probe

**Why:** MMS-1162 list membership ≠ working adapter. Many advertised adapters underperform or fail to load. Test before committing to an init strategy.

Script: `scripts/mms_probe.py <ISO>`

- Load `facebook/mms-1b-all` with `target_lang=<ISO>`
- Run inference on 50 random transcribed clips from the cleanest paired corpus (typically AfriVoice if available)
- Compute WER + CER
- Write report → `data/research/<ISO>_mms_baseline.json`

Decision:

| Baseline WER | Init strategy |
|---|---|
| < 30% | Start from stock adapter weights (fast convergence, 5-10k steps) |
| 30-50% | Stock adapter + higher LR / more warmup |
| > 50% or load fails | Train adapter from scratch on base only |

## 1. Master manifest

Script: `scripts/asr_build_manifest.py <ISO>`

Unify all paired-audio sources into `data/manifests/<ISO>_asr.jsonl`:

```json
{
  "audio_path": "/abs/path/to/clip.wav",
  "text": "normalized transcript",
  "duration": 4.38,
  "speaker_id": "...",
  "source": "afrivoice|waxal|dbp_bible|storyrunners|...",
  "split": "train|dev|test"
}
```

Standard source filters:

| Source | Filter | Notes |
|---|---|---|
| AfriVoice (`audio/<ISO>/afrivoice/manifest.jsonl`) | `transcription != null`, duration 1-30s | extract wavs from `Shona/audio_shards/audio_N.tar.xz` lazily into `wavs/` |
| WAXAL / WaxalNLP | duration 1-30s, text not empty | audio in HF cache; absolute-path the symlinks |
| DBP Bible (FCBH) | force-align verse → utterance via MMS aligner | single-speaker — must cap in training mix |
| StoryRunners | already verse-aligned | small, parallel across languages; reserve 100% for test |
| Other (NCHLT, custom) | per-source as needed | — |

**Text normalization** (consistent across all sources):

1. NFKC unicode normalize
2. Lowercase
3. Strip punctuation except apostrophe (Bantu languages use `'` for elision)
4. Collapse whitespace
5. Keep diacritics + tone marks (do NOT strip)

## 2. Speaker-disjoint splits

Speaker-disjoint train/dev/test prevents leakage (same voice in train+test = inflated WER scores).

Algorithm:

1. Collect unique `speaker_id` per source (skip sources where speaker_id is null/single)
2. Hash speaker → bucket: `hashlib.md5(spk).hexdigest()` mod 100 → 0-79 train, 80-89 dev, 90-99 test
3. Single-speaker corpora (DBP Bible): all rows train, OR hold 10% verse-ids for in-domain dev
4. Tiny parallel corpora (StoryRunners): 100% test

Save speaker → bucket map at `data/manifests/<ISO>_speaker_buckets.json` for reproducibility.

Target proportions: ~80% train / ~10% dev / ~10% test of total paired hours.

## 3. Audio prep

Decode on-the-fly in the dataloader — no pre-decode to disk:

- `torchaudio.load(path)` → resample to 16k mono float32
- For AfriVoice tar.xz shards: extract once to `data/audio/<ISO>/afrivoice/wavs/` (or stream via `tarfile`)
- Skip clips outside 1-20s (training stability)

## 4. Training

Script: `scripts/train_mms_asr.py <ISO>`

Core config (defaults, tune per language):

```python
base = "facebook/mms-1b-all"
target_lang = "<ISO>"
adapter_only = True              # freeze base; train CTC head + per-language adapter
lr = 1e-3
warmup_steps = 500
batch_size = 16
grad_accum = 4                   # effective batch 64
max_steps = 20_000               # ~5-8 epochs over 100-200h
mixed_precision = "bf16"
audio_max_sec = 20
ctc_zero_infinity = True
```

Source-mix sampling cap to prevent single-speaker dominance:

```python
per_source_cap_pct = {"dbp_bible": 30, "default": 100}
```

(Bible audio is high quality but one voice; capping prevents over-fit to that prosody.)

Save checkpoint every 2k steps. Eval dev WER. Early-stop patience 3.

VRAM: MMS-1B + adapter, batch 16, 20s clips, bf16 ≈ 14-16 GB. Fits 20GB RTX 4000 Ada.

Tokenizer: MMS ships per-language `vocab.json`. If missing for `<ISO>`, generate from training text (character vocab; reserve `<pad>`, `<unk>`, `|` for word boundary).

## 5. Eval

Script: `scripts/eval_mms_asr.py <ISO>`

Metrics:

- WER + CER overall test set
- WER broken out by source (Bible vs conversational vs read-aloud)
- Per-speaker WER for top-10 test speakers (variance is the real story)
- Worst-50 hypotheses dumped to `eval/<ISO>_worst.tsv` for manual inspection

Report → `data/research/<ISO>_mms_asr_eval.json`. Production target: WER < 10% conversational, < 5% Bible.

## 6. Deliverables (per language)

```
scripts/mms_probe.py
scripts/asr_build_manifest.py
scripts/train_mms_asr.py
scripts/eval_mms_asr.py
data/manifests/<ISO>_asr.jsonl
data/manifests/<ISO>_speaker_buckets.json
models/mms-<ISO>-adapter-v1/
data/research/<ISO>_mms_baseline.json
data/research/<ISO>_mms_asr_eval.json
```

Scripts are reusable across languages — `<ISO>` is a CLI arg, not hardcoded.

## 7. Execution order

1. **Probe** (1h incl debug) → decide adapter init
2. **Manifest build + split** (1-2h, incl tar extract)
3. **Smoke train** (500 steps on 10% data, 30 min) → confirms loss curve + eval pipeline
4. **Full train** (8-16h wall clock)
5. **Eval + worst-case inspection** (1h)

## 8. Per-language notes

Maintain `data/research/<ISO>_notes.md` capturing:

- Sources used + hours
- Speaker count
- Probe baseline WER
- Final eval WER (overall + per-source)
- Known failure modes (e.g. code-switching, tone confusion)

## 9. Risks / standard gotchas

- **Transcript quality**: review 100 random rows per source before training; bad transcripts poison the model worse than missing data
- **License chains**: derived models inherit corpus licenses (CC-BY-SA propagates; CC-BY-NC chained with CC-BY-NC stays CC-BY-NC; non-comm project so safe)
- **Single-speaker dominance**: enforce `per_source_cap_pct` for Bible / single-reader sources
- **MMS adapter absence**: if probe fails, scratch adapter still works but needs 2-3× more data to match
- **Tone-marked orthographies**: confirm tone marks survive normalization; some Bantu langs (Shona standard, Zulu) use little to no tone; others (Tonga) do
- **Class imbalance** in character vocab: rare characters may need oversampling or smoothing
