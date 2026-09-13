# Aster Production Corpus Expansion

> Status: Active — Milestone 1 source register
>
> Project owner: Jason
>
> Proposed: 2026-09-13
>
> Started: 2026-09-13
>
> Authorization: Stream A — accepted by Jason 2026-09-13

## Purpose and desired outcome

Populate the graduated private HomeLab wiki with useful, version-matched,
human-readable documentation for the systems actually deployed in Jason's lab.
Replace the synthetic-only corpus with a production corpus covering the ARR
stack, Home Assistant, infrastructure software, hardware manuals and the
reviewed local operating references. Generate and validate Aster's derived
mirror without changing Aster's authority or tool access.

The target is useful coverage, not indiscriminate mirroring. Git sources are
restricted to documentation, release and schema paths relevant to installed
versions. Vendor manuals enter protected local storage only where local-use
terms permit; otherwise the wiki records versioned metadata and the canonical
vendor link. Generated summaries remain non-authoritative.

## Current state and evidence

- The wiki, authenticated intake, daily collector, monthly corpus health,
  protected originals, deterministic mirror and Aster retrieval path are
  graduated and healthy on LXC 113/LXC 104.
- The live corpus has one synthetic manual source and seven synthetic/operator
  seed pages. It is an acceptance fixture, not production coverage.
- Installed ARR-family versions are Sonarr 4.0.19.2979, Radarr 6.3.0.10514,
  Lidarr 3.1.0.4875, Prowlarr 2.5.2.5491, SABnzbd 5.1.2 and Jellyfin 10.11.11.
- Home Assistant runs HAOS 18.2, Core 2026.9.1 and Supervisor 2026.09.0, with
  Hue, Lutron Caseta, Aqara Matter, Sonos and HomeKit Bridge in the reviewed
  integration boundary.
- Production infrastructure includes OPNsense on VMware SD-WAN Edge 620,
  Arista DCS-7050TX, Proxmox on Dell Precision T5810, TrueNAS SCALE 25.10.5,
  Synology DS920+/DS220j, UniFi Network 10.5.67 with two U7 Pro XG APs,
  Frigate with Reolink Duo 2V PoE and Coral TPU, Pi-hole, Authentik, Forgejo,
  NPM, Prometheus/Grafana, NUT and the recorded CyberPower/APC UPS models.
- Official initial Git candidates include the upstream Sonarr, Radarr, Lidarr,
  Prowlarr, SABnzbd, Jellyfin, Home Assistant Core, HAOS, Supervisor,
  Home Assistant documentation and official add-on repositories. Exact refs
  and permitted documentation paths must be resolved before enrollment.

## Scope and exclusions

### Included

- Version-pinned official documentation paths and release notes for the six
  deployed media services.
- Home Assistant user documentation, HAOS/Supervisor recovery material and
  only the integrations used in this lab.
- Official documentation for deployed infrastructure software and services.
- Exact-model vendor manuals for recorded networking, storage, camera, compute,
  wireless and UPS hardware where model identity and licence are verified.
- Reviewed current-state pages from `homelab`/`homelab-reference`, linked or
  version-imported without changing their authority.
- Deterministic mirror rebuild, provenance verification, focused Aster
  retrieval evaluation, corpus-health and recovery evidence.

### Excluded

- Whole source trees, issue trackers, forums, community wikis and arbitrary
  Internet crawling.
- Secrets, raw configurations, user/entity/media names, histories, telemetry,
  credentials, serial numbers in derived public-style pages or private data not
  required for documentation.
- Unverified model matches, firmware binaries, redistribution of manuals whose
  terms do not permit it, and any automatic software/firmware update.
- New Aster tools, network authority, Home Assistant control or ARR mutation.
- Public exposure, authentication weakening, firewall broadening or changes to
  production application configuration.

## Authority and collection model

Current live reports and adopted systems of record continue to outrank the
wiki. Reviewed HomeLab references own lab-specific topology and procedures.
Version-matched official documentation owns product behavior within its stated
version. Vendor manuals own model specifications. The mirror owns no facts: it
must cite the complete human source hash and locator and fall back when scope,
version or authority is insufficient.

The collector may fetch only accepted HTTPS hosts and Git repositories. Each
source records publisher, canonical URL, selected ref, exact path boundary,
licence status, installed-version relationship, size limit and refresh policy.
Redirects outside the displayed/accepted boundary quarantine the source.

## Pre-start risk assessment

