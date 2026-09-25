---
status: approved
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
   - **Deviation, found in step 1:** 3 of the 10 stressed runs failed
     earlier, at stage 9's `service sees the new targets: en,fr`. The service
     gets its settings only on the next `query(ctx)` (`Service.qml:213`), and
     under load the check ran before the palette re-queried. Stage 9 now
     waits for the re-queried rows (`rows[2]` is German) **before** that
     check. Both assertions are unchanged; only their order moved.
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

## Results

Run on p620 on 2026-09-25. Stress was `taskset -c 0 stress-ng --cpu 4` with every
check pinned to core 0, and stress-ng was killed by its PID after each batch.
Each harness run used a fresh temp `HOME` and `OMARCHY_PATH` set to the flake's
omarchy input, inside `nix develop`.

### Step 1: translate evidence

- **Before the fix:** 6 of 10 passed under stress.
  - **Run 8** reproduced `FAIL timeout at stage 10`. Stage 10 began at
    `…281757`, and a config reload landed at `…281777`, 20 ms **after**
    stage 9's `applyConfigText(config([]))`. The reloaded text was
    `{"providers":{"translate":{"enabled":true,"targets":"en,fr,de"}}}`,
    which is stage 81's save. **The race is confirmed. It is not an unload
    hang.**
  - **Runs 3, 7 and 10** failed earlier, at stage 9 with `service sees the
    new targets: en,fr`. This is the second race, the deviation recorded
    under step 2.
  - In the passing runs, no reload landed after the first load.
- **After the fix:** 10 of 10 passed under stress (two batches of 5), and
  the idle run passed.

### Step 3: gif-search

- **Before the fix:** 15 of 15 passed under stress (batches of 5 and 10).
  **The failure did not reproduce here.** The intent reported 4 of 5
  passing.
  - The race is still in the code. Four 100 ms ticks run against the
    300 ms debounce, and a tick that fires late makes the next ones due
    early.
  - It was fixed as planned.
- **After the fix:** 5 of 5 passed under stress, and the idle run passed.

### Step 4: the keystroke-speed test

**Idle ratios** (Match time over the indexOf scan, 10 runs): 108.5, 110.1,
118.8, 95.5, 90.9, 88.7, 102.1, 96.5, 105.1, 101.3.
- The idle baseline scan took 19–23 ms.
- **K = 360**, which is 3 × 118.8 ≈ 356, rounded up.

**Under stress:**
- **Before the fix:** the old `perKeystroke < 40` would have failed **10 of
  10**. Matching took 95–111 ms per keystroke. These figures come from the
  same loop, timed in the measurement runs.
- **After the fix:** 10 of 10 passed, with ratios of 94.3–107.1 and a
  baseline of 116–137 ms. Load moves both sides of the ratio together.

**Injected slowdown** (temporary, then reverted; `core/Match.js` is
unchanged):
- **A quadratic loop over `title`** (about 33 characters) made Match about
  2.7× slower. The ratio was 280.0, below 360, so **the test still passed**.
  The ceiling of `K` is that it trips only above about 3.6× the mean idle
  ratio, so regressions smaller than that pass.
- **A quadratic loop over all four fields** (about 130 characters, a 30×
  regression) gave a ratio of 3079.0, and the test **failed** (`verify()`
  returned FALSE).

### Step 5

- The QML suite passed idle: 277 passed, 0 failed.
- `nix flake check` passed.
