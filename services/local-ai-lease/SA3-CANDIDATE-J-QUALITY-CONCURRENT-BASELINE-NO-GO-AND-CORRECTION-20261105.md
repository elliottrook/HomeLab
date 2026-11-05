# SA3 Candidate-J quality concurrent-baseline NO-GO and correction — 2026-11-05

The first approved inactive-install attempt was a safe NO-GO before mutation.
Its first failure was `CUSTODY:lab_hours_workloads.py`; no checkpoint or target
file was created. Independent postcheck confirmed all Candidate-J quality host
and guest targets remained absent.

The cause was a legitimate concurrent platform release between the original
baseline read and installation. The live release had advanced to
`aster-tts-dual-cpu-screen-v1`, adding EPUB word-alignment and TTS CPU-screen
workloads and changing three additional full-drain control files. The
Candidate-J installer correctly refused to overwrite those bytes.

The corrected source imports every one of the newer live release's 43 pinned
files, then layers Candidate-J's three platform files and four-file guest
runtime on top. The combined release
`aster-tts-dual-cpu-screen-plus-candidate-j-quality-v1` has 46 exact pins and
preserves both concurrent workloads. Installer baseline hashes and modes now
match the newly observed live root-owned files, including mode 0755 for
`lab_hours_workloads.py` and mode 0600 for the manifest.

The combined joined suite passes 61/61. No production service, model, booking,
timer, lease or workload was changed by the failed attempt or source
correction. Applying the corrected inactive installer remains a new deployment
gate; the prior approval was spent on the failed baseline attempt.

The second approved attempt was also a pre-mutation NO-GO, this time at guest
preflight: `TARGET_PRESENT:sa3_evidence_matrix_candidate_j_contract.py`.
Independent readback proved the contract and runner were the exact accepted
public Candidate-J hashes already installed in LXC110. All three
quality-specific guest targets and all three quality host targets remained
absent. The host preflight checkpoint is retained as evidence; no guest
checkpoint was created.

The R2 installer now classifies the exact contract and runner as shared
existing pinned dependencies and adds only the packet, key-free quality runtime
and quality wrapper. It uses a distinct R2 checkpoint and fails closed if
either shared hash changes. The 61/61 suite still passes. Applying R2 is a new
deployment gate because the prior approval was spent on this safely failed
attempt.
