---
status: approved
issue: 1
author: olafkfreund
epic: 6
---

# Intent: Rename Keystroke to nixarchy-menu and migrate user state

## Problem

The fork still presents itself as upstream Keystroke everywhere a user,
nixarchy or another plugin sees it (461 mentions in 92 files):

- **Identity:**
  - Plugin id `evindor.keystroke` (`manifest.json:3`), which the README
    calls permanent.
  - Name, author, homepage and description in `manifest.json`.
  - Entry file `Keystroke.qml`.
  - Bar widget module `evindor.keystroke` (`BarWidget.qml:19`).
  - `bin/keystroke`.
  - UI strings such as "Keystroke Settings" and "Learn Keystroke".
- **Upstream links:**
  - the usage guide (`core/SettingsTree.js:18`) → evindor.github.io
  - extension source and guide (`core/Extensions.js:22-23`)
  - README install line `omarchy plugin add https://github.com/evindor/keystroke.git`
  - the engine attestation command (`docs/engine-provenance.md:69-70`)
- **User state under the old name:**
  - `~/.config/omarchy/keystroke.json` (settings)
  - `~/.local/state/keystroke/` (frecency `usage.json`, Codex history, currency usage)
  - `~/.local/share/keystroke/` (user extensions, the Smart Match model and runtime)
  - `~/.cache/keystroke/` (currency rates)
  - the voice bind block in `~/.config/hypr/bindings.lua`, delimited by
    `-- >>> keystroke voice` … `-- <<< keystroke voice`
    (`core/VoiceBindings.js:15-16`)
- **The README** describes installing upstream Keystroke on Arch Omarchy, not
  nixarchy-menu on nixarchy. Its full rewrite was deferred from #2.

## Proposed outcome

- **Identity:** the plugin is **`nixarchy.menu`** (decided on 2026-09-24),
  named **nixarchy-menu** in the manifest, bar widget, settings, footer, CLI
  and docs. It still replaces the stock menu through
  `omarchy.clonedFrom: "omarchy.menu"`.
- **Your state carries over.** A user who ran Keystroke opens nixarchy-menu
  and finds their settings, frecency, recent Codex questions, user
  extensions, downloaded model and voice binds as they left them. The old
  files are copied, never moved or deleted, so going back still works.
- **The voice bind block** is recognised under its old markers and rewritten
  under new ones, never duplicated.
- **Upstream is credited, not presented as the product:** the README says
  it is a fork of evindor/keystroke by Arseniy Zarechnev, MIT, with
  `LICENSE` kept. All links point at olafkfreund/nixarchy-menu or its docs.
- **The README is short and nixarchy-first:** what it is, how nixarchy
  enables it, keys, and where the details live.

## Affected users and systems

- **This repo:** most files. Tests and fixtures that name paths or the id
  change with it.
- **razer:** has Keystroke 1.4.2 installed as `evindor.keystroke`
  (disabled), with real state to migrate. It is the migration test host.
  p620 has none.
- **nixarchy:** nothing yet. #3 wires the plugin in under the new id.

## Constraints

- **Never lose or rewrite user data in place:**
  - Copy old paths to new ones once, only when the new path is absent.
  - A failed copy leaves the old data untouched and says so.
- **Don't fight another menu:** two enabled plugins cloned from
  `omarchy.menu` must not fight over the menu. The new plugin must not
  silently leave `evindor.keystroke` enabled beside it.
- **Keep the vendored matching engine binary name** (`keystroke-matching`)
  and its CI attestation unchanged until #3 replaces it with a Nix build.
  Renaming it now forces a container rebuild that #3 throws away.
- **Leave `codex/` alone** apart from strings and paths. #4 deletes it.
- **No behaviour change beyond names, paths and migration:**
  - The QML suite stays at 265/265.
  - No new qmllint warnings.

## Open questions

1. **What happens to an enabled `evindor.keystroke`?**
   Proposed: on first start, if `evindor.keystroke` is enabled, disable it
   through the shell's `setPluginEnabled` and tell the user once. Never
   remove its files.
2. **Should the file and CLI names change too?** (`Keystroke.qml` →
   `NixarchyMenu.qml`, `bin/keystroke` → `bin/nixarchy-menu`)
   Proposed: yes for both. They show in `omarchy-plugin-list`, the
   manifest's entry points and the docs.
3. **Where does "Learn nixarchy-menu" point?** The upstream usage guide was
   deleted with `site/` in #2.
   Proposed: point it at the repo's README on GitHub. Nixi's `learn` action
   is the longer-term home once #5 lands.
4. **What happens to the stale `io.github.evindor.keystroke-timer` key in
   `keystroke.example.json`?** Extensions are keyed by folder name
   (`timer`).
   Proposed: rename it to `timer` in the renamed example file.
