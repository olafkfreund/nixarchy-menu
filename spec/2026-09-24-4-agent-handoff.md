---
status: draft
issue: 4
intent: intent/2026-09-24-4-agent-handoff.md
---

# Spec: Hand off to every nixarchy agent; delete the Codex-only client

## Design

### 1. Delete the Codex client

- **Delete:**
  - `codex/` (AppServer, CodexSession, ConversationView, Policy.js)
  - `providers/Codex.qml`, `helpers/codex-start.sh`
  - `tests/codex_session_check.py`, `tests/codex_fake_server.py`,
    `tests/tst_codexpolicy.qml`
  - `docs/codex-integration-plan.md`, `docs/codex-integration-verification.md`

  That is about 1,200 lines.
- **Edits:**
  - `providers/Registry.qml:40,45`: drop `Codex { … }` and `codex` from
    `bundled`.
  - `NixarchyMenu.qml:1203-1206`: delete `inspectConversation()`.
  - `flake.nix`: drop `codex` from the plugin copy (:109) and
    `codex_session_check.py` from the quickshell check (:281). Take "Codex"
    out of the descriptions (:2, :98).
  - `bin/nixarchy-menu:97`: drop the codex check.
  - `manifest.json`: take "Codex" out of the description.
  - `nixarchy-menu.example.json`: remove the `codex` block.
  - `CONTRIBUTING.md:20`, `README.md`, `docs/architecture.md` (`## Codex`
    and its mentions).
- **Kept:**
  - the generic provider-view plumbing (`activeProviderKey`, the Loader,
    `provider-view`, voice routing into a view). Translate and Keyboard
    Cleaner use it.
  - the `.codex` entries in the harnesses' copytree ignore lists, which are
    harmless.
- **`tests/palette_dictation_check.py:138-146`** uses the Codex view to test
  going back from a provider view. It is repointed at Translate's view,
  with the translate extension enabled in that harness's config.
- **Orphaned state:** `~/.local/state/nixarchy-menu/codex.json` and
  `questions/` are left untouched, and the README says they can be deleted.

### 2. The agent hand-off rows (`providers/AiWeb.qml`, `core/AiTargets.js`, rewritten)

The provider keeps id `ai`, so existing configs keep their `enabled`
switch, and is renamed "Agents & Web Search". Its `provider`, `mode` and
`autoSend` settings are removed; old values in user configs are preserved
and ignored.

**`core/AiTargets.js`** becomes pure data and string functions:

- `AGENTS`: id → `{ name, bin, promptless }` for every id `omarchy-agent`
  launches. Examples: claude→Claude Code/`claude`, codex→Codex/`codex`,
  opencode→OpenCode/`opencode`, gemini→Gemini CLI/`gemini`,
  copilot→GitHub Copilot/`copilot`, crush, grok, pi, omp,
  **antigravity→Antigravity/`agy`, promptless**, cursor-agent, hermes,
  muse, openclaw (`omarchy-launch-openclaw`).
