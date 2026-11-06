# SA4 LXC observer-proof exchange source — 2026-11-05

The LXC side of the independent-observer pause now has a fixed file protocol.
It accepts only the compiled canonical observer statement, sequences one or two
requests, creates each request exclusively as mode `0600` under a root-owned
mode-`0700` fixed runtime directory, and accepts only a single-link regular
root-owned mode-`0600` 512-hex signature response.

Duplicate requests, changed directory custody, malformed responses and
symlinked responses fail closed. A bounded timeout retains the request for
manual reconciliation. The protocol neither contains nor accesses the
observer private key and has no arbitrary command surface.

Five focused tests pass, taking the complete SA4 suite to 176/176. The source
is not installed. Next is the Proxmox half that reads only these fixed requests,
invokes only the installed bounded observer signer, and returns only the fixed
signature response, followed by joined protocol rehearsal and inactive-install
review.
