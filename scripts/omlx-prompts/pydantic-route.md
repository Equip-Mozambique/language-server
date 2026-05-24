Write a Python file `<<filename.py>>` containing FastAPI routes. Output Python code only. No markdown fences. No commentary.

Module docstring: """<<one-line module purpose>>"""

Imports (verbatim, in this order):
    from __future__ import annotations
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field
    <<other imports — list each module + symbol explicitly>>

Module-level: `router = APIRouter()`.

Pydantic request model `<<RequestName>>`:
    <<field_name>>: <<type>> = Field(<<constraints>>)
    <<...>>

Pydantic response model `<<ResponseName>>`:
    <<field_name>>: <<type>>
    <<...>>

Route handler:

    @router.<<verb>>("/<<path>>", response_model=<<ResponseName>>)
    async def <<func_name>>(req: <<RequestName>>) -> <<ResponseName>>:
        <<exact docstring>>
        <<numbered behaviour:
        1. Validate ...
        2. Call ...
        3. Map to response>>

Validation error codes:
- 400 for <<condition>> with detail "<<text>>"
- 404 for <<condition>> with detail "<<text>>"
- 413 for <<condition>> with detail "<<text>>"

No `__main__` block. No example usage. No print statements.
