"""Compact DBP coverage summary across all 19 target langs."""

from aiserver import dbp
from aiserver.languages import LANGS


def main() -> None:
    print(f"{'ISO':<5} {'Lang':<22} {'#bibles':<8} {'audio?':<7} {'text?':<6} {'top_audio_fileset'}")
    print("-" * 95)
    for iso, lang in LANGS.items():
        try:
            bibles = dbp.list_bibles(language_code=iso)
        except Exception as e:
            print(f"{iso:<5} {lang.name:<22} ERROR {e}")
            continue
        audio_b = [b for b in bibles if any("audio" in f.set_type_code for f in b.filesets)]
        text_b = [b for b in bibles if any("text" in f.set_type_code for f in b.filesets)]
        top_audio = ""
        if audio_b:
            for f in audio_b[0].filesets:
                if "audio" in f.set_type_code:
                    top_audio = f"{f.fileset_id} ({f.set_size_code} {f.set_type_code})"
                    break
        print(f"{iso:<5} {lang.name:<22} {len(bibles):<8} {len(audio_b):<7} {len(text_b):<6} {top_audio}")


if __name__ == "__main__":
    main()
