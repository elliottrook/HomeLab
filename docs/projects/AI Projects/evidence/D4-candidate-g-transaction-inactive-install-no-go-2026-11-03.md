# D4 candidate-g transaction inactive install — NO-GO and correction

The approved v1 installation failed closed at its guest import postcheck. The
new wrapper imported the prior SA3 wrapper as a module, but the prior wrapper
is deployed only as a fixed executable. No runner activation, booking, lease,
service stop, model request or production effect occurred.

Host and guest targets rolled back to absence, the old release manifest was
restored, both root-only checkpoints were retained and production remained
healthy. Platform commits `1b471579` and `51004d55` retain the diagnosis and
make the wrapper self-contained under a fresh v2 identity.

The corrected suite passes 58/58. A direct target-Linux import passed, and its
temporary files were removed. Two corrected seven-file bundles match at
`b7e415c2cdacdd7227b362e8dec48cf6506690824a7deba189d8c5c3700a0bb5`.

Jason authorized continuing Stream A without routine approval pauses. The
fresh v2 install then completed successfully and is retained in platform
commit `52278a9c`. The installed inactive identities are:

- host transaction `b906f30d…fa26`;
- host listener adapter `e668c6ca…3ae`;
- host release manifest `9dfea8ad…792`;
- guest wrapper `8e9e01eb…36f`.

Both host and guest imports passed. The v2 checkpoints are root-owned mode
0700 with mode-0600 manifests. No runner kind or unit was activated, no booking,
lease, service stop or model request occurred, and the accepted production
services remained healthy. The failed v1 evidence and rollback checkpoints
remain retained. Candidate-g is now ready for source-only runner activation
implementation and tests; it is not ready to run.
