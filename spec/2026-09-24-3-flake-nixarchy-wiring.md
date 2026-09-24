---
status: draft
issue: 3
intent: intent/2026-09-24-3-flake-nixarchy-wiring.md
---

# Spec: Package nixarchy-menu as a flake and wire it into nixarchy

This spec covers the flake in **this repo**. The nixarchy wiring (input, the
`defaultPluginSet.menu` entry, the opt-in `defaultPlugins.menu` toggle, hook
placement and the competing-clone pre-disable) is olafkfreund/nixarchy#946,
with its own artifacts. It depends on this landing first.

## Design

### 1. Flake shape

The sibling repos' pattern (nixarchy-pkg, nixarchy-devenv) is: a plain-copy
`runCommand`, no symlinks in the plugin tree (`omarchy-plugin-validate`
refuses them), no Home Manager module, `x86_64-linux` and `aarch64-linux`.

- **Inputs:**
  - `nixpkgs`: nixpkgs-unstable. nixarchy sets `follows`, and its pin has
    rustc 1.98.1, which the engine's `Cargo.lock` needs.
  - `omarchy = { url = "github:basecamp/omarchy/v4.0.4"; flake = false; }`,
    used **only by checks** (`$OMARCHY_PATH` for the `qs` module and
    `MenuModel.js`). Upstream's `shell/Commons`, `shell/Ui` and
    `plugins/menu/MenuModel.js` are identical to nixarchy's patched tree.
    Taking nixarchy as an input would be circular. nixarchy sets
    `inputs.nixarchy-menu.inputs.omarchy.follows = "omarchy"`.
- **`packages.<sys>`:**
  - `matching-engine`: `rustPlatform.buildRustPackage { pname = "keystroke-matching"; version = "0.1.0"; src = ./matching/engine; cargoLock.lockFile = ./matching/engine/Cargo.lock; }`.
    It has four direct crates.io dependencies, no `build.rs` and no git
    dependencies. The binary keeps the name `keystroke-matching`, per #1.
  - `model-small`, `model-large`: one directory each, holding `config.json`,
    `tokenizer.json` and `model.safetensors` from `fetchurl` with the
    revisions and sha256 digests already pinned in `helpers/matching-start.py`:
    - `minishlab/potion-base-2M@389b9f6`: 8.2 MB
    - `minishlab/potion-base-8M@bf8b056`: 30.9 MB

    The two share the `tokenizer.json` store path (0.7 MB, identical digest).
    These are separate store paths, not part of the plugin tree.
  - `plugin` (`default`): a `runCommand` that copies only runtime files:
    - `manifest.json`, `LICENSE`, `*.qml`
    - `core/`, `providers/`, `ui/`, `voice/`, `codex/`, `extensions/` (minus
      their `tests/`), `helpers/`
    - `matching/Session.qml`, `matching/descriptions.json`,
      `matching/description-keys.json`
    - `bin/`

    Then it runs `substituteInPlace matching/Session.qml --replace-fail
    @matchingEngine@ … @modelSmall@ … @modelLarge@ …`. Excluded: `tests`,
    `intent`, `spec`, `plan`, `docs`, `tools`, `matching/engine`,
    `__pycache__`.
- **`checks.<sys>`** (all offline, in the sandbox). They share one `src`: a
  copy with the MenuModel URL substituted to `file://${omarchy}`, and
  `OMARCHY_PATH=${omarchy}`.

  | Check | Covers | Runtime inputs |
  |---|---|---|
  | `plugin` | manifest id `nixarchy.menu` and `clonedFrom`, entry files present, **no symlinks**, the **pacman/yay grep identical to nixarchy's `validatedPlugins`**, no leftover `@…@` placeholder | the `plugin` output |
  | `qml-unit` | `qmltestrunner` on `tests/` plus `tools/check_extensions.py` (the extension tests) | qt6.qtdeclarative, qtbase, python3 |
  | `lint` | `tests/lint.sh` | qtdeclarative, ripgrep |
  | `quickshell` | the quickshell `*_check.py` palette and session checks, and the three extension palette checks, run sequentially | quickshell 0.3.1 (nixpkgs), python3, bash, jq, coreutils, qtbase, `HOME=$TMPDIR` |
  | `migrate-state` | `tests/migrate_state_check.py` | python3, jq |
  | `engine` | `tests/matching_engine_check.py`, rewritten: protocol plus tokenizer parity with HF `tokenizers` on the real small model | `matching-engine`, `model-small`, python3 with tokenizers 0.23.2 |
  | `shellcheck` | `helpers/*.sh`, `bin/nixarchy-menu` | shellcheck |

  Excluded: `tests/hotkeys_check.py`. It needs a live Hyprland, so it runs
  via `bin/nixarchy-menu test` on a host, and it now skips cleanly when
  `hyprctl` is absent.
