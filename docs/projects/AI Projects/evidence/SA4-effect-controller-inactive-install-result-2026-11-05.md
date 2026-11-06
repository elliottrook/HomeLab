# SA4 effect-controller inactive-install result — 2026-11-05

The corrected approved inactive installation completed after the first attempt
failed its isolated import and rolled back fully. The installed root-owned,
mode-`0644`, single-link regular files are:

- LXC controller `4d7a2392…11e7`;
- LXC observer exchange `6cddfd31…3a63`;
- Proxmox observer bridge `f6f6016c…8632`.

Both LXC modules and the Proxmox bridge import cleanly. No runtime exchange
directory, operation lock, emergency stop or ledger exists. The controller and
signer were not invoked, the whole-host lease is ready, the canary remains
`19b4e02d…df1a`, LXC 104/110/116 are running, Aster Agent and Proxmox daemons
are active, and no service action or restart occurred. The exact temporary
staging directory was removed after validation.

The controller path is installed but inert. The next offline work is an
installed-manifest/result verifier and live zero-effect protocol preflight.
The independent result verifier now accepts exactly three rows with canonical
digest `27f5dfef…f057`, rejects effect/custody mutations, and raises the complete
SA4 suite to 187/187. A real repair still requires a fresh exact approval
because the prior approval was spent by the controller pre-effect NO-GO.
