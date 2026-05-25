# FDV (Fonte da Vida Bot) — chatbot config

Source-of-truth for the Equip Mozambique WhatsApp Bible-audio chatbot served
via Ollama + Open WebUI on `ai-server`.

## Files

| File | Purpose |
|------|---------|
| `system_prompt.v2.md` | Exact current prompt extracted from `fdv06-v2:latest` (with original truncation bugs preserved — see below). |
| `system_prompt.v3.md` | Cleaned-up prompt: truncations fixed, book code list completed, examples expanded. |
| `Modelfile.v2` | Rebuilds the current model from a vanilla `llama3:8b-instruct-q8_0` base + v2 prompt. |
| `Modelfile.v3` | Same base + v3 prompt. |
| `params.yaml` | Runtime params (temperature, top_p, num_ctx, num_keep, stop tokens, keep_alive). |

## Known bugs in v2 prompt (carried from production)

1. Line 1 truncated: `...utilize a versão Almeida Revi>` — should be `Almeida Revisada e Atualizada` (or `Almeida Revista e Corrigida`).
2. Line ~17 truncated (book code list): `...Daniel: DAN, Ap>` — full 66-book list missing.

**v3 fixes both.** Run an eval pass before promoting.

## Lineage

```
llama3:8b-instruct-q8_0  (Meta, Q8 GGUF, 8.5GB)
  └─ fdv06:latest         (= llama3 + earlier prompt, same digest)
       └─ fdv06-v2:latest (different blob digest — current prod)
```

`fdv05`, `fdv04-julho` are older 3.3B-class lineage (different base, deprecated).

## Build + promote

```bash
# rebuild v2 from clean base (smoke test only — should match prod behaviour)
scripts/fdv_build.sh v2

# build candidate v3
scripts/fdv_build.sh v3

# evaluate v3 against the eval set
scripts/fdv_eval.sh fdv06-v3

# if green: re-tag and switch Open WebUI default model to fdv06-v3
ssh ai-server 'ollama cp fdv06-v3 fdv06-prod'
```

## Fine-tuning paths (ranked)

1. **System prompt + few-shot iteration** — fastest. Edit `system_prompt.v3.md`, rebuild, eval.
2. **RAG via Open WebUI Knowledge** — drop Almeida full text + book lookup table into the Open WebUI knowledge base. Solves bible reference hallucination without training.
3. **QLoRA SFT** — for systemic JSON-format failures or multilingual quality. Use `src/aiserver/fdv/train_lora.py`. 200–500 (user, ideal_response) pairs from WhatsApp logs is enough. Fits comfortably on RTX 4000 Ada 20GB.
4. **DPO** — preference tuning after SFT. Improve "prefer correct ref over hallucination" behaviour.
5. **Base swap** — try Qwen3 8B (already cached as `qwen3.6:35b` ancestor, better PT and Bantu handling than Llama 3).
