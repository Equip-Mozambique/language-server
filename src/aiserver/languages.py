"""Target language registry and routing decisions.

Each entry maps an ISO code to:
- name (human)
- mms_iso (MMS-1B-all adapter code, or None if not in MMS)
- mms_tts (mms-tts-<code> repo suffix, or None)
- whisper_code (Whisper language code, or None)
- preferred_stt: "whisper" | "mms" | "toucan"
- preferred_tts: "mms" | "piper" | "xtts" | "toucan"
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    iso: str
    name: str
    country: str
    mms_iso: str | None          # adapter in facebook/mms-1b-all (None if absent)
    mms_tts: str | None           # facebook/mms-tts-<code> repo (None if absent)
    whisper_code: str | None      # Whisper language code (None if unsupported)
    preferred_stt: str            # "whisper" | "mms" | "toucan"
    preferred_tts: str            # "mms" | "piper" | "xtts" | "toucan"
    proxy_iso: str | None = None  # cross-lingual fallback ISO if no native model


# MMS coverage verified empirically 2026-05-23 against facebook/mms-1b-all and
# mms-tts-<iso> repos. Many languages from the published MMS paper are NOT in
# the public HF release. Use proxy_iso for cross-lingual fallback.
LANGS: dict[str, Lang] = {
    "sna": Lang("sna", "Shona", "ZW", "sna", "sna", "sn", "whisper", "mms"),
    "nde": Lang("nde", "Ndebele (N.)", "ZW", None, None, None, "toucan", "toucan", proxy_iso="zul"),
    "nbl": Lang("nbl", "Ndebele (S.)", "ZW", None, None, None, "toucan", "toucan", proxy_iso="zul"),
    "nya": Lang("nya", "Chichewa/Nyanja", "ZW/MZ", "nya", "nya", "ny", "whisper", "mms"),
    "toi": Lang("toi", "Tonga", "ZW", None, None, None, "mms", "mms", proxy_iso="nya"),
    "kck": Lang("kck", "Kalanga", "ZW", None, None, None, "toucan", "toucan", proxy_iso="sna"),
    "nmq": Lang("nmq", "Nambya", "ZW", None, None, None, "toucan", "toucan", proxy_iso="sna"),
    "ven": Lang("ven", "Venda", "ZW", None, None, None, "mms", "mms", proxy_iso="sna"),
    "tso": Lang("tso", "Tsonga/Changana", "ZW/MZ", "tso", "tso", None, "mms", "mms"),
    "por": Lang("por", "Portuguese", "MZ", "por", "por", "pt", "whisper", "piper"),
    "vmw": Lang("vmw", "Makhuwa", "MZ", "vmw", "vmw", None, "mms", "mms"),
    "seh": Lang("seh", "Sena", "MZ", "seh", "seh", None, "mms", "mms"),
    "ngl": Lang("ngl", "Lomwe", "MZ", "ngl", "ngl", None, "mms", "mms"),
    "chw": Lang("chw", "Chuwabo", "MZ", None, None, None, "mms", "mms", proxy_iso="seh"),
    "ndc": Lang("ndc", "Ndau", "MZ/ZW", None, None, None, "mms", "mms", proxy_iso="sna"),
    "tsc": Lang("tsc", "Tswa", "MZ", None, None, None, "mms", "mms", proxy_iso="tso"),
    "rng": Lang("rng", "Ronga", "MZ", "rng", "rng", None, "mms", "mms"),
    "yao": Lang("yao", "Yao", "MZ", "yao", "yao", None, "mms", "mms"),
}


def resolve(iso: str) -> tuple[str, str]:
    """Resolve a target ISO to (effective_iso, status).

    status is one of: "native" (model exists), "proxy" (using related lang),
    "missing" (no model and no proxy).
    """
    lang = get(iso)
    if lang.mms_iso or lang.mms_tts or lang.whisper_code:
        return iso, "native"
    if lang.proxy_iso:
        return lang.proxy_iso, "proxy"
    return iso, "missing"


def get(iso: str) -> Lang:
    if iso not in LANGS:
        raise KeyError(f"Unknown language: {iso}. Available: {sorted(LANGS)}")
    return LANGS[iso]


def by_country(country: str) -> list[Lang]:
    return [l for l in LANGS.values() if country in l.country]