- **`devShells.default`:** qtdeclarative, qtbase, quickshell, python3, jq,
  fd and shellcheck. Development then runs `bin/nixarchy-menu test`.

### 2. Smart Match: Nix-provided engine and models

- **Starting the engine:** `matching/Session.qml:9` runs the engine directly:
  `["@matchingEngine@", "--model-dir", model === "large" ? "@modelLarge@" : "@modelSmall@", "--model", model]`.
  The engine already speaks the same stdout protocol (ready, result,
  error). The model switch, retry, idle unload and restart stay unchanged.
  The startup timeout drops from 300 s to 10 s, and the "downloaded once"
  and "check your connection" wording goes.
- **Deleted:**
  - `helpers/matching-start.py`, `helpers/matching-worker.py`
  - `matching/requirements.{in,lock}`
  - `matching/bin/keystroke-matching` and its `.json`
  - `matching/engine/build-prebuilt.sh`
  - `.github/workflows/engine.yml`, `docs/engine-provenance.md`
  - `tests/matching_worker_check.py`
  - `bin/nixarchy-menu` `matching`/`engine` subcommands and its install matching step
  - the `models` pair in `helpers/migrate-state.sh` (models are in the
    store now) and its assertions in `tests/migrate_state_check.py`
- **Kept:** `matching/engine/**` (built by Nix, byte-identical),
  `matching/descriptions.json` and `description-keys.json` (read by
  `NixarchyMenu.qml`), `tests/matching_session_check.py` and
  `tests/palette_matching_check.py` (fake workers).
- **An unsubstituted checkout** (raw copy without Nix) fails the engine start
  as "Matching helper stopped", and ordinary search keeps working.

### 3. Arch paths → NixOS

- **Qt tools come from `PATH`:**
  - `bin/nixarchy-menu:83` and `tests/lint.sh:10` use `qmltestrunner` and
    `qmllint` from PATH. `lint.sh` drops the `-I /usr/lib/qt6/qml`.
  - `tools/check_extensions.py`: delete `QT_BIN` (it already falls back to
    `shutil.which`) and the `-I /usr/lib/qt6/qml` at :141.
- **The omarchy tree comes from `$OMARCHY_PATH`:** the 16 quickshell checks
  and three extension palette checks use
  `OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")` for both
  the `qs` symlink and the injected `omarchyPath`. `bin/nixarchy-menu test`
  defaults `OMARCHY_PATH` to `/run/current-system/sw/share/omarchy` when it
  is unset.
- **Fake helper scripts** use `#!{sys.executable}` and `shutil.which("bash")`
  instead of `#!/usr/bin/python3`, `/bin/bash` and `#!/usr/bin/env python3`
  (`palette_url_check`, `voice_session_check`, the translate and gif-search
  palette checks).
- **`tests/hotkeys_check.py:19`:** skip when `shutil.which("hyprctl")` is
  None, instead of crashing.
- **`core/Hotkeys.js:18`:** the fallback becomes
  `/run/current-system/sw/share/omarchy`. The shell normally injects the path.
