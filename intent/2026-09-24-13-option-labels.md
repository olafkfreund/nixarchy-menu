---
status: approved
issue: 13
author: olafkfreund
epic: 6
---

# Intent: Files' enum option labels never apply

## Problem

Settings › Files › Search in the main palette shows its third choice as
**Prefix** instead of **Only with ~**.

- **Files uses the wrong form.** `providers/Files.qml:36` declares
  `optionLabels` as an array (`["Fuzzy", "Literal", "Only with ~"]`).
- **The documented contract is a map.** `docs/providers.md:212-214` says:
  `optionLabels: { value: "Visible label" }`.
- **Every other declaration already uses the map:** `core/SmartMatch.js`,
  `NixarchyMenu.qml:125`, and the timer, translate, gif-search and currency
  extensions.
- **The only readers look up by option value.** `core/SettingsTree.js:40`
  (current-value accessory) and `:47` (choice rows) read
  `optionLabels[value]`. For Files that lookup misses, and the row falls back
  to `titleCase("prefix")`.
- **No test covers `optionLabels` at all.**

## Proposed outcome

- The choice row, and the current-value accessory when that choice is
  selected, both read **Only with ~**.
- A test asserts the labels, so any provider breaking the documented form is
  caught.

## Affected users and systems

- This repo: `providers/Files.qml` (one line) and
  `tests/tst_settingstree.qml` (a new case).
- No stored config changes. The stored values stay `fuzzy`, `literal` and
  `prefix`.

## Constraints

- Keep the documented map contract. Do not make `SettingsTree` also accept
  arrays: the array form exists only because of this bug.
- No change to option values or validation.

## Open questions

None. This is a one-line fix plus a test, so the spec and plan will be a few
lines each.
