---
status: approved
issue: 4
author: olafkfreund
epic: 6
---

# Intent: Hand off to every nixarchy agent; delete the Codex-only client

## Problem

The palette's agent support is Codex-only and built for upstream Arch
Keystroke:

- **Codex-only client.** `codex/` plus `providers/Codex.qml` and
  `helpers/codex-start.sh` (about 1,200 lines with tests and docs) speaks
  Codex's private `app-server` JSON-RPC.
  - It pins `codex-cli 0.153.2` exactly, while nixpkgs ships 0.156.x, so on
    nixarchy it fails to start.
  - It is the only user of the `?` prefix and of the `codex-external` action.
- **AI rows know only Claude and ChatGPT/Codex.** `providers/AiWeb.qml` and
  `core/AiTargets.js` offer desktop apps, CLI or browser for those two, with
  their own "preferred assistant" and "mode" settings.
  - They ignore nixarchy's **default agent**, which the Omarchy menu,
    `Super+Shift+Ctrl+A` and Nixi all use.
  - That default is `~/.config/omarchy/defaults/agent`, written by
    `omarchy-default-agent`, launched by `omarchy-agent` or
    `omarchy-agent-prompt`. It covers claude, codex, opencode, gemini,
    copilot, crush, grok, pi, omp, antigravity, cursor-agent, hermes, muse
    and openclaw.
- **Agent chat belongs in Nixi, not here** (decided 2026-09-24). Nixi runs
  claude, codex and opencode over ACP with nixarchy's skills and reads the
  same default-agent file. But it cannot yet be opened with a question
  (nixi-nixarchy#37).
- **The hand-off is risky as it stands:**
  - `omarchy-agent` starts every agent with **auto-approve** flags
    (`--permission-mode auto`, `--yolo`, `--allow-all`,
    `bypassPermissions`, …).
  - `omarchy-agent-prompt` passes the text unescaped and unconfirmed.
  - Text typed, spoken or pasted into the palette would become the first
    instruction to an agent that runs shell commands without asking.
  - Launch errors (no default agent, agent not installed) are lost when
    started detached.

## Proposed outcome

- **Ask \<default agent\>.** With text in the palette, one explicit row,
  "Ask \<your default agent\>", opens that agent in a terminal with the text
  as its prompt, through `omarchy-agent-prompt` (a plain argv, no shell).
  This works for every agent nixarchy supports.
  - It is never an automatic answer: never top-ranked by the tier, never
    triggered by a dictation result.
  - The row shows the agent's name and the text.
  - Text that came from voice or the clipboard asks for confirmation first.
- **No default agent.** When none is set, the row instead opens the stock
  **Default Agent** picker (`setup.default.agent`) that the palette already
  renders from Omarchy's menu. There is no second picker. When the chosen
  agent isn't installed, the row says so and launches nothing.
- **Ask Nixi.** An "Ask Nixi" row appears when the Nixi card is enabled,
  and `?` makes it the top answer.
  - Once nixi-nixarchy#37 lands, it opens Nixi with the question asked.
  - Until then, it opens Nixi and puts the question on the clipboard, with
    a notice.
- **Search Google stays** as the last row when nothing matched.
- **Removed:**
  - `codex/`, `providers/Codex.qml`, `helpers/codex-start.sh`
  - the Codex tests and docs
  - the Claude/ChatGPT desktop, CLI and browser plumbing, and the
    "preferred assistant" and "mode" settings
- **Kept:** the generic provider-view machinery, which Translate and
  Keyboard Cleaner still use.

## Affected users and systems

- **This repo:**
  - `providers/AiWeb.qml` and `core/AiTargets.js` (rewrite)
  - `providers/Registry.qml`, `NixarchyMenu.qml` (one Codex hook)
  - `flake.nix` (file list and check list), `bin/nixarchy-menu`, the manifest
    and the example config
  - the docs, `tests/tst_ai.qml` (rewrite) and `tests/palette_dictation_check.py`
    (its back-navigation test uses the Codex view)
- **Users** lose the in-palette Codex conversation and its recent-questions
  history. Their `~/.local/state/nixarchy-menu/codex.json` and `questions/`
  are left orphaned and untouched.
- **Nixi:** nixi-nixarchy#37, about 20 lines plus tests.
- **nixarchy:** three bugs the research found in the stock agent picker and
  launcher. See open question 3.
- **razer:** runtime test host.

## Constraints

- **The hand-off is always an explicit row** with the agent named. It is
  never automatic, and there is no silent launch after a dictation result.
- **The argv is passed intact** (no shell): `["omarchy-agent-prompt", text]`.
  Text is clipped (the existing 2,000-character `clip()`), and empty text
  launches nothing.
- **Pre-checks happen in the palette:** default agent set and binary on
  PATH. A detached launch cannot report failure.
- **No new agent picker.** Reuse Omarchy's `setup.default.agent` rows.
- **The menu stays a hand-off only.** No conversation UI and no agent
  protocol code (agent-chat-in-nixi).

## Open questions

1. **Keep the claude.ai / chatgpt.com browser rows as extra choices?**
   Proposed: **no**. The default agent plus Nixi cover it. Google stays.
2. **Implement nixi-nixarchy#37 as part of this work** (a separate small PR
   in the Nixi repo, merged first)? Proposed: **yes**:
   - a new card asks the question
   - an already-open, idle card asks it
   - a busy card only fills the text box
   - plus `nixi --ask`

   Then the menu never needs the clipboard stopgap.
3. **File the three nixarchy launcher bugs** as a nixarchy issue? Proposed:
   **yes**:
   - (a) the picker rows for cursor-agent, hermes, muse and openclaw call
     `omarchy-default-agent`, which rejects those ids
   - (b) antigravity never launches: `command -v antigravity`, while the
     binary is `agy`
   - (c) picking an uninstalled agent from a headless menu action runs a
     sudo rebuild with no tty

   Also: `crush`/`pi` take a prompt starting with `-` as a flag, and
   `antigravity` drops the prompt. Until nixarchy fixes these, the palette
   pads a leading `-` with a space, and shows antigravity as "opens without
   a prompt".
4. **Add an "Ask about this machine" row** through `nixarchy-ask anything
   <text>`, which frames the prompt as a NixOS task naming the skills?
   Proposed: **not in #4**. Nixi already brings the skills, and #5 (skill-
   backed help rows) is where it fits.
