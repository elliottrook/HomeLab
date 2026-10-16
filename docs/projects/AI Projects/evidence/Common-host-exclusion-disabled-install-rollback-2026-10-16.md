# Common host exclusion — disabled install failed and rolled back

**October 16, 2026, Vancouver.** Jason approved the exact six-path disabled
installation. Fresh Proxmox preflight matched its three replacement hashes,
three add-only absences, inactive timers and absent lease state. The transfer
archive first carried macOS metadata members, so the installer rejected it
before modifying installed files. A clean archive passed source-hash checks;
the installer preserved the three originals in a root-only checkpoint and
staged only the six pinned files.

Target-Linux import then failed because `application_b60_controller.py` was
staged in `/usr/local/libexec/local-ai-lease`, but its existing
`application_b60_lease.py` dependency and real wrapper `PYTHONPATH` are in
`/usr/local/libexec/aster-a1`. Read-only inspection confirmed the A1 module
and installed controller there; the original A1 controller imports normally.

The approved rollback restored the three whole-host originals to their exact
preflight hashes and removed the three additions. Independent postcheck found
both lease namespaces absent, watchdog/heartbeat timers disabled and
inactive, LXC104/110/116 services active, unchanged old manual-controller and
recovery-module hashes, and unchanged Proxmox backup schedule digest. No
archive scan, receipt write, lease, service stop, model call or schedule change
occurred. The root-only checkpoint and source stage remain for provenance.

The first card is superseded. A corrected seven-path, two-root card and the
full result are in local `codex/aster-lease-compat` commit `cc03cc2b`. It
adds a second identical host-exclusion module under the A1 root and replaces
the *existing* A1 controller, with four originals to checkpoint. This is a
materially different host change and needs a new exact approval. F2/F3/F6
remain open; October 17's scan is not yet admitted or scheduled.