- **Privacy/confidentiality:** upstream material is public, but local system
  pages are private. Controls: no raw configuration or credentials; private
  repositories and authenticated portal remain unchanged.
- **Integrity:** wrong product variants or current `main` documentation could
  teach behavior absent from installed versions. Controls: exact model/ref
  matching, installed-version annotations, quarantine on ambiguity and current
  HomeLab references taking precedence.
- **Licensing:** manuals may allow reading but not redistribution. Controls:
  record licence evidence; retain protected local originals only when allowed;
  otherwise store metadata, hash where obtainable and canonical link.
- **Availability/storage:** large repositories/PDFs could exhaust or slow the
  collector. Controls: documentation-only paths, per-source limits, staged
  batches, existing atomic publication and last-good rollback.
- **Supply chain:** upstream Git content can contain malicious instructions.
  Controls: text is data, never executable; existing secret/injection lint,
  exact-path provenance and adversarial evaluation remain mandatory.
- **Recovery:** bad batches must not replace accepted knowledge. Controls:
  verify the current LXC113 archive and accepted hashes before the first batch,
  publish atomically, retain prior corpus/lock/mirror and test rollback.
- **Interruption:** collection and mirror publication are bounded background
  jobs; the existing wiki remains available. Abort on secret exposure,
  unexplained authority conflict, licence uncertainty, model ambiguity,
  unbounded scope, failed backup or failed accepted-state verification.
- **Residual risk:** official documentation can change or omit deployment-
  specific behavior. Monthly staleness checks and human-source fallback reduce
  but do not eliminate that risk.

## Persistence and synchronization

The source register, exact accepted refs, paths, hashes, licence decisions,
batch results and rollback points live in this document and the wiki manifest.
Each completed milestone ends with validation, evidence, a focused local commit
and one separately confirmed Forgejo push. Intermediate stages do not push.

## Milestones

### Milestone 1 — Exact inventory and source register

- [ ] Reconcile live software versions and exact hardware models without
  reading secret-bearing configuration.
- [ ] Map every included system to an official canonical source and licence.
- [ ] Select exact Git refs/docs paths and manual variants; quarantine ambiguous
  identities instead of guessing.
- [ ] Record size, refresh policy, source class and authority for each source.

Gate: the reviewed register has no unknown source boundary, silent version
substitution, secret-bearing path or unassessed licence.

### Milestone 2 — ARR and media documentation

- [ ] Enroll version-matched Sonarr, Radarr, Lidarr and Prowlarr documentation.
- [ ] Enroll SABnzbd and Jellyfin documentation relevant to the deployed roles.
- [ ] Import the reviewed local ARR operating reference with higher local
  authority and explicit exclusions.
- [ ] Verify collection, provenance, navigation and fail-closed behavior.

Gate: all six deployed services have useful complete-source coverage and Aster
can distinguish generic product behavior from lab-specific current state.

### Milestone 3 — Home Assistant documentation

- [ ] Enroll version-matched HAOS, Core, Supervisor and backup/recovery docs.
- [ ] Enroll official documentation only for the reviewed Hue, Lutron, Matter,
  Aqara-facing, Sonos, HomeKit Bridge, scene/script/timer and automation paths.
- [ ] Import the reviewed local Home Assistant reference with higher authority.
- [ ] Verify privacy exclusions and exact integration/version provenance.

Gate: Home Assistant questions route to the correct generic, integration or
lab-specific source without exposing entity or household data.

### Milestone 4 — Infrastructure and hardware manuals

- [ ] Enroll official docs for OPNsense, Arista EOS, Proxmox, TrueNAS, Synology,
  UniFi, Frigate, Pi-hole, Authentik, Forgejo, NPM, Prometheus/Grafana and NUT.
- [ ] Enroll exact-model manuals for the recorded compute, switching, wireless,
  storage, camera, TPU and UPS equipment where licensing permits.
- [ ] Record metadata-only links for non-redistributable manuals and quarantine
  the model-unknown Binarui AP switch.
- [ ] Cross-link each source to the authoritative NetBox/local inventory identity.

Gate: every accepted manual matches an inventoried model, retains provenance and
does not overwrite current-state authority.

### Milestone 5 — Mirror, evaluation and graduation

- [ ] Rebuild and independently verify the deterministic mirror twice.
- [ ] Evaluate representative ARR, Home Assistant, network, storage, power and
  recovery questions, including stale/version conflict and poisoned-source cases.
- [ ] Run corpus health, Doctor and existing Aster regressions.
- [ ] Prove rollback and recovery coverage for the expanded corpus.
- [ ] Record exact accepted versions/hashes, owners, limitations and maintenance.

