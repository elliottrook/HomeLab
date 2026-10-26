"""Public-development runner for deterministic-envelope ensemble v5."""
from __future__ import annotations

import nlu_ensemble_candidate_v5 as candidate
import nlu_ensemble_development_runner_v1 as v1


v1.candidate = candidate
run = v1.run
summarize = v1.summarize


def main() -> int:
    return v1.main()


if __name__ == "__main__":
    raise SystemExit(main())
