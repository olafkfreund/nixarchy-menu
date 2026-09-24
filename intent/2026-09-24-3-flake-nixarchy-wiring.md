---
status: approved
issue: 3
author: olafkfreund
epic: 6
---

# Intent: Package nixarchy-menu as a flake and wire it into nixarchy

## Problem

nixarchy-menu can only be installed imperatively, and parts of it assume
Arch:

- **Install is imperative.** `bin/nixarchy-menu install` rsync-copies a
  checkout into `~/.config/omarchy/plugins/nixarchy.menu`. nixarchy cannot
  declare it, pin it or roll it back like its other plugins (nixarchy-pkg,
  -devenv, -herdr, …).
- **Smart Match installs itself at runtime:**
  - `helpers/matching-start.py` downloads the model at first use.
  - It then picks between a committed prebuilt x86_64 binary, a `cargo`
    build into `$XDG_DATA_HOME`, and a `uv` Python venv.
  - None of this is declarative, offline-safe or reproducible on NixOS.
    On razer the helper failed until a manual run fetched the model.
- **Tests assume Arch paths and do not run in CI.**
  - `/usr/lib/qt6` (`bin/nixarchy-menu:83`, `tests/lint.sh`,
    `tools/check_extensions.py`) and `/usr/share/omarchy` (16 palette
    checks, the three extension palette checks, and `core/Hotkeys.js:18`).
  - Fake helpers with `#!/usr/bin/python3` shebangs.
  - The Python palette checks have never run on NixOS in this fork, and no
    CI job runs `tests/`.
- **nixarchy would reject the plugin at build time.**
  - Its `validatedPlugins` pacman/yay grep hits `providers/Files.qml:114`
    ("sudo pacman -S fd").
  - Its enable-once hook hard-codes `omarchy-plugin-enable "$id" right`,
    which would drag the menu button to the right-hand section.
  - The hook has no way to disable an already-enabled `evindor.keystroke`
    first. The #1 research showed the order matters: otherwise the old
    menu keeps winning, or the stock menu comes back.

## Proposed outcome

- **This repo has a `flake.nix`:**
  - `packages.<system>.plugin` (and `default`): a plain-copy plugin tree
    with no symlinks, which `omarchy-plugin-validate` requires.
  - A Nix-built Smart Match engine, and the pinned models fetched with
    their existing SHA-256 digests.
  - `checks` that run the QML unit tests, qmllint, the quickshell palette
    checks, the migration check and the engine/tokenizer parity check,
    all in the sandbox, offline.
- **Smart Match works on a fresh nixarchy machine with no network at first
  use.** The download, cargo and uv install chain is deleted, along with
  the committed binary and its CI attestation. Nix builds from source.
- **The tests run on NixOS.** `bin/nixarchy-menu test` and the checks use
  `$OMARCHY_PATH` and binaries on `PATH`, not `/usr/...`.
- **nixarchy can enable it declaratively** (a separate nixarchy issue):
  - a pinned flake input
  - a `defaultPluginSet.menu` entry and a `defaultPlugins.menu` toggle
  - an enable-once hook that disables any other enabled `omarchy.menu`
    clone first, and places the menu in the stock menu's slot
  - `Super+Space` opens nixarchy-menu, and turning the toggle off restores
    the stock menu

## Affected users and systems

- **This repo:** new `flake.nix` and `flake.lock`. `matching/Session.qml`,
  `helpers/`, `bin/nixarchy-menu`, `tests/`, `tools/check_extensions.py`,
  and the docs about the engine. `engine.yml` is removed, and a Nix CI
  workflow is added.
- **nixarchy:** `flake.nix` input, `modules/home.nix` (defaultPluginSet, the
  hook), `docs/internals/flake.md`, and `checks.options`. It has its own
  issue and its own intent → spec → plan in the nixarchy repo.
- **razer:** the first declarative install test. **p620 stays untouched**
  until the user chooses.
- **Existing Keystroke users** are handled by #1's migration. The hook's
  disable-first step covers an enabled `evindor.keystroke`.

## Constraints

- **No circular flake inputs.** This repo takes upstream omarchy
  (`github:basecamp/omarchy/v4.0.4`, `flake = false`) for its checks, and
  nixarchy `follows` it so there is one pin.
- **Models are fixed-output fetches of the exact revisions and digests
  already pinned in `helpers/matching-start.py`.** No unpinned download.
- **The plugin tree contains no symlinks.** It is a plain copy, as in the
  siblings.
- **The QML behaviour of the palette does not change,** apart from Smart
  Match no longer downloading or building anything.
- **nixarchy's pacman/yay ban and plugin validation must pass.**
- **The Python checks keep working on a plain host** through
  `bin/nixarchy-menu test` (OMARCHY_PATH-aware), not only in the sandbox.

## Open questions

1. **On by default in nixarchy, or opt-in?** Proposed: **opt-in first**
   (`defaultPlugins.menu = false`). Flip it to default-on in a follow-up once
   it has run on razer and p620 for a while. Replacing everyone's menu is
   the biggest user-visible change in the epic.
2. **Which Smart Match models ship?** Proposed: **both**, as separate store
   paths (about 8 MB small and 30 MB large; estimated, measured in the
   spec). The Settings model switch keeps working without a rebuild. The
   tokenizer file is shared.
3. **The nixarchy half:** a separate issue in `olafkfreund/nixarchy`, with
   its own artifacts. Proposed: yes, filed once this intent is approved,
   and it depends on this repo's flake landing first.
4. **Dev checkout without Nix:** after this, Smart Match paths are filled
   in at build time, so a raw checkout copied by `bin/nixarchy-menu install`
   has no engine and ordinary search still works. Proposed: accept this.
   Development uses `nix build` / `nix develop`, and `install` installs
   `nix build .#plugin`'s output instead of rsync-copying the checkout.