Gate: production documentation is navigable and recoverable, every mirror
claim maps to an exact accepted source, critical evaluations pass twice and
Aster's authority remains unchanged.

## Integration impact assessment

- [ ] **HomeLab Doctor:** retain existing wiki checks; add only actionable source
  batch/version drift if monthly health does not already cover it.
- [ ] **Monitoring/alerting:** reuse daily/monthly reporting without duplicate noise.
- [ ] **Backup/recovery:** verify expanded originals/corpus/mirror coverage and restore.
- [ ] **NetBox:** read-only identity/model authority; correct drift separately.
- [ ] **Human wiki:** primary project output.
- [ ] **Aster mirror/snapshot:** rebuild and validate without authority expansion.
- [ ] **Operational reference/runbooks:** import/link reviewed current state.
- [ ] **Repository documentation:** project, portfolio and source ownership records.
- [ ] **Diagrams/rack:** not applicable unless discovery finds actual documented drift.
- [ ] **Homepage:** existing authenticated link is sufficient unless health behavior drifts.
- [ ] **Authentication:** existing owner-only Authentik boundary remains unchanged.
- [ ] **DNS/certificates/firewall:** no change expected or authorized.
- [ ] **Automation:** reuse the graduated collector and health timers.
- [ ] **Security inventory:** no secrets in sources; restrictive protected-original modes.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-13 | Proposal discovery | Reconciled the graduated synthetic-only corpus with reviewed ARR, Home Assistant, hardware and network inventories. Confirmed initial official Git candidates and identified model/version/licensing, corpus-size and authority risks | Proposed bounded production-corpus expansion; no source was enrolled and no remote system was modified before authorization |
| 2026-09-13 | Authorization | Jason accepted the documented Stream A scope, risks, exclusions, recovery controls and milestone gates | Project active; bounded autonomous implementation may proceed, while repository/platform remote-mutation confirmations and non-waivable stops remain in force |
| 2026-09-13 | 1 immutable Git prerequisite | Live reconciliation confirmed HAOS 18.2, Core 2026.9.1, Supervisor 2026.09.0 and Proxmox VE 9.2.10; the fresh bounded ARR report remained healthy/warning as expected without exposing configuration. Exact installed release refs resolved for Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd, Jellyfin, HA Core, HAOS and Supervisor. Review then found the pilot collector fetched Git `HEAD` only and accepted only three text suffixes. Added required safe Git ref plus expected 40-character commit fields, ref/commit mismatch quarantine, portal inputs and support for Markdown, RST, AsciiDoc and MDX documentation. Two new regressions prove missing pin rejection, tagged checkout, additional document formats and fail-closed commit drift; 41/41 tests pass | No production Git source was enrolled against a mutable branch. The version-pinning candidate is locally validated and awaits bounded deployment before any real Git enrollment |
| 2026-09-13 | 1 pinned collector deployment | Retained `/opt/aster-wiki/aster_wiki.before-6cdac27`, deployed the exact four application modules, installed Debian Git 2.47.3 plus only its required dependencies and restarted only the intake service. The complete disposable deployed suite passes 41/41, including a real tagged checkout and expected-commit mismatch quarantine. Accepted-corpus verification remains 1/1, portal health returns `ok`, and intake, daily collection and monthly corpus health remain active. Removed the disposable deployment/test archives and trees while retaining the rollback copy | LXC 113 is ready for immutable Git sources without changing the accepted corpus or service authority |
| 2026-09-13 | 1 source licence boundary | Added validated `allow-derived`/`human-only` source policy and bounded licence identifiers; propagated both through intake, accepted provenance and derivative entry provenance. Pipeline 1.3.0 retains human-only sources in accepted input while generating no Aster entries from them. New fail-closed policy, exclusion and attribution regressions bring the local suite to 44/44 passing | No-derivatives and vendor-manual content can be retained for private human use without silently entering Aster's derivative mirror; production deployment remains a separately validated change |
| 2026-09-13 | 1 source licence deployment | Retained `/opt/aster-wiki/aster_wiki.before-bd32e56`, deployed the five policy-aware modules and restarted only intake. The complete deployed suite passes 44/44 after restoring the omitted disposable seed fixture; accepted-corpus verification succeeds, `/healthz` returns `ok`, and intake, collector and corpus-health timers are active. All disposable archives and test trees were removed | Production now enforces human-only exclusion and licence provenance before restricted source enrollment; accepted corpus content remains unchanged |
