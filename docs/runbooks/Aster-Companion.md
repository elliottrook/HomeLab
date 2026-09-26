# Aster Companion operator guide

> Authority: operator-guide
> Reviewed: 2026-09-23
> Sources: `homelab/docs/projects/completed projects/Aster-Companion-App.md`, live service and NetBox verification
> Owner: Jason

## Use Aster

Open **Aster Companion** in Homepage, or visit
`https://aster.elliottrook.com/companion`. Sign in with the registered passkey.
The same hostname works on the LAN and through the existing Tailscale route;
there is no public WAN port forward. On iPhone, Safari's Add to Home Screen is
optional. On Mac, reopen `/Applications/AsterCompanion.app` after an update.
The ad-hoc Mac build can prompt for Keychain access again after a rebuild.
Use the native **Aster Companion**, not the older Safari **Aster.app**. Browser
presentation during passkey sign-in is the system authentication session; normal
native chat/voice uses the API directly. Session tokens persist as one Keychain
record (`oidc_session_v2`). A visible session-only warning means persistence failed;
resolve Keychain access and sign in again. Temporary network errors retain the
saved session; a revoked refresh token requires a fresh sign-in. Quit the app
before replacing its bundle, and replace it cleanly rather than merging bundles.

Choose **Sysadmin Aster**, **Media Automation Aster**, or **Home Assistant Aster**.
Sysadmin has the broad existing read-only lab tools. Media is limited to ARR
context; Home Assistant is limited to its sanitized HA report. Tool checkboxes
only remove tools from that conversation; they cannot expand a persona's scope.
A model's general knowledge or speculation is not live lab evidence.

### Native AI-PAM

The native Mac app's **AI-PAM** button opens the same authenticated approval and
management surface as the web Companion. The approval tab shows only the
broker-provided reason, target, effect, rollback, expiry and payload hash. Yellow
may be approved directly from a valid Companion session; Red explicitly starts
a fresh passkey flow (`max_age=0`) before submitting the payload-bound approval.
Deny never executes the request.

Management shows the global switch, AI clients and their capabilities, services
and credential-custody identifiers, active requests, history and metadata-only
audit. Agent state, service enablement, request revocation and global controls
always start a fresh passkey flow. The app has no broker socket, service token,
OpenBao credential or raw secret model; it calls only the existing authenticated
Companion API. If the API is unavailable or returns an unexpected shape, the
native surface reports the error and performs no fallback action.

For acceptance after an update: refresh the inbox, approve one disposable
request, deny another, apply and restore one reversible lifecycle change, and
disable/re-enable global access. Verify the web view shows the same final state,
no pending request remains, and ordinary chat/voice still work. Quit the app
before bundle replacement and retain the previous complete bundle until this
matrix passes.

The current AI-PAM parity candidate is native version 0.2.1 (build 3). Fresh
privileged actions use an ephemeral web-authentication session in addition to
`max_age=0`, preventing a cached Authentik browser session from returning an
old `auth_time` that the broker must reject. Its
temporary acceptance rollback is
`/Applications/AsterCompanion.pre-ai-pam-20260925.app`; do not remove that copy
until the matrix above and ordinary chat/voice regression have passed.

Tap the small orb to record, then tap again to finish. The web client limits
recordings to 60 seconds. It reports transcription and response progress.
Only voice-initiated replies are spoken. If the browser blocks automatic audio,
use the visible Play control; Stop speech skips the remaining spoken reply.
Keep the phone page foregrounded during a turn. Listening, thinking, speaking
and acting have distinct orb effects. Typed messages remain available if audio
is unavailable.

## ARR repair is a separate follow-up

Jason deferred live ARR-repair execution on 2026-09-23. Production dry-run and
execution broker services remain inactive, and no candidate is currently
available. The retained action-card UI is not an enabled repair capability.
Do not enable it merely to demonstrate the UI, seed a live queue fault, or run
the operator's approval CLI on Jason's behalf. The follow-up must preserve a
short-lived, single-candidate approval, fresh-state recheck, replay refusal and
audit trail before enabling the existing bounded queue-record operation.
Aster chat never grants approval or adds repair authority.

## Service dependencies and diagnosis

| Component | Location | Dependency |
|---|---|---|
| Companion and Aster API | LXC 104, `192.168.70.10:9120` | Existing B60 inference service on LXC 110 |
| Speech STT/TTS | LXC 116, `192.168.70.14:9130` | CPU Whisper `base.en`, Piper `en_US-lessac-high` |
| HTTPS proxy | NPM LXC 107, `192.168.50.23` | `/voice/` forwards to speech; other routes to Aster |
| Sign-in and signing keys | Authentik, `auth.elliottrook.com` | Public client `aster-companion`, PKCE, passkey-only flow |

