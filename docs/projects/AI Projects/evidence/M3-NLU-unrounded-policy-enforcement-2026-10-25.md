# M3 NLU unrounded policy enforcement — 2026-10-25

> Status: offline boundary correction; no routing, egress or authority

## Finding

The threshold selector calculated exact calibration coverage and selective-error
ratios, rounded both values to twelve decimal places for its result artifact,
and then applied the registered policy to those rounded report values. A
candidate just outside a registered boundary could therefore be admitted when
rounding moved the reported value onto the accepted side of the boundary.

## Correction

Policy enforcement now compares the unrounded ratios with the registered
minimum coverage and maximum selective-error rate. The bounded selection
artifact still reports twelve-decimal values for stable review output. A
regression case constructs a candidate whose true error rate exceeds the
registered maximum by less than the report precision and verifies that no
threshold is selected.

## Verification

The focused NLU suite passed **53/53** tests with the repository sources on
2026-10-25. The test used the bundled workspace Python runtime and did not read
private cases, call a model, contact a provider or change a live route.

This correction hardens future calibration only. No threshold policy is
registered or frozen, and automatic routing remains off.
