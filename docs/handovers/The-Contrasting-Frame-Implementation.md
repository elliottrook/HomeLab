# Dual-site photography publishing implementation handoff

Owner: Jason Elliott. Prepared 2026-10-09. Start with M0, not deployment.

Update 2026-10-09: Jason added The Closet Fatman at
`theclosetfatman.com`. It shares the Contrasting Frame page geometry and the
same private workflow, but has separate site-keyed content, approvals, assets,
releases and a future whimsical brand package. The dearJoe font is Contrasting
Frame-only. The shared private desk is `tcf.elliottrook.com` and uses a
`Contrast` / `Closet` pill. Closet assets are authoritative at
`/Users/jasonelliott/Documents/The Closet Fatman`; its website/template will
arrive later. Media is normally distinct, with deliberate cross-publication
represented by two independently reviewed and approved records.

## Execution order

Jason requested a new Codex conversation to complete this project in Stream A,
but explicitly required the first milestone to be Stream M. Read
[the hosting and publishing project](../projects/The-Contrasting-Frame-Hosting-and-Publishing.md)
and both applicable guides: the
[public brand style guide](../design/The-Contrasting-Frame-Style-Guide.md) and
[Aster internal UI style guide](../design/HomeLab-UI-Style-Guide.md).
Begin the design discussion with Jason, flesh out the workflow and concrete
hosting/security choices, record his acceptance, then transition to A1–A6.
No infrastructure mutation or public exposure before M0 passes.

Do not merely restate the plan and call the project complete. After the design
gate, implement, validate, document, prove recovery and provide operator training
within the accepted autonomous scope. Preserve non-waivable stops and platform
approvals. No new model choice or recurring Codex automation is requested.

## Files and accepted assets

Preparation checkout:
`/Users/jasonelliott/Documents/ChatGPT/Aster Hardware Development/homelab-work`

Start by reading `AGENTS.md`, `docs/Project-Creation-Standard.md`,
`docs/Standards.md`, project portfolio, the project above and both applicable
style guides. The TCF guide governs the public website and rendered public
previews. The Aster internal guide and HomeLab app-icon family govern the
private Content Desk. The preview embedded in the Desk must remain faithful to
the TCF guide.

Accepted website source:
`/Users/jasonelliott/Documents/ChatGPT/Aster Hardware Development/sites/the-closet-fatman`
(commit `5b23ccb9d8d746196948246f936427495220ed28`, separate repository).
Preserve and migrate this source; keep its private hosted reference and audience
unchanged. Do not deploy its .openai hosting identity to the internal server.
Use static dist output, not a dependency on Sites at runtime.

Additional logo sources:
`/Users/jasonelliott/Documents/ChatGPT/Aster Hardware Development/tcf-vector-assets/website-adapted`.

Font purchase pack:
`/Users/jasonelliott/Downloads/dearJoe 4 R PRO WEB Pack/dearJoe 4 regular PRO_WEB.zip`
contains the JBgfx Webfont EULA. The chosen font is dearJoe 4 Regular PRO, not
The Contrasting Hand or the other four comparison fonts. Licence/domain/traffic
verification is a launch gate; do not put the pack or receipts in public Git.
The current light-background camera uses dark lettering with its full-colour
emblem; do not restore unreadable light lettering on warm paper.

## Forgejo reconciliation

Live Forgejo:
`https://git.elliottrook.com/jason/homelab.git`,
SSH clone path `git@192.168.20.30:jason/homelab.git`.
The inspected live main was `2f929145953445b1be3695f02ee5c969bc1e9c1a`.
This preparation checkout's pre-change HEAD was
`5d260ba6bf14ff786579b353d5d44c314000e3e7` and origin points to a local clone
chain under Documents/Codex, not directly to live Forgejo.
Standard/style blobs matched live Forgejo before our edits.

Transfer only this project's focused documentation commit/patch onto a fresh,
current authoritative checkout. Preserve other agents' commits and work;
inspect diff and history before any push. Do not push the whole divergent local
branch or change its origin casually. Repository instructions require explicit
confirmation immediately before each remote write, even in Stream A.
No Forgejo write was made by project preparation. Verify the automatic GitHub
mirror read-only after an approved Forgejo push; never push directly to GitHub.

## Initial conversation

Explain the proposed separation of public static origin, private Content Desk
and TrueNAS curated assets. Ask a compact set of design questions: where Jason's
chosen pictures/stories live and how he wants to edit; review and scheduling
preferences; approved public launch content/rights; domain/mail access and edge
provider budget/privacy. Show a simple private editor mockup and one image/story
preview before committing to a CMS or service stack.

Recheck current LAN resources, NetBox allocations, broker/inference capability,
font licence and Cloudflare image-delivery terms. The project lists exact
observed storage paths and provisional new paths, clearly distinguished.
Do not mount originals or private editorial datasets in the public origin.
Do not silently upload photos to a cloud AI.

## Completion evidence

Persist each milestone's result, approved decisions, current step, safe next
action and rollback checkpoint in Git-tracked non-secret text. Service job state
must be durable, locked and atomic. AI suggestions remain drafts; scheduled
promotion uses explicit immutable approvals. Graduate only after two
independent scheduled passes, isolation/rights checks, isolated restore,
monitoring/NetBox reconciliation, performance review and Jason's validated
operator walkthrough.
