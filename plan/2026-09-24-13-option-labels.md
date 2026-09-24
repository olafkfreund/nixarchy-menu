---
status: approved
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
2. **tst_settingstree.qml:** the new case, with its own Files entry.
   **files_check.py:** assert `optionLabels.prefix === "Only with ~"` on the
   real `Files.qml` provider.
   → Verify: the QML suite passes, `files_check.py` passes, and
   `files_check.py` fails if Files is reverted to the array (checked once,
   then restored).
3. **Lead:**
   - commit
   - `nix flake check`
   - PR, merged when CI is green and the user agrees

## Deviation (during implementation, agreed with the lead)
- `tests/tst_settingstree.qml` has no shared Files fixture, and adding one to
  `model()` would break the settings listing assertions. The unit case pushes
  its own Files entry onto a copy of the model, as `voiceModel()` does.
- qmltestrunner cannot load `Files.qml` because it imports Quickshell. The unit
  case therefore tests a copy of the labels, and reverting `Files.qml` leaves it
  passing. The revert check moves to `tests/files_check.py`, which loads the
  real provider in quickshell.
- Step 2's check becomes: `files_check.py` fails when `Files.qml` has the array.

## Tests
- `cd tests && nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
  gives 0 failed.
- `nix flake check` passes.

## Rollback
Revert the commit.
