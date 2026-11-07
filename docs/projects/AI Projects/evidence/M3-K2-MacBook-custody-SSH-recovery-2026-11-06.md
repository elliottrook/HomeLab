# M3 K2 MacBook custody SSH recovery — 2026-11-06

## Result

The Mac mini can again reach the independent MacBook custodian. The earlier
failure targeted `192.168.1.206`, which is the Mac mini itself, and then used
the wrong local account/key pair against the corrected MacBook address.

The proven mapping is:

- host: `192.168.1.241` (the documented MacBook reservation);
- account: `jasonelliott`;
- identity: the mini's enrolled `~/.ssh/id_ed25519`;
- `IdentitiesOnly yes`.

That exact mapping is now present in the mini's private SSH configuration for
both alias `macbook` and the full address. Independent BatchMode checks through
both forms returned success. No password, private-key content or new access
grant was used.

## Custody verification

The MacBook still holds the R5 sealed evaluation inside its mode-0700 private
directory. Its private key remains mode 0600. The sealed evaluation file was
found mode 0644; although the non-traversable parent already prevented access,
its file mode was tightened to 0600 without reading or changing its bytes.

The five content-free export files remain byte-identical to the accepted
custody record:

- public key: `46685b0e…fa9498`;
- evaluation receipt: `0600a78e…3ddc3`;
- evaluation proof: `912a8736…1261cb`;
- disjointness receipt: `05da5fa2…007f0`;
- disjointness proof: `27bbc168…68fc6`.

No sealed request text was opened or transferred, and no model endpoint was
called. This clears the SSH/custody transport uncertainty; it does not itself
authorize the conditional sealed-evaluation effect.
