# D4 candidate-H descriptor launcher proposal — 2026-10-25

**State:** source-only proposal; not reviewed, installed or authorized

Read-only LXC104 inspection found the existing service authentication custody:

- /etc/aster is root:aster mode 0750;
- /etc/aster/aster.env is root:aster mode 0640;
- Aster Agent runs as aster:aster and receives that file through its existing
  systemd EnvironmentFiles boundary;
- /opt/aster-agent/venv/bin/python resolves to /usr/bin/python3.13;
- the target is Python 3.13.5, root:root mode 0755, SHA-256
  889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9.

No credential content was read during that inspection.

The proposed launcher at scripts/deploy/launch_d4_candidate_h.py converts the
existing file custody into candidate-H's descriptor interface without placing
the value in the child environment:

1. require root execution;
2. fail if either output already exists;
3. require a root:root mode-0700 packet containing exactly the frozen eleven
   files, each root:root mode 0600 with exact length and SHA-256;
4. pin the interpreter target and hash;
5. open the non-symlink credential file with O_NOFOLLOW and O_CLOEXEC, verify
   its custody again after open, bound the file to 65,536 bytes and require
   exactly one bounded printable ASTER_LLAMA_API_KEY value;
6. create a close-on-exec pipe, inherit only its read descriptor into the
   candidate process, remove the API key from the child environment, and pass
   only the descriptor number through --key-fd;
7. enforce the 2,200-second outer deadline and bounded termination; and
8. close all descriptors and overwrite the in-memory credential buffers.

The child environment is a small non-secret portability allowlist. It cannot
inherit ASTER_LLAMA_API_KEY. The candidate packet, digest, fixtures, model-call
limits and journal path are fully fixed in source; no operator-selected path or
digest is accepted.

Source identities:

- launcher SHA-256:
  95dc756a8038152aba3ed20d0f11338b1fc9d0f2b2eff064ac131f06e75b7be3
- launcher-test SHA-256:
  34e4314578195d22cd90e533f5ca59a0ce4704e53da5b56b9fccc2ded8224021
- candidate-H run digest:
  423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4

Four synthetic launcher tests and all 168 evaluation tests pass. Tests prove
exact manifest binding, packet custody failure, unique fictional-key parsing,
descriptor delivery, child-environment exclusion and buffer clearing. They use
only fictional bytes.

This proposal does not claim that reading the existing file is the platform's
accepted secret-broker primitive. The platform owner must independently decide
whether this root-only conversion is acceptable or replace it with a named
broker opener. No file has been copied to LXC104, no credential was opened, no
journal was created and no model request ran.
