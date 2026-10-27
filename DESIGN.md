# Flakewise design direction

## User and surface

This is an operational application for engineers investigating test evidence, not a landing page full of statistics. The first screen should make the upload/commit/analysis task immediately understandable. Outcomes should be inspectable at the level of each run, and all values should come from actual uploaded or clearly labeled sample reports.

## Visual principles

A light, uncluttered canvas with deep ink text, a restrained accent, soft borders and subtle polished surfaces. Gloss is a material cue for controls and panels, not a source of visual noise. Maintain a confident typographic hierarchy, comfortable reading sizes and clearly grouped controls. The project uses self-hosted Manrope (OFL) where included; system fallbacks apply if unavailable. Status is communicated with text and shape as well as color.

Palette: canvas `#f6f8f5`, ink `#172e31`, primary green `#246c67`, white surfaces `#ffffff`, mint `#d8f0e9`, muted text `#617678`, and warning surface `#fff5e9`. Use the strongest contrast available for ordinary text. Uppercase metadata is short and tracked; functional text remains readable and the main title uses a larger editorial scale. The workspace comprises a header, concise introduction, report-and-commit inputs, results and selected-test evidence, followed by the guide.

Reference principles were drawn from [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/), the information structure of [GitLab test reports](https://docs.gitlab.com/ci/testing/unit_test_reports/) and general [test-results UI references](https://dribbble.com/search/test-results); no artwork or complete interface is copied.

## Interaction and accessibility

- Show sample data as sample data. Use friendly, precise error messages and meaningful empty/loading states.
- Keep input context (report and user-asserted commit) clear; do not imply source provenance was independently verified.
- Interactive elements require visible keyboard focus, readable labels and touch-friendly hit areas.
- Respect reduced-motion preferences. Use short transitions only when they explain state changes; avoid decorative looping effects.
- Display actual observations before interpretation. Results and error details are untrusted text, never interpreted as markup.
- Responsive desktop, tablet and narrow phone layouts should preserve the same full user journey.

## Avoid

No fake activity stream, claimed prediction, fabricated outcome or made-up usage numbers. No copied reference assets, abstract decorative dashboard or excessive gradient/glass effects. Do not use “confirmed flaky” where changed environments or data could explain the results.
