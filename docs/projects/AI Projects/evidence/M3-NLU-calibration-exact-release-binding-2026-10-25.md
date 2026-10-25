# M3 NLU calibration exact-release binding — 2026-10-25

## Problem

The calibration bundle validator checked a structured manifest and separately
hashed supplied release bytes against the registered threshold policy. It did
not prove that those exact bytes decoded to the manifest under validation. A
caller could therefore pair one valid manifest object with different valid
release bytes that happened to be the artifact registered by policy.

## Correction

The validator now decodes the exact policy-bound release bytes and requires
them to equal the structured manifest before continuing. Malformed UTF-8/JSON
and object/byte mismatch fail closed. The existing canonical manifest digest,
candidate digest, sample minima, custody roles and registered-policy checks
remain in force.

## Validation

The focused NLU suite passes **49/49** under the bundled Python environment.
The new regression test builds two independently valid calibration manifests,
binds policy to one exact byte sequence and confirms that validating the other
manifest against those bytes is rejected.

This is an offline custody correction. It creates or reads no private cases or
labels, selects no threshold, enables no route or egress, and grants no
authority.
