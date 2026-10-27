# Problem and competition research

## The problem

In the [2019 study “Understanding Flaky Tests: The Developer’s Perspective”](https://www.mozillafoundation.org/en/research/library/understanding-flaky-tests-the-developers-perspective/), surveyed Mozilla developers reported flaky tests affecting trust in test suites, scheduling and resources, with reproduction and identifying causes among the major challenges. This is evidence that the problem matters to those studied; it is not a claim about Flakewise's adoption or time saved.

GitLab [accepts JUnit test reports as CI artifacts](https://docs.gitlab.com/ci/testing/unit_test_reports/) and documents [investigation of unhealthy tests](https://docs.gitlab.com/development/testing_guide/unhealthy_tests/). A practitioner can therefore obtain the input format from an existing workflow rather than being asked to integrate a new agent into their application.

## Similar solutions

- GitLab already presents JUnit test results and has its own detection and investigation practices; see its [test reporting](https://docs.gitlab.com/ci/testing/unit_test_reports/) and [flaky-test handbook](https://handbook.gitlab.com/handbook/engineering/testing/flaky-tests/).
- [Trunk Flaky Tests](https://docs.trunk.io/flaky-tests) offers test monitoring and automation; it is a richer operational service, not evidence that Flakewise is the first product in this area.
- Existing tools such as [junit-flaky-check](https://github.com/INNERLUXES/junit-flaky-check) aggregate reports. Any differentiation claim must be bounded to what this project demonstrates: explicit per-report commit assertions, separated groups, individual evidence, and a reviewable output without an account connection.

## Ideas considered

1. **Flakewise:** compare real JUnit artifacts and expose inconsistent outcomes; useful to CI maintainers with accessible inputs. Existing alternatives make precise positioning important.
2. **Webhook-retry simulator:** exposes transaction failures well but fixed synthetic scenarios are harder for a user to apply to their own work.
3. **Incident handover assistant:** potentially useful but credible results need connected incident data, permissions and strong safeguards against made-up summaries.
4. **Dependency auto-remediation:** addresses a real supply-chain concern but substantially overlaps with existing security tools and requires elevated integration access.
5. **Deployment-to-incident correlation:** valuable when powered by real telemetry but difficult to validate honestly without access to an operational system.
6. **Migration rollback preflight:** meaningful for mixed-version deployments but has existing strong tools and would require a distinct, verified schema contract and repair workflow.

Flakewise was selected for the combination of a recognizable user problem, the ability to bring actual artifacts, bounded implementation scope and a direct connection to the GitLab CI verification stage.

## Interpretation limits

JUnit files generally do not establish a reliable commit on their own. Flakewise uses each user-entered identifier and groups only identical normalized strings. Users must ensure reports, environments, test data and identifiers are comparable. Mixed outcomes may arise from changed external conditions, environment or data. They are evidence to investigate, not a proof of test flakiness or diagnosis.

## Visual references

Apple's [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) inform clear hierarchy, legibility, predictable interaction and touch targets. [GitLab unit test reports](https://docs.gitlab.com/ci/testing/unit_test_reports/) ground test-first information hierarchy. The [Dribbble test results collection](https://dribbble.com/search/test-results) was consulted for general presentation patterns; no protected artwork or whole layout is copied.

## Event constraints

Life After Code requires a public MIT-licensed GitLab project, visible GitLab CI/CD history, meaningful GitLab Duo Agent Platform use, a project description and a public YouTube video under three minutes. The five judging dimensions are technical implementation, design, potential impact, idea/innovation, and presentation. Google Cloud deployment is optional. Verify all submission fields and the [official rules](https://gitlab-transcend.devpost.com/rules) before finalizing. Do not describe a configured agent as an executed agent. This project's event automation evidence is pending until an actual Flakewise run is verified.
