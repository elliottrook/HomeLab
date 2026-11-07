# Aster Games infrastructure candidate

This directory is the infrastructure-first candidate for the AsterTV v4 retro
gaming addition. It deliberately contains no Kodi skin, add-on, fleet overlay,
release bundle, or appliance mutation.

The stack separates four responsibilities:

- **ROMarr 1.8.0** acquires, verifies against DAT catalogues, quarantines, and
  imports games.
- **RomM 5.4.0** owns the browsable catalogue, metadata, saves, play history,
  and the future device-sync contract.
- **MariaDB and Valkey** provide RomM's documented state services.
- **Aster Games Broker** exposes a small read/proposal API. It cannot approve
  or execute proposals in this release.

All upstream images are version- and manifest-digest-pinned. The web UIs bind
only to loopback in the candidate compose file. State and service networks are
internal; only ROMarr and RomM join a separate outbound bridge for approved
ARR/metadata dependencies. A private reverse proxy and Authentik may be added
during the separately approved live-deployment milestone; no public ingress is
permitted.

## Safety gate

`config/release-gate.json` is intentionally closed. Do not set its AsterTV v3
acceptance fields from expectation or bundle eligibility. It may be opened
only from recorded deployment and owner-acceptance evidence. Even after that,
the broker in this directory has no execution route: AsterTV implementation is
a later v4 milestone owned by the AsterTV design and fleet authorities.

## Local validation

```sh
python3 services/aster-games/validate_stack.py
python3 -m unittest discover services/aster-games/broker/tests -v
```

The candidate is rendered only after deployment-local paths, IDs, and secrets
are supplied outside Git:

```sh
docker compose --env-file /secure/path/aster-games.env \
  -f services/aster-games/compose.yaml config
```

Do not use the example environment as a deployment environment. The live
milestone must first allocate storage, identity, DNS, firewall, monitoring,
backup, and NetBox records and obtain the Stream M approval recorded in the
project document.

## Storage contract

| Mount | Writer | Purpose | Recovery class |
|---|---|---|---|
| `/roms` | ROMarr | Verified canonical library | Media; snapshots, not app backup |
| `/media/usenet/complete/retro-games` | SABnzbd and ROMarr | Untrusted staging with an identical container path | Disposable |
| `/dats` | operator/curated updater | No-Intro/Redump verification inputs | Reproducible, version-recorded |
| RomM database/config/assets | RomM/MariaDB | Metadata, accounts, saves, states | Protected + restore-tested |
| ROMarr config | ROMarr | Settings, history, API key/password hash | Protected + restore-tested |
| Broker state | broker | Content-silent proposal ledger | Protected + restore-tested |

The canonical ROM tree is mounted read-only in RomM and read-write only in
ROMarr. Downloads never share a path with the canonical library.

