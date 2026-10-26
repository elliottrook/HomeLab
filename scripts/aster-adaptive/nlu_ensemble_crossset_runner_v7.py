"""Six-set nested evaluation for token-confidence ensemble v7."""
from __future__ import annotations

import nlu_ensemble_candidate_v7 as candidate
import nlu_ensemble_crossset_runner_v5 as v5


v5.candidate = candidate
v5._bounded_envelope = candidate.bounded_envelope
run = v5.run
nested_evaluate = v5.nested_evaluate


def main() -> int:
    return v5.main()


if __name__ == "__main__":
    raise SystemExit(main())

