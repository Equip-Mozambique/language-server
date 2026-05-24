# omlx prompt templates

Fill-in-blanks templates for delegating mechanical code generation to the
local MLX coder model (`Qwen3-Coder-30B` by default).

## Usage

1. Copy template content. Replace every `<<...>>` placeholder with concrete
   text. Do NOT leave placeholders in the rendered prompt — `omlx` has zero
   repo context and cannot infer.
2. Save the rendered prompt to a temp file, e.g. `work/prompt.txt`.
3. Run:
   ```
   scripts/omlx-write.sh --out path/to/dest.py --prompt-file work/prompt.txt
   ```
4. Wrapper enforces 90s timeout, strips markdown fences, runs ruff/tsc, and
   retries once with error feedback if lint fails.

## Templates

- `pydantic-route.md` — FastAPI route + Pydantic request/response models.
- `test-stub.md` — pytest tests from a function signature + I/O examples.
- `angular-v18-component.md` — standalone Angular 18 component (signals + new
  control flow), pin all syntax to defeat the model's older-Angular bias.
- `sql-ddl-from-pydantic.md` — SQLite CREATE TABLE from a Pydantic model.
- `type-annotate.md` — add type annotations to an existing untyped Python
  module.

## When NOT to use omlx (defer to Claude)

- < 40 LOC (orchestration overhead > savings)
- Async / WebSocket plumbing (race conditions need repo context)
- Security validation (auditable trail must come from Claude)
- Cross-file refactors needing repo grep
- Anything where the existing codebase patterns matter
