# Local AI maintenance lease

The Local AI lease is a manual Proxmox-host operation. The installed adapter
`/usr/local/sbin/local-ai-lease` is intentionally unscheduled; no systemd unit
or timer starts it automatically.

## Bounded service-drain operation

Run only after the backup chain is complete and verified and the scheduled
window is open. The first live-tested mode is deliberately narrow:

```sh
/usr/local/sbin/local-ai-lease acquire --light --backup-verified
/usr/local/sbin/local-ai-lease status
/usr/local/sbin/local-ai-lease release
```

For an operator-supervised test outside the scheduled window, add
`--test-window`. `--light` stops only the accepted V1 production services in
LXC 104, 110 and 116. It does not stop unrelated guests, reboot the host or
enable a scheduler. The controller records a root-private checkpoint and
holds a lease lock until restoration and health validation succeed.

## Safety contract

- The Proxmox control plane, network, UPS protection and minimum monitoring
  path must remain active.
- Do not release a failed lease by deleting its state or lock. Restore the
  checkpointed services and resolve the health-gate failure first.
- Full guest draining and host restart are not enabled by the tested adapter;
  they require a separate implementation and validation milestone.
- Never print checkpoint contents or host configuration into an issue or chat;
  they are root-private operational state.
