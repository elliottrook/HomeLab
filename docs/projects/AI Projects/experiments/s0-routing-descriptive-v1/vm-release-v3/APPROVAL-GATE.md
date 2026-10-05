# V3 execution approval gate

Status: **approval not yet requested for this exact release**.

A future explicit approval may authorize one bounded window to stage the exact
manifest-bound files, create and validate the new ISO and stopped VM120, then perform
one V3 boot and retrieve the bounded evidence. The window must end on any mismatch;
there is no automatic retry.

That approval would cover only the invented fixture. It would not authorize accepted
corpus access, V4 routing evaluation, network attachment, credentials, package
installation, VM118/119 modification, cleanup/destruction, production deployment,
policy or permission change, or Git push. Failure leaves VM120 stopped and retained
for review.
