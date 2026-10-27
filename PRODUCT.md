# Flakewise product brief

## The person and problem

A developer or CI maintainer sees a failing test turn green on retry. They need to decide whether the failure is a repeatable regression, an inconsistent observation worth investigating, or simply too little evidence. Manually opening multiple JUnit artifacts and matching test names and commits is slow and easy to get wrong.

Flakewise is a focused evidence workbench for that moment. It accepts the user's JUnit XML reports and the commit identifier associated with each one, groups observations for the same test and identical supplied commit, and creates a reviewable summary. A pass and a failure in one group is an **inconsistent outcome**, not proof of a defect in the test or its root cause. GitLab and commercial products already offer related test reporting and flaky-test analysis; the intended advantage here is a small, portable, explicit evidence-first workflow that does not require connecting an account.

## Journey

1. Export JUnit XML from two or more CI runs; keep each file's commit identifier.
2. Add reports and their matching commit identifiers, then run analysis.
3. Inspect an inconsistent test's individual pass/fail observations and messages. Separate commits stay separate.
4. Export evidence or a reviewable issue description for a teammate; inspect the information before sharing it.
5. Run more comparable tests to strengthen the evidence. Do not infer the cause from one report.

Users can load labeled example reports to understand the workflow without representing them as their own results.

## Product rules

- A report and its commit are provided by the user. Commit identifiers are asserted, not fetched or verified; identical short prefixes do not prove identity.
- A group must contain a pass and a failure to be marked inconsistent. Skipped tests do not count as either. A single non-skipped observation is insufficient evidence.
- Results are derived from the input, with explicit limits and validation; no fabricated metrics or detection of root cause.
- Analysis runs in the service on submitted XML. No application-level database, account, outbound webhook or agent action is needed for the core flow. Do not claim that infrastructure logs or networks provide absolute privacy.
- Never automatically create issues, execute uploaded code, quarantine tests, or mutate a repository.
- Preserve responsive layout, keyboard access, meaningful errors, and truthful empty/loading states.

## Acceptance

With two JUnit reports with identical user-supplied commit identifiers and a matching `classname`/`name` test that passes once and fails once, show that test's two observations as inconsistent. With different commit identifiers, do not aggregate those outcomes as the same group. Reject malformed XML, unsafe DTD/entity declarations, duplicate identities within a report, invalid commit identifiers, and oversized submissions with clear feedback. Test an actual hosted run and a user-supplied report flow before claiming deployment success.
