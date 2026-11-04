# SA3 release-manifest EPUB pin install — 2026-11-04

Status: **PASS; installed inactive**

The one-file correction installed without a booking, service restart or
workload effect. It retained predecessor manifest `c970bd70…9886` in
`/var/lib/local-ai-lab/checkpoints/sa3-release-manifest-epub-pin-20261104`
under `root:root 0700`, then installed candidate `4d8e7db2…2b92` as
`root:root 0644`.

The focused target suite passed 22/22. Most importantly, the actual installed
`lab_hours_reserved_runner.load_manifest()` accepted all 34 installed pins and
returned the corrected source/validator hashes `6103da31…13ad` and
`094d588b…bf31`. The lease remained ready and shared state/locks remained
absent.

No failed booking was retried. A future booking remains a fresh one-attempt
service-stop/start decision with current ledger and runtime gates.
