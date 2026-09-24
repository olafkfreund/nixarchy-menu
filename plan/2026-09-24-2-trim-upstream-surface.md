---
status: approved
issue: 2
spec: spec/2026-09-24-2-trim-upstream-surface.md
---

# Plan: Remove upstream surface nixarchy does not need

## Approved decisions (carried over from the spec)

- **Scope.** Pure deletion, plus the edits that keep the remaining code
  consistent. No renames (#1). `codex/` untouched (#4). `/usr/lib/qt6` and
  `/usr/share/omarchy` test paths untouched (#3).
- **Smart Match deleted entirely.** The palette always takes the existing
  `matching.mode: "off"` path:
  - `Match.rank(collected)` does the ranking.
  - Voice goes through `Intent.normalize`.
  - A `matching` key in user config is still preserved, and `"matching"`
    stays a reserved id.
- **Catalog functions deleted.** The bundled providers' `catalog()` fed only
  Smart Match. `requery({catalog})` still accepts the option and ignores it.
- **Marketplace.** Remove the `marketplace`, `autoCheck` and `indexUrl` keys
  from the example config. There is no code to remove.
- **MenuModel.** The menu imports the shell's copy through
  `file:///run/current-system/sw/share/omarchy/shell/plugins/menu/MenuModel.js`,
  the same way as Nixi. The vendored `omarchy/MenuModel.js` is deleted. No
  behaviour change.
- **Removed outright:**
  - `site/`, `experiments/`, `tools/showcase/`, `tools/profile_palette.py`
  - root `assets/`, `preview.png`
  - `docs/releases/`, `docs/history/`, `docs/verification.md`,
    `docs/engine-provenance.md`
  - the `engine.yml` and `pages.yml` workflows
- **Accepted losses:**
  - Chromium is no longer offered for "Chrome".
  - Rows from different providers that run the same command are no longer
    deduplicated.
  - Cross-catalog typo recovery is weaker.
- **Deferred to #3:** the Python quickshell checks.

## Team split

Three teammates edit disjoint file sets in the same working tree. The lead
reviews each diff, runs the checks and makes the commits. No teammate
commits. Steps A, B and C run in parallel. Step D runs after all three.

### A: `smartmatch` (Smart Match code path)

Owns `Keystroke.qml`, `core/SmartMatch.js`, `core/Intent.js`,
`core/SettingsTree.js`, `providers/SettingsProvider.qml`,
`providers/Applications.qml`, `providers/Hotkeys.qml`, `matching/`,
`helpers/matching-*.py`, `tests/tst_match.qml`, `tests/tst_smartmatch.qml`,
`tests/matching_*_check.py` and `tests/palette_matching_check.py`.

1. `git rm -r matching/ helpers/matching-start.py helpers/matching-worker.py core/SmartMatch.js`
2. `Keystroke.qml`:
   - Remove the imports (:18, :21).
   - Remove the matching schema, settings, stamp, session and the
     description FileViews, plus `describe()` (:126-161).
   - Remove the prewarm timer, `catalogFor()` and `documentsFor()`
     (:749-812). `invalidateCatalog()` now only calls
     `invalidateProviders()`.
   - Remove every `matchingSession.cancelRequest()`.
   - Remove the `SmartMatch.request/merge` branches (:823-828, :850-862),
     keeping `Match.rank(collected)`.
   - Set `pending = pend` and delete the matching error line (:866-867).
   - Remove the `row.smartMatch` re-query (:1111-1116), `matching-retry`
     (:1145) and `inspect().matching` (:1211).

   Verify: `rg -n 'SmartMatch|matchingSession|matchingStamp|matchingModel|catalogFor|documentsFor|describe\(' Keystroke.qml` is empty.
3. `core/SettingsTree.js:116-125`: remove the Matching screen.
   `providers/SettingsProvider.qml:38,45`: remove `matchingModel()` and
   `matchingStamp`. Delete its `catalog()` (:24).
4. `core/Intent.js`: delete `arithmetic()`. Delete `catalog()` in
   `providers/Applications.qml` (:27) and `providers/Hotkeys.qml` (:34, :69),
   together with any helper used only by them.
5. Tests:
   - `git rm tests/tst_smartmatch.qml tests/matching_session_check.py tests/matching_worker_check.py tests/matching_engine_check.py tests/palette_matching_check.py`
   - `tests/tst_match.qml`: drop the `Smart` import (:6) and lines :98-99.
     The rest of that case stays.

### B: `menumodel` (menu model and the menu provider)

Owns `providers/OmarchyMenu.qml`, `omarchy/`, `tests/tst_menumodel.qml` and
`tests/catalog_check.py`.

1. `providers/OmarchyMenu.qml:5`: switch to the shell's copy, with the
   file URL above.
2. `providers/OmarchyMenu.qml`: delete `catalog()` (:61, :350) and any
   helper used only by it.
3. `tests/tst_menumodel.qml:3`: use the same URL.
4. `git rm omarchy/MenuModel.js tests/catalog_check.py`. Remove the
   MenuModel entry from `omarchy/LICENSE`, or `git rm` the file if nothing
   else is vendored.

Verify: `rg -n 'omarchy/MenuModel|catalog' providers/OmarchyMenu.qml tests/tst_menumodel.qml` is empty.

### C: `surface` (files, CI, tooling and docs)

Owns everything else listed in the spec.

1. `git rm -r site/ experiments/ tools/showcase/ tools/profile_palette.py assets/ preview.png docs/releases/ docs/history/ docs/verification.md docs/engine-provenance.md .github/workflows/engine.yml .github/workflows/pages.yml`
2. `.gitignore:2`: remove `matching/engine/target/`.
   `keystroke.example.json`:
   - Delete the `matching` block (:15-18).
   - Delete the `marketplace`, `autoCheck` and `indexUrl` keys (:80-82).
   - Keep the result valid JSON.
3. `bin/keystroke`:
   - Remove the usage lines (:23-24).
   - Remove the exclude (:36).
   - Remove the install matching step (:44-46).
   - Remove the `matching` and `engine` cases (:72-73).
   - Remove the four test lines (:79-80, :85-86).
4. Docs:
   - `README.md`: delete :5, :9, :11, :23-31, :64-84 and the `site/assets`
     images (:41-46, :90, :104, :130, :136). Reword :147.
   - `CONTRIBUTING.md:51,146`: drop the `verification.md` advice.
   - `docs/architecture.md`: delete the Smart Match and catalog sections
     (:114-14x) and "and semantic" (:60).
   - `docs/providers.md`: delete "Optional Smart Match catalog" (:186-). At
     :53, say `catalog` is accepted and ignored.
   - `docs/codex-integration-verification.md:66,94`: unlink `experiments/`.

Verify: `jq . keystroke.example.json` succeeds, and `bash -n bin/keystroke` succeeds.

### D: `lead` (integrate and verify, after A, B and C)

1. Run the checks under **Tests**. On a failure, send the fix back to the
   owning teammate. Do not patch across ownership.
2. Make three commits, one per team, each `chore: … (#2)`, so each can be
   reverted on its own.
3. Runtime check on this machine (Tests, step 4).
4. Tick #2 on epic #6. Open a PR from
   `chore/2-trim-upstream-surface` that links the intent, spec and plan.
   Push only when the user says to.

## Tests

1. **QML suite**, from `tests/`:
   `nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
   Baseline: 265 passed, 0 failed. Expected: 0 failed, and the total drops
   only by `tst_smartmatch`'s cases.
2. **qmllint**: run the same package's `qmllint` with
   `-I <qtdeclarative>/lib/qt-6/qml` and the `qs` shim pointing at
   `$OMARCHY_PATH/shell`, on `Keystroke.qml`, `providers/*.qml` and `ui/*.qml`.
   Expected: no warnings that the baseline run on `main` does not already
   have.
3. **Dangling references**:
   `rg -n 'SmartMatch|matchingSession|matching-start|matching-worker|keystroke-matching|omarchy/MenuModel|site/assets|docs/releases|verification\.md|engine-provenance|indexUrl|profile_palette|showcase' -g '!intent/**' -g '!spec/**' -g '!plan/**'`
   Expected: no output.
4. **Runtime**:
   - Copy the tree into `~/.config/omarchy/plugins/evindor.keystroke`
     (`bin/keystroke install`), after backing up the current copy if one
     exists.
   - Check that:
     - `Super+Space` opens the palette.
     - `sysshut` finds System › Shutdown, and `ffx` finds Firefox.
     - `2m in feet` answers.
     - Settings has no Matching screen.
     - Voice "27 plus 90" gives 117.
     - The Ask group rows match the stock menu.
   - Then restore the previous state.
5. **Not run**: the `tests/*_check.py` quickshell checks. They need #3's
   `$OMARCHY_PATH` fix. This gap is recorded in the PR.

## Rollback

- Each team's change is one commit, and `git revert <sha>` undoes one team.
- Nothing is pushed or deployed, so abandoning the branch undoes everything.
- Runtime: the backup restores the previous plugin copy, and
  `omarchy plugin disable evindor.keystroke` restores the stock menu.

## Deviations during implementation

### C: surface
- `bin/keystroke test` also no longer runs `tests/catalog_check.py`, which B deletes.
- Because B deleted the vendored copy, the MenuModel references in `README.md` (License line), `CONTRIBUTING.md` (table row, vendored-code bullet) and `docs/architecture.md:21` now say the model is loaded from the installed shell.
- `README.md`:
  - The Smart Match sentence is removed from the intro.
  - The screenshot table is deleted, because every cell was a `site/assets` image.
- `CONTRIBUTING.md` no longer refers to `helpers/matching-start.py`.
- `docs/providers.md`:
  - "Smart Match stays out" is removed from Routing.
  - The `optionLabels` paragraph is kept under a new "Enum option labels" heading, because it was not about the catalog.
- The rsync `--exclude assets --exclude experiments` flags in `bin/keystroke` stay. They are harmless.

### B: menumodel
- `omarchy/LICENSE` never existed. `MenuModel.js` was the only file in `omarchy/`, so the directory is gone. Attribution now lives in the root `README.md` License line (commit C).
- `catalogVisible()` is deleted with `catalog()`, because it had no other caller.

### A: smartmatch
- **`Intent.arithmetic()` is kept (step A4).** The spec called it dead, which is wrong. `Intent.normalize()` calls it first, and it turns "two plus two" into `2 + 2`, so spoken maths depends on it. Only `SmartMatch.request`'s use of it is gone.
- **`tests/tst_match.qml`:** later code in the case uses `rows`, so it is set to `[video, window, folder]` instead of deleting lines 98-99. The duplicate "embeddings off" `compare` is removed.
- **`requery(options)`** now calls `invalidateProviders(options && options.provider)`. `requery({provider})` without `catalog:false` used to clear every provider's cached rows, because the catalog was dirty. It now clears only the named provider's cache, which is correct because each cache holds only that provider's rows.
- **`core/SettingsTree.js`:** `catalog(tree, scope)`, used only by `SettingsProvider.catalog`, is deleted with the Matching screen.
