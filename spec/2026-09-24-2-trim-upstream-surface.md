---
status: approved
issue: 2
intent: intent/2026-09-24-2-trim-upstream-surface.md
---

# Spec: Remove upstream surface nixarchy does not need

## Design

Pure deletion plus the edits that keep the remaining code consistent. Nothing
is renamed (#1), `codex/` is untouched (#4), and hardcoded `/usr` paths are
left for packaging (#3).

### 1. Smart Match → the existing "off" path

`core/SmartMatch.js` is more than embeddings. It also does:
- a lexical pass across every provider's rows (typo recovery)
- install/remove/on/off intent filters
- the Chromium stand-in for "Chrome"
- removal of duplicate rows that run the same command
- spoken arithmetic

The palette already has a tested `matching.mode: "off"` path that skips all
of this. Every provider already searches its own full tree, and voice text
still goes through `Intent.normalize`. Spoken maths keeps working, because
`Calc.calculate(Intent.normalize(text))` is enough (`tests/tst_smartmatch.qml:27`).
The design makes the "off" path the only path.

Delete these files:
- `matching/` (engine source, prebuilt binary, `Session.qml`, descriptions)
- `helpers/matching-start.py`, `helpers/matching-worker.py`, `core/SmartMatch.js`

Edit `Keystroke.qml`:
- Remove the `SmartMatch`/`Matching` imports (:18, :21).
- Remove the matching schema, settings, stamp and session, and the two
  description FileViews (:126-161).
- Remove the prewarm timer, `catalogFor()` and `documentsFor()` (:749-812).
  Keep `invalidateCatalog()` as a call to `invalidateProviders()`, because
  it has three callers (:689, :731, :758).
- Remove every `matchingSession.cancelRequest()` (:90, :671, :707, :858, :862).
- In the query path, remove the `SmartMatch.request/merge` branch
  (:823-828, :850-862). `Match.rank(collected)` at :864 is already the
  fuzzy path. Simplify pending/error to not reference the session (:866-867).
- Remove the `row.smartMatch` re-query (:1111-1116), the `matching-retry`
  perform (:1145) and the `matching` key in `inspect()` (:1211).

Edit the other files:
- `core/SettingsTree.js:116-125`: remove the Matching screen.
- `providers/SettingsProvider.qml:38,45`: drop `matchingModel()` and
  `matchingStamp`.
- `core/Intent.js`: delete `arithmetic()`, which is dead once SmartMatch is
  gone. `normalize()` stays.
- The bundled providers' `catalog()` functions (Applications, Hotkeys,
  OmarchyMenu, SettingsProvider) feed only Smart Match, so they are deleted.
  `requery({catalog: …})` still accepts the option and ignores it, so
  existing extensions keep working.
- `keystroke.example.json:15-18`: delete the `matching` block.
- `providers/Registry.qml:46` and `tools/check_extensions.py:25`: keep
  `"matching"` as a reserved id. Old configs may still have the key, and
  `core/Settings.js` preserves unknown fields.

### 2. Marketplace feed

No code reads `marketplace`, `autoCheck` or `indexUrl`, and
`extensions/index.json` does not exist. Delete the three keys from
`keystroke.example.json:80-82` and keep `"enabled": true`. Bundled
`extensions/` are unaffected. The upstream links in `core/Extensions.js:22-23`
and `core/SettingsTree.js:18` (GUIDE_URL) still resolve, so they are
repointed in #1 together with the name.

### 3. Vendored MenuModel → the shell's copy

`omarchy/MenuModel.js` is byte-identical to
`$OMARCHY_PATH/shell/plugins/menu/MenuModel.js` apart from its stale 6-line
header ("4.0.2-1"; the shell is 4.0.4). All ten functions the provider calls
exist with the same signatures.

- `providers/OmarchyMenu.qml:5` gets the same import Nixi uses
  (`nixi-nixarchy/MenuSearch.qml:21`):
  `import "file:///run/current-system/sw/share/omarchy/shell/plugins/menu/MenuModel.js" as MenuModel`.
  A QML import cannot read `$OMARCHY_PATH`, and the store path changes on
  every update. Menu *data* is still read from `$OMARCHY_PATH`
  (`OmarchyMenu.qml:14-16`), as Nixi does.
- `tests/tst_menumodel.qml:3` gets the same URL.
- Delete `omarchy/MenuModel.js`, and remove it from `omarchy/LICENSE` (or
  delete that file if nothing else is vendored).
- There is no behaviour change, since the logic is identical. The ✓ marks
  stay absent, because the provider never calls `labelFor`; adding them is
  out of scope.

### 4. Files and CI removed outright

- `site/`, `experiments/`, `tools/showcase/`, `tools/profile_palette.py`
- Root `assets/` (`keystroke.svg` plus 14 screenshots, nothing references
  them) and `preview.png`
- `docs/releases/`, `docs/history/`, `docs/verification.md`,
  `docs/engine-provenance.md`
- `.github/workflows/engine.yml` and `.github/workflows/pages.yml`.
  `extensions.yml` stays.
- `.gitignore:2` (`matching/engine/target/`)

### 5. Tests

- Delete `tests/tst_smartmatch.qml`, `tests/matching_session_check.py`,
  `tests/matching_worker_check.py`, `tests/matching_engine_check.py`,
  `tests/palette_matching_check.py` and `tests/catalog_check.py` (it tests
  the deleted `OmarchyMenu.catalog()`).
- `tests/tst_match.qml`: drop the `Smart` import (:6) and the
  `Smart.merge/request` lines in `test_query_learning…` (:98-99). The rest
  of the case still asserts the behaviour.
- The leftover `matching:{mode:"off"}` and `"experiments"` ignore entries in
  palette checks are no-ops, so they stay. This keeps the diff small.

### 6. Tooling and docs

- `bin/keystroke`:
  - Remove the `matching` and `engine` usage lines and cases (:23-24, :72-73).
  - Remove the install step that calls `matching-start.py` (:44-46).
  - Remove the `matching/engine/target` exclude (:36).
  - Remove the four matching test lines (:79-80, :85-86).
- `README.md`:
  - Delete the release link (:9), the showcase line (:11), the Smart Match
    install paragraph (:23-31) and the `## Smart Match` section (:64-84).
  - Delete the `site/assets` images (:5, :41-46, :90, :104, :130, :136).
  - Reword the `verification.md` link (:147).
  - The full rewrite is #1.
- `CONTRIBUTING.md:51,146`: drop the "record in docs/verification.md" advice.
- `docs/architecture.md`: delete the Smart Match and catalog sections
  (:114-14x) and "and semantic" (:60).
- `docs/providers.md`:
  - Delete "Optional Smart Match catalog" (:186-).
  - Note that `requery({catalog})` is accepted and ignored (:53).
- `docs/codex-integration-verification.md:66,94`: unlink `experiments/`.
  The file itself goes with #4.

## Alternatives rejected

- **Keep SmartMatch.js's lexical half** (request/merge without embeddings).
  It is 1 file and more tests kept for typo recovery that fuzzy match mostly
  covers already. If it is missed, nixarchy Local AI (Ollama) embeddings are
  the follow-up, and that would replace this code anyway.
- **Keep the vendored MenuModel and refresh its header.** It is a second
  copy that will drift from the shell nixarchy builds; Nixi already proved
  the import works.
- **Import MenuModel through `qs.plugins.menu`.** Quickshell's generated
  module lists `.qml` types, so it probably does not expose the `.js` file.
  This is unverified, and the file URL is proven.
- **Fix the `/usr/lib/qt6` and `/usr/share/omarchy` test paths here.** That
  is packaging (#3). Mixing it in would turn a pure-deletion diff into a
  refactor.

## Risks

- **Lost behaviour, accepted by design:**
  - "launch Chrome" no longer offers Chromium.
  - Rows from different providers that run the same command are no longer
    deduplicated.
  - Typo recovery across the whole catalogue is weaker. Each provider's own
    fuzzy search still recovers typos in its own rows.
- **MenuModel path:**
  - `file:///run/current-system/sw/...` exists only on NixOS with Omarchy in
    `systemPackages`, and not inside a Nix build sandbox. That is acceptable
    for a nixarchy-only plugin.
  - The sandboxed test run is solved in #3, by substituting the store path
    at build time.
  - If the shell's MenuModel API changes on an Omarchy update, the menu
    breaks at runtime instead of drifting silently. That is the point, but
    it needs the #3 CI to catch it.
- **User config:** an existing `keystroke.json` with a `matching` block keeps
  loading, because unknown fields are preserved and the id stays reserved.
- **Leftover user state:** a user's already-downloaded model and venv under
  `~/.local/share/keystroke/matching` are left in place. #1's migration can
  skip copying them.
- **No CI coverage:** after this, no CI job runs `tests/`, only the
  extensions check. #3 adds `nix flake check`.

## Verification

1. **QML unit suite** on this NixOS host, from `tests/`:
   `nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
   Baseline before the change is 265 passed, 0 failed. After the change,
   everything passes; the count drops only by `tst_smartmatch`'s cases.
2. **qmllint** from the same package over every `.qml` file, with
   `-I $OMARCHY_PATH/shell` via the `qs` shim: no new warnings compared with
   the baseline.
3. **No dangling references:**
   `rg -n 'SmartMatch|matchingSession|matching-start|matching-worker|keystroke-matching|omarchy/MenuModel|site/assets|docs/releases|verification\.md|engine-provenance|indexUrl|profile_palette|showcase'`
   returns nothing outside `intent/`, `spec/` and `plan/`.
4. **Runtime**, installed as the menu on this machine:
   - `Super+Space` opens the palette.
   - `sysshut` finds System › Shutdown, and `ffx` finds Firefox.
   - `2m in feet` answers.
   - Settings has no Matching screen.
   - Voice: `Super+Space` twice with "27 plus 90" gives 117.
   - Every nixarchy menu row, including the Ask group, matches the stock menu.
5. **Deferred to #3:** the Python quickshell checks (`tests/*_check.py`).
   They hardcode `/usr/share/omarchy`, so they cannot run on NixOS before
   #3. This is stated as a gap, not claimed as passing.
