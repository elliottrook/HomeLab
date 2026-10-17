# M3 decision sensitivity boundary — offline correction

**Evidence class:** source-only contract check. No route, model, tool, network
or production configuration changed.

Review of the offline Decision contract found that `validate_proposal` checked
capability identity and registry freshness but did not compare a planned
capability's declared sensitivity with the request's sensitivity. A synthetic
`public` request could therefore pass the compatibility check while planning
an `internal` capability. The catalogue and request remain non-authoritative;
this was a contract omission, not evidence of a live privacy incident.

The validator now rejects any planned capability whose registered sensitivity
is higher than the request's (`public < internal < personal`). Focused
negative checks cover public-to-internal and internal-to-personal cases. The
combined `test_contracts` and `test_conformance` suites passed 32/32 using the
bundled Python runtime.
The default system Python lacked Pydantic and could not run those suites; that
environment failure was not an implementation failure.

This check does not classify a request's sensitivity, authenticate a caller,
grant a capability, prove routing quality, or permit model egress. Those
remain separate policy, identity and evaluation gates. Automatic routing
stays off.
