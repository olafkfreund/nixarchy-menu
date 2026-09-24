---
status: approved
issue: 12
author: olafkfreund
epic: 6
---

# Intent: Settings saved before the config has loaded can overwrite it

## Problem

#12 was filed as a test-harness race under heavy CPU load. Research shows it is also a **real, low-probability data-loss bug** in the palette.

**The startup order today:**
- **The migration runs first.** It sets `stateReady`, and only then does `configFile` load `~/.config/omarchy/nixarchy-menu.json` (`NixarchyMenu.qml:264-270, 410-415`).
- **The load is asynchronous.** When it finishes, it replaces the whole config (`applyConfigText`). A missing file resets the config to defaults.

**The bug:** a settings change made before the load finishes is lost, or it destroys the saved config:
- **Before `stateReady`:** `saveConfig` changes memory only. The later load silently overwrites the user's change.
- **After `stateReady`, before the load:** `saveConfig` builds on the *defaults* and **writes them to disk** (`:256-261, 1170`), replacing the user's real config file.
- **The "edit config" action** rewrites the file the same way (`:1197`).

The window is short: from when the migration finishes to when a small file is read. It is real, though, and a lost config is not recoverable.

**The same race makes tests flaky.** Ten palette harnesses call `applyConfigText` early and wait only on fixed timers or on extension manifests. The manifests appear even before `stateReady` (`providers/Registry.qml:153`), so a late load clobbers the test's config. gif-search failed this way under heavy contention.

## Proposed outcome

- **The palette knows when its config has settled:** loaded, missing, or skipped because the migration failed.
- **A settings change before then is refused** with "Settings are still loading", and nothing is written. The saved config can never be overwritten with defaults, and a change is never silently lost.
- **"Edit config" still opens the file** before then, but doesn't rewrite it.
- **If the migration fails,** the config still counts as settled, on the defaults in memory, so nothing waits forever.
- **Every palette harness waits for the config to settle** before its first config change, instead of a fixed timer.
- **A new check proves it:**
  - a change made before the config settles is refused, and the file on disk is unchanged
  - once settled, the palette has the on-disk values
  - a later change saves and keeps the existing keys
  - a failed migration still settles

## Affected users and systems

- **This repo:**
  - `NixarchyMenu.qml`: one `configSettled` flag, and the save and edit guards.
  - Ten harnesses: the gate before their first config change.
  - One new check, wired into the flake's `quickshell` check.
- **Users:** a settings change in the first moments after the shell starts shows a brief "still loading" message instead of risking their config.

## Constraints

- **No timers, and nothing that can hang.** The flag is set from the load's own success and failure callbacks, and from the migration's failure.
- **The migration-failure design from #1 is unchanged:** nothing is written at the new paths that session.
- **Stress testing stays pinned to one core** (`taskset -c 0`), never all CPUs on p620.

## Open questions

1. **Refuse a change while loading, or queue it and apply it after the load?**
   Proposed: **refuse**, with a visible message. Queuing needs merge rules for a config the user hasn't seen yet. The window is milliseconds long, so the user simply tries again.
