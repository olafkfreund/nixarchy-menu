---
status: approved
issue: 12
spec: spec/2026-09-24-12-config-load-race.md
---

# Plan: Settings saved before the config has loaded can overwrite it

## Approved decisions
- **`NixarchyMenu.qml`:** `property bool configSettled: false`. It is set to
  true, after applying, in `configFile.onLoaded` and `onLoadFailed`, and in
  `migrateState.onExited` when `code !== 0`.
- **`saveConfig`:** first line
  `if (!root.configSettled) throw new Error("Settings are still loading")`.
  The `setting` effect already catches and shows it.
- **`edit` effect:** rewrite only when
  `configSettled && !configError && stateReady`. It always opens the file.
- **Harnesses wait for `palette.configSettled`** before their first
  `applyConfigText`:
  - **stage gate:** url, extensions, gif-search, translate, browser-search,
    commands
  - **repeating check:** route, motion, matching, shortcut
- **New `tests/palette_config_settle_check.py`** with 4 cases:
  - refused before settle, and the file is unchanged
  - on-disk values once settled
  - a save that keeps the other keys
  - migration failure still settles

  It is added to the flake `quickshell` list and `bin/nixarchy-menu test`.
- **Stress runs only ever pin to core 0** (`taskset -c 0`), never all CPUs on
  p620.

## Steps (one implementer)
1. **`NixarchyMenu.qml`:** the flag, the three setters, and the save and edit
   guards.
   → Verify: qmllint shows no new warning.
2. **The ten harnesses:** the gate per the lists above. Each keeps its outer
   guard timeout.
   → Verify: each passes once locally
   (`nix develop`, `OMARCHY_PATH=<omarchy input>`, temp HOME).
3. **New check:** its 4 cases, wired into flake.nix and bin.
   → Verify: it passes, and it fails when the `saveConfig` guard is removed
   (checked once, then restored).
4. **Stress:**
   - `taskset -c 0 stress-ng --cpu 4 &`
   - each of the ten harnesses plus the new check, 5× with `taskset -c 0`
   - kill the stress

   → Verify: all pass, including gif-search.
5. **Lead:**
   - commit
   - `nix flake check` plus a forced `--rebuild` of `quickshell`
   - Codex review
   - PR, merged when CI is green and the user agrees

## Tests
- QML suite, `nix flake check`, and a forced `nix build --rebuild -L .#checks.x86_64-linux.quickshell`.
- The pinned stress runs from step 4.

## Rollback
Revert the commit. The harness gates are harmless on their own.
