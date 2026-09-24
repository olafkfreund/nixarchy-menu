---
status: approved
issue: 3
spec: spec/2026-09-24-3-flake-nixarchy-wiring.md
---

# Plan: Package nixarchy-menu as a flake

## Approved decisions (carried over from the spec)

- **Flake inputs:** `nixpkgs` (unstable; nixarchy's pin has rustc 1.98.1)
  and `omarchy = github:basecamp/omarchy/v4.0.4, flake = false`, for checks
  only. No nixarchy input. Systems are x86_64-linux and aarch64-linux.
- **Packages:**
  - `matching-engine`: `buildRustPackage` from `matching/engine/Cargo.lock`.
    The binary stays `keystroke-matching`.
  - `model-small`: potion-base-2M@389b9f6, 8.2 MB.
  - `model-large`: potion-base-8M@bf8b056, 30.9 MB.
  - The models are `fetchurl` with the sha256 hex already in
    `helpers/matching-start.py`, and they share `tokenizer.json`.
  - `plugin` = `default`: a plain-copy `runCommand` with no symlinks and
    runtime files only. It runs `substituteInPlace matching/Session.qml` for
    `@matchingEngine@`, `@modelSmall@` and `@modelLarge@`.
- **Checks** (offline): `plugin`, `qml-unit`, `lint`, `quickshell`,
  `migrate-state`, `engine`, `shellcheck`.
  - They share a `src` with the MenuModel URL substituted to
    `file://${omarchy}`, and `OMARCHY_PATH=${omarchy}`.
  - `hotkeys_check` is excluded and skips without `hyprctl`.
- **devShell:** qtdeclarative, qtbase, quickshell, python3, jq, fd,
  shellcheck.
- **Smart Match:** `Session.qml` runs the engine directly, and the timeout is
  10 s.
  - **Deleted:** `matching-start.py`, `matching-worker.py`, the
    requirements, the prebuilt binary and its json, `build-prebuilt.sh`,
    `engine.yml`, `engine-provenance.md`, `matching_worker_check.py`, the
    bin `matching`/`engine` subcommands and install step, and the models
    migration pair.
  - **Kept:** `matching/engine/**`, the descriptions files, and the
    session/palette matching checks.
- **Paths:**
  - Qt tools come from PATH.
  - `OMARCHY_PATH` with fallback `/usr/share/omarchy` in the tests.
    `bin/nixarchy-menu test` defaults it to
    `/run/current-system/sw/share/omarchy`.
  - Fake scripts use `sys.executable` and `which("bash")`.
  - `core/Hotkeys.js` falls back to `/run/current-system/sw/share/omarchy`.
- **Validator:** `providers/Files.qml:114` → "fd is not installed; install
  fd, then search again".
- **`bin/nixarchy-menu install`:** `nix build .#plugin`, validate, migrate,
  copy (writable), the disable-other-clone swap, enable. No rsync of the
  checkout.
- **CI:** `.github/workflows/nix.yml` runs `nix flake check -L`, with the
  action pinned by SHA.
- **Out of scope:**
  - the nixarchy wiring (nixarchy#946)
  - the timer sound path
  - codex (#4)

## Team split

Three teammates edit disjoint files. None of them commits. The lead
integrates, runs `nix flake check`, updates razer, gets the Codex review and
opens the PR.

### J: `flake`

Owns `flake.nix`, `flake.lock`, `.github/workflows/nix.yml`, and the deletion
of `.github/workflows/engine.yml`.

1. Write `flake.nix`, following the pattern of `nixarchy-pkg/flake.nix` and
   `nixarchy-devenv/flake.nix`:
   - inputs
   - packages: engine, models, plugin
   - checks as in the spec table, with the check commands read from K's and
     L's files by name
   - `devShells.default`

   Run `nix flake lock`.
2. Build and verify:
   - `nix build .#matching-engine .#model-small .#model-large .#plugin`.
   - Verify with `find result -type l` (empty for plugin), no `@…@` left in
     the plugin, and `omarchy-plugin-validate` on the plugin output.
3. Write `nix.yml`, modelled on the existing workflow style (SHA-pinned
   actions, `permissions: contents: read`). Delete `engine.yml`.

→ **Verify:** the four packages build. `nix flake check --no-build` evaluates.
The `plugin` and `shellcheck` checks pass once K and L are done. The lead
runs the whole set.

### K: `smartmatch`

Owns:
- `matching/Session.qml` and `matching/README.md`
- the deletions `helpers/matching-*.py`, `matching/requirements.*`,
  `matching/bin/`, `matching/engine/build-prebuilt.sh`,
  `docs/engine-provenance.md` and `tests/matching_worker_check.py`
- `tests/matching_engine_check.py`
- `helpers/migrate-state.sh` and `tests/migrate_state_check.py`
- the Smart Match strings in `core/SettingsTree.js`
- `bin/nixarchy-menu`

1. `Session.qml`: set the command with the placeholders, set the timeout to
   10 s, and fix the messages. `SettingsTree.js`: reword the "downloaded
   once" and retry texts.
2. Make the deletions above.
3. Rewrite `matching_engine_check.py`:
   - It takes `--engine` and `--model-dir`, and no longer runs cargo or reads
     the manifest.
   - It keeps the protocol and tokenizer parity tests on the real model, and
     skips parity only if `tokenizers` is missing.
4. Drop the models pair and its assertions from `migrate-state.sh` and
   `migrate_state_check.py`.
5. Update `bin/nixarchy-menu`:
   - `install` uses `nix build --no-link --print-out-paths .#plugin`, copies
     the result writable, runs `omarchy plugin validate` on the copy, and
     keeps the #1 migration and swap.
   - `test` uses PATH tools and the `OMARCHY_PATH` default, and runs the
     engine check with the built engine and model.
   - Remove the `matching` and `engine` subcommands.
6. Rewrite the Engine section of `matching/README.md`.

→ **Verify:**
- `python3 tests/migrate_state_check.py` passes.
- `sh -n` and `shellcheck` are clean.
- With `nix build .#matching-engine .#model-small`, running
  `python3 tests/matching_engine_check.py --engine … --model-dir …` passes.
- The QML suite still passes.

### L: `paths` (tests, validator, docs)

Owns:
- every `tests/*_check.py` except `matching_engine_check`,
  `matching_worker_check` and `migrate_state_check`
- `extensions/*/tests/palette_check.py`
- `tests/lint.sh`, `tools/check_extensions.py`
- `core/Hotkeys.js`, `providers/Files.qml`
- `README.md`, `docs/architecture.md`, `CONTRIBUTING.md`

1. Replace `/usr/share/omarchy` with `OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")`
   in the 16 quickshell checks and the three extension palette checks, for
   both the `qs` symlink and `omarchyPath`.
2. Fix the fake shebangs to `sys.executable` and `shutil.which("bash")`.
   Make `hotkeys_check` skip without `hyprctl`.
3. `lint.sh`: use `qmllint` from PATH, no `/usr/lib/qt6`.
   `check_extensions.py`: drop `QT_BIN` and the `-I /usr/lib/qt6/qml`.
4. `core/Hotkeys.js:18` fallback. `providers/Files.qml:114` wording.
5. Docs:
   - README: enable via nixarchy#946 (`programs.nixarchy.defaultPlugins.menu`),
     otherwise `bin/nixarchy-menu install`.
   - Develop/test: `nix develop`, `nix flake check`.
   - Smart Match: models ship with the package.
   - `architecture.md:114-125` and `CONTRIBUTING.md:124`.

→ **Verify:**
- Inside `nix develop`, or `nix shell` with quickshell, qt and python3, with
  `OMARCHY_PATH` pointing at an omarchy tree:
  - every quickshell check passes on p620 (read-only: temp HOME, no install)
  - the QML suite and `tools/check_extensions.py` pass
- `rg -n '/usr/(lib/qt6|share/omarchy)'` is left only as fallback defaults.

### M: `lead`

1. **`nix flake check -L`:** all checks pass. Send failures back to their
   owner.
2. **Commits:** J, K, L, each with its deviations in this file.
3. **Razer**, which the user allows to be updated and left updated (it is
   the Smart Match test box):
   - Announce on the agent bus.
   - Sync the branch to `~/dev/nixarchy-menu-test`.
   - Run `bin/nixarchy-menu install`, which builds on razer, then restart
     the shell.
   - Check:
     - `nixarchy.menu` enabled, `omarchy.menu` and `evindor.keystroke`
       disabled, and the button in the stock slot
     - Smart Match **Ready**
     - the engine running from `/nix/store` (`ps` shows the store path)
     - **no** `~/.local/share/nixarchy-menu/matching` created, so no
       download
     - "27 plus 90" gives 117, and "launch chrome" offers Chromium
     - switching the model to Large gives Ready, then switch back to Small
   - **Leave it installed** so the user can test Smart Match on razer.
4. **Codex review:** read-only, `codex review --base main`. Verify each
   finding, and fix it with a plan note.
5. **PR:** link the intent, spec and plan, and include CI (`nix.yml` green).
   Merge when the user says so.

## Tests

1. `nix flake check -L` → all checks pass (x86_64-linux).
2. `nix build .#plugin` → no symlinks, no placeholders, validator passes.
3. `bin/nixarchy-menu test` on p620 inside `nix develop` (read-only, temp
   HOME) → passes.
4. The razer checks in step M3.
5. CI `nix.yml` is green on the PR.

## Rollback

- Revert the three commits.
- Razer: `bin/nixarchy-menu uninstall`, or
  `omarchy plugin disable nixarchy.menu`, which restores the stock menu.
  Old Keystroke data is never touched.

## Deviations during implementation

### K: smartmatch
- **Installed plugin permissions:** `bin/nixarchy-menu install` sets `chmod 755` on the stage dir, because `mktemp -d` creates it as 0700 and the old rsync produced 755.
- **Engine test coverage:** `matching_engine_check.py` also covers the startup exit codes (2 for bad arguments, 1 for an unloadable model) and one real-model ranking query.
- **Parity must not skip:** `nix shell nixpkgs#python3Packages.tokenizers` does not make `tokenizers` importable, and parity would then SKIP silently. The engine check and the devShell use `python3.withPackages (p: [p.tokenizers])`, and the engine check fails on any `SKIP`.
- **Leftover reference:** `matching/engine/src/main.rs:9` still mentions `matching-worker.py` in a doc comment. It is left unchanged because the engine tree stays byte-identical.

### L: paths
- **Pre-existing test failures fixed in L's files:**
  - `catalog_check` still copied `omarchy/`, which #2 deleted.
  - The browser-search palette check picked up the host's real default browser through `xdg-mime`. A fake `xdg-mime` stub now sits next to the fake `xdg-settings`.
- **`codex_session_check`:** the harness QML failed to parse (`Unexpected token ';'`) because of the inline `host: QtObject {…}` stub added in #1. It now sits on its own line.
- **Read-only sandbox source:** checks that `copytree` the repo then rewrite a copied file failed with PermissionError. Every `copytree` in L's checks is now followed by making the copy owner-writable, including `files_check` and `matching_session_check`.
- **`palette_currency_check` was flaky under sandbox load.** A cached pass hid it; the lead's forced `--rebuild` exposed it. There were two harness races, both from Quickshell FileView's asynchronous writes:
  - **Stage 3:** the fake curl's mode file sometimes lagged behind the fetch. The fake curl now answers by call count: the first call returns empty, later calls return the table.
  - **Stage 5:** `rates.reload()` ran only once, possibly before the async write landed. It is now polled.
  - No timeout was raised.
  - **Verified:** 4 runs by L (one build plus 3 `--rebuild`) and 2 more `--rebuild` runs by the lead, each 20/20 PASS.
- **README:** "Smart Match models" was dropped from the Keystroke-migration sentence, because models are no longer migrated.

### J: flake
- **nixpkgs pin:** pinned to nixarchy's exact revision `e554fab7` (rustc 1.98.1, quickshell 0.3.1).
- **Sizes:** engine 728K, model-small 7.9M, model-large 30M, plugin 1016K.
- **Extra environment the sandbox checks needed:**
  - `quickshell` needs `XDG_RUNTIME_DIR`, otherwise it hangs indefinitely.
  - `quickshell` and `qml-unit` need `QML2_IMPORT_PATH` and `QT_PLUGIN_PATH` for offscreen QtQuick.Window.
  - `fd` is required by `files_check`.
  - `ripgrep` is in `lint` and the devShell, for `lint.sh`.
- **Quickshell check list:** it runs an explicit list of 20 files, including `clipboard_transfer_check` and `files_check`, which need only temp state.
- **Commit attribution:** `engine.yml`'s deletion (J) landed in commit `9b6717d` (L) because it was already staged when L was committed. There is no content difference.

### Lead: verification note
- **Cache:** `nix flake check` served every check from cache on the first integration run, and the log showed no test output. Forced `nix build --rebuild -L` on `quickshell` and `engine` is what exposed the flaky currency check.
- **CI:** CI builds from scratch, so a flaky check would have failed there at random.

### Razer results (f67fab8), left installed
- **Build:** `bin/nixarchy-menu install` built the engine, both models and the plugin on razer, then installed and enabled the plugin.
- **Plugins:** `nixarchy.menu` enabled; `omarchy.menu` and `evindor.keystroke` disabled. The bar entry is `nixarchy.menu` only.
- **Engine process:** `/nix/store/…-keystroke-matching-0.1.0/bin/keystroke-matching --model-dir /nix/store/…-keystroke-model-small --model small`.
- **No download:** `~/.local/share/nixarchy-menu/matching` does not exist.
- **Palette:**
  - Smart Match is Ready. "27 plus 90" gives 117, "launch chrome" offers Chromium, and `sysshut` finds Shutdown.
  - No provider problems.
- **Large model:** switching to Large in the config gave Ready, with the engine on the `model-large` store path. Switching back to Small gave Ready. The config was restored byte-identical afterwards.
- **Left installed for the user to test Smart Match**, as requested.

### CI fix 1: quickshell harness re-entrancy (L)
- **Symptom:** PR #11's first CI run failed `palette_dictation_check` with `TimeoutExpired` after 12 s on the GitHub runner. It passed on p620.
- **Root cause:** a repeating timer called QtTest `keyClick`, which runs a nested event loop. Under load that loop outlasted the timer interval, so the same stage re-entered, ran to completion, and failed the outer tick's check. `check()` then called `Qt.quit()` inside the nested loop, which crashed quickshell. The crash handler kept the pipes open, so the process hung silently until the outer timeout. Any failed check could turn into a silent hang in the same way.
- **Fix (test files only):**
  - Stages move on before calling `keyClick`. A `busy` re-entrancy guard is added in the codex_session, palette_shortcut and gif-search harnesses.
  - `check()` stops the stages and quits through `Qt.callLater` (11 harnesses).
  - The dictation stage waits for search focus, and its QML guard goes from 6 s to 20 s.
  - The outer subprocess timeouts go to 120 s as a hang backstop only. The QML guards remain the deadlines.
- **Verified:**
  - dictation under 1-core stress: 3/3 hung before, 7/7 pass after
  - all 20 checks pinned to 4 cores with 4 pinned stressors: 20/20
  - sandbox `--rebuild`: 20/20
- **Out of scope:** a separate config-load ordering race under extreme contention (one core shared five ways) is filed as #12.
- **Process:** L's first pressure run used stress-ng on all CPUs of p620, the user's desktop. The lead stopped it; later runs were pinned to 4 cores.

### CI fix 2: lint actually lints in the sandbox (lead)
- **Problem:** the sandbox `lint` check passed while qmllint printed "Failed to import QtQuick/Quickshell…" for every file. Without Qt import paths it resolves nothing and only warns, so the check was vacuous.
- **Fix:** `tests/lint.sh` turns each `QML2_IMPORT_PATH` entry into a qmllint `-I`, and the flake's lint check sets `QML2_IMPORT_PATH` to qtdeclarative's and quickshell's `lib/qt-6/qml`.
- **Result:** 0 "Failed to import", 264 real warnings, and the check passes. Warnings do not fail qmllint, as on a host.
