# F2 result projection boundary — source only

**Status:** uninstalled candidate. The October 17 F2 attempt remains
FAILED/UNKNOWN, and its one-cycle scan approval is consumed.

The one-shot guard previously accepted a child result marked `complete` when
its date was unrelated to the backup cycle, a row named another archive, or
the reported size or elapsed time was impossible. The child producer has its
own fixed-source checks, but the parent is the final boundary before a
complete result is reported. Its projection now requires the local cycle date,
the fixed 104/110/116 archive-name shape, positive size and ctime, and
non-negative elapsed time within each fixed per-archive bound. It continues
to reject extra fields, nonzero/boolean exits and any receipt-written claim.

The focused synthetic suite passed 13 tests; the local `scripts/local-ai`
suite passed 213 tests with four macOS root-custody skips. No archive was
opened, model called, lease acquired or host file changed. These checks do
not authenticate the child or prove a retained archive is sound. They cannot
identify why the October 17 guard returned `F2NoGo`. A future host release
needs new exact hashes, target-Linux synthetic validation, a reviewed card
and separate approval. A future scan needs its own one-cycle approval.
