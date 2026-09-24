---
status: approved
issue: 1
spec: spec/2026-09-24-1-rename-nixarchy-menu.md
---

# Plan: Rename Keystroke to nixarchy-menu and migrate user state

## Approved decisions (carried over from the spec)

- **Identity:**
  - Id `nixarchy.menu`, name `nixarchy-menu`, author olafkfreund, homepage
    github.com/olafkfreund/nixarchy-menu.
  - `Keystroke.qml` → `NixarchyMenu.qml`, so the QML type is `NixarchyMenu`.
  - `bin/keystroke` → `bin/nixarchy-menu`.
  - `keystroke.example.json` → `nixarchy-menu.example.json`, with the timer
    key `timer` and `example.hello`.
  - CODEOWNERS `@olafkfreund`.
  - `BarWidget.qml` moduleName must equal the id.
- **Strings:**
  - The user-visible proper noun "Keystroke" becomes "nixarchy-menu".
  - "keystroke" meaning a key press is **never** touched. **No blind sed.**
  - GUIDE_URL → `https://github.com/olafkfreund/nixarchy-menu#readme`.
  - Extension and attestation links point at the fork.
  - Internal log prefixes, argv labels, the voice runtime file, test
    temp-dir prefixes and `KEYSTROKE_*` env vars are renamed to the
    nixarchy-menu form.
