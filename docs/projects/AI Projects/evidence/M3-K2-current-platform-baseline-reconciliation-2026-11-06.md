# M3 K2 current platform baseline reconciliation — 2026-11-06

## Result

The first inactive-install preflight was stopped before mutation because the
platform source branch was older than the installed Lab Hours release. The
installed root-custodied release was
`aster-news-video-musetalk-openvino-smoke-v1-b60-fixed-card-capture-v1`
with 53 manifest pins. Its four admission-control identities were:

- `lab_hours_workloads.py`:
  `24ebdcacb4f1a950985360cf400c97742346568b280e30f83c36c12dbb7adf1e`
- `lab_hours_reserved_runner.py`:
  `e7da5a1bdefb02e8611398ea4a6b4f0a3ab30d666a5ca2c867bb01185aded51e`
- `full_inference_lab_runtime.py`:
  `59d3547b2efd291545c143da1b8a48781f31f704845366b60398c49c0c474537`
- `lab_hours_release_manifest.json`:
  `f697e2e085052e5b3b179d74882ebcc3e3bd1f5ce928ed469c23a17a509ac0ee`

The K2 package was rebased onto the exact installed sources rather than
overwriting them. The combined release retains all 53 installed pins and adds
only the three K2 host entry points. Its manifest contains 56 pins. The
inactive installer now accepts only the four exact installed baseline hashes
above and fails closed on any subsequent drift.

The source-exact release test and the focused K2/platform suite pass. No host
file, guest file, booking, timer, lease, process, service or model was changed
during this reconciliation.
