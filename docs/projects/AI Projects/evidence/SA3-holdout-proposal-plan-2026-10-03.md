# SA3 sealed holdout proposal plan

Status: **ASSISTANT-PROPOSED; NO HOLDOUT CASES OR ANSWER KEYS CREATED**

The completed 12-case development corpus is not an evaluation corpus. A later
20-case holdout must be created as a separate sealed batch before any model,
prompt, harness, or provider tuning begins.

For this single-operator lab, the holdout batch will be explicitly limited to
within-lab comparative evidence. It must:

- use sanitized abstractions distinct from the development cases;
- receive a manifest digest before development tuning or evaluation;
- store any answer keys only in the private local custody directory;
- remain outside retrieval, prompt tuning, implementation tuning and provider
  selection until frozen evaluation; and
- carry a non-independent, single-operator limitation in every later report.

No holdout request, label, answer, model input, or evaluation has been created
by this plan.
