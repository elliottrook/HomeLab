# SA4 installed-controller live zero-effect preflight — 2026-11-05

The installed controller, LXC exchange and Proxmox bridge each imported from
their final path. Import created no exchange directory, operation lock,
emergency stop or ledger. The bridge runtime directory is also absent.

No controller or signer was invoked. The canary remains at the registered
drifted digest `19b4e02d…df1a`, and the whole-host lease remains exactly
`ready`. Static installed evidence remains canonical at `27f5dfef…f057`; the
complete source suite passes 187/187.

This closes the installed zero-effect protocol preflight. The next SA4 step is
a fresh post-controller release packet binding the corrected installed result,
then a new exact approval for the single supervised canary repair. No prior
repair approval or authority may be reused.
