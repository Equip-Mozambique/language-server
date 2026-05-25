# FDV RAG corpus

Files to drop into Open WebUI Knowledge collection `fdv-knowledge`. The LLM
retrieves from these per query, reducing bible-ref hallucination without any
training.

## Expected files

| File | Source | Purpose |
|------|--------|---------|
| `almeida_rc.txt` | Almeida Revista e Corrigida (public domain) | Full bible text — query-time retrieval for verse text + cross-ref. |
| `book_id_lookup.md` | Generated from `../training/book_id_lookup.json` | Human-readable book→ID table for retrieval. |
| `faq_pt.md` | Hand-curated FAQ in Portuguese | "How do I use the bot", "what languages", etc. |
| `faq_en.md` | English FAQ | mirror of above. |

## How to load into Open WebUI

1. Open WebUI → Workspace → Knowledge → "+ Create Knowledge"
2. Name: `fdv-knowledge`
3. Upload all files from this directory
4. In the FDV model settings → attach knowledge `fdv-knowledge`
5. Test: ask "qual o versículo de João 3 16" — model should retrieve verse text

## To-do

- [ ] Download Almeida RC text (public domain) → `almeida_rc.txt`
- [ ] Generate `book_id_lookup.md` from the JSON via `src/aiserver/fdv/build.py`
- [ ] Write FAQ docs (~2 pages each, focused on the most common WhatsApp questions)