Run `python3 /opt/aster-speech/health_check.py` inside LXC 116. It checks the
speech endpoint and the Authentik signing-key URL. A healthy speech `/health`
alone is insufficient: both application servers must fetch signing keys via
NPM TCP 443. Speech's permit is source `.70.14` to `.50.23:443` only, OPNsense
UUID `bc811346-6714-44b4-bc65-46e7430f46a8`.

For a stalled voice turn, check that dependency, then request status and
sanitized journal errors. Do not collect microphone recordings or transcript
text for routine diagnostics. Speech retains temporary input only during the
request; logs contain timing/size or error classes. Sign-in failures should be
resolved through the existing passkey flow, never by sharing a server key.

An unexpected SSH host key must not be accepted blindly. On September 23 a
single conflicting key was observed, followed by matching verified scans from
Mac, OPNsense and the trusted Proxmox console. The cause is unresolved. The
verified speech guest ED25519 fingerprint is
`SHA256:66HLSB1V/TUC0bTP374cCqQcGh8zsM56+qrfTiwNpcI` and its MAC is
`BC:24:11:E1:11:68`. Confirm through Proxmox if the anomaly recurs.

## Identity, revocation and administration

Mac tokens use Keychain; web tokens use browser local storage. Sign out to
remove this client's local session. Use Authentik's provider/session controls
for revocation. To immediately cut off Companion while investigating an account
incident, disable the dedicated NPM host `aster.elliottrook.com`; the private
legacy API remains a separate, credential-protected recovery path. Removing an
Authentik application assignment alone must not be assumed to revoke already
issued JWTs before expiry.

The speech service key is in `/etc/aster-speech/speech.env` on LXC 116; the
existing Aster service environment is `/etc/aster/aster.env` on LXC 104. Never
copy values into Git, chat, dashboards or wiki. Jason owns rotation; rotate only
as a separately authorized credential operation and update dependent callers.

AI administration: **not currently supported** by the speech API. Its token
permits STT/TTS, not host management. Existing human SSH administration and
Proxmox console access remain the recovery route. This project grants no new
standing administrator identity or broker capability.

## Recovery

Daily Proxmox `vzdump` covers guest 116. TrueNAS task 1 includes only its
`vzdump-lxc-116-*.tar.zst` archives alongside the existing guest allowlist, under
`/mnt/Media/backup/homelab-proxmox-guests`. Compare source and destination hashes
before choosing a recovery archive. Restoring speech requires its service code,
venv, cached Whisper model, Piper binary/voice, systemd unit, and protected
environment. No microphone history is needed.

Restore into an isolated directory or guest first; do not boot a duplicate IP.
Validate Piper output and cached-model transcription on synthetic audio, then
restore the intended guest's configuration and verify HTTPS and JWKS access.
On September 23 an isolated file-level restore from the real backup successfully
ran the restored Piper binary, cached Whisper model and speech module. A full
guest boot/cutover was not performed.

Keep a pre-deploy source copy and revert only the changed service if an update
fails. Do not overwrite the whole firewall configuration over later changes.
Mac bundle rollback from the preceding repair is temporarily available at
`/tmp/AsterCompanion.pre-voice-fix-20260923.app`; durable recovery is rebuilding
from committed source plus the existing Keychain/passkey login.

## Deliberate limits

Native iOS installation, Aster web research, new mutating tools, stable paid
Apple signing and changes to the inference model are outside this project.
Shared inference is single-slot: simultaneous news summarization can increase
chat latency. Source and operational records take precedence over this guide.

## System notifications (accepted September 23)

Mac voice and iPhone Wi-Fi/Tailscale voice are accepted. Jason also accepted
iPhone notification delivery on/off Wi-Fi and native Mac sign-in, reopening and
background reply notifications. Automated tests cover denied/revoked permissions,
failed unsubscribe and stale state. A fresh physical OS Settings toggle was not
performed; review that path on the next app/OS upgrade or notification regression.
Jason requested both lab system alerts and reply-ready notices and approved
Apple Web Push with generic encrypted content on 2026-09-23.

### Enable and use

- **iPhone:** open the installed Home Screen Aster app, expand **Notifications**,
  choose **Enable notifications**, accept the OS prompt, then **Send test
  notification**. Test with the app backgrounded on Wi-Fi and on Tailscale.
  Ordinary browser tabs may not support this path. Apple Web Push requires a
  supported iOS Home Screen web app; no paid Apple Developer membership is used.
- **Mac:** quit/reopen `/Applications/AsterCompanion.app`, expand Notifications
  and enable them. Send a question and switch apps before the reply completes.
  Native alerts require Aster to remain running; a fully quit app does not
  receive them. No launch-at-login agent or native APNs entitlement was added.
- Alerts contain generic text only. Open Aster and use normal authentication
  to see the reply or lab health. An alert cannot approve or execute an action.
  Focus/OS notification settings may silence alerts.
