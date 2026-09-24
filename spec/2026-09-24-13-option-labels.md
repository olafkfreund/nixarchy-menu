---
status: approved
issue: 13
intent: intent/2026-09-24-13-option-labels.md
---

# Spec: Files' enum option labels never apply

## Design

- **The fix.** `providers/Files.qml:36` changes to
  `optionLabels: { fuzzy: "Fuzzy", literal: "Literal", prefix: "Only with ~" }`,
  the documented map (`docs/providers.md:212-214`). Nothing else changes:
  - `core/SettingsTree.js:40,47` already read `optionLabels[value]`.
  - `core/Settings.js` validates only `options`.
- **The test.** In `tests/tst_settingstree.qml`, the Files `searchMode` fixture
  (~:20) gains the same `optionLabels`. A new case asserts:
  - the choice row under `settings/files/searchMode` is titled **Only with ~**
  - with `values.searchMode: "prefix"`, the parent row's accessory is **Only with ~**

  The existing "Literal" assertions still hold.

## Alternatives rejected

- **Make `SettingsTree` also accept arrays aligned to `options`:** the array
  form exists only because of this bug. No other provider or extension uses
  it, and it would widen a documented contract for no user.
- **A check_extensions guard rejecting non-map `optionLabels`:** YAGNI.
  Extensions already use the map. Add the guard if a second bad declaration
  ever appears.

## Risks

None of note. Stored values (`fuzzy`/`literal`/`prefix`) and validation are
unchanged.

## Verification

- The QML suite passes, including the new case.
- Settings › Files › Search in the main palette shows **Only with ~**. Checked
  with the new test; the palette render is the same code path.

## Amendment (2026-09-24, user decision during implementation)
The `prefix` label is **Starts with ~**, not "Only with ~". The latter ranked
its choice row above the setting for abbreviations ending in `mo`. See the
amendment in `plan/2026-09-24-13-option-labels.md`.
