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
This is a new exact packet; it has not been retried and needs fresh approval.
