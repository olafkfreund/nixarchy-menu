---
status: approved
issue: 18
author: olafkfreund
---

# Intent: palette checks that pass or fail on what they test, not on how busy the machine is

## Problem

Three checks in `nix flake check` depend on timing. Under CPU load they fail
with no product fault behind them, and it has now happened in CI too.

1. **translate** (`extensions/translate/tests/palette_check.py`): it times
   out at **stage 10**, where it waits for the translate service to unload
   after `applyConfigText(config([]))`. It passed 1 of 5 runs under pinned
   stress, and it **failed in CI** on PR #21 (run 36073173890, attempt 1)
   with no assertion failure. Nobody knows yet whether the unload is just
   slow, or can really get stuck, which would be a product bug.
2. **gif-search** (`extensions/gif-search/tests/palette_check.py:213`): the
   fake curl's request log is missing `slow`. The harness counts 4 ticks of
   100 ms before searching "new", but the service debounces for 300 ms. On a
   starved core the ticks win, and "slow" is never sent. It passed 4 of 5
   runs under stress.
3. **`tst_match.qml` `test_a_keystroke_over_a_full_menu_stays_fast`** is a
   wall-clock bound on milliseconds per keystroke. It failed once in CI (PR
   #19) and fails when the suite is pinned to one core.

Each flake costs a re-run and teaches people to ignore red CI. That already
nearly hid a real failure during PR #19's review.

## Proposed outcome

- **All three checks pass reliably**, in CI and under the same pinned
  stress (`stress-ng --cpu 4` plus the check, both on one core), 5 of 5.
- **They still fail when the behaviour they guard breaks.** Each keeps its
  assertion. What changes is how it waits: for a state rather than for a
  fixed time.
- **The translate unload gets an answer:** slow, or stuck. If it's stuck,
  that's fixed in the service, not hidden by the harness.

## Affected users and systems

- **The two extension harnesses and `tests/tst_match.qml`.** Possibly the
  translate extension's service, if its unload really can hang.
- **CI** (`.github/workflows/nix.yml`) and anyone running
  `bin/nixarchy-menu test`.
- **No change to the palette's behaviour for users**, unless the translate
  unload turns out to be a real bug.

## Constraints

- **No weakened assertions.** Longer timeouts alone don't count as a fix. An
  outer guard can grow only if the check also waits on a condition.
- **Stress runs stay pinned to one core** (`taskset -c 0`), never all CPUs on
  p620.
- **The existing checks keep passing on an idle machine,** with no new
  flakes elsewhere.

## Open questions

1. **What to do with the keystroke-speed test?** It guards performance, which
   is real. Options:
   - (a) a looser bound
   - (b) a count of work done (rows scored) instead of time
   - (c) keep the timing, but only in `bin/nixarchy-menu test`, not in the
     sandboxed flake check

   My lean is (b), so it stays deterministic. The spec will propose it.
