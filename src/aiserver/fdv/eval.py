"""Run an eval JSONL against an Ollama model. Score JSON validity + field match.

Usage:
    python -m aiserver.fdv.eval fdv06-v3
    python -m aiserver.fdv.eval fdv06-v3 --eval data/fdv/eval/real_whatsapp.jsonl

Eval row schema:
    {"id": "...", "input": "user text",
     "expect_json": true,
     "expect": {"book_id": "MAT", ...},        # required fields to match
     "must_contain_any": ["..."]               # if expect_json=false
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVAL = ROOT / "data" / "fdv" / "eval" / "real_whatsapp.example.jsonl"


def query(model: str, prompt: str, host: str) -> str:
    r = httpx.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def score(row: dict, output: str) -> tuple[bool, str]:
    if row.get("expect_json"):
        try:
            obj = json.loads(output.strip())
        except json.JSONDecodeError:
            return False, "invalid_json"
        for k, v in row.get("expect", {}).items():
            if obj.get(k) != v:
                return False, f"mismatch {k}: got {obj.get(k)!r} want {v!r}"
        return True, "ok"
    needles = row.get("must_contain_any", [])
    if needles and not any(n.lower() in output.lower() for n in needles):
        return False, f"missing any of {needles}"
    return True, "ok"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("model", help="Ollama model tag, e.g. fdv06-v3")
    p.add_argument("--eval", type=Path, default=DEFAULT_EVAL)
    p.add_argument("--host", default="http://localhost:11434")
    args = p.parse_args()

    if not args.eval.exists():
        sys.exit(f"missing eval file {args.eval}")

    rows = [json.loads(l) for l in args.eval.read_text().splitlines() if l.strip()]
    print(f"running {len(rows)} eval cases against {args.model}\n")

    passed = 0
    for row in rows:
        out = query(args.model, row["input"], args.host)
        ok, reason = score(row, out)
        passed += ok
        flag = "OK " if ok else "FAIL"
        print(f"[{flag}] {row['id']:10s} {row['input'][:40]:40s} → {reason}")
        if not ok:
            print(f"          got: {out[:200]}")

    pct = 100 * passed // len(rows)
    print(f"\n{passed}/{len(rows)} passed ({pct}%)")
    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
