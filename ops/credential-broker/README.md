# credential-broker

Untested skeleton for a HomelabHero-style SSH credential broker: a
sudoers-narrowed script lets a low-privilege agent user run remote commands
via a separate vault-owning user, without the agent ever reading key
material. See ../../docs/projects/homelab-credential-broker.md for the full
project document, risk assessment, and milestones (Stream M — requires
approval before each state-changing step).

Layout:
  bin/hb              - operator/agent entrypoint (calls hb-connect via sudo)
  bin/hb-connect       - the broker itself; only this may run as the vault user
  setup/setup-vault.sh - one-time user/directory/sudoers installer
  setup/etc-sudoers.d-homelab-broker - the sudoers rule installed by the above
