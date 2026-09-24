---
status: approved
issue: 4
spec: spec/2026-09-24-4-agent-handoff.md
---

# Plan: Hand off to every nixarchy agent; delete the Codex-only client

## Approved decisions (carried over from the spec)

- **Delete** `codex/`, `providers/Codex.qml`, `helpers/codex-start.sh`, the
  three Codex tests and the two `docs/codex-integration-*.md`. Keep the
  generic provider-view plumbing. Leave the `.codex` ignore patterns and
  Omarchy's `setup.default.agent.codex` data alone. Leave the users' orphaned
  `codex.json` and `questions/` untouched.
- **`palette_dictation_check`'s back-navigation test** is repointed from the
  Codex view to Translate's view.
- **Provider `ai`** is renamed "Agents & Web Search". It loses its `provider`,
  `mode` and `autoSend` settings; old values are preserved and ignored.
- **`core/AiTargets.js`:**
  - `AGENTS`: id → `{name, bin, promptless}` for every id `omarchy-agent`
    launches. antigravity is `agy` and promptless.
  - `clip()`: 2,000 characters, pads a leading `/` or `-`, empty stays empty.
  - `agentRow()`: no agent → navigate `omarchy/setup.default.agent`; unknown
    → no action; not installed → navigate to the picker, no launch;
    installed → `exec ["omarchy-agent-prompt", clip(text)]` plus the confirm
    fields; promptless → `exec ["omarchy-agent"]`.
  - `nixiRow()`: `exec ["nixi","--ask",clip(text)]`.
  - `googleUrl()`.
- **`providers/AiWeb.qml`:**
  - FileView with `watchChanges` on `~/.config/omarchy/defaults/agent`.
  - One `command -v <bin>` Process, re-run on an agent change or a
    desktop-entries change.
  - `nixarchy-plugin --enabled io.github.olafkfreund.nixi` plus
    `command -v nixi`, in `opened()`.
  - Rows are in the "Continue with" section, tier `fallback`: Ask Nixi 3.5,
    Ask \<agent\> 3, Search Google 2.
  - A leading `?` is stripped and raises only Ask Nixi to tier `answer`.
- **Every "Ask \<agent\>" asks for confirmation:**
  - `confirm` "Ask \<Name\>?"
  - `confirmDetail` is the text plus "\<Name\> starts with automatic approval
    and can run commands without asking."
  - `confirmText` "Open \<Name\>"
- **nixi-nixarchy#37 comes first**, with its own gates in the Nixi repo. If
  it is not merged when #4 is ready, Ask Nixi uses `nixi` plus a `wl-copy` of
  the text and a notice; switching to `--ask` becomes a follow-up.
- **`tests/tst_ai.qml`** is rewritten per spec §5, keeping the
  literal-argv injection test.

## Order

1. **nixi-nixarchy#37**: intent → spec → plan → PR in the Nixi repo, in a
   git worktree, because another session works there. Merge it first.
2. **This plan**, steps P and Q in parallel, then R.

## Team split (disjoint files; no teammate commits)

### P: `remove-codex`

Owns the deletions listed above and:
- `providers/Registry.qml`
- `NixarchyMenu.qml` (only `inspectConversation`)
- `flake.nix`, `bin/nixarchy-menu`, `manifest.json`,
  `nixarchy-menu.example.json`
- `CONTRIBUTING.md`, `docs/architecture.md`
- `tests/palette_dictation_check.py`

1. `git rm` the Codex files. Edit Registry (:40, :45), `NixarchyMenu.qml`
   (:1203-1206), `flake.nix` (:2, :98, :109, :281), `bin/nixarchy-menu`
   (:97), the manifest description and the example `codex` block.
2. Repoint `palette_dictation_check` (:138-146) at Translate's view, enabling
   the translate extension in that harness's config. Keep the three back-
   navigation assertions.
3. Docs: `CONTRIBUTING.md:20`, and `docs/architecture.md` `## Codex` plus its
   mentions.

→ **Verify:**
- `rg -a -n -i codex -g '!intent/**' -g '!spec/**' -g '!plan/**'` leaves only
  the ignore patterns and `matching/`.
- `palette_dictation_check` passes locally (in `nix develop`, with
  `OMARCHY_PATH` set).
- The QML suite passes.

### Q: `handoff`

Owns `core/AiTargets.js`, `providers/AiWeb.qml`, `tests/tst_ai.qml`,
`README.md`, and the "Preferred assistant" fixtures in `tests/tst_match.qml`
and `tests/tst_settingstree.qml`.

