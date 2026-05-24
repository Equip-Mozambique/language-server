"""Smoke test: load Whisper-turbo, MMS-ASR, MMS-TTS; synthesize a short clip; transcribe it back."""

from pathlib import Path

from rich import print as rprint

from aiserver import stt, tts


def main() -> None:
    out = Path("/tmp/aisrv_smoke.wav")

    # 1. MMS-TTS: synth a Shona phrase
    sample = "Mhoroi, makadini henyu?"
    rprint(f"[cyan]Synth Shona:[/cyan] {sample!r}")
    tts.synthesize(sample, "sna", out)
    rprint(f"  -> wrote {out} ({out.stat().st_size} bytes)")

    # 2. Whisper STT round-trip on the synth audio
    rprint("[cyan]Transcribe with Whisper (lang=sn):[/cyan]")
    text = stt.transcribe_whisper(out, "sna")
    rprint(f"  -> {text!r}")

    # 3. MMS STT on same audio
    rprint("[cyan]Transcribe with MMS (adapter=sna):[/cyan]")
    text2 = stt.transcribe_mms(out, "sna")
    rprint(f"  -> {text2!r}")

    rprint("[green]Smoke test passed.[/green]")


if __name__ == "__main__":
    main()
