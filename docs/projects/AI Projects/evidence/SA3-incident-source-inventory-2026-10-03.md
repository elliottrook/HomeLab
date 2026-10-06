# SA3 incident source inventory

Date: 2026-10-03  
Status: **SOURCE DISCOVERY ONLY; NO CASES COLLECTED**

## Purpose

This inventory identifies existing operational records that may support later
SA3 incident-case authoring. It is not an incident corpus, a label set, an
answer key, or an evaluation dataset. No source content has been copied into
the custody directory.

## Candidate sources

| Source | Potential incident family | Collection risk | Current disposition |
|---|---|---|---|
| `docs/runbooks/Lab-Health-Remediation-2026-09-23.md` | Monitoring finding, diagnosis, bounded remediation, verification | Contains infrastructure identifiers and operational detail | Candidate only; extract a sanitized abstract later |
| `docs/runbooks/Paperless-IP-Collision.md` | Address collision, scoped correction, network validation | Contains addresses, MACs, hostnames, rule identifiers and checkpoints | Candidate only; substantial sanitization required |
| `docs/runbooks/ARR-SSO-Repair-2026-09-27.md` | Authentication regression, negative tests, bounded proxy repair | Contains service topology and configuration detail | Candidate only; substantial sanitization required |
| `docs/runbooks/Backup-Coverage-Audit-2026-09-26.md` | Protection-gap assessment and decision boundary | Contains storage and service inventory details | Candidate only; substantial sanitization required |
| `docs/runbooks/Video-Archiver-Repair-2026-09-28.md` | Failed media-processing repair and postcheck | Contains operational hashes, media references and implementation detail | Candidate only; substantial sanitization required |

## Exclusions and limits

The source documents remain their own historical records. They are not to be
copied wholesale into an SA3 case, answer key, prompt, retrieval corpus or test
fixture. Any later case must omit credentials, raw logs, private content, live
tool output, production commands, network identifiers, checkpoint paths and
model output.

For the single-operator path, Jason must explicitly accept each sanitized case
and its temporal assignment before it enters development or sealed holdout
storage. The resulting evidence remains within-lab and non-independent.

## Next action

Create no more than one sanitized candidate abstract at a time, retain it in
private draft storage, and obtain Jason's acceptance before durable retention.
