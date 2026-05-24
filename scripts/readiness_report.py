"""Print per-language readiness table for all target ISOs.

Columns: ISO · Name · ASR (tier/score) · TTS · Text · Overall · Top gap.
"""

from __future__ import annotations

from rich import print as rprint
from rich.table import Table

from aiserver import readiness
from aiserver.languages import LANGS


def main() -> None:
    t = Table(title="Language readiness (ASR / TTS / Text)")
    for col in ["ISO", "Name", "Country", "ASR", "TTS", "Text", "Overall", "Top gap"]:
        t.add_column(col)

    rows: list[tuple] = []
    for iso, lang in LANGS.items():
        try:
            reports = readiness.readiness_all(iso)
        except Exception as e:
            rows.append((iso, lang.name, lang.country, f"ERR: {e}", "", "", 0, ""))
            continue
        overall = readiness.overall_score(reports)
        top = (
            reports["asr"].missing_resources
            or reports["tts"].missing_resources
            or reports["text"].missing_resources
            or ["—"]
        )[0]
        rows.append((
            iso, lang.name, lang.country,
            f'{reports["asr"].tier.value[:9]}/{reports["asr"].score}',
            f'{reports["tts"].tier.value[:9]}/{reports["tts"].score}',
            f'{reports["text"].tier.value[:9]}/{reports["text"].score}',
            overall, top[:55],
        ))

    rows.sort(key=lambda r: -r[6])  # sort by overall desc
    for r in rows:
        t.add_row(*[str(x) for x in r])
    rprint(t)


if __name__ == "__main__":
    main()
