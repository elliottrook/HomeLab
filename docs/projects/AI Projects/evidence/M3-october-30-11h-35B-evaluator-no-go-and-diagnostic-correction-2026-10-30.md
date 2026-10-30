# M3 October 30 11:00 35B evaluator NO-GO and diagnostic correction

Booking `aster-stream-a-m3-35b-20261030-1100` was claimed on time and reached
the fixed guest public evaluator. Read-only supervision confirmed that the
earlier admission, whole-stack drain, exact backup-excluded mount, LXC110
restart, transient 35B health and stable sole GPU-holder gates all passed.

The evaluator returned nonzero. Recovery completed and the root-custodied
terminal recorded `OWNER_TRANSACTION_FAILED_RESTORED` with
`production_restored=true`. No public result was retained. The lease returned
to `ready`; LXC104/110/116, Aster Agent, accepted 9B llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` were healthy; the candidate mount, drain state,
locks and 35B process were absent.

The run exposed a diagnostic-boundary defect rather than another isolation
defect. The guest already stopped on the first incomplete result, but HTTP
status failures collapsed into `engine_error`; the host wrapper then discarded
the guest's bounded stdout whenever its exit status was nonzero. The final
terminal could therefore not distinguish an HTTP request rejection, engine
transport failure or invalid response.

Platform commit `d0ec71e1` fixes that boundary without retaining prompts,
answers, credentials, response bodies or hidden reasoning. It permits only
fixed `http_4xx`, `http_5xx`, `engine_error` and `invalid_response` classes,
plus attempted/valid counts. Arbitrary or malformed output remains fail-closed.
The booked runner accepts the projection only after its own production
restoration postcheck. Source tests pass 18/18; the related wider set passes
40/40; all 32 release pins match.

The inactive installation from platform commit `0207b19e` passed 14/14 host
and 4/4 guest target tests with all 32 installed pins exact. Production was not
restarted and no model request ran during installation. The spent 11:00 booking
was not retried. A fresh booking is required for the next public-gate attempt;
automatic routing remains off and the sealed holdout is unchanged.