- **Out of scope, noted:** `extensions/timer` sound path
  `/usr/share/sounds/freedesktop` (a runtime feature, own follow-up), and
  the codex prompt text (#4 deletes it).

### 4. nixarchy validator fix

`providers/Files.qml:114` "sudo pacman -S fd, then search again" becomes
"fd is not installed; install fd, then search again". It is the only
pacman/yay hit, and the `plugin` check enforces the same grep from now on.

### 5. `bin/nixarchy-menu`

- **`install`:**
  1. `nix build .#plugin` (a writable copy of the output, `cp -r` plus `chmod -R u+w`)
  2. `omarchy plugin validate` on it
  3. the #1 migration
  4. the copy to `~/.config/omarchy/plugins/nixarchy.menu`
  5. the disable-other-clone-first swap from #1 (unchanged)
  6. enable

  No rsync of the checkout.
- **`test`:** as above, with PATH tools and `OMARCHY_PATH`. The engine check
  takes `--engine`/`--model-dir` arguments, and `test` passes the
  `nix build` outputs.

### 6. CI and docs

- **CI:** `.github/workflows/nix.yml` runs `nix flake check -L` on push and
  PR, with the action pinned by SHA like the existing workflows.
  `extensions.yml` stays.
- **Docs:**
  - README: enable via nixarchy (`programs.nixarchy.defaultPlugins.menu =
    true`, once nixarchy#946 lands), otherwise `bin/nixarchy-menu install`.
    The develop/test section uses `nix develop` / `nix flake check`. The
    Smart Match text says models ship with the package.
  - `matching/README.md`: rewrite the Engine section.
  - `docs/architecture.md:114-125` and `CONTRIBUTING.md:124` (pinning
    example): update.

## Alternatives rejected

- **nixarchy as a flake input** (for the omarchy tree): circular, because
  nixarchy takes nixarchy-menu as an input.
- **Paths via an env var or wrapper:** needs a wrapper around
  `omarchy-shell`, which we don't own.
- **Paths via a generated JSON file read with FileView:** adds an async load
  and a startup race.
- **Keep the prebuilt binary plus CI attestation:** Nix builds it from
  source per system, so reproducibility is structural. The prebuilt only
  ever served x86_64.
- **A Home Manager module in this repo:** nixarchy's `defaultPluginSet`
  already installs, validates and enables plugins. A second module is YAGNI.
- **Only the small model:** the Settings switch to Large would then need a
  rebuild. The large model costs 30.9 MB.
- **Keep `helpers/matching-start.py` as a thin launcher:** it has no job
  left.

## Risks

- **Omarchy drift:** the standalone checks pin omarchy v4.0.4. When nixarchy
  moves to a newer Omarchy, `follows` makes this repo's checks use it when
  built via nixarchy. The standalone flake lags until its lock is bumped.
- **Check run time:** the `quickshell` check runs about 22 scripts
  (roughly 1.5–2 min). It is acceptable.
- **aarch64:** declared and evaluated, but not built or run by anyone yet.
  CI builds x86_64 only.
- **The engine check with a real model** is new. If HF `tokenizers` 0.23.2
  and the hand-written tokenizer disagree, it fails. That is the point, but
  it may surface an old latent mismatch.
- **Existing users of a `bin/nixarchy-menu install`ed copy** (razer) lose
  Smart Match until they reinstall from `nix build`. The notice text says
  so.

## Verification

1. **`nix flake check -L` passes on x86_64-linux:**
   - `qml-unit`: all pass, at least 266.
   - `lint`: no warning beyond today's set.
   - `quickshell`: every check passes, with hotkeys skipped.
   - `migrate-state`, `engine` (protocol plus parity on real potion-2M),
     `shellcheck`, and `plugin` all pass.
2. **`nix build .#plugin`:**
   - `find result -type l` is empty.
   - `rg '@(matchingEngine|modelSmall|modelLarge)@' result` is empty.
   - `omarchy-plugin-validate result` passes.
   - The pacman/yay grep is clean.
3. **The same checks on a plain NixOS host:** `bin/nixarchy-menu test` inside
   `nix develop`, with `OMARCHY_PATH` unset (it uses the default).
4. **Razer** (never p620):
   - `bin/nixarchy-menu install` from the Nix output, then a shell restart.
   - Smart Match is **Ready with no network access**: block the network, or
     at least confirm nothing new appears under
     `~/.local/share/nixarchy-menu/matching`.
   - "27 plus 90" gives 117.
   - Switching the model to Large in Settings reports Ready.
   - The palette checks from #1 still pass.
   - Restore razer afterwards.
5. **CI:** the `nix.yml` job is green on the PR, and `engine.yml` is gone.
