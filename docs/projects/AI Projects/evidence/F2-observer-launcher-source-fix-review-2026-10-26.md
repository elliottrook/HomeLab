# F2 observer launcher source-fix review — 2026-10-26

Stream A independently reviewed platform commit `d00073e5`, which corrects the
October 26 observer communication defect without installing or activating it.

The coordinator now selects `subprocess.Popen` when no test launcher is
injected. It therefore returns the live process contract expected by
`communicate()`, while preserving the existing captured stdout, suppressed
stderr, new process group, bounded timeout and process-group kill behavior.
The added regression calls `final()` through its real default-launcher branch,
patches `subprocess.Popen`, and verifies both successful completion and
`start_new_session=True`.

Independent validation in the platform checkout passed:

- focused coordinator suite: 15/15;
- broader `test_f2*.py` suite: 50 passed and one expected skip, 51 total;
- repository diff check: clean for the four committed paths.

The source-only candidate pins coordinator SHA-256
`6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193`
and test SHA-256
`2a21d2427a7110227cd7bbef0d6dcc5aae6ff97432dc0c102ffb49df8fc2032a`.

This closes the source defect and missing-regression gap only. The corrected
coordinator is not installed, no timer is active, and the spent October 26
cycle remains terminal. A reviewed inactive installation with target-Linux
installed-entrypoint proof is the next gate before any fresh-cycle card.
