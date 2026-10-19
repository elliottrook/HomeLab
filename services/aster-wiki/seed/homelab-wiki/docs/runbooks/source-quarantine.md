# Review a quarantined source

> Authority: reviewed-wiki-runbook
> Reviewed: 2026-09-10

Read the bounded failure reason and safe extracted preview. Confirm hostname,
scope, media type, size, provenance and license. Correct the manifest candidate
or retire it; never bypass a blocking validator.

`repository-ref-commit-mismatch` means the configured branch or tag now points
at a different commit than the reviewed pin. It does not mean the accepted Wiki
was altered: the last accepted corpus remains live. Review the upstream delta.
For a moving documentation branch, retain the reviewed commit by using that
same 40-character SHA for both `git_ref` and `expected_commit`; update both only
after a later revision has been reviewed. Use a release branch only when its
movement is itself intended to trigger another review.
