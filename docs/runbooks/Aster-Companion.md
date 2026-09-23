# Aster Companion operator guide

> Authority: operator-guide
> Reviewed: 2026-09-23
> Sources: `homelab/docs/projects/Aster-Companion-App.md`, live service and NetBox verification
> Owner: Jason

## Use Aster

Open **Aster Companion** in Homepage, or visit
`https://aster.elliottrook.com/companion`. Sign in with the registered passkey.
The same hostname works on the LAN and through the existing Tailscale route;
there is no public WAN port forward. On iPhone, Safari's Add to Home Screen is
optional. On Mac, reopen `/Applications/AsterCompanion.app` after an update.
The ad-hoc Mac build can prompt for Keychain access again after a rebuild.

Choose **Sysadmin Aster**, **Media Automation Aster**, or **Home Assistant Aster**.
Sysadmin has the broad existing read-only lab tools. Media is limited to ARR
context; Home Assistant is limited to its sanitized HA report. Tool checkboxes
only remove tools from that conversation; they cannot expand a persona's scope.
A model's general knowledge or speculation is not live lab evidence.

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
