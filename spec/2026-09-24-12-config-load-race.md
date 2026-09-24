---
status: draft
issue: 12
intent: intent/2026-09-24-12-config-load-race.md
---

# Spec: Settings saved before the config has loaded can overwrite it

## Design

### 1. `NixarchyMenu.qml`
- **A new flag,** `property bool configSettled: false`, next to `configError`.
  It is set to true in three places, each only **after** the config is applied:
  - `configFile.onLoaded`: `applyConfigText(text()); configSettled = true`
  - `configFile.onLoadFailed`: `applyConfigText(""); configSettled = true`
  - `migrateState.onExited`: when `code !== 0`, set `configSettled = true`.
    `stateReady` stays false, `configFile.path` stays `""`, and neither load
    callback ever fires. The defaults in memory are that session's config.
- **`saveConfig(next)`** refuses before settling. Its first line becomes
  `if (!root.configSettled) throw new Error("Settings are still loading")`.
  - Its only caller, the `setting` effect, already catches and shows it as
    `errorMessage`.
  - Nothing changes in memory or on disk, and the later load can't erase a
    change it never accepted.
- **The `edit` effect** rewrites the file only when
  `configSettled && !configError && stateReady`. It always opens the real
  file.
- **Unchanged:** a later `onLoadFailed` (for example, the file deleted while
  running) still resets to defaults, as today.

### 2. Harnesses: wait for `palette.configSettled` before the first `applyConfigText`
- **Stage-gated harnesses** add `if (!palette.configSettled) return` to their
  case-0 gate: url, extensions, gif-search, translate, browser-search and
  commands. commands is already safe, and gets the gate for consistency.
- **Fixed-timer harnesses** (route, motion, matching, shortcut) turn their
  one-shot 250 ms timer into a repeating check that starts when
  `palette.configSettled` is true. matching needs `repeat: true` plus a
  started flag.

### 3. The new check, `tests/palette_config_settle_check.py`
It uses the real palette, the same harness style as `palette_url_check.py`,
a fake HOME, and a config file on disk with `providers.open-url.prefix: "zz"`.
1. **Before settling,** in the test root's `Component.onCompleted`, which runs
   before migrateState can exit, `perform` a `setting` effect. Assert
   `errorMessage` contains "still loading" and the file still has "zz".
2. **After `configSettled`,** assert `palette.config` has prefix "zz", not the
   default.
3. **Save again.** Assert the file has both the old keys and the new value.
4. **Migration failure.** With a HOME where `helpers/migrate-state.sh` exits
   non-zero (the setup `migrate_state_check.py` uses), assert `configSettled`
   becomes true within the guard while `stateReady` stays false.

It is added to the flake's `quickshell` check list and to `bin/nixarchy-menu test`.

## Alternatives rejected

- **Queue a change made while loading and merge it after:** that needs merge
  rules for a config the user hasn't seen, for a window measured in
  milliseconds. The intent answered: refuse.
- **Longer harness timers:** that hides the race and keeps the product bug.
- **Load the config synchronously:** FileView is asynchronous, and blocking
  shell startup on disk I/O is worse.

## Risks

- **A user who changes a setting in the first few hundred milliseconds sees
  "Settings are still loading".** This is visible and harmless.
- **A harness gate that never opens would hang.** Every path sets the flag:
  loaded, failed, or migration failed. Each harness keeps its existing outer
  guard timeout.

## Verification

- `nix flake check`, plus a forced `--rebuild` of `quickshell`, all pass,
  including the new check.
- **Stress run,** pinned to one core only (never all CPUs on p620): with
  `taskset -c 0 stress-ng --cpu 4 &`, run each of the ten harnesses and the new
  check 5× with `taskset -c 0`. All pass, including gif-search, which failed
  before. Stress is killed afterwards.
