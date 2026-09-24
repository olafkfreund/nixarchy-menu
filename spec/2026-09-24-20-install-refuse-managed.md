---
status: approved
issue: 20
intent: intent/2026-09-24-20-install-refuse-managed.md
---

# Spec: the installer leaves a nixarchy-managed menu alone

## Decision on the intent's open question

**No `--force`.** The intent was approved without an answer, so it takes the
default it proposed. The supported way to go back to a hand install is to turn
`programs.nixarchy.defaultPlugins.menu` off first. A force flag would bring back
the silent-outranking state the intent removes.

## Design

### 1. One guard function in `bin/nixarchy-menu`

```bash
# nixarchy manages the plugin (programs.nixarchy.defaultPlugins.menu): the
# target is Home Manager's link into the store. Replacing it with a copy would
# outrank the declared pin, and removing it lasts only until the next
# activation (olafkfreund/nixarchy#946).
refuse_if_managed() {
  [[ -L $TARGET && $(readlink -f "$TARGET") == /nix/store/* ]] || return 0
  cat >&2 <<MSG
nixarchy-menu: $TARGET is managed by nixarchy
(programs.nixarchy.defaultPlugins.menu), so '$1' would fight Home Manager.
  - To try a local build: point nixarchy's nixarchy-menu input at this checkout
    (nix build --override-input nixarchy-menu path:$ROOT ...).
  - To go back to a hand install: set defaultPlugins.menu = false, rebuild,
    then run '$0 $1' again.
MSG
  exit 1
}
```

- **Only the target path is checked.** A symlink whose resolved target is
  under `/nix/store` counts as managed. Nothing else is needed from nixarchy
  or Nix to decide.
- **Every other state passes through unchanged:** no target at all, a real
  directory from an earlier hand install, or a symlink somewhere else (for
  example a developer's `ln -s ~/src/...`).

### 2. Where it's called

- **`install)`:** the first line, `refuse_if_managed install`, comes
  **before** `stage_plugin`, so a refused run does no `nix build` and leaves
  no staging directory.
- **`uninstall)`:** the first line, `refuse_if_managed uninstall`, comes
  before any `omarchy plugin disable` or `rm`.
- **Not guarded:** `enable`, `disable`, `open`, `toggle`, `dictate`,
  `validate`, `check-extensions` and `test` go through the shell or only read
  the checkout.

### 3. The check: `tests/install_guard_check.py`

A standard-library Python check in the style of `migrate_state_check.py`. It
runs `bin/nixarchy-menu` against a temp `$HOME`, with a temp `PATH` whose
`nix`, `omarchy`, `omarchy-shell` and `omarchy-plugin-list` are stubs that
append their arguments to a log and exit 0. It has four cases:

1. **Managed, install:** the target is a symlink to a `/nix/store` path (the
   check's own source directory in the sandbox, which is under `/nix/store`).
   Expected:
   - exit status 1
   - stderr names `defaultPlugins.menu`
   - the stub log is **empty**, so no `nix build`
   - the link is unchanged
   - no `.nixarchy-menu.*` staging directory
2. **Managed, uninstall:** the same expectations, plus no `plugin disable`.
3. **Real directory, install:** the guard lets it through, and the stub log
   shows the `nix build` call. It is the first external command, and the run
   stops at the stubbed build's empty output, which the check tolerates. That
   is today's path, unchanged.
4. **Symlink outside the store** (a temp directory): the guard lets it
   through, the same as case 3.

**Wiring:**
- a new flake check `install-guard`, a `runCommand` like `migrate-state`
  (`flake.nix:295`)
- the new check added to the `checks` list and to `bin/nixarchy-menu test`
- `bin/nixarchy-menu` is already covered by the `shellcheck` check
  (`flake.nix:329`)

## Alternatives rejected

- **Detect nixarchy by querying Home Manager or `omarchy-plugin-list`:** it
  needs a running shell or HM tooling. The link target is exact and needs
  neither.
- **A warning instead of a refusal:** a warning scrolls past, and the damage
  (silent outranking) happens anyway.
- **`--force`:** see the decision above.

## Risks

- **A developer who symlinks the plugin to a `/nix/store` build by hand**
  (`ln -s $(nix build ...)`) is treated as managed. That's a rare workflow,
  and the message explains the way out. They can remove the link by hand.
- **Stub fidelity in case 3:** the check only asserts that `nix build` is
  attempted. It doesn't assert the rest of the install, which it can't run in
  the sandbox. The existing install path is otherwise unchanged by this diff.

## Verification

- `nix build .#checks.x86_64-linux.install-guard` passes, and it fails when
  `refuse_if_managed` is removed from `install)` (checked once, then
  restored).
- `nix flake check` passes, including shellcheck on the changed script.
- **Manual, on razer** (which is now nixarchy-managed, generation 2957):
  `bin/nixarchy-menu install` from a checkout exits 1 with the message, and
  `readlink ~/.config/omarchy/plugins/nixarchy.menu` is unchanged. This is
  read-only apart from the refused command, and gets a bus notice first.
