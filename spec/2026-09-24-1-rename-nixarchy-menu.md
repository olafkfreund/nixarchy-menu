---
status: draft
issue: 1
intent: intent/2026-09-24-1-rename-nixarchy-menu.md
---

# Spec: Rename Keystroke to nixarchy-menu and migrate user state

## Design

There are 469 lines mentioning "keystroke" in 92 files. They split into
things we rename, things we keep, and one-time migration of what users
already have. **No blind search-and-replace:** about 30 sites use
"keystroke" to mean a key press (for example `core/Match.js:64,217`,
`Keystroke.qml:168,752`, and the `tests/tst_match.qml:125-138` timing test).

### 1. Identity

| What | Now | New |
|---|---|---|
| `manifest.json` id | `evindor.keystroke` | `nixarchy.menu`. It is valid: `omarchy-plugin-validate` accepts `^[A-Za-z0-9][A-Za-z0-9._-]*$`, only `omarchy.` is reserved, and `nixarchy.` is already the house prefix for nixarchy's plugins. |
| name, barWidget displayName | Keystroke | nixarchy-menu |
| author, homepage, description | upstream | olafkfreund, github.com/olafkfreund/nixarchy-menu, nixarchy wording. Upstream credit moves to the README and `LICENSE`, which stays as is. |
| entry file | `Keystroke.qml` | `NixarchyMenu.qml`. The QML type name follows the file name, so the 26 `Keystroke {` references in 13 palette checks become `NixarchyMenu {`. |
| `BarWidget.qml:19` moduleName | `evindor.keystroke` | `nixarchy.menu`. It must equal the id, because `:24` looks up `shell.panelLoaders[moduleName]`. The same applies to the fake at `tests/palette_extensions_check.py:93`. |
| CLI | `bin/keystroke` | `bin/nixarchy-menu`. About 27 callers in docs, the PR template and extension READMEs. Its stage dir becomes `.nixarchy-menu.XXXXXX`. |
| example config | `keystroke.example.json` | `nixarchy-menu.example.json`. The `io.github.evindor.keystroke-timer` key becomes `timer` (extensions are keyed by folder), and `example.keystroke-hello` becomes `example.hello`. |
| `.github/CODEOWNERS` | `* @evindor` | `* @olafkfreund`. The intent did not cover this; without the change, every review request would go to upstream's author. |

### 2. Strings and links

- **User-visible proper noun "Keystroke" becomes "nixarchy-menu"** in about 40
  code sites:
  - `ROOT_TITLE` and the "Keystroke" section in `core/SettingsTree.js`
  - footer fallback `:1607`, Accessible.name `:1258` and the disabled-provider
    message `:245`
  - the dictation notify title `:323`
  - `providers/SettingsProvider.qml:18` and `providers/CommandsProvider.qml:31`
  - the extension screen texts in `core/Extensions.js` and `providers/Extensions.qml`
  - the "Needs Keystroke provider API 1" message. `apiVersion: 1` itself is unchanged.
  - the Smart Match retry messages
  - the timer setting description
  - the codex/ user-facing strings

  About 25 test assertions follow the rename.
- **Links:**
  - "Learn nixarchy-menu" (`GUIDE_URL`) becomes `https://github.com/olafkfreund/nixarchy-menu#readme`.
  - `core/Extensions.js` SOURCE_URL and GUIDE_URL point at the fork.
  - `docs/engine-provenance.md` attestation `--repo` and `--signer-workflow` point at `olafkfreund/nixarchy-menu`, where `engine.yml` now attests.
- **Internal identifiers that are renamed**, so the journal and `ps` read
  correctly:
  - `console.warn` prefixes
  - argv[0] labels: `keystroke-extensions-scan`, `-setup`, `-currency`, `-timer-sound`, `-translate`, voice
  - `$XDG_RUNTIME_DIR/keystroke-voice.txt`
  - test temp-dir prefixes
  - the `KEYSTROKE_*` test env vars become `NIXARCHY_MENU_*`