- Disable in Aster or revoke its OS notification permission. Web sign-out
  attempts server deletion and browser unsubscribe, then clears local state;
  an unavailable server never prevents local logout. If both revocation paths
  fail, disable Aster notifications in system settings.

### Delivery and limits

The Mac polls the authenticated `/v1/companion/lab-health` endpoint each minute
while signed in and suppresses foreground local alerts. The existing daily
08:15 Mac `ca.yampy.homelab-report` job now publishes its already-collected
Doctor output to `/var/lib/aster/health/latest.json` on LXC 104. This is a daily
health summary, not real-time monitoring of every service. A sleeping/offline
Mac can delay collection. Reports over 36 hours old, malformed or future-dated
are excluded from alerts; the UI and Doctor report that collection is stale.
The September 23 refresh found existing TrueNAS Media capacity pressure (93%).

Web subscriptions belong to the authenticated Authentik issuer/subject and
expire after 30 days without renewal by opening the app. The sender accepts
only `https://web.push.apple.com` endpoints, disables redirects and ambient
proxy use, and sends only an event kind and random ID. Apple sees delivery
metadata; the Web Push payload is encrypted. Outbound Apple HTTPS was already
reachable from LXC 104; no new ingress, DNS or firewall rule was installed.

Notifications-enabled web requests use `/v1/companion/jobs`: the request
continues after the phone disconnects. The reply is kept **in memory only** for
at most one hour and can be recovered on reopen. Requests are bounded to four
active globally, one per account, 64 per hour, and 240 seconds per reply.
Requests have stable random IDs to prevent a repeated submission starting a
second job. Restarted/interrupted jobs fail visibly; no inference/action is
silently replayed. Reply text and input history are absent from SQLite/backups.
Clients without enabled Web Push retain the existing streaming chat path.

A reply fetched before its push is dispatched cancels that pending alert.
Races can still show a generic foreground Web Push: received pushes must produce
a visible notification under Safari policy. The worker never uses arbitrary
payload text or URLs. Delivery retries are limited to five attempts, Apple TTL
is five minutes, and event metadata is pruned after one hour. Provider 404/410
removes the subscription. Push acceptance is not proof of device presentation.
Lab report fingerprints and stable notification tags reduce duplicate alerts.

### Monitoring, custody and recovery

`/opt/aster-agent/check_notifications.py` reports only coarse failure reasons:
worker heartbeat older than 90 seconds, failed delivery attempts, state/key
permission problems or stale Doctor data. `scripts/doctor.sh` invokes it through
the existing Proxmox path. Delivery metadata stays local, without raw endpoints
or credentials in diagnostic output. Jason owns notification preferences and
provider/OS troubleshooting; Aster owns no new administrative capability.

- VAPID identity: `/etc/aster/notification-vapid.pem`, root:aster 0640, generated
  on LXC 104; never copied into Git or an AI prompt. This is the custody location,
  not a credential value. Replacing it requires re-enrolling web devices; revoke
  by disabling the sender/removing subscriptions, then explicitly plan rotation.
  Central AI-PAM custody is not yet available and is not presumed operational.
- Subscription/event/job metadata: `/var/lib/aster/notifications/notifications.sqlite3`,
  aster-owned 0600 in a 0700 directory. SQLite has secure deletion enabled.
- systemd drop-in: `aster-agent.service.d/companion-notifications.conf` grants
  write access only to that state directory. Normal Authentik checks remain.
- Rollback source/unit: `/var/backups/aster-notifications-20260923/` on LXC 104.
  Restore the saved `aster_agent.py`, disable the notification drop-in, reload
  systemd and restart. The earlier voice build is retained at
  `/tmp/AsterCompanion.before-notifications-20260923.app` on Mac (temporary, not
  durable storage). Use a clean app replacement; merging bundles leaves stale
  resource signatures. Existing voice/chat can operate without notifications.
- Protected bootstrap archive: `recovery.tar.gz` in that guest directory and
  `/root/aster-notifications-20260923/` on Proxmox, mode 0600 in private parents.
  SHA-256 `1aff545d3a361a48a63b32a38ecd52f271a603da2c0353e7b3b0fb7729793d54`.
  An isolated restore verified identity/public-key equality, SQLite integrity and
  absence of stored reply content. This initial copy had no device subscriptions.
  Subsequent state/key coverage is verified in the September 23 12:22:05 and
  13:00:35 whole-guest LXC 104 archives. The 13:00 archive passed an isolated
  key-equality/SQLite-integrity restore; the 12:22 archive matches its TrueNAS
  copy with SHA-256 `de3bee598ff106205cc49e10e9052cd4a9b3c2e3acfb3bf096c9c52a0adee197`.
  The enabled 02:30 all-guests schedule includes these paths. These were on-demand
  checkpoints; Jason should review the next overnight run after September 24
  02:30 through normal backup/Doctor maintenance, without inferring it ran already.

References: [WebKit Home Screen Web Push](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)
and [Apple notification permission](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications).
