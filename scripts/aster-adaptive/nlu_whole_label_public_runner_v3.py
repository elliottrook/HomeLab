"""Public gate entry point for whole-label choice v3."""

import nlu_whole_label_choice_v3 as candidate
import nlu_whole_label_public_runner_v1 as base


if __name__ == "__main__":
    raise SystemExit(base.main_for(candidate, "whole-label-choice-v3"))
