# SA4 bounded observer signer source — 2026-11-05

The fixed Proxmox observer signer is now source-complete. It accepts only a
canonical independent-receipt proof statement for observer `aster-observer`,
the accepted public-key digest `a8b5e876…0892b`, one receipt digest,
RSA-PKCS1v1.5/SHA-256 and `observer-proof-only-no-effect` authority.

The OpenSSL binary and private-key path are compiled constants. Input is
bounded to 4096 bytes and symlinks are refused. The adapter captures only one
256-byte signature and exposes no key-path option, export operation or
arbitrary-message interface. Tests use a fake runner; the Proxmox private key
was not read or invoked.

Four focused tests and the complete SA4 suite pass; the suite is **109/109**.
The signer is not installed. Next is its reversible inactive installation and
the content-free postcheck/rollback receipt producer. No repair is authorized.

