# ai-server

Remote GPU box for running LLMs / audio AI workloads.

## Project Use

**NON-COMMERCIAL PROJECT.** Operated by Equip Mozambique (NGO). All work here —
model use, dataset use, fine-tuning, derived weights, deployments — is for
non-commercial research, mission, and civic-good purposes only.

This unlocks:
- **MMS / MMS-TTS** (CC-BY-NC 4.0) — usable directly without licensing negotiation
- **FCBH / Bible.is / DBP audio** — usable under FCBH research/mission terms
- **SeamlessM4T v2** (CC-BY-NC) — usable directly
- **Coqui XTTS-v2** (CPML non-commercial) — usable directly
- **StoryRunners storysets** — usable for non-commercial research
- **DSFSI ZA-African-Next-Voices** — TTS prohibited regardless; ASR fine for research
- **NCHLT / SADILaR** (CC-BY 3.0) — already commercially-permissive

No need to plan a w2v-BERT-from-scratch / VITS-from-scratch alternative.
Disregard "commercial fallback" notes in earlier research; they don't apply.

## Connection

Server reachable via **Tailscale** (preferred) or public DNS.

- **Tailscale name**: `eu-ai1`
- **Public DNS**: `eu-ai1.equipmoz.org`
- **Port**: 10501
- **User**: `audioai`
- **Key**: `~/.ssh/audioai`

SSH alias `ai-server` configured in `~/.ssh/config`:

```
Host ai-server
    HostName eu-ai1.equipmoz.org
    User audioai
    IdentityFile ~/.ssh/audioai
    Port 10501
```

Connect: `ssh ai-server`

Run remote command: `ssh ai-server '<cmd>'`

### Tailscale direct

Via Tailscale hostname (works when both ends on tailnet):

```bash
ssh -p 10501 audioai@eu-ai1
```

Optional: add a second alias for tailnet-only access:

```
Host eu-ai1
    HostName eu-ai1
    User audioai
    IdentityFile ~/.ssh/audioai
    Port 10501
```

## Hardware

- **GPU**: NVIDIA RTX 4000 SFF Ada Generation, 20 GB VRAM
- **Driver**: 595.71.05
- **CUDA**: 12.0 (nvcc)
- **RAM**: 62 GB
- **Disk**: 1.7 TB root, 1.4 TB free
- **CPU arch**: x86_64

## Software

- **OS**: Ubuntu 24.04.4 LTS (kernel 6.8.0-107)
- **Python**: 3.12.3 (`/usr/bin/python3`)
- **Docker**: 29.1.3
- **Ollama**: `/usr/local/bin/ollama` (installed)

## User

- Login: `audioai`
- Home: `/home/audioai`
- Groups: `audioai video users docker render` (GPU + Docker access ready)

## GPU verify

```bash
ssh ai-server nvidia-smi
```

## Sync rules (CRITICAL)

**The server is shared — other programmers work on it directly.** The local
folder is **not** the source of truth.

- `scripts/sync.sh` is **ADD/UPDATE only** (no `--delete`)
- Never run `rsync --delete` against the server
- Never `rm -rf` paths you didn't personally create
- Files renamed/removed locally must be cleaned up manually with explicit SSH
  if removal is actually intended
- The `~/ai-server/data/` directory on the server contains valuable work
  (downloads, research, models) that may not exist locally — treat as read-only
  unless explicitly told otherwise
- Past incidents: sync with `--delete` wiped `.env` (DBP key), then later wiped
  `data/research/progress_bible/` after a successful authenticated fetch

## Common ops

```bash
# Ollama
ssh ai-server 'ollama list'
ssh ai-server 'ollama pull llama3.1:8b'
ssh ai-server 'ollama run llama3.1:8b "prompt"'

# Push local files
rsync -avz ./ ai-server:~/ai-server/

# Reverse tunnel (expose remote port 11434 → local 11434 for Ollama API)
ssh -L 11434:localhost:11434 ai-server
```

## Notes

- Server hosted under `equipmoz.org` infra
- On Tailscale tailnet as `eu-ai1` (use for private/secure access from any tailnet device)
- Port 10501 (non-standard SSH)
- 20 GB VRAM = comfortably runs 7B–13B models quantized; 70B will need heavy quant (Q3/Q2) or CPU offload
