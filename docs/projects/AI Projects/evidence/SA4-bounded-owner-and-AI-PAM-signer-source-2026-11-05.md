# SA4 bounded owner and AI-PAM signer source — 2026-11-05

## Result

The two authority-side signing adapters are now source-complete for the first
zero-effect ceremony.

The macOS owner helper now requires the exact accepted signer ID
`jason-owner` and public-key digest
`17738e78d92b3ba4fff496f4d51904b6c6dd18d4acf80b3ef2a34a27ea6de946`
before it can ask Keychain to sign. It already restricted input to a canonical
owner-approval detached-proof statement, used the permanent sensitive and
non-extractable key, and exposed no private-key export command. The corrected
source SHA-256 is
`03bf11c798f31f57c7ac5cb8ce0ebd5b1b1f180892032423fefed52854b67b44`.

The new AI-PAM adapter accepts only canonical `ai-pam-grant` proof statements
for signer `aster-ai-pam` and accepted public-key digest
`f9ff0e192840dc0794e4adb65dad91a608e32e5d1d389bccbeac3612f54e9cb0`.
It uses a fixed `/usr/bin/openssl` command and the fixed target-local private
key path `/var/lib/homelab-broker/sa4-signing/ai-pam-grant-v1.pem`. It applies
a 4096-byte bound, refuses symlinks, captures only a fixed 256-byte RSA
signature and exposes no key-path option, export operation or arbitrary-message
interface. Its source SHA-256 is
`10a7e39faacd6b42bd7529720d896683e6722fd954e15af17db57246d1792e55`.

The source tests use a fake signer runner and do not read or invoke either
private key. The macOS helper compiles and its self-test does not query
Keychain. Four focused AI-PAM tests, two owner-helper tests and the complete
SA4 suite pass; the complete suite is **90/90**.

## Boundary and next work

Neither corrected adapter is installed. No Keychain prompt, signature, grant,
claim, checkpoint or repair occurred. The next step is an exact reversible
installation packet: replace the installed owner helper only after matching its
current binary digest, install the AI-PAM adapter with fixed custody, and
install the corrected preflight composition on LXC 104 with retained old
bytes. Installed-path tests must run without signing. The later first signed
ceremony remains zero-effect, and the first repair remains a separate exact
immediate approval gate.

