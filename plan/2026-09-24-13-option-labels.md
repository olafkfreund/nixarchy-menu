---
status: draft
issue: 13
spec: spec/2026-09-24-13-option-labels.md
---

# Plan: Files' enum option labels never apply

## Approved decisions
- `providers/Files.qml:36` becomes
  `optionLabels: { fuzzy: "Fuzzy", literal: "Literal", prefix: "Only with ~" }`
  (the documented map).
- `SettingsTree` is not changed, and no check_extensions guard is added.
- `tests/tst_settingstree.qml`: the Files `searchMode` fixture gets the same
  labels. A new case asserts that the choice row reads "Only with ~" and that
  the parent accessory with `searchMode: "prefix"` reads "Only with ~".

## Steps (one implementer)
1. **Files.qml:36:** the map.
   → Verify: `rg -a -n optionLabels providers/Files.qml` shows the map.
2. **tst_settingstree.qml:** the fixture labels plus the new case.
   → Verify: the QML suite passes, and the new case fails if Files is
   reverted to the array (checked once, then restored).
3. **Lead:**
   - commit
   - `nix flake check`
   - PR, merged when CI is green and the user agrees

## Tests
- `cd tests && nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
  gives 0 failed.
- `nix flake check` passes.

## Rollback
Revert the commit.