- **Kept byte-identical** (#3 or #4 replaces them): `matching/engine/**`,
  `matching/bin/**`, `matching/descriptions.json`,
  `matching/description-keys.json`, `build-prebuilt.sh`, `engine.yml`, and the
  `keystroke-matching` binary name and User-Agent in `helpers/matching-start.py`.
- **Kept, with no rename:**
  - codex/ internals (argv, serviceName, clientInfo). Codex user strings and
    state paths **are** renamed.
  - The upstream voxtype detection path `~/.local/share/keystroke/voxtype`.
  - Credits of other people's repos, `LICENSE`, `docs/codex-integration-*.md`,
    and fixture data.
- **Migration:**
  - `helpers/migrate-state.sh` copies these pairs, each with its reader's XDG
    rule, and never overwrites or touches the old path:
    - config `keystroke.json` → `nixarchy-menu.json`
    - state dir
    - cache dir
    - `share/…/extensions`
    - `share/…/matching/models` only
  - Each copy goes to `NEW.migrating.$$` and is moved into place with `mv -T`.
  - After the copies, the script runs `mkdir -p` on the new state dir. The
    mkdir at `Keystroke.qml:403` is removed.
  - One `Process` runs the script at load. In `onExited`,
    `stateReady = true`, then `providerRegistry.scan()`.
  - While `stateReady` is false, `configFile`, `usageFile` and codex
    `historyFile` have an empty path, and matching is disabled.
  - Each failed copy sends one `omarchy-notification-send` notice.
- **Voice markers:** new BEGIN/END, with the old pair kept as legacy. A legacy
  block reads as outdated, and Update rewrites it in place. Nothing is
  rewritten automatically.
- **Old plugin:**
  - `bin/nixarchy-menu install` disables an enabled `evindor.keystroke`
    **before** enabling `nixarchy.menu`, and never removes its files.
  - At runtime, the script only notifies when
    `omarchy-shell shell listPlugins` shows `evindor.keystroke` enabled.
- **README** is rewritten short and nixarchy-first (11 sections, see the
  spec), fixing the misplaced `## Voice` heading.

## Team split

Three teammates edit disjoint files in the same working tree. None of them
commits. The lead reviews, tests and commits once per team, in the order
F → G → H.

Until G lands, palette checks still name `Keystroke.qml`. They cannot run on
NixOS before #3 anyway.

### F: `app` (entry file, identity, migration)

Owns `Keystroke.qml`→`NixarchyMenu.qml`, `manifest.json`, `BarWidget.qml`,
`helpers/migrate-state.sh` (new) and `tests/migrate_state_check.py` (new).

1. `git mv Keystroke.qml NixarchyMenu.qml`. Update `manifest.json`: id, name,
   author, description, homepage, `entryPoints.menu`, and the barWidget
   displayName and description.
2. `BarWidget.qml`: set `moduleName: "nixarchy.menu"`, rename the internal
   `keystroke` property to `menu`, and rename the proper noun in comments.
3. Edit `NixarchyMenu.qml`:
   - **Paths:** `configPath` → `nixarchy-menu.json`, `usagePath` →
     `state/nixarchy-menu`.
   - **Remove** the `stateDir` mkdir Process (:403).
   - **Add** the migrate `Process`, `stateReady`, and the gated FileView
     paths. Gate the codex `historyFile` through a `host.stateReady` property
     that codex reads. Owner G adds the one-line codex binding.
   - **Gate matching** with `stateReady`.
   - **Strings** (:245, :323, :1258, :1607), **log prefixes**, and **comments**
     that use the proper noun.
4. `helpers/migrate-state.sh`:
   - the `m OLD NEW` function, with XDG handling per reader
   - `mkdir -p` of the new state dir
   - the `listPlugins` check, and one notice through
     `${OMARCHY_PATH}/bin/omarchy-notification-send`, falling back to `notify-send`
   - failures printed on stderr, exit 1 if any copy failed
   - `POSIX sh`, no bashisms
5. `tests/migrate_state_check.py`: temp `$HOME`, the spec's verification #3
   cases, and a stub `omarchy-shell` on `PATH` for the `listPlugins` fixture.

→ **Verify:**
- `python3 tests/migrate_state_check.py` passes.
- `sh -n helpers/migrate-state.sh` is clean.
- `rg -n 'keystroke' NixarchyMenu.qml manifest.json BarWidget.qml` shows only
  the key-press sense.

### G: `strings` (code, tests and extensions)

Owns `core/`, `providers/`, `voice/`, `ui/`, `matching/Session.qml`,
`helpers/matching-start.py` (the data-dir default and messages only),
`helpers/codex-start.sh`, `codex/`, `extensions/**` (code, extension.json,
tests, READMEs), and `tests/` (everything except `migrate_state_check.py`).

1. `core/SettingsTree.js`: ROOT_TITLE, section names, "Learn nixarchy-menu",
   GUIDE_URL and descriptions.
   `core/Extensions.js`: SOURCE_URL and GUIDE_URL → the fork, the local dir →
   `.local/share/nixarchy-menu/extensions`, texts, argv labels.
   `providers/*.qml`: user strings and the "provider API 1" message.
2. `core/VoiceBindings.js`:
   - new markers, legacy pair kept, `find()` new then legacy
   - `tests/tst_voicebindings.qml`: update :13, :18, :38 and :43
   - add a legacy case: outdated → `apply` gives one new block → `remove` works
3. `voice/VoiceSession.qml`:
   - rename the argv label and the `keystroke-voice.txt` file
   - **keep** the legacy `share/keystroke/voxtype` detection path
4. Smart Match:
   - `matching/Session.qml`: messages and the log prefix, plus `enabled`
     honouring `host.stateReady`.
   - `helpers/matching-start.py`: the `--data-dir` default becomes
     `$XDG_DATA_HOME/nixarchy-menu/matching`, and messages are renamed.
   - **Do not touch** `matching/engine`, `matching/bin`, the descriptions
     files, the `keystroke-matching` name or the User-Agent.
5. Codex:
   - `codex/CodexSession.qml`, `codex/Policy.js`, `helpers/codex-start.sh`:
     state paths → `state/nixarchy-menu`, and user-facing strings.
   - `historyFile.path` is gated on `host.stateReady`.
   - Internals are kept.
6. `extensions/**`:
   - currency: `stateDir` and `cacheDir` → `nixarchy-menu`, argv label
   - timer and translate: argv labels
   - setting and description strings
   - READMEs: the proper noun and `bin/nixarchy-menu`
   - keep the upstream and third-party credits
7. `tests/**` and `extensions/*/tests/**`:
   - palette checks copy `NixarchyMenu.qml` and instantiate `NixarchyMenu {`
     (26 references)
   - config path `.config/omarchy/nixarchy-menu.json`
   - the `panelLoaders` key `nixarchy.menu`
   - string assertions (`tst_settingstree`, `tst_extensions`,
     `palette_route_check:42`, `tst_currency`)
   - `tst_match` fixture paths **with** the query at :37
   - temp prefixes and `KEYSTROKE_*` env vars renamed
   - fixture data kept

→ **Verify:**
- The QML suite passes with the new voice cases.
- `git diff main -- matching/engine matching/bin matching/descriptions.json matching/description-keys.json` is empty.

### H: `docs` (tooling and docs)

Owns `bin/keystroke`→`bin/nixarchy-menu`, `keystroke.example.json`→
`nixarchy-menu.example.json`, `README.md`, `CONTRIBUTING.md`, `docs/*.md`
(except `codex-integration-*`), `matching/README.md`, `.github/CODEOWNERS`
and `.github/PULL_REQUEST_TEMPLATE.md`.

1. `git mv bin/keystroke bin/nixarchy-menu`:
   - Rename the usage text, messages and stage dir.
   - In `install`: if `omarchy-plugin-list --json` shows `evindor.keystroke`
     enabled, run `omarchy plugin disable evindor.keystroke` **before**
     `omarchy plugin enable "$ID"`, and never remove it.
   - Update the test runner line for `tests/migrate_state_check.py`.
2. `git mv keystroke.example.json nixarchy-menu.example.json`. Set the timer
   key to `timer` and `example.hello`, and keep the result valid JSON.
3. Rewrite the README to the 11-section outline in the spec. Keep "What it
   does", Smart Match, Voice (under its own heading, with the
   olafkfreund/nixarchy#942 note), Extensions and Settings nearly verbatim,
   with names and paths updated. Credits: a fork of evindor/keystroke by
   Arseniy Zarechnev, MIT.
4. `CONTRIBUTING.md`, `docs/architecture.md`, `docs/providers.md`,
   `matching/README.md`: the proper noun, paths and `bin/nixarchy-menu`.
   `docs/engine-provenance.md`: attestation `--repo` and `--signer-workflow`
   → `olafkfreund/nixarchy-menu`, and the binary name is kept. CODEOWNERS →
   `* @olafkfreund`. The PR template gets `bin/nixarchy-menu`.

→ **Verify:**
- `bash -n bin/nixarchy-menu` succeeds, and `jq . nixarchy-menu.example.json` succeeds.
- Every local markdown link resolves.

### I: `lead` (integrate and verify)

1. Run **Tests**. Send failures back to the owning teammate.
2. Make three commits (F, G, H) with plan deviations recorded in the same
   commit.
3. Run the razer check (Tests, step 5).
4. Open a PR that links the intent, spec and plan, then merge it when the
   user says so.

## Tests

1. **QML:** `cd tests && nix shell nixpkgs#qt6.qtdeclarative nixpkgs#qt6.qtbase -c env QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software qmltestrunner -silent -input .`
   → 0 failed, more than 265 total.
2. **Migration:** `python3 tests/migrate_state_check.py` → pass.
3. **qmllint:** the scratchpad loop against `NixarchyMenu.qml` and the rest →
   no warning beyond the 484-line baseline, with line numbers normalised.
4. **Leftover references:** the spec's verification #4 `rg`, with only the
   listed expected hits. Also `rg -n -w 'Keystroke'` → only
   credits/history/legacy.
5. **razer** (never p620), after a fresh backup of the `evindor.keystroke`
   dir, `shell.json`, `keystroke.json` and state:
   - `rsync` the tree to `~/dev/nixarchy-menu-test`.
   - Run `bin/nixarchy-menu install`, then restart the shell.
   - Check with inspect and the files:
     - `nixarchy-menu.json` has `providers.ai.provider=claude`.
     - `share/nixarchy-menu/matching/models/small` exists, and Smart Match
       is Ready with no re-download.
     - The old paths are unchanged (`diff -r` against the backup).
     - `nixarchy.menu` is enabled; `omarchy.menu` and `evindor.keystroke`
       are disabled.
     - The Settings root is "nixarchy-menu Settings".
     - "27 plus 90" gives 117.
   - Coexistence check: enable `evindor.keystroke` on razer, re-run
     `install`, and confirm it ends up disabled with the menu button in the
     stock slot.
   - Restore razer afterwards: remove `plugins/nixarchy.menu` and the new
     state paths, restore the backup, restart the shell.

## Rollback

- Each team commit reverts on its own.
- Users' old data is never modified, so going back to `evindor.keystroke`
  (`omarchy plugin enable evindor.keystroke` after disabling
  `nixarchy.menu`) finds everything as it was.

## Deviations during implementation

### F: app
- The migrate Process path is `helpers/migrate-state.sh`, not `../helpers`. The entry file sits at the repo root, as with the existing `matching/descriptions.json` load.
- `matchingSession` is created in `NixarchyMenu.qml`, so F gated it there (`enabled: root.stateReady && …`). `matching/Session.qml` has no `host` and needs no gate of its own.
- F once ran the real script against p620's `$HOME` by mistake. There was no Keystroke data, so it only created an empty `~/.local/state/nixarchy-menu`, which F removed. The lead confirmed no new paths remain on p620.

### G: strings
- The fuzzy-abbreviation fixtures depended on the old "Keystroke Settings" breadcrumb, so `keysepro` became `nixsepro` and `kspa` became `nmspa` (tests and comments). The `tst_match` query at :37 is now `nixarchy`.
- `codex_session_check.py` passes a host stub with `stateReady: true`, so the gated history path is still exercised.
- `rg` treats `tests/tst_extensions.qml` as binary and silently skips it. It was edited by hand, and the lead's reference search uses `rg -a`.
- `extensions/browser-search/extension.json` keeps `"author": "Keystroke contributors"` as upstream credit.
- QML: 266 passed, 0 failed. That is 265 plus the legacy voice-block case.