- **Kept, with the reason:**
  - The Smart Match engine (`matching/bin/keystroke-matching`, `matching/engine/**`,
    `build-prebuilt.sh`, `engine.yml` job and artefact names, the
    `helpers/matching-start.py` User-Agent and binary name). Editing `Cargo.toml` or
    `main.rs` changes the engine fingerprint, and `tests/matching_engine_check.py`
    then fails the shipped binary. #3 replaces all of it.
  - `matching/descriptions.json` and `description-keys.json` ("Keystroke
    launcher"), which are keyed by hash.
  - codex/ internals (`keystroke-codex`, `serviceName`, clientInfo). #4 deletes codex/.
  - `~/.local/share/keystroke/voxtype`, which detects a leftover *upstream*
    install on purpose (`voice/VoiceSession.qml:52`).
  - Other people's repos and credits in `extension.json` and READMEs.
  - The `LICENSE` copyright line.
  - `docs/codex-integration-*.md`, which are historical records.
  - Arbitrary fixture data such as "Keystroke Test App".
- **Comments:** the proper noun is renamed; "keystroke" meaning a key press
  is not touched.

### 3. State migration

New paths are derived **exactly as each reader derives them today**. The
XDG handling differs per reader, and unifying it would be a behaviour change.

| Old | New | Reader |
|---|---|---|
| `~/.config/omarchy/keystroke.json` | `~/.config/omarchy/nixarchy-menu.json` | `NixarchyMenu.qml` configPath (`$HOME`) |
| `~/.local/state/keystroke/` | `~/.local/state/nixarchy-menu/` | usage.json, codex.json, `questions/`, `currency/` (`$HOME`; currency uses `$XDG_STATE_HOME`) |
| `$XDG_CACHE_HOME/keystroke/` | `…/nixarchy-menu/` | currency rates (`$XDG_CACHE_HOME` or `~/.cache`) |
| `~/.local/share/keystroke/extensions/` | `~/.local/share/nixarchy-menu/extensions/` | `core/Extensions.js:28` (`$HOME`) |
| `$XDG_DATA_HOME/keystroke/matching/models/` | `…/nixarchy-menu/matching/models/` | `helpers/matching-start.py:189` (`$XDG_DATA_HOME`) |

**Not copied:**
- `matching/runtime` (a uv venv with absolute paths in shebangs and `pyvenv.cfg`; it is rebuilt)
- `matching/engine` (rebuilt when needed)
- `install.lock`
- `share/keystroke/voxtype`

**Mechanism.** One script, `helpers/migrate-state.sh`, runs from one `Process`
in `NixarchyMenu.qml` at load. It has a function `m OLD NEW`:
- It does nothing if NEW exists or OLD is absent.
- Otherwise it runs `cp -a OLD NEW.migrating.$$ && mv -T NEW.migrating.$$ NEW`,
  so the copy lands in a sibling and is then renamed atomically.
- On failure it removes the temp copy and prints OLD on stderr.
- The old path is never touched.

After the copies, it runs `mkdir -p` on the new state dir. **That mkdir moves
out of `Keystroke.qml:403`.** If it ran first, it would create the new dir
empty, and the migration would skip the user's state.

**Ordering.** Everything waits on `property bool stateReady`, which is set in
`onExited` whatever the exit code:
- The FileViews that load at creation get `path: stateReady ? realPath : ""`:
  `configFile :259`, `usageFile :396`, and codex `historyFile`. A FileView
  with an empty path does not load.
- `providerRegistry.scan()` runs from `onExited`.
- `matchingSession.enabled` includes `stateReady`, so a very fast first query
  cannot create an empty `matching/` and trigger a 7.9 MB re-download.
- Nothing blocks. It is one short Process at shell start.

**Failure.** Each failed copy is reported once with
`$OMARCHY_PATH/bin/omarchy-notification-send`, as `Keystroke.qml:1174` already
does. The notice names the path and says the old data is untouched. The
palette is closed at shell start, so `statusMessage` would never be seen.

### 4. Voice bind markers

- `core/VoiceBindings.js` gets new markers:
  `-- >>> nixarchy-menu voice: hold the palette hotkey to dictate (written by nixarchy-menu Settings › Voice)`
  and `-- <<< nixarchy-menu voice`.
- The current pair stays as `LEGACY_BEGIN`/`LEGACY_END`. `find()` tries the
  new pair first, then the legacy pair.
- A legacy block reads as **outdated**, so Settings offers **Update**. After
  that, `apply()` and `remove()` replace the block in place under the new
  markers, with no duplicate.
- Nothing edits `bindings.lua` or runs `hyprctl reload` without the user
  choosing Update.
- The old block keeps working meanwhile, because it calls `omarchy.menu`,
  which routes to the enabled clone.

### 5. An enabled `evindor.keystroke` — ⚠️ differs from the approved intent

The intent's answer to open question 1 was that the plugin disables
`evindor.keystroke` itself on first start. **Research shows that is not
possible and not safe from inside the plugin:**
- A third-party plugin only gets a scoped `shell` (`PluginShellApi`) and a
  read-only, self-only `pluginRegistry`. It has no `setEnabled`. Disabling
  needs IPC (`omarchy-shell shell setPluginEnabled`, `shell.qml:1625-1627`).
- While both clones are enabled, the old one wins every `omarchy.menu` call
  silently (`PluginRegistry.qml:171-182`, alphabetical folder order).
- **Disabling the old one while the new one is enabled goes wrong** (`PluginRegistry.qml:449-470, 548-551`):
  - It converts the old bar entry back into a stock `omarchy.menu` button.
  - It re-enables the stock menu, because the old plugin holds the restore
    flag, and the new plugin never got one.
- **Disabling it first and then enabling `nixarchy.menu`** is clean: the new
  plugin takes over the same bar slot, disables the stock menu and records
  its own restore flag.

**So the swap happens where it can be done in the right order:**
- **`bin/nixarchy-menu install`:** if `omarchy-plugin-list --json` shows
  `evindor.keystroke` enabled, it runs `omarchy plugin disable
  evindor.keystroke` **before** `omarchy plugin enable nixarchy.menu`. It
  never removes the old files.
- **#3 (Nix wiring)** does the same in its enable-once hook.
- **At runtime,** `helpers/migrate-state.sh` also runs
  `omarchy-shell shell listPlugins`. If `evindor.keystroke` is still enabled,
  it sends one notice: "Keystroke is still enabled and keeps the menu. Run:
  `omarchy plugin disable evindor.keystroke`". **It only notifies; it does
  not change the shell config.**

### 6. Docs

- **README** is rewritten short and nixarchy-first:
  1. What it is
  2. Enable on nixarchy: `bin/nixarchy-menu install` for now; declarative
     wiring comes in #3. It includes the "coming from Keystroke" note.
  3. Bar button
  4. Keys and what you can type (kept)
  5. Providers (link to `docs/providers.md`)
  6. Smart Match (kept)
  7. Voice (needs the voxtype daemon, olafkfreund/nixarchy#942; kept)
  8. Extensions
  9. Settings file
  10. Develop and test, with the `nix shell … qmltestrunner` command
  11. Credits and license: a fork of evindor/keystroke by Arseniy Zarechnev, MIT

  It fixes the empty `## Voice` heading that sits above `## Smart Match`,
  where the Voice text currently lives.
- **Other docs:**
  - `CONTRIBUTING.md`, `docs/architecture.md`, `docs/providers.md`,
    `matching/README.md` and the extension READMEs: the proper noun, the
    paths, and `bin/nixarchy-menu`.
  - `.github/PULL_REQUEST_TEMPLATE.md`: `bin/nixarchy-menu`.

## Alternatives rejected

- **Keep the id `evindor.keystroke`, rename only the display.** The id is
  what nixarchy wires, what `shell.json` names, and what users see in
  `omarchy plugin list`. The user decided on `nixarchy.menu`.
- **Move instead of copy.** A failed or partial move loses data, and going
  back to Keystroke would find nothing.
- **`cp -an` alone.** An interrupted directory copy leaves a partial new
  path, and every later run then skips it.
- **The plugin disables the old plugin itself** (the intent's original
  answer). It is impossible from plugin scope, and wrong in that order (§5).
- **Rewrite the voice block automatically.** That edits `bindings.lua` and
  reloads Hyprland without asking.
- **Rename the matching engine now.** It forces a container rebuild and a new
  attestation that #3 throws away.
- **One script to rename everything.** It corrupts "keystroke" where it
  means a key press, and breaks hash-keyed data.

## Risks

- **A user keeps `evindor.keystroke` enabled and ignores the notice.** The old
  menu keeps winning, which is the same as today. The notice and the README
  say how to fix it.
- **A migration copy fails** (for example, disk full). The user is notified
  with the path. The old data is untouched and the new path is absent, so the
  next start retries.
- **`XDG_DATA_HOME` is set.** The extensions and matching directories are
  derived differently, as they are today. The migration mirrors each reader.
  A test covers it.
- **A user with a custom `~/.local/share/keystroke/extensions` symlink**
  (developers). `cp -a` copies the link itself, so it still points at their
  checkout.
- **razer has no enabled `evindor.keystroke` and no voice block,** so the
  coexistence and legacy-marker paths are proven by tests and a fixture, not
  by razer's live state.

## Verification

1. **QML suite**, from `tests/`, using the `nix shell` qmltestrunner command:
   **all pass**, 265 plus the new voice-marker cases:
   - a legacy block reads as outdated
   - `apply` leaves exactly one block under the new markers
   - `remove` works on a legacy block
2. **qmllint:** no warning beyond the 484-line baseline.
3. **`tests/migrate_state_check.py`**, new. It is pure Python plus sh and needs
   no quickshell, so it runs on NixOS now. Against a temp `$HOME`:
   - It copies each pair and skips runtime, engine and voxtype.
   - The old files are unchanged.
   - It does not overwrite an existing new path.
   - A failed copy leaves no partial new path.
   - It honours `XDG_DATA_HOME`, `XDG_STATE_HOME` and `XDG_CACHE_HOME` per
     reader.
   - The `listPlugins` fixture with `evindor.keystroke` enabled produces one
     notice line.
4. **Leftover references:**
   `rg -n -i 'evindor\.keystroke|Keystroke Settings|Learn Keystroke|bin/keystroke|keystroke\.json|share/keystroke/extensions|state/keystroke'`
   Expected hits, and nothing else:
   - the migration script and its test (old paths on purpose)
   - `VoiceBindings.js` legacy markers
   - the voxtype legacy path
   - the README "coming from Keystroke" note
   - `docs/codex-integration-*`
5. **Engine untouched:** `git diff main -- matching/engine matching/bin matching/descriptions.json matching/description-keys.json` is empty.
6. **Razer**, which has real Keystroke 1.4.2 state (`keystroke.json` with
   `providers.ai.provider=claude`, `usage.json`, and the 7.9 MB model), after
   `bin/nixarchy-menu install` and a shell restart:
   - `~/.config/omarchy/nixarchy-menu.json` has `providers.ai.provider=claude`.
   - Frecency is preserved.
   - `share/nixarchy-menu/matching/models/small` exists with no re-download,
     and Smart Match is Ready.
   - The old paths are byte-identical.
   - `omarchy-plugin-list` shows `nixarchy.menu` enabled, and `omarchy.menu`
     and `evindor.keystroke` disabled.
   - The bar button is in the stock menu's slot.
   - Settings says "nixarchy-menu Settings".
   - Voice still works.

   Afterwards, restore razer from a fresh backup.
