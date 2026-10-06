# SA3 Doctor unknown reconciliation candidate

Status: offline candidate; not deployed.

A new operator-only store method can close only an exact `doctor` job in the
`unknown/interrupted/none` state. It records the original result in an audit
table and changes the job to failed with no diagnostic claim. It has no HTTP,
model, worker, or automatic invocation path. 23 Lab Operations tests passed in
the deployed Aster virtual environment. Deployment and use remain separate
Stream A gates.
