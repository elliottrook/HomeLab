# Brand Design standard

This directory contains the durable operating standard used by the installed `$brand-design` skill. It is not a HomeLab enhancement project and has no completion/archive lifecycle.

## Relationship between the skill, standard and brand records

- The installed skill orchestrates work and selects the applicable image-generation, PDF, SVG, validation and deployment capabilities.
- `BRAND-CREATION-STANDARD.md` defines the mandatory gates and deliverables.
- `docs/templates/brand-design/` contains the files copied into each new brand engagement.
- `/Users/jasonelliott/Documents/Brand Asset Library` is the canonical local store for brand-specific inputs, working files, approved assets, sources and releases.
- Git stores the reusable standard, schemas and templates—not customer-specific generated artwork or large release packages.

Each invocation creates or resumes an isolated project inside the resolved brand directory and advances it through the standard milestones. A brand engagement may finish, pause or remain blocked; this reusable standard remains current until deliberately revised.

## Files

- `BRAND-CREATION-STANDARD.md` — normative workflow, gates, storage model and completion criteria.
- `MIGRATION-AND-COMPATIBILITY.md` — crosswalk from Brand SVG Studio and the compatibility policy.
- `EVIDENCE-REQUIREMENTS.md` — minimum evidence needed to make approval, validation and deployment claims.
- `FORGEJO-DEPLOYMENT-GUIDANCE.md` — design guidance for securely synchronizing changes through private Forgejo.