- `clip(text)`:
  - trim and cut to 2,000 characters
  - pad a leading `/` or `-` with a space (`-` for crush and pi, see
    nixarchy#949)
  - empty stays empty
- `agentRow(agentId, installed, text)` returns one of:
  - **no agent set:** "Choose a default agent", navigate
    `omarchy/setup.default.agent` (the stock rows, already rendered by
    `providers/OmarchyMenu.qml`)
  - **unknown id:** "Default agent “x” is not supported here", with no
    action
  - **not installed:** "\<Name\> is not installed", navigate to the same
    picker, with no launch
  - **installed:** "Ask \<Name\>", subtitle "Opens \<Name\> in a terminal ·
    runs without asking", effect
    `{ type: "exec", argv: ["omarchy-agent-prompt", clip(text)] }`, and a
    `confirm` (below). A promptless agent opens with argv
    `["omarchy-agent"]` and the subtitle says "opens without your text".
- `nixiRow(text, stage)`: "Ask Nixi", effect
  `{ type: "exec", argv: ["nixi", "--ask", clip(text)] }` (needs
  nixi-nixarchy#37).
- `googleUrl(query)`: unchanged.

**`providers/AiWeb.qml`:**

- **Default agent:** a `FileView` on `~/.config/omarchy/defaults/agent`
  with `watchChanges`. The first line is the id. Missing or empty means
  none. No process runs per keystroke.
- **Agent installed:** one `Process` running
  `command -v <bin> >/dev/null && echo yes`, re-run when the id or the
  desktop entries change. This is the existing detect pattern, reduced to
  one binary.
- **Nixi enabled:** one `Process` running
  `nixarchy-plugin --enabled io.github.olafkfreund.nixi`, re-run in the
  provider's `opened()` hook, so once per palette open. It reads
  `shell.json` directly with no IPC. It also checks that `nixi` is on PATH.
- **Rows:** with text, outside any scope, in section "Continue with", all
  `tier: "fallback"`:
  - Ask Nixi (when enabled): score 3.5
  - Ask \<agent\>: score 3
  - Search Google: score 2

  With a leading `?`, the `?` is stripped and **only Ask Nixi** is raised
  to `tier: "answer"`. The agent row never gets tier `answer`.
- **The agent row is never activated automatically.** Rows only run on
  Enter, and dictation fills the query but does not activate.

### 3. Always confirm an agent hand-off

The palette cannot tell typed text from pasted text. Voice is detectable
(`ctx.host.voiceRawText`), but the clipboard is not. So **every** "Ask
\<agent\>" activation uses the existing confirm sheet (row fields
`confirm`, `confirmDetail`, `confirmText`; `NixarchyMenu.qml:950-952,
1138`):

- **confirm:** "Ask \<Name\>?"
- **confirmDetail:** the clipped text, then "\<Name\> starts with automatic
  approval and can run commands without asking."
- **confirmText:** "Open \<Name\>"

This is stricter than the intent's "voice or clipboard". Ask Nixi needs no
confirmation, because Nixi asks before tools run (ACP permission
requests). The Default Agent picker rows are Omarchy's own.

### 4. nixi-nixarchy#37 (done first, its own gates in the Nixi repo)

These are the Nixi repo's artifacts and PR, merged before #4's code
merges. The research estimate is about 20 lines plus tests.

- **New card:** `Ask.qml createConversation` handles
  `{"action":"ask","prompt"}` → `askQuestion`.
- **Open, idle card:** `Ask.open()` handles it on the open card →
  `askQuestion`.
- **Open card that is busy** (`waiting`): only fill the prompt through a
  new `Conversation.setPrompt(text)`. No steer, no interrupt.
- **CLI:** `bin/nixi --ask <prompt>` summons, never toggles, and JSON-
  escapes the prompt.
- **Tests:** `tools/test_nixi.py` `test_nixi_launcher` covers enabled,
  disabled and missing-argument, and a round-trip of JSON with quotes and a
  newline. The manual checklist in `docs/testing.md` gets the matching
  steps.

If #37 has not merged when #4 is otherwise ready, the Ask Nixi row falls
back to `nixi` (open the card) plus `wl-copy` of the text, with a notice.
It switches to `--ask` in a follow-up.

### 5. Tests (`tests/tst_ai.qml`, rewritten)

- `clip`:
  - bounds the text at 2,000 characters
  - pads a leading `/` and a leading `-`
  - keeps empty text empty
- `agentRow`:
  - **no agent:** a navigate row to `omarchy/setup.default.agent`
  - **not installed:** no exec effect
  - **installed:** argv is exactly `["omarchy-agent-prompt", <text>]` with
    a shell-injection payload passed **literally** (kept from today's CLI
    test), plus the confirm fields present
  - **promptless (antigravity):** argv is `["omarchy-agent"]`
  - **unknown id:** no action
- `nixiRow`: argv `["nixi","--ask",<text>]`.
- `googleUrl`: unchanged.
- The `tst_match` and `tst_settingstree` fixtures that name "Preferred
  assistant" are self-contained and are updated only for consistency.
- The README's fuzzy examples (`setaiprv`, `prefcla`) are replaced.

## Alternatives rejected

- **Generalise the Codex app-server client into an ACP client:** Nixi
  already is one (agent-chat-in-nixi).
- **Keep the claude.ai / chatgpt.com browser rows:** the user decided no.
- **A palette-owned agent picker:** Omarchy's `setup.default.agent` rows
  already exist, show ✓, and are rendered by the palette.
- **Run `omarchy-default-agent` per query to read the agent:** that is a
  process per keystroke. A watched FileView on the same file is free.
- **Confirm only when the text came from voice:** pasted text can't be
  told from typed text, and the agent auto-approves.
- **`nixarchy-ask anything` as the default target:** it frames every prompt
  as a NixOS task. Deferred to #5.

## Risks

- **Nixi does not support every default agent.** Nixi supports only claude,
  codex and opencode. With gemini or crush as the default, Ask Nixi opens
  Nixi, which reports "not supported". The row stays, because Nixi owns
  that message and it may support more later.
- **The shared `omarchy-agent` behaviour is not ours to fix here.** It
  changes to `~/Work`, and its flags follow each agent's CLI; nixarchy#949
  tracks the bugs.
- **#37 lands late:** the clipboard fallback in §4 applies.
- **Users lose the in-palette Codex history.** Their files are kept.

## Verification

1. `nix flake check` passes. `quickshell` gets a forced `--rebuild` and
   passes. `tst_ai` covers the cases in §5.
2. `rg -a -n -i 'codex' -g '!intent/**' -g '!spec/**' -g '!plan/**'`
   leaves only the copytree ignore patterns and Omarchy's own
   `setup.default.agent.codex` entries in `matching/`.
3. **Razer**, with the default agent set to claude, then opencode, then
   unset:
   - "Ask \<Name\>" appears.
   - Enter opens the confirm sheet, which names the agent and warns about
     auto-approval.
   - Confirming opens the agent in a terminal with the exact text,
     including quotes and a newline.
   - With none set, the row opens the Default Agent picker.
   - With an uninstalled agent, nothing launches.
   - With Nixi enabled, "Ask Nixi" opens Nixi with the question asked,
     after #37.
   - `? how do I …` puts Ask Nixi first.
4. **Nixi #37:** `tools/test_nixi.py` passes, plus the manual steps
   (new card, open idle card, busy card only prefills).
