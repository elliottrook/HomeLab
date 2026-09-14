# Aster Production Corpus Expansion

> Status: Active — Milestone 5 mirror, evaluation and graduation
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
- The live corpus has eleven accepted sources: the original synthetic manual,
  six version-matched ARR/media products, two selected documentation sources
  and two reviewed local ARR pages. The synthetic source remains an acceptance
  fixture while production coverage expands by milestone.
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

- [x] Reconcile live software versions and exact hardware models without
  reading secret-bearing configuration.
- [x] Map every included system to an official canonical source and licence.
- [x] Select exact Git refs/docs paths and manual variants; quarantine ambiguous
  identities instead of guessing.
- [x] Record size, refresh policy, source class and authority for each source.

Gate: the reviewed register has no unknown source boundary, silent version
substitution, secret-bearing path or unassessed licence.

### Milestone 2 — ARR and media documentation

- [x] Enroll version-matched Sonarr, Radarr, Lidarr and Prowlarr documentation.
- [x] Enroll SABnzbd and Jellyfin documentation relevant to the deployed roles.
- [x] Import the reviewed local ARR operating reference with higher local
  authority and explicit exclusions.
- [x] Verify collection, provenance, navigation and fail-closed behavior.

Gate: all six deployed services have useful complete-source coverage and Aster
can distinguish generic product behavior from lab-specific current state.

### Milestone 3 — Home Assistant documentation

- [x] Enroll version-matched HAOS, Core, Supervisor and backup/recovery docs.
- [x] Enroll official documentation only for the reviewed Hue, Lutron, Matter,
  Aqara-facing, Sonos, HomeKit Bridge, scene/script/timer and automation paths.
- [x] Import the reviewed local Home Assistant reference with higher authority.
- [x] Verify privacy exclusions and exact integration/version provenance.

Gate: Home Assistant questions route to the correct generic, integration or
lab-specific source without exposing entity or household data.

### Milestone 4 — Infrastructure and hardware manuals

- [x] Enroll permitted official docs—and retain reviewed links where copying or
  version matching is unavailable—for OPNsense, Arista EOS, Proxmox, TrueNAS,
  Synology, UniFi, Frigate, Pi-hole, Authentik, Forgejo, NPM,
  Prometheus/Grafana and NUT.
- [x] Enroll exact-model manuals for the recorded compute, switching, wireless,
  storage, camera, TPU and UPS equipment where licensing permits.
- [x] Record metadata-only links for non-redistributable manuals and quarantine
  the model-unknown Binarui AP switch.
