"""Doctor adapter with a deterministic cause/repair limitation boundary."""
from __future__ import annotations

import fixed_doctor_usefulness_9b_adapter_v2 as model_adapter


LIMITATION = (
    "This fixed observation alone cannot establish a cause or a repair, and "
    "it does not establish broader system health."
)


def invoke(case: dict, key: str, *, timeout: float = 60, opener=None) -> str:
    answer = model_adapter.invoke(case, key, timeout=timeout, opener=opener).strip()
    if not answer:
        raise ValueError("local model returned an empty answer")
    return answer + "\n\n" + LIMITATION