1. Rewrite `AiTargets.js` and `AiWeb.qml` per the decisions above. For the
   agent names and binaries, read `$OMARCHY_PATH/bin/omarchy-agent`; never
   guess them.
2. Rewrite `tst_ai.qml` per spec §5. Update the fixtures that name
   "Preferred assistant", for consistency.
3. README:
   - Replace the hand-off bullet with Ask \<default agent\>, Ask Nixi and `?`.
   - Delete the **Codex** paragraph and the provider-list mention.
   - Replace the fuzzy examples `setaiprv` and `prefcla` with working ones.
   - Add a note that `codex.json` and `questions/` can be deleted.

→ **Verify:**
- The QML suite passes, and `tst_ai` covers every spec §5 case.
- qmllint shows no new warnings for `AiWeb.qml`.

### R: `lead`

1. **Checks:** `nix flake check`, plus a forced
   `nix build --rebuild -L .#checks.x86_64-linux.quickshell`, passing.
2. **Commits:** P, Q, each with its deviations in this file.
3. **Razer**, after announcing on the agent bus and syncing the checkout:
   - `bin/nixarchy-menu install`, then a shell restart.
   - With the default agent set to claude, then opencode, then unset:
     - The Ask row appears.
     - The confirm sheet names the agent and warns.
     - Confirming opens the agent in a terminal with the exact text,
       including quotes and a newline.
     - With none set, the row opens the picker.
     - With an uninstalled agent, nothing launches.
     - Ask Nixi appears only when Nixi is enabled, and with #37 merged it
       asks the question.
     - `?` puts Ask Nixi first.
   - Restore razer's default agent afterwards.
4. **Codex review:** `codex review --base main`, read-only. Verify each
   finding.
5. **PR:** open it, and merge when CI is green and the user agrees.

## Tests

1. `nix flake check`, plus a `--rebuild` of `quickshell`.
2. `tst_ai`: all spec §5 cases.
3. The `rg` sweep for codex.
4. The razer checks in step R3.
5. Nixi #37's own `tools/test_nixi.py`.

## Rollback

- Revert the P and Q commits. The Codex client comes back from history.
  Users' `codex.json` history was never deleted.
- Razer: reinstall the previous `nixarchy.menu` build.

## Deviations during implementation

### nixi#37 landed, but nixarchy still pins an older nixi
- nixi-nixarchy#43 merged (`4e6c1b5`), but nixarchy pins `nixi` at `1e25cb8`, so no machine has `nixi --ask` yet. The pin bump is nixarchy#956.
- **Change to the plan:** Ask Nixi probes support once per palette open with `nixi --nixarchy-menu-probe 2>&1 | grep -- --ask`. An unknown flag prints nixi's usage line, which lists `--ask` only on new builds.
- Without `--ask`, the row uses the spec §4 fallback, built from the host's existing `compound` effect, so there is no shell: `copy` the text, then `exec ["nixi"]`, then a "Question copied" `notify`.

### P: remove-codex
- **`palette_dictation_check`:** it moved to Translate's view, and the harness enables the `translate` extension. Stage 2 also waits for the translate service to load, because extensions load asynchronously.
- **Extras:** P also cleaned `docs/providers.md:147` (a reference to the deleted Codex files) and removed the ignored `provider`/`mode`/`autoSend` settings from the example config's `ai` block.

### Q: handoff
- **Installed check mirrors `omarchy-agent`'s gate.** It requires the id **and** the binary on PATH (`commandsFor` / `isInstalled`, nixarchy#949). `omarchy-agent` refuses an agent whose id isn't a command, so antigravity with only `agy` shows "not installed" instead of a launch that fails. The same applies to openclaw.
- **mise shims:** the check puts mise shims on PATH, as `omarchy-agent` does, and passes the commands as arguments.
- **Fixtures:** "Preferred assistant" no longer exists, so the `tst_match` and `tst_settingstree` fixtures and the README fuzzy examples use Settings › Files › Search in the main palette (`filmod`, `nixsefimo`, `setfilmo`, `sealit`, `fil mode`, all asserted in tests). Stale comments in `core/SettingsTree.js` and `core/Match.js` were updated.
- **Found, filed as #13:** Files' `optionLabels` never apply. Files declares an array, and SettingsTree looks labels up by name.

### Results
- `nix flake check`: all checks passed.
- Forced `--rebuild` of `quickshell`: 19/19. codex_session was deleted.
- QML: 264 passed, 0 failed.
- `git grep -i codex` leaves only the AGENTS id, the README upgrade note, the ignore patterns and `matching/`.
