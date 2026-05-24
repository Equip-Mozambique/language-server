Re-output the Python source below with full type annotations added. Output Python code only. No markdown fences. No commentary. Preserve every behaviour exactly — do NOT rename, reorder, refactor, or "improve" code. Only add types.

Rules:
- Add return type annotation to every `def` / `async def`. Use `-> None` if it returns nothing.
- Add parameter annotations to every parameter. Use `Any` only as last resort.
- Add module-level annotations where a variable is later mutated to a different type.
- Use modern syntax: `list[int]` not `List[int]`, `dict[str, Any]` not `Dict[str, Any]`, `str | None` not `Optional[str]`.
- Add `from __future__ import annotations` at the top if not present.
- Do NOT add new imports for types that are already inferable (only add `from typing import Any` etc. if actually used).
- Do NOT add docstrings if absent. Do NOT add comments.
- Preserve every blank line and existing comment exactly.

Source to annotate:

```python
<<paste source here>>
```
