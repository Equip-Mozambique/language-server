"""Ndau (ndc) MMS round-trip test — via Shona (sna) proxy.

CORRECTION 2026-05-23: Probed all 3 MMS variants — `ndc` NOT covered for either
ASR or TTS. Fallback: use Shona (`sna`) as cross-lingual proxy since Ndau is in
Shona macrolang. Expect mishandling of Ndau-specific breathy/depressor consonants.
"""

from pathlib import Path

from rich import print as rprint

from aiserver import stt, tts

PROXY = "sna"  # Shona — closest MMS-covered relative


# Mix of greetings/conversational + religious register (matches MMS training domain)
PHRASES = [
    ("Makadii? Ndakaita zvakanaka, ndatenda.", "greeting (Shona-shared form)"),
    ("Mwari anodisa vandhu vese.", "religious — domain match"),
    ("Vana vari kudzidza kuverenga.", "everyday"),
    ("Ndinokuda zvikuru, hama yangu.", "everyday"),
]


def main() -> None:
    out_dir = Path("/tmp/aisrv_ndau")
    out_dir.mkdir(exist_ok=True)

    rprint(f"[bold cyan]Ndau (ndc) round-trip via Shona ({PROXY}) proxy[/bold cyan]")
    rprint(f"  TTS: facebook/mms-tts-{PROXY}")
    rprint(f"  ASR: facebook/mms-1b-all adapter={PROXY}\n")

    for i, (text, note) in enumerate(PHRASES):
        wav = out_dir / f"ndc_{i}.wav"
        rprint(f"[yellow]#{i}[/yellow] [dim]({note})[/dim]")
        rprint(f"  in : {text!r}")

        try:
            tts.synthesize_mms(text, PROXY, wav)
            rprint(f"  wav: {wav} ({wav.stat().st_size} bytes)")
        except Exception as e:
            rprint(f"  [red]TTS failed:[/red] {e}")
            continue

        try:
            asr = stt.transcribe_mms(wav, PROXY)
            rprint(f"  out: {asr!r}\n")
        except Exception as e:
            rprint(f"  [red]ASR failed:[/red] {e}\n")


if __name__ == "__main__":
    main()
