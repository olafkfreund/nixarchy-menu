---
status: approved
issue: 20
author: olafkfreund
---

# Intent: the installer leaves a nixarchy-managed menu alone

## Problem

nixarchy can now declare nixarchy-menu (olafkfreund/nixarchy#946,
`programs.nixarchy.defaultPlugins.menu = true`). On such a host,
`~/.config/omarchy/plugins/nixarchy.menu` is a **symlink into `/nix/store`**,
and Home Manager owns it.

This repo's own `bin/nixarchy-menu` doesn't know that:
- **`install`** (`bin/nixarchy-menu:41-61`) builds and stages the plugin, then
  runs `rm -rf "$TARGET"` and moves a **real directory** into its place.
  nixarchy's activation leaves a real directory at a plugin id alone
  ("your own directory, not replacing it"). So from then on the hand copy
  silently outranks the declared pin. Nothing says so except a log line from
  nixarchy's hook at the next login.
- **`uninstall`** (`:62-67`) runs `rm -rf` on the managed link, and then says
  "the stock Omarchy menu is active again", which is not what happens on a
  managed host. HM puts the link back at the next activation.

Both were seen on razer while testing nixarchy#946. A hand install there sat in
front of the declared plugin until it was removed by hand.

## Proposed outcome

On a host where the plugin path is a link into `/nix/store`:
- `install` and `uninstall` **refuse before changing anything**. They don't
  build, stage, remove or enable.
- The message says what manages the plugin (nixarchy,
  `programs.nixarchy.defaultPlugins.menu`) and what to do instead. To try a
  local build, point nixarchy's `nixarchy-menu` input at it; to go back to a
  hand install, turn the default off first.

Everywhere else (no plugin yet, or a real directory from an earlier hand
install) both commands behave exactly as today.

## Affected users and systems

- **`bin/nixarchy-menu`,** its `install` and `uninstall` subcommands only.
  `enable`, `disable`, `open`, `toggle` and `dictate` go through the shell and
  are harmless on a managed host.
- **Anyone who runs the installer on a nixarchy host** with the menu declared.
  Today that's nobody by default, because the menu is opt-in.
- **Tests:** a new check for the refusal, wired in like the other `tests/`
  checks.

## Constraints

- No behaviour change on non-managed hosts, and Arch/Omarchy installs keep
  working.
- Detect the managed case from the filesystem only: a symlink whose target
  resolves under `/nix/store`. Don't require nixarchy or Nix tooling to be
  present to decide.
- Refuse **before** the `nix build`, so a refused run is fast and leaves no
  staging directory.

## Open questions

1. Should there be an explicit override, such as `--force`, for someone who
   knowingly wants a hand copy on a managed host? My lean is no: turning the
   default off is the supported way, and a force flag would bring back the
   silent-outranking state this intent removes.
