# AsterTV v3 M2 Jen account-authority evidence

Date: 2026-11-04

Target: `AsterTV-Jen` (`192.168.1.180`)

Authorization: `SA-M2-JEN-REAL` in `docs/projects/AsterTV-v3.md`

## Adopted decisions and boundary

AsterTV's schema-versioned local registry is the profile authority. Jason is
the recovery administrator, ordinary profiles initially require no PIN, and
Guest remains fail-closed without a service mapping. Guest catalogue playback
is not enabled because no independently scoped Guest Jellyfin identity/adapter
has been proven.

Only Jen changed. Family, Bedroom, source services, tokens, network policy,
YouTube, Home Assistant, cameras and Aster AI were outside this envelope and
were not modified. Jen's 1080p/18 Mb/s/stereo limits remain a separate client
capability policy and are not AsterTV v3 defaults.

## Non-secret identity inventory

Read-only inspection exposed field names and boolean consistency results, not
credential values. Jen already had independently revocable mode-`0600` custody:

- Jellyfin: one client session; its hashed user subject matched the existing
  provisioning record and its credential was present;
- Audiobookshelf: its account marker, progress enablement and client-key
  custody were consistent; and
- Seerr: the dedicated Jen client token existed mode `0600`.

The registry stores only allowlisted opaque subject references. Runtime
resolution compares each reference with the current local custody. A mismatch
disables only that mapping in memory; it never substitutes another identity.

## Candidate and recovery

- retained candidate: `astertv-v3-m2-jen-authority-r9.tar.gz`
- SHA-256: `ca12344725db6127f95d21bf3f0b45d4f798b536c5208a9a0fc83cdf3c4ce1d4`
- add-on: `script.asterprofiles.v3lab` version `0.3.2`
- retained final checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-authority-r9-final-20261104`
- exact rollback rehearsal checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-authority-r7-rehearsal-20261104`
- accepted-v2 guard: 528 files, `outcome: clean`

The r7 rehearsal migrated, resolved all three services, switched to Jason,
signed out, then restored all 14 checkpointed r6 files byte-for-byte. The v2
guard remained clean. Subsequent r8 testing found and corrected the explicit
malformed-state recovery write; r9 additionally ensures missing state rebuilds
from the local authority rather than recreating synthetic members.

The retained helper supports a guarded full return to r6, while Kodi is idle,
with:

`python3 /storage/.aster-staging/migrate_jen_authority.py rollback --checkpoint-id astertv-v3-m2-jen-authority-r7-rehearsal-20261104`

## Passed live gates

- installation required hostname `AsterTV-Jen`, idle playback and a clean
  528-file accepted-v2 guard;
- migrated registry contains recovery-admin Jason and restricted Guest, starts
  as Guest and is mode `0600`;
- Jason resolves exactly the existing Jellyfin, Audiobookshelf and Seerr
  identities; no credential entered the registry, package, Git or output;
- Media, Books, Music, Requests and administrative Settings resolve for Jason;
  YouTube, Home/cameras and Aster remain denied because they have no authorized
  profile mapping in this milestone;
- switching to Jason, sign-out and both Jason/Guest restart persistence pass;
- Guest direct activation of Media Home and Books returns to public News;
- a deliberately mismatched Jellyfin subject changed its effective state to
  `identity-mismatch` and denied Media while leaving Books resolved;
- malformed state published restricted Guest and the on-screen recovery row
  rebuilt Jason + Guest without retaining the malformed payload;
- missing state rebuilt Jason + Guest from the mode-`0600` local authority and
  remained active as Guest; and
- Kodi ended active and idle, Guest persisted with identity state `resolved`,
  and the accepted-v2 guard remained clean.

## Regression and residual boundary

Ninety-four cumulative tests pass: 27 account/authority/migration, 11 contract,
25 shared-language, 5 trailer, 7 TV, 11 reliability, 4 News and 4 candidate
build tests. The archive is deterministic and contains no authority state,
profile state, credential or Jen playback limits.

This is a retained Jen candidate, not a production v3 release. A Guest-safe
catalogue adapter, named additional household profiles, isolated YouTube state,
Home/camera/Aster identities and Family/Bedroom acceptance require later
bounded milestones.
