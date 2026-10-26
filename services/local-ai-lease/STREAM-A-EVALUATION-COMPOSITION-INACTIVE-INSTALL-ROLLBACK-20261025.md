# Stream A evaluation composition — inactive install rollback

Date: 2026-10-25 America/Vancouver  
Result: **ROLLED BACK; NO RUNTIME EFFECT**

Jason approved the revised 13-path inactive installation from source
`37452660`. The transaction created a root-only rollback checkpoint and passed
the clean-archive 95-test source suite. After placement, the mandatory host
import failed before any runtime invocation because
`stream_a_evaluation_evidence_loader.py` could not resolve the already
installed parent-directory module `f2_scheduled_release_candidate` from the
composition-only import path.

The error trap restored the prior observer SHA-256
`70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`,
removed the eight host additions and both additions from each guest, and
retained checkpoint
`/var/lib/local-ai-lab/checkpoints/stream-a-evaluation-composition-37452660-20261026T044009Z`.
Postcheck found all five F6 units disabled/inactive, the whole-host lease
exactly ready, Aster Agent, the accepted llama.cpp/SYCL service, Speech, News
timers, `pvescheduler` and `pvestatd` active, and the approved October 26 F2
timers still enabled/active for 01:15 and 01:20 PDT.

No F6 arm, lease, consumer stop, private-result read, model request, F2 change,
D4 run or M3 run occurred. The failed packet must not be retried. The source
correction must make the host composition dependency-closed or explicitly pin
its existing parent dependency root, then pass a clean target import before a
fresh installation decision.
