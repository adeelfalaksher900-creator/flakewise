# Flakewise — Devpost story draft

**Draft. Do not claim a completed GitLab Duo workflow or deployment until verified. No video or image gallery should be created until the user requests that phase.**

## Short pitch

Compare CI test results across runs and turn an inconsistent test into clear evidence for investigation.

## Inspiration

A failed test followed by a successful retry leaves a developer with a difficult question: is there a repeatable regression, a changing environment, or an unreliable test? Mozilla's research on developers' experience with flaky tests highlights the difficulty of reproducing the behavior and finding its cause. CI systems already generate JUnit XML reports, but opening several files and piecing the observations together is tedious.

## What it does

Flakewise reads reports provided by the user and groups test outcomes by test identity and user-asserted commit. It displays individual observations and flags groups with both a pass and a failure as inconsistent. Developers can inspect the evidence and prepare a reviewable summary. Example data is labeled as such, and real reports are accepted through the same workflow.

The result does not identify the cause, prove that environments matched, verify commit provenance, or claim a test is safe to ignore. Skipped and insufficient observations are treated separately.

## How it was built

A responsive HTML, CSS and JavaScript interface sends bounded JSON and JUnit XML to a Python service. The service validates inputs, rejects DTD/entity declarations and duplicate test identities in the same report, and compares outcomes only where the supplied commit and test identity match. It returns structured evidence for the interface to render. There is no app-level data store or account requirement for analysis.

## GitLab Duo and CI

**Pending actual run and verification.** Explain only the real agent session and CI results that are actually completed for this project, with source and evidence links. Prior Retryframe/AfterAck automation is not proof of a Flakewise-specific workflow.

## Challenges and learning

Distinguishing conflicting observations from a diagnosis matters: the same code revision can run with different test data or environments. Commit IDs are user assertions; exact matches group evidence but do not prove provenance. Exports should make the evidence usable in a human review rather than quietly changing a team's test policy.

## Impact and differentiation

The intended user is a developer investigating a suspicious CI retry. The project converts their actual JUnit files into a compact evidence view without requiring a GitLab account connection. GitLab and other products already provide flaky-test tools; this project does not claim to be first or to have measured time savings or user adoption.

## Testing and links

Add only actual tested application URL, public GitLab source, executed Duo session, pipeline, test instructions and measured results once available. Eligibility declarations and team contributions must come from the participant. Final video and images are deferred.
