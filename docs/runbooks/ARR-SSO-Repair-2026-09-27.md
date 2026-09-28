# ARR dashboard second-login repair — September 27

Jason reported native Sonarr/Radarr login prompts after Authentik, reached from
the dashboard, with old application passwords rejected. Requested outcome:
restore the existing Authentik-only browser path without resetting credentials.

Read-only checks reproduced the issue: from NPM, all five ARR backends return200
without forwarded client-address headers. Forwarding a client address triggers
Sonarr Basic401 and Radarr/Prowlarr form-login302 (Lidarr depends on address).
All four ARR XML configs retain native authentication with
`AuthenticationRequired=DisabledForLocalAddresses`; no password was inspected.
The original rollout preserved these settings. Authentik providers remain
owner-only. This is separate from the Aster-only reauthentication repair.

## Bounded repair and risk

Modify only NPM hosts10–14 (Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd) in LXC107.
In the protected application location, suppress `X-Real-IP`, `X-Forwarded-For`
and `Forwarded`. This lets the apps classify the actual existing NPM backend
connection instead of the browser address. Keep Authentik's subrequest,
owner-only policy, original client-address forwarding to Authentik, TLS and
routes unchanged. Existing app login requirements on direct paths remain as
configured; no API key, app password, library, download or network setting changes.

Risk: losing the Authentik gate would expose the local-auth exception on this
route. Preconditions require the exact gate and owner bindings; negative HTTPS
probes must still redirect to Authentik, including spoofed identity headers.
Application logs will see the proxy address; NPM/Authentik retain client-address
attribution. Preserve database and rendered-config checkpoints on LXC107, prove
SQLite integrity and restored-copy row counts, validate nginx before reload,
and roll back only these five configurations on validation failure. No global
authentication relaxation or backend auth disable is authorized or proposed.

Status: deployed and machine checks passed; real dashboard acceptance pending.
No Git push. No change to other apps or shared Authentik login flows.

## Evidence and recovery

Protected LXC107 checkpoint: `/root/arr-sso-header-repair-20260927` contains an
online NPM SQLite backup, verified restored copy, original target rows and rendered
configs10–14. Both databases pass integrity checks and proxy-host counts agree.
The persisted database and rendered files match after the change; nginx syntax
and graceful reload pass. Every non-ARR proxy-host row is unchanged.

All five unauthenticated HTTPS routes return their Authentik start redirect;
forged `X-Authentik-Username`, `Remote-User`, `X-Forwarded-For` and `X-Real-IP`
do not bypass that gate. All five owner-only application bindings were verified.
The outpost location still receives original forwarded client addresses.
All five backends return200 to the existing NPM connection without forwarded
addresses. No ARR container restart or application/configuration write occurred.

To roll back, restore only `advanced_config` (and original `modified_on`) for
hosts10–14 from `target-rows.json`, plus their matching rendered `.conf` files;
run `docker exec nginx-proxy-manager nginx -t` before a graceful reload. Do not
restore the entire NPM database over later changes or remove the Authentik gate.

NetBox, DNS, certificates and firewall: unchanged. Existing browser-boundary
monitoring still covers the five Authentik gates; a positive human login is
required to assess second-prompt usability. Existing configuration backups cover
NPM state. App passwords were neither read nor reset; their reported rejection
was not separately diagnosed because the intended dashboard workflow uses SSO.
