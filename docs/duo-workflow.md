# Supervised GitLab Duo workflow

Status: this is a **prepared workflow**. Do not describe a live Flakewise agent repair, passing pipeline, or human approval until the corresponding GitLab session and jobs have actually run and their URLs are recorded. A previous agent session for a different product does not establish this workflow.

## Why this is useful

A maintainer receives JUnit reports from repeated CI jobs and needs to distinguish changing outcomes for the same reported test and user-asserted commit. The application reports mixed outcomes as evidence, not proof of a cause or of an unchanged runtime environment. Its input is untrusted and is bounded; no arbitrary code or network fetch is triggered by a report.

## Supervised challenge

1. Begin with a clean, reviewed product branch containing the original independent tests and CI configuration. Create a `repair/*` branch.
2. In a clearly labeled challenge-seed commit, deliberately replace only `classify_counts` in `flakewise/analyzer.py` with an incorrect implementation, such as reporting every test with a pass as `passed` even when it also failed. Push it; record the actual failing CI job. This seed is intentionally introduced to demonstrate the repair workflow.
3. Give the GitLab Duo Developer flow the task of investigating the failing tests and repairing the classifier. Allow it to change only the body of `classify_counts` and, optionally, `docs/repair.md`. It must not alter tests, parser validation, CI, the scope gate, or any network/access setting. It must not inspect secrets or execute report content.
4. Ask the agent to run `python -m unittest discover -s tests -v` and `python scripts/ci_security_scan.py`, then push its repair commit and open a **draft** merge request to the clean product branch. Include the actual failing-before and passing-after job links and the limitations in its description. If any check fails, report the failure honestly.
5. The merge-request `repair-scope` job obtains its checker from the target branch. The checker compares Python ASTs and allows changes only in the classifier function body and optional repair notes; it rejects code outside the bounded pure syntax subset. The independent unit tests and security check also run. Review the MR and pipeline before merging. Tests and a narrow edit scope are evidence, not a proof that a repair is safe.

The scope gate expects a **final** classifier edit relative to the clean target branch. If an agent simply restores the byte-for-byte original, the final MR may contain no classifier diff; ask it to express an equivalent correct implementation clearly (without changing its signature or external behavior) and rerun all checks. Never claim a change if the MR has no final classifier diff.

The static security check is intentionally limited to Python AST patterns for `eval`, `exec`, and `shell=True`; it is not a penetration test, dependency/CVE audit, or guarantee of security. Do not include real user report contents, credentials, tokens, or private CI logs in a public agent task or merge request.

## Developer-flow goal template

Replace placeholders with the actual event project and an existing product branch after the source is in GitLab. Use synthetic example reports and repository tests only.

> In project `<event-project>`, create `repair/classification-contract` from `<product-branch>`. First replace only the body of `classify_counts(p, f, s)` in `flakewise/analyzer.py` with a clearly incorrect implementation that returns `passed` whenever `p` is nonzero, returns `failed` when only `f` is nonzero, and otherwise returns `skipped`. Commit it as a challenge seed and push. Run the independent tests, wait for the failing pipeline, and record its actual job URL. Diagnose the failed tests and implement the correct classifier without changing any other function, its signature, tests, CI, or policy. The final classifier must differ in code from the clean product branch while satisfying the same behavior, so the MR's scope gate has a real classifier diff. Write a short `docs/repair.md` explaining the cause and outcome. Run Python tests and the bounded security scan, commit the repair, push, and open a draft MR targeting `<product-branch>`. Read the job logs and include real failing and passing pipeline links. If something fails, report it; do not fabricate results. Do not merge, deploy, inspect credentials, alter access or network policies, or make purchases. Human review remains required.

## Before a hackathon claim

Record the exact native Developer session URL, seed commit, failed job, repair commit, passing job, draft MR, and the MR pipeline including the scope gate. Check the public project actually contains the submitted application's current source and the MIT license. The official event requires GitLab Duo Agent Platform usage, a public MIT-licensed GitLab repository, visible CI history, and a video under three minutes. The video and final submission are separate user-controlled steps.
