# SA4 partial key creation and owner ACL correction — 2026-11-05

## Measured result

Jason approved creation of the three dedicated SA4 signing identities. The
first owner-helper build from commit `c851ed9e` compiled, passed its no-effect
self-test and was ad-hoc signed and installed under the private SA4 Application
Support directory. The exact owner tag was absent before creation.

Owner-key creation then failed closed with macOS status `-34018`
(`errSecMissingEntitlement`). A second exact-tag query confirmed the owner key
remained absent. No key, public identity or partial Keychain item was created.
Apple's macOS Keychain guidance explains the boundary: biometric/user-presence
`SecAccessControl` uses the data-protection Keychain, whose access group must be
authorized by a provisioning profile. An ad-hoc command-line helper has no such
authorized group. See Apple's
[TN3137: On Mac keychain APIs and implementations](https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains)
and [`errSecMissingEntitlement`](https://developer.apple.com/documentation/security/errsecmissingentitlement).

The other two independently approved custodians completed successfully:

- AI-PAM: one RSA-2048 key under
  `/var/lib/homelab-broker/sa4-signing/ai-pam-grant-v1.pem` in LXC 104. The
  directory is `hlabroker:hlabroker` mode 0700, private key mode 0600, public
  key mode 0644. OpenSSL's internal key check passed. Public DER SHA-256 is
  `01f7f7eaddec6a2b1125b70826d65c6117f9a762e5a95c4944496df8721aec07`;
  canonical public-JWK SHA-256 is
  `f9ff0e192840dc0794e4adb65dad91a608e32e5d1d389bccbeac3612f54e9cb0`.
- independent observer: one RSA-2048 key under
  `/var/lib/aster/sa4-observer/independent-observer-v1.pem` on Proxmox. The
  directory is root:root mode 0700, private key mode 0600, public key mode
  0644. OpenSSL's internal key check passed. Public DER SHA-256 is
  `04307b1efae3dbe9c2bdc1cf89570c265f201315ec3e127e84f5a4e04fd3e23e`;
  canonical public-JWK SHA-256 is
  `a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b`.

Only the two public moduli and fingerprints were returned. Private bytes were
not printed, copied, exported or placed in Git/model context. No service was
restarted or changed.

## Owner correction

The corrected helper uses the traditional macOS login Keychain ACL model,
which Apple documents separately from the entitlement-backed data-protection
Keychain. It creates a fixed `SecAccess` ACL with an empty trusted-application
list: private-key use therefore requires explicit Keychain authorization. The
RSA key remains sensitive and non-extractable. The helper still exposes only
self-test, one-time create, public JWK and canonical owner-proof signing.

Corrected source SHA-256 is
`fd311076dbd47f14524e545a9f93817cd038960c96807c96aba3f621396b3696`.
The source compiles and its no-effect self-test passes. The complete SA4 suite
remains **74/74**. The corrected binary has not been installed and owner-key
creation has not been retried.

## Boundary and next gate

The installed LXC 104 SA4 trust registries and slots remain empty; the two new
machine keys grant no authority. Replacing the owner helper and retrying the
owner-key creation is a changed credential mechanism and requires exact
approval. After a successful public-only three-key candidate passes admission,
public trust compilation and installation remain later separate gates. No
grant, checkpoint or repair is authorized.
