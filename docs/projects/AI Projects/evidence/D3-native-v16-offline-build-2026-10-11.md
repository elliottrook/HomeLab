# D3 native Companion version-16 offline build — 2026-10-11

**Historical pre-installation checkpoint.** This records the local candidate before its later owner signing and bounded ordinary-mode installation. See the [installation checkpoint](D3-native-v16-installation-2026-10-11.md) for current state. No Codex turn was sent. Routine manual handoff remains **HOLD**.

## Purpose and scope

Bundle two previously tested, user-visible job-handling changes in the next reviewed native candidate: fixed-code session-refresh observations and durable failure categories. The first can distinguish an actual natural refresh from merely remaining signed in; the second can tell Jason whether a confirmed failed Codex turn was a quota, rate, authentication or provider failure after restarting Companion. Neither adds a tool, route, permission, automatic retry, cloud consent or background worker.

The bundle version was advanced from 15 to 16. The manual bridge pin was updated from the installed version-15 fingerprint to the exact metadata-only fingerprint of the current reviewed source, `57140f720aa9097592699986bc03b891ecc67307fe5821af9d48d14c3ef844fa`. This pin includes source and Codex executable hashes; if either changes before a later release, preparation must be reviewed and repinned rather than bypassed. The assembled bundle's own `--prepare` returned the same fingerprint with `inference=false`; its manifest required the ChatGPT account, native OpenAI provider, read-only sandbox, disabled web, zero enabled MCP servers, one turn and no automatic retry. This was not an inference request.

## Verification

- The local Swift suite passed 57/57 after the version and pin edit. SwiftPM's first shell-sandbox run failed because SwiftPM could not initialize its own sandbox; the permitted rerun passed. The delegation bridge suite passed 305/305 in the existing dependency environment. No dependency was installed.
- `ASTER_REGISTER_APP=0 ASTER_CODESIGN_IDENTITY=- ./build-app.sh debug` assembled an ad-hoc-signed local `.app` without registering or installing it. Strict/deep signature verification passed for that disposable bundle, its `CFBundleVersion` is 16, and the executable SHA-256 is `8c8ed986a8343b307dcbc556ecae322066825be17d312e2f5eeb2358d601adba`. The bundled `local_bridge_cli.py` matched source byte-for-byte and its metadata-only preflight returned the reviewed fingerprint.
- Read-only verification confirmed `/Applications/AsterCompanion.app` remains version 15, executable SHA-256 `f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1`, with a valid strict/deep signature.

## Next release gate

The ad-hoc build is **not suitable for replacing the installed Keychain-using app**. Before a controlled v16 installation, prepare an owner-signed bundle using the established stable identity, verify its designated requirement against v15, preserve a hash-checked v15 rollback copy, and confirm no Codex request is active or uncertain. Install one ordinary-mode instance only, with the manual-send surface hidden. A Keychain prompt on update or first launch must be counted separately; do not alter the Keychain ACL or copy credentials to suppress it. Observe a normal authenticated read-only Companion request after refresh is naturally needed, using only the fixed-code event, app response and prompt count. No extra Codex question is needed. If the new build prompts repeatedly, loses ordinary Aster access or the refresh result is volatile/invalid, stop and restore v15; human sign-in may still be required after rollback. One successful event does not prove long-term reliability.

No owner signing or installation was attempted here. The D3 release decision remains open until that bounded ordinary-use observation and rollback readiness are reviewed.
