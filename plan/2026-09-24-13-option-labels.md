---
status: approved
issue: 13
spec: spec/2026-09-24-13-option-labels.md
---

# Plan: Files' enum option labels never apply

## Approved decisions
- `providers/Files.qml:36` becomes
  `optionLabels: { fuzzy: "Fuzzy", literal: "Literal", prefix: "Starts with ~" }`
  (the documented map).
- `SettingsTree` is not changed, and no check_extensions guard is added.
- `tests/tst_settingstree.qml`: the Files `searchMode` fixture gets the same
  labels. A new case asserts that the choice row reads "Starts with ~" and that
  the parent accessory with `searchMode: "prefix"` reads "Starts with ~".

## Steps (one implementer)
1. **Files.qml:36:** the map.
   → Verify: `rg -a -n optionLabels providers/Files.qml` shows the map.
2. **tst_settingstree.qml:** the shared Files fixture gets the labels, and the
   new case sets its `searchMode` to `prefix`.
   **files_check.py:** assert `optionLabels.prefix === "Starts with ~"` on the
   real `Files.qml` provider.
   → Verify: the QML suite passes, `files_check.py` passes, and
   `files_check.py` fails if Files is reverted to the array (checked once,
   then restored).
3. **Lead:**
   - commit
   - `nix flake check`
   - PR, merged when CI is green and the user agrees

## Deviation (during implementation, agreed with the lead)
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

## Amendment: label "Starts with ~" (user decision, 2026-09-24)
The approved label "Only with ~" changed search ranking. Abbreviations ending
in `mo` (`setfilmo`, `nixsefimo`) matched **m**ain palette › **O**nly at word
starts and ranked that choice (which switches the mode to prefix) above the
setting itself, failing `test_abbreviations_reach_a_deep_setting_from_the_root`.
The user chose to change the label rather than the matcher or the test. The
label is now **Starts with ~** (no word starting with m or o), and the
abbreviation test is unchanged. The test's existing raw `"fuzzy"` accessory
assertion becomes `"Fuzzy"`, the label this fix now applies.
