---
status: approved
issue: 2
intent: intent/2026-09-24-2-trim-upstream-surface.md
amends: approved version at b433b08
---

# Spec: Remove upstream surface nixarchy does not need

## Design

Pure deletion, plus the edits that keep the remaining code consistent.
Nothing is renamed (#1). `codex/` is untouched (#4). Hardcoded `/usr`
paths are left for packaging (#3).

### 1. Smart Match: kept, and packaged by Nix in #3 (amended)

The approved version deleted Smart Match. That removal turned out to take
away more than embeddings, and the cost that motivated it was only the
impure install path, which Nix removes cleanly. Smart Match therefore stays
in #2 exactly as it is today: code, settings, helpers, prebuilt engine,
tests, CI attestation and docs.

What #2 has to put back, because all three teams' commits removed Smart
Match pieces:

- **Commit A (`604f2b1`):** revert it in full. That restores:
  - `core/SmartMatch.js`
  - `matching/` (engine source, prebuilt binary, `Session.qml`, descriptions)
  - `helpers/matching-*.py`
  - the Smart Match paths in `Keystroke.qml`
  - the Matching settings screen and `SettingsTree.catalog()`
  - the providers' `catalog()` functions (Applications, Hotkeys, SettingsProvider)
  - `Intent.js` as it was
  - the Smart Match tests, and `tst_match.qml` as it was
- **Commit B (`8c6c9db`), partially:**
  - Restore `OmarchyMenu.catalog()` and `catalogVisible()`, and
    `tests/catalog_check.py`.
  - The MenuModel switch (§3) stays.
- **Commit C (`5561061`), partially.** Restore:
  - every matching part of `bin/keystroke`:
    - the `matching` and `engine` usage lines and cases
    - the install step
    - the `matching/engine/target` exclude
    - the four matching test lines
  - `.gitignore`'s `matching/engine/target/` entry
  - the example config's `matching` block
  - `.github/workflows/engine.yml` and `docs/engine-provenance.md`. The
    prebuilt binary stays shipped until #3, and a shipped binary keeps its
    reproducibility check.
  - the Smart Match text in the docs:
    - README install paragraph and `## Smart Match` section
    - `docs/architecture.md` Smart Match and catalog sections
    - `docs/providers.md` "Optional Smart Match catalog" section and the
      `requery({catalog})` wording
    - `CONTRIBUTING.md`'s `matching-start.py` mention
  - Deleted docs links that those sections contain are dropped, not restored.

**What #3 then does**, added to #3's intent when it is written:
- Build `matching/engine` with `rustPlatform.buildRustPackage` from its
  `Cargo.lock`.
- Fetch the model's three files (`minishlab/potion-base-2M` at revision
  `389b9f6`, and optionally 8M) with `fetchurl`, using the SHA-256 digests
  already pinned in `helpers/matching-start.py`.
- Have `matching/Session.qml` start the engine directly with the store
  model directory.
- Delete the prebuilt binary, `build-prebuilt.sh`, the download/cargo/uv
  chain, the Python worker and its lockfile, and `engine.yml`. Nix builds
  from source, so reproducibility is structural.

### 2. Marketplace feed

No code reads `marketplace`, `autoCheck` or `indexUrl`, and
`extensions/index.json` does not exist. Delete the three keys from
`keystroke.example.json:80-82` and keep `"enabled": true`. Bundled
`extensions/` are unaffected. The upstream links in `core/Extensions.js:22-23`
and `core/SettingsTree.js:18` (GUIDE_URL) still resolve, and are repointed
in #1 together with the name.

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
  (`OmarchyMenu.qml:14-16`), as Nixi does. Since nixarchy#220, that data is
  the full menu with nixarchy's overrides already merged.
- `tests/tst_menumodel.qml:3` gets the same URL.
- Delete `omarchy/MenuModel.js`. `omarchy/` held nothing else and there is
  no `omarchy/LICENSE`. Attribution moves to the root README License line.
- There is no behaviour change, since the logic is identical.

### 4. Files and CI removed outright

- `site/`, `experiments/`, `tools/showcase/`, `tools/profile_palette.py`
- Root `assets/` (`keystroke.svg` plus 14 screenshots, nothing references
  them) and `preview.png`
- `docs/releases/`, `docs/history/`, `docs/verification.md`
- `.github/workflows/pages.yml`. `engine.yml` and `extensions.yml` stay.

### 5. Tests

- No test is deleted except the ones for files removed in §4, and there are
  none.
- `tests/catalog_check.py` and the Smart Match tests stay, because the code
  they test stays.
- `tests/tst_menumodel.qml` switches its import (§3).

### 6. Tooling and docs

- `bin/keystroke`: no change. Every edit the first version made there was
  Smart Match.
- `README.md`:
  - Delete the release link (:9), the showcase line (:11), the `site/assets`
    images and screenshot table, and links to deleted files.
  - The Smart Match paragraph and section stay.
  - The License line names the shell's `MenuModel.js`.
- `CONTRIBUTING.md`:
  - Drop the "record in docs/verification.md" advice.
  - Replace the vendored-MenuModel row and bullet with the shell import.
- `docs/architecture.md`: replace the MenuModel file-tree line and the
  "vendored" wording with the shell import. The Smart Match sections stay.
- `docs/codex-integration-verification.md:66,94`: unlink `experiments/`.
  The file itself goes with #4.

## Alternatives rejected

- **Delete Smart Match (the first approved version).** It loses:
  - typed "27 plus 90"
  - the Chromium stand-in
  - de-duplication across providers
  - cross-catalog typo recovery
  - semantic matching

  It saved nothing Nix packaging does not also remove.
- **Semantic matching through nixarchy Local AI (Ollama).** It only works
  with `localAi.enable`, which is off by default. It is slower, and it is
  new code.
- **Keep only SmartMatch.js's lexical half.** It recovers most behaviour but
  not semantic matching, for about the same effort as packaging the whole
  thing.
- **Keep the vendored MenuModel and refresh its header.** It is a second
  copy that drifts from the shell nixarchy builds.
- **Import MenuModel through `qs.plugins.menu`.** This is unverified, and
  the file URL is proven.
- **Fix the `/usr/lib/qt6` and `/usr/share/omarchy` test paths here.** That
  is packaging (#3).

## Risks

- **Smart Match stays as broken on nixarchy as it is today until #3.** On
  razer the helper reports "Matching helper stopped", with no python3/uv or
  model. This is not a regression, and #3 fixes it.
- **MenuModel path:**
  - `file:///run/current-system/sw/...` exists only on NixOS, and not inside
    a Nix build sandbox. #3 substitutes the store path for sandboxed tests.
  - An incompatible change to the shell's MenuModel breaks the menu at
    runtime instead of drifting silently. #3's CI catches it.
- **No CI coverage for `tests/`:** after this, only `extensions.yml` and
  `engine.yml` run. #3 adds `nix flake check`.

## Verification

1. **QML unit suite** on this NixOS host, from `tests/`:
   `nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
   Expected: **265 passed, 0 failed**, the same as the baseline before #2.
2. **qmllint** from the same package over every `.qml` file, with the `qs`
   shim: no new warnings compared with the baseline (484 lines).
3. **Smart Match is intact:** `git diff 6a99b6c -- core/SmartMatch.js matching helpers Keystroke.qml core/SettingsTree.js core/Intent.js providers/Applications.qml providers/Hotkeys.qml providers/SettingsProvider.qml tests bin/keystroke .gitignore .github/workflows/engine.yml docs/engine-provenance.md`
   shows only the §3 MenuModel import changes (in `tests/tst_menumodel.qml`).
4. **No dangling references:**
   `rg -n 'omarchy/MenuModel|site/assets|docs/releases|verification\.md|indexUrl|profile_palette|tools/showcase' -g '!intent/**' -g '!spec/**' -g '!plan/**'`
   returns nothing except the `codex-integration-verification.md` filename,
   which goes with #4.
5. **Runtime on razer**, installed as the menu:
   - `sysshut`, `ffx`, `2m in feet` and the `ask` rows behave as in the
     first run.
   - Settings has a Matching screen again.
   - Voice: "27 plus 90" gives 117.
   - Typed "27 plus 90" is expected to work only when the matching helper
     can start. On razer today it cannot, so this is recorded rather than
     claimed.
6. **Deferred to #3:** the Python quickshell checks (`tests/*_check.py`).
