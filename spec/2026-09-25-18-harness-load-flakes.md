---
status: draft
issue: 18
intent: intent/2026-09-25-18-harness-load-flakes.md
---

# Spec: palette checks that pass or fail on what they test, not on how busy the machine is

## Design

### 1. translate: a config race in the harness, verified first

**Hypothesis from the code:**
1. Stage 81 picks German with `palette.activateAt(...)`. That **saves** the
   config (`saveConfig` → `configFile.setText`, `NixarchyMenu.qml:264`).
2. The config file is watched (`watchChanges: true`,
   `onFileChanged: reload()`, `:269-274`), and `onLoaded` re-applies what's
   on disk.
3. Stage 9 then turns translate off with `palette.applyConfigText(config([]))`,
   which is **in memory only**.
4. When the reload from step 1's write lands **after** step 3, it re-applies
   "translate on". Stage 10 (`!entry("translate").loaded`) is never met, and
   the 20 s guard fires.

The guard covers the **whole run** (`:215`), which is why every failure is
reported at stage 10. Under load the file-change event arrives later, so the
race is lost more often. In the product, every change goes through the disk,
so re-reading its own write is harmless. **This is a harness race, not a
product bug**, if the evidence agrees.

**Evidence before any fix** (plan step 1): log each stage change with
`Date.now()`, and log `configFile` reloads (`onLoaded` count, read through the
harness). Then run under the pinned stress until the stage-10 timeout
reproduces:
- If a reload lands after stage 9's apply → **race confirmed**.
- If no reload lands and `loaded` just stays true → the unload really hangs.
  Stop there and re-spec as a service fix.

**Fix, if the race is confirmed:** stage 9 turns translate off through the
**same disk path** the product uses, with `palette.saveConfig(<config with
translate off>)`, and doesn't mix in `applyConfigText`. Stage 10 then waits for
`!entry("translate").loaded`, as today. Any reload re-applies the same "off"
config, so there is nothing left to race. The whole-run guard stays at 20 s.

### 2. gif-search: wait for the request, not for ticks

Stage 5 today is `if (++test.ticks < 4) return; svc.search("new")`. The
service debounces for 300 ms (`Service.qml:54`), and `fetch()` sets
`requestedRevision = revision` when the request actually starts (`:80-87`).

The new stage 4 records `test.slowRev = svc.revision` right after
`svc.search("slow")`. The new stage 5 waits for
`svc.requestedRevision === test.slowRev`, which means "slow" is on the wire,
and only then searches "new". Stage 6's "stale response ignored" assertion and
the Python request-log assertion (`palette_check.py:213`) are unchanged.

### 3. `tst_match.qml` keystroke speed: relative to a baseline measured in the same run

The test asserts that the per-keystroke time is under 40 ms, which is wall
clock and so depends on load. It guards against **algorithmic** regressions
such as backtracking blow-ups on abbreviations, not the absolute speed of the
machine.

**Change:** keep the same 700 rows, six queries and 20 rounds, and also time
a **baseline** in the same run: a plain `String.indexOf` scan of the same
fields for the same queries. Assert `matchTime / baselineTime < K`. The value
of `K` is taken from about 10 idle runs, as roughly 3× the worst observed
ratio, and recorded in the plan with the measurements. Load slows both sides
alike, so the ratio holds, while an algorithmic regression (10× or more)
still fails.

This is how the intent's option **(b)** is realised. A literal work counter
would put instrumentation in `Match.js`'s hot path, which is the code this
test keeps fast.

## Alternatives rejected

- **Longer timeouts or looser bounds alone:** they hide the race, and they
  don't stop the next flake. The intent rules them out.
- **translate: a stage-9 wait for "the reload landed":** it depends on
  whether a reload happens at all. Using the product's own disk path removes
  the race.
- **A work counter in `Match.js`:** see §3.
- **Timing checks only in `bin/nixarchy-menu test`** (option c): it leaves
  the flake check without a performance guard.

## Risks

- **The translate evidence may show a real unload hang.** Then this spec's §1
  fix is wrong, and it comes back to this gate as a service change.
- **`K` needs real measurements.** If idle runs vary widely, the ratio may
  need a warm-up round. The plan records the numbers.
- **`saveConfig` in the harness writes the config file in the check's temp
  `$HOME`.** Harnesses already use a temp HOME, so nothing is shared.

## Verification

- **translate** and **gif-search** each pass **5 of 5** under
  `taskset -c 0 stress-ng --cpu 4` with the check itself pinned to core 0.
  Before the fix, the same runs reproduce the failure (gif-search 4/5,
  translate about 1/5).
- **The keystroke-speed test** passes 10 of 10 pinned under the same stress.
  It **fails** when a deliberate quadratic slowdown is injected into
  `Match.match` (checked once, then reverted).
- **`nix flake check`** passes, and the other harnesses are unchanged.
