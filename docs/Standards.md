# HomeLab Engineering Standards

The normative process for creating and running enhancement projects, including
the lab ethos, authorization streams, risk assessment, milestone gates and
integration checklist, is [HomeLab Project Creation Standard](Project-Creation-Standard.md).

## Core Principles

1. Document before implementing.
2. Automate repetitive work.
3. Every change must be backed up.
4. Security before convenience.
5. Prefer open standards.
6. Version control everything.
7. Test before deployment.
8. Keep production and lab separated.
9. Minimize single points of failure.
10. Build for long-term maintainability.

---

## Documentation Rules

Every major project must include:

- Purpose
- Design
- Configuration
- Validation
- Recovery
- Pre-start risk assessment
- Authorization stream
- Persistence/resume plan
- Systems-of-record and integration impact assessment

---

## Operational Workflow

Plan

↓

Document

↓

Implement

↓

Validate

↓

Backup

↓

Commit to Git

↓

Tag Release

Tags and releases are optional and require the applicable remote-operation
authorization. The standard milestone unit is a validated, documented commit.
