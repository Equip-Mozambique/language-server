"""Build an Ollama model from a versioned Modelfile + system prompt markdown.

Usage:
    python -m aiserver.fdv.build v3                    # builds fdv06-v3
    python -m aiserver.fdv.build v3 --name fdv06-v3-x  # custom tag

Renders configs/fdv/Modelfile.<ver> by replacing {{SYSTEM_PROMPT}} with the
content of configs/fdv/system_prompt.<ver>.md (with HTML comments stripped),
then `ollama create`s it.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / "configs" / "fdv"


def load_prompt(version: str) -> str:
    path = CFG / f"system_prompt.{version}.md"
    if not path.exists():
        sys.exit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    return text


def render_modelfile(version: str) -> str:
    mf = CFG / f"Modelfile.{version}"
    if not mf.exists():
        sys.exit(f"missing {mf}")
    template = mf.read_text(encoding="utf-8")
    prompt = load_prompt(version).replace('"""', '\\"\\"\\"')
    return template.replace("{{SYSTEM_PROMPT}}", prompt)


def ollama_create(name: str, modelfile_text: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".Modelfile", delete=False) as f:
        f.write(modelfile_text)
        tmp = f.name
    print(f"ollama create {name} -f {tmp}")
    subprocess.run(["ollama", "create", name, "-f", tmp], check=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("version", help="e.g. v2, v3")
    p.add_argument("--name", default=None)
    p.add_argument("--print", action="store_true", help="print rendered Modelfile, don't build")
    args = p.parse_args()

    rendered = render_modelfile(args.version)
    if args.print:
        print(rendered)
        return

    name = args.name or f"fdv06-{args.version}"
    ollama_create(name, rendered)
    print(f"built {name}")


if __name__ == "__main__":
    main()
