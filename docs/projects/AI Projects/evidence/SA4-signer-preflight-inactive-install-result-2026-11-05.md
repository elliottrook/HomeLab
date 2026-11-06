# SA4 signer/preflight inactive install result — 2026-11-05

## Result

The approved inactive signer/preflight packet completed on the Mac owner host
and LXC 104. A packaging preflight first caught that macOS ad-hoc code-signing
binds the executable's versioned filename: the unversioned build digest in the
first packet was therefore wrong. No installation had started. Two builds
under the exact installed name then matched, the plan was corrected in commit
`674a600e`, and Forgejo plus its GitHub mirror both reached that correction
before installation.

The final installed state is:

| Target | Installed identity | SHA-256 / custody |
|---|---|---|
| Mac owner | `sa4-owner-signer-4148fee1` | `ecf91f6356c368777a5910d8e4c228418ebc05728f3c11f1d7b0b53ed6288836`, `jelliott:staff` 0755 |
| LXC 104 | corrected `sa4_preflight_composition_v1.py` | `d96fcba0bda17ae48f2061a9c7977bbc70c67271a16d02ed11530b05d0a2ea06`, root:root 0644 |
| LXC 104 | `sa4_ai_pam_signer_v1.py` | `10a7e39faacd6b42bd7529720d896683e6722fd954e15af17db57246d1792e55`, root:`hlabroker` 0640 |

The prior Mac helper remains unchanged at SHA-256
`b56d9a35d1edd66a4efcc5a1624e5c1640797678e7397a9a1c2489f3720e372b`.
The prior LXC preflight source is retained root:root mode 0600 at SHA-256
`a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569`
inside root-owned mode-0700 checkpoint `preflight-correction-v1`.

## Postchecks

The new Mac binary passed strict code-sign verification and its no-Keychain
self-test. The installed LXC preflight resolved the production canary to
`lxc104`. The AI-PAM wrapper imported and accepted an exact synthetic canonical
statement without invoking OpenSSL or the private key. Exact file hashes,
owner/group/mode and checkpoint metadata matched.

LXC 104/110/116 are running. Aster Agent, accepted llama.cpp/SYCL, Aster
Speech, `pvescheduler` and `pvestatd` are active. No service was started,
stopped, reloaded or restarted. No Keychain prompt, signature, grant, one-use
claim, repair checkpoint, receipt or repair occurred; automatic routing and
effect authority remain off.

## Next gate

The next source step is the fail-closed signed-packet assembler and offline
verification boundary. Running the first real zero-effect ceremony will then
require owner presence for the exact Keychain signature. That ceremony still
cannot create a repair checkpoint or effect. The first repair itself remains a
separate exact immediate approval after fresh static and runtime preflight.

