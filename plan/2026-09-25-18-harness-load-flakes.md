---
status: draft
issue: 18
spec: spec/2026-09-25-18-harness-load-flakes.md
---

# Plan: palette checks that pass or fail on what they test

## The approved decisions, carried over

1. **translate:** the suspected cause is a harness race. Stage 81's
   `activateAt` saves the config, the watched file reloads (`onFileChanged:
   reload()` → `onLoaded: applyConfigText`), and the late reload undoes stage
   9's in-memory `applyConfigText(config([]))`.
   - **Evidence comes first.** If the evidence shows a real unload hang
     instead, stop and re-spec.
   - **The fix:** stage 9 turns translate off with `palette.saveConfig(...)`,
     the disk path, and no `applyConfigText`. The 20 s whole-run guard is
     unchanged.
2. **gif-search:** stage 4 records `test.slowRev = svc.revision` after
   `svc.search("slow")`. Stage 5 waits for
   `svc.requestedRevision === test.slowRev` before `svc.search("new")`. No
   assertion changes.
3. **The keystroke-speed test** asserts
   `matchTime / baselineTime < K`, with the baseline being a same-run
   `String.indexOf` scan of the same fields and queries. `K` is about 3× the
   worst ratio over roughly 10 idle runs, recorded here. `Match.js` is not
   changed.
4. **Stress** is `taskset -c 0 stress-ng --cpu 4` with every check pinned to
   core 0, never all CPUs, and killed by PID afterwards.

## Steps

1. **translate evidence, no fix.** Add temporary logging to the harness:
   each stage change with `Date.now()`, and the palette's config reloads.
   Run it 10× pinned under stress.
   → Verify that at least one run reproduces the stage-10 timeout, and
   record whether a config reload landed **after** stage 9's apply.
   - If a reload landed after → go on to step 2.
   - If no reload landed and `loaded` stayed true → **stop** and report back
     for a re-spec.
2. **translate fix:** stage 9 uses `saveConfig`, and the temporary logging is
   removed.
   → Verify: 5 of 5 pinned under stress, and the idle run passes.
3. **gif-search fix:** the `slowRev` wait.
   → Verify: before the fix, reproduce at least 1 failure in 5 under stress,
   recorded. After it, 5 of 5.
4. **Keystroke-speed test:**
   - Measure the idle ratio 10× and set `K`.
   - Rewrite the assertion as the ratio.

   → Verify:
   - 10 of 10 pinned under stress.
   - With a deliberate quadratic slowdown in `Match.match` (for example a
     nested loop over the title), it **fails** (checked once, then reverted).
5. **Full check:** `nix flake check`, and the QML suite idle.
   → Verify: both pass.
6. **Commit, Codex review, PR** linking the intent, spec and plan, closing
   #18. Merge when CI is green and the user agrees. Then tick epic #6 and
   close it, since this is the last item.

## Tests

- The pinned stress tallies from steps 2 to 4, before and after.
- The injected-slowdown failure for the speed test.
- `nix flake check` passes.

## Rollback

Revert the commit. The three checks go back to their timing-dependent
versions. There is no product code change unless step 1 turns up a real hang,
in which case this plan stops.
