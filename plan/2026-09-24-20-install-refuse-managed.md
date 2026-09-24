---
status: draft
issue: 20
spec: spec/2026-09-24-20-install-refuse-managed.md
---

# Plan: the installer leaves a nixarchy-managed menu alone

## The approved decisions, carried over

1. **A managed target** is `$TARGET` being a symlink whose `readlink -f`
   resolves under `/nix/store/`. Everything else passes through unchanged:
   no target, a real directory, or a symlink elsewhere.
2. **The guard function `refuse_if_managed <verb>`** in `bin/nixarchy-menu`
   exits 1 with a message that:
   - names `programs.nixarchy.defaultPlugins.menu`
   - gives both ways out: `--override-input nixarchy-menu path:$ROOT`, or
     turning the default off and re-running
3. **Where it's called:** the first line of `install)`, before
   `stage_plugin`, and the first line of `uninstall)`. No other subcommand
   calls it.
4. **No `--force`.**
5. **A new check, `tests/install_guard_check.py`** (standard library only),
   with four cases: managed install, managed uninstall, real-dir install,
   and a symlink outside the store. It uses temp `$HOME` and a `PATH` of
   logging stubs. It is wired in as flake check `install-guard` (a
   `runCommand` like `migrate-state`), in the `checks` list, and in
   `bin/nixarchy-menu test`.

## Steps

1. **`bin/nixarchy-menu`:** add `refuse_if_managed` after `usage()`, and call
   it first in `install)` and `uninstall)`.
   → Verify: `shellcheck bin/nixarchy-menu` is clean.
2. **`tests/install_guard_check.py`:** the four cases.
   → Verify: it passes when run with `python3`. Removing the `install)` call
   makes case 1 fail (checked once, then restored).
3. **`flake.nix`:** add the `install-guard` check, modelled on
   `migrate-state` at `:295`, and add it to the checks list. Add the check to
   `bin/nixarchy-menu test`.
   → Verify: `nix build .#checks.x86_64-linux.install-guard` passes, and
   `nix flake check` passes.
4. **razer, manual.** Post a bus notice first. It's read-only apart from the
   refused command.
   - Copy the branch's `bin/nixarchy-menu` and `manifest.json` to
     `~/dev/zz-08903c-ig/`.
   - Run `bin/nixarchy-menu install` there.

   → Verify:
   - exit 1 with the message
   - `readlink ~/.config/omarchy/plugins/nixarchy.menu` is unchanged
     (`gh2g5346…`)

   Then remove `~/dev/zz-08903c-ig`.
5. **PR** linking the intent, spec and plan, and closing #20. Merge when CI
   is green and the user agrees. Tick epic #6.

## Tests

- `nix build .#checks.x86_64-linux.install-guard` passes and fails when the
  guard is reverted.
- `nix flake check` passes.
- The razer check in step 4.

## Rollback

Revert the commit. The installer goes back to overwriting unconditionally.