- [x] Cross-link each source to the authoritative NetBox/local inventory identity.

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
- [x] **NetBox:** read-only identity/model authority; correct drift separately.
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
| 2026-09-13 | 1 source register gate | Reconciled live versions for TrueNAS, DSM, UniFi OS/Network, Frigate, authentik, Forgejo, NPM, Prometheus and Grafana in addition to the ARR/HA/Proxmox set. Resolved exact release commits where available; enumerated every accepted Git boundary at its expected commit with 2–187 text files and explicit 256 KiB–2 MiB limits. Matched exact official manuals for the recorded Dell, ASRock, LSI, UniFi, CyberPower, Synology, Arista, Reolink and Coral variants. The unknown TP-Link/Binarui models, unavailable Edge 620/Lenovo/APC manual locators, DS220j DSM release and version-mismatched EOS manual remain explicitly quarantined or link-only | **Milestone 1 complete.** The reviewed register contains no mutable accepted Git source, silent version substitution, unassessed derivative path, secret-bearing boundary or accepted ambiguous model |
| 2026-09-13 | 2 ARR batch candidate | Created the reproducible ten-source ARR batch: exact installed tags for Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd and Jellyfin; commit-pinned SABnzbd 5.1 and selected Jellyfin docs; the reviewed lab ARR reference; and a locally authored link page for unlicensed Servarr material. A clean isolated collector run accepted 10/10 with no quarantine, corpus verification checked 10/10, deterministic mirror double-build produced and verified 578 entries, and the Jellyfin CC-BY-ND source remained accepted for human use while producing no derivative entry | Candidate is ready for a separately confirmed production enrollment; no live wiki content changed during validation |
| 2026-09-13 | 2 production enrollment | Queued the ten reviewed sources with the tested batch utility and retained the prior manifest. Production collection accepted all ten alongside the existing fixture (11/11, zero failed or quarantined); verification checked all 11. Two mirror builds returned the same accepted-input/content hashes and 581 verified entries. The source dashboard listed all ten with no pending candidates, `/healthz` returned `ok`, and intake plus both timers remained active. Jellyfin CC-BY-ND documentation remained human-only and generated no derivative directory | Complete version-matched human coverage is live for all six deployed ARR/media services without widening authority or exposing configuration |
| 2026-09-13 | 2 authority gate | Review found the first accepted lock labelled local-reviewed and upstream sources identically. Added an explicit provenance mapping and regression, bringing the suite to 47/47. The corrected collector was tested from a disposable deployed tree, installed with a retained rollback copy, and re-collected 11/11. The local operating reference and reviewed link page now declare `current-with-exclusions`; product documentation remains `upstream-reference`. Two rebuilt mirrors matched at content SHA-256 `d255484ed484f6f91713aa3573ac5f712f67321ffeab8e00dad2386621bc504e` and verified 581/581 | **Milestone 2 complete.** Generic product behavior and lab-specific current state are machine-distinguishable. Corpus health has no failures, broken links, stale sources or unclassified sources; its 157 duplicate extractive claims remain a warning for Milestone 5 quality evaluation rather than an integrity failure |
| 2026-09-13 | 3 Home Assistant batch candidate | Created the five-source batch for exact Core 2026.9.1, OS 18.2 and Supervisor 2026.09.0 releases; commit-pinned user, integration, automation and recovery documentation; and the reviewed local operational reference. Privacy review narrowed that local source to `human-only` because it contains household workflow labels and internal addressing. The full suite passes 47/47. An isolated collector accepted and verified 5/5 with no failures or quarantine; deterministic mirror build produced and verified 209 entries and no local-reference derivative directory | Candidate covers only the reviewed Hue, Lutron, Matter, Sonos, HomeKit, scene, script, timer, automation, OS and backup paths. Production enrollment remains a separately confirmed operation |
| 2026-09-13 | 3 production enrollment and gate | Enrolled the five reviewed sources alongside the existing corpus. Collection accepted 16/16 total with zero failures or quarantine, and verification checked all 16. Two mirror builds matched at accepted-input SHA-256 `e948a20ab201823fc987c51898f21c8a85f29ab5c536a6f3bf7d624bca319906` and content SHA-256 `43d6516b30f4132a07d109ec2e096f4e6790f8b4266a9fc3b7319ce49ef7b5b8`; 790/790 entries verified. Dashboard navigation found all five sources with no pending work. The local source is `current-with-exclusions`/`human-only`; generic and integration material is `upstream-reference`/`allow-derived`. A direct mirror scan found none of the reviewed household workflow labels or internal addresses, while service, recovery and version indexes contain the bounded HA docs and HAOS sources. Portal and timers remain active | **Milestone 3 complete.** Generic, integration and local-current sources are provenance-distinct; the private local reference remains human-readable without entering the new derivative set. Corpus health reports no failures, broken links, staleness or unclassified sources. Its 165 duplicate extractive claims remain an explicit Milestone 5 quality warning |
| 2026-09-13 | 4 core infrastructure candidate | Enumerated exact pinned paths for OPNsense firewall/DNS/backup/diagnostics, Proxmox VE host/network/firewall/guest/storage/backup, Pi-hole DNS, and NUT service/driver/shutdown documentation. The first isolated run failed closed because two broad NUT compilations contain a password-syntax example matching the secret guard; removed those duplicate compilations while retaining the focused operational and man-page sources. The corrected run accepted and verified 4/4 with no quarantine; deterministic mirror build produced and verified 471 entries at content SHA-256 `7b903b8d441f41ff40be333905dc73a5251513e52275d2adc8338274090e767a` | Core batch candidate is clean. Remaining infrastructure repositories, exact-model manuals, metadata-only links and NetBox identity cross-links remain inside Milestone 4 before its production gate |
| 2026-09-13 | 4 infrastructure services candidate | Resolved exact registered commits and bounded operational paths for TrueNAS SCALE, Frigate, authentik, Forgejo, Nginx Proxy Manager, Prometheus and Grafana. Initial broad selections were rejected by the unchanged secret/injection scanner. Replaced them with explicit useful files that omit credential examples, a misleading TrueNAS “system prompts” phrase and Forgejo's runner-state exfiltration scenario. The second isolated run accepted six sources; the final narrowed Forgejo source then accepted and verified independently and produced 124 verified entries | All seven service candidates now pass the real collector without weakening security checks. A full combined build will run with the manual/link/identity batch before production enrollment |
| 2026-09-13 | 4 hardware, identity and combined candidate | Validated official exact-model locators. Synology DS220j and DS920+ installation PDFs return direct `application/pdf` responses within fixed 4/8 MiB bounds and passed protected human-only collection. Arista's exact DCS-7050TX-64 HTML guide remains link-only because the PDF is bot-gated; Coral's indexed exact-part datasheet origin returns 404. Recorded exact official links for Dell, ASRock, LSI, UniFi, Reolink, CyberPower and APC, and retained Edge 620, Lenovo, TP-Link and Binarui uncertainties without guessing. A human-only identity page binds every accepted software/manual source to the recorded inventory identity. The hardware batch passed 3/3 and generated zero derivative entries. The final combined isolated run accepted and verified 14/14 with zero failures or quarantine; deterministic mirror build produced and verified 1,335 entries at content SHA-256 `0d2f14df49df0857881f99df4759d0993d67a817dd6f4bfc4c5d3e649da8d430` | Complete Milestone 4 candidate is ready for separately confirmed production enrollment; security checks and model/licence ambiguity boundaries remain intact |
| 2026-09-13 | 4 production enrollment and gate | Enrolled all 14 reviewed candidates beside the existing corpus. Collection accepted 30/30 total with zero failures or quarantine and verification checked every source and retained original. Two mirror builds matched at accepted-input SHA-256 `780b0a1a7255990a557c36e717debc1f3d1148c1311196485e1de6ac0948324b` and content SHA-256 `6a88911b0a4e13ec35e4644f53738fd6bdcf7cb3d520c8209b45d06f9ed0b962`; 2,125/2,125 entries verified. Dashboard navigation found all 14 with no pending candidates; both exact Synology PDFs retain `application/pdf`/`human-only` provenance, and the two PDFs plus identity page have no derivative directories. Asset, service, recovery and version indexes contain the core infrastructure sources. Portal and timers remain active | **Milestone 4 complete.** Every copied manual matches a recorded model, non-copyable or unavailable material is linked/quarantined explicitly, and current-state authority remains with NetBox/local inventory. Corpus health has no failures, broken links, stale or unclassified sources; 248 duplicate extractive claims remain the known Milestone 5 quality warning |
| 2026-09-13 | 5 extraction-quality candidate | Analysed all 2,125 production entries: all 248 exact duplicates were cross-source, with none repeated inside a source. Most were shared licence bodies or structural fragments such as source markers, headings and fence tokens. Pipeline 1.4.0 now keeps complete accepted sources and licence provenance but does not emit licence-file or structural-only sections as retrievable claims; file-aware locators improve human fallback. A new regression brings the suite to 48/48. Rebuilding the 14-source Milestone 4 corpus produced and verified 1,357 source-located entries with zero duplicate, broken-link, stale or unclassified findings | Isolated corpus health is fully healthy without deduplicating or discarding substantive cross-source operational claims. Production deployment and complete 30-source measurement remain separately gated |
| 2026-09-13 | 5 extraction-quality production | Retained the full pre-change mirror and deployed 1.4.0 after 48/48 disposable tests. The complete 30-source double-build verified 1,813 entries and reduced duplicates from 248 to seven; health deliberately remained warning. Review proved all seven were attribution boilerplate: an Open Home Foundation badge, a shared GitHub-issues notice and sponsor acknowledgements. Pipeline 1.4.1 adds only those precise exclusions and retains the 1.4 mirror separately. Its complete production double-build matched at content SHA-256 `11e0dee8a518502ef69b94e22331ed4ac9e63cb0e0420a3d2481284c7b35f2b5`; 1,796/1,796 entries verify and all five human-only sources remain excluded. Corpus health is `healthy` with zero failures, warnings, broken links, duplicates, stale sources or unclassified sources | Production extraction-quality gate passed without weakening source safety, merging distinct provenance or removing substantive operational claims; pre-1.4 and 1.4 rollback trees remain retained |
