# V5b exact approval gate

No file in this packet is self-authorizing. A human approval must name frozen
release-manifest SHA-256
`721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`
and authorize the one mutation window in `PREFLIGHT.md`.

Approval permits one stage/create/boot/capture/stop-and-retain sequence for VM123.
It does not permit a retry, changed artifact, tuning or relabeling, network or
credential attachment, promotion, cleanup, mutation of VMs118–122, or Git push.
Any preflight drift stops the operation and grants no authority to improvise.
