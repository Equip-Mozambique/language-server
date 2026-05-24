"""CLI: `aisrv` command for STT/TTS ops."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table

from . import stt, tts
from .languages import LANGS

app = typer.Typer(help="ai-server CLI")


@app.command("langs")
def list_langs() -> None:
    """List supported languages and engine routing."""
    t = Table(title="Supported languages")
    t.add_column("ISO")
    t.add_column("Name")
    t.add_column("Country")
    t.add_column("STT")
    t.add_column("TTS")
    for lang in LANGS.values():
        t.add_row(lang.iso, lang.name, lang.country, lang.preferred_stt, lang.preferred_tts)
    rprint(t)


@app.command("stt")
def stt_cmd(audio: Path, lang: str) -> None:
    """Transcribe an audio file in the given language."""
    text = stt.transcribe(audio, lang)
    rprint(f"[bold]{lang}[/bold]: {text}")


@app.command("tts")
def tts_cmd(text: str, lang: str, out: Path = Path("out.wav")) -> None:
    """Synthesize speech from text in the given language."""
    path = tts.synthesize(text, lang, out)
    rprint(f"Wrote [bold]{path}[/bold]")


@app.command("serve")
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    preload: bool = True,
    reload: bool = False,
) -> None:
    """Run the FastAPI HTTP server (tailnet-only by default).

    Bind to 100.94.x.x for Tailscale-only exposure. Default 127.0.0.1 is safe for
    local dev. preload=True warms Whisper + MMS into VRAM on startup.
    """
    import os

    import uvicorn

    if preload:
        os.environ["AISERVER_PRELOAD_MODELS"] = "1"
    uvicorn.run("aiserver.api.app:app", host=host, port=port, reload=reload)


@app.command("gpu")
def gpu() -> None:
    """Show GPU info."""
    import torch

    if not torch.cuda.is_available():
        rprint("[red]No CUDA[/red]")
        return
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        rprint(f"GPU {i}: {p.name}, {p.total_memory / 1e9:.1f} GB, CC {p.major}.{p.minor}")


if __name__ == "__main__":
    app()
