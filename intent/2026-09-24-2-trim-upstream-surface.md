---
status: approved
issue: 2
author: olafkfreund
epic: 6
---

# Intent: Remove upstream surface nixarchy does not need

## Problem

The fork still carries upstream Keystroke's product surface. None of it is
part of the menu that nixarchy will run, but every piece has to be renamed
(#1), packaged (#3) and tested before anything new can be added:

- `site/` (7.0 MB): evindor's GitHub Pages showcase.
- `experiments/`: Codex cloud experiments.
- `docs/releases/`, `docs/history/`: upstream release notes and design history.
- `preview.png`, `assets/` screenshots, `tools/showcase/`.
- **Upstream extension marketplace feed**: `providers.extensions.indexUrl`
  points at `evindor/keystroke` (`keystroke.example.json:82`). That is
  unreviewed third-party QML loaded into our shell.
- **Vendored `omarchy/MenuModel.js`**:
  - It is a copy of the shell's own menu model, so it can drift from the
    jsonc that nixarchy generates.
  - Nixi's `MenuSearch.qml` already reuses the shell's copy instead.

## Proposed outcome

- The tree contains only what the menu runs, plus developer docs
  (`docs/architecture.md`, `docs/providers.md`).
- **Smart Match stays** (amended 2026-09-24, see below). Its impure
  install (prebuilt binary, runtime cargo/uv, model download) is replaced by
  Nix packaging in #3, not by deletion.
- No extension or index is ever fetched from upstream. The bundled
  extensions in `extensions/` stay and remain off by default.
- Menu rows, guards and ✓ marks come from the shell's `MenuModel.js`, so
  the palette shows exactly the rows the stock nixarchy menu shows,
  including the skill-backed "Ask" group.
- Voice stays: it drives the user's own `voxtype`, which nixarchy ships.
- The palette opens, searches, runs Omarchy rows and hands off to
  assistants exactly as before, minus semantic matching.

## Affected users and systems

- Only this repo. Nothing in nixarchy consumes it yet (wiring is #3).
- CI: `.github/workflows/` loses the Pages job.

## Constraints

- Must not rename anything. The rename is #1, so this diff stays reviewable
  as pure deletion.
- Must not touch `codex/`. Its replacement is #4.
- Must keep `LICENSE` and upstream attribution.
- The existing tests that remain must still pass. Tests for deleted code go
  with it.
- A deleted piece can be brought back from git history.

## Open questions

1. Delete `docs/verification.md` (1,069 lines of upstream manual QA) and
   `docs/codex-integration-*.md`, or keep them until #4 lands?
   Proposed: delete verification now; the codex docs go with #4.
2. Should the README keep its screenshots, or be rewritten short for
   nixarchy? Proposed: rewrite it short under #1, the rename, and just drop
   the dead links here.
3. The voice bind writer (`core/VoiceBindings.js`) may conflict with the
   binds that nixarchy seeds in `bindings.lua`. Is that in scope here, or
   does it get its own issue? Proposed: its own issue.

## Amendment (2026-09-24, after implementation review)

The first approved version deleted Smart Match. Testing on razer showed that
this loses more than embeddings: typed spoken-style arithmetic ("27 plus
90"), the Chromium stand-in for "Chrome", de-duplication across providers
and cross-catalog typo recovery. The cost that motivated deletion was only
the *install path*:
- a prebuilt binary
- runtime cargo/uv
- a model download

Nix can package all of it:
- **Engine:** a 4-crate Rust program with `Cargo.lock`.
- **Model:** three files, SHA-256 already pinned.

So Smart Match is kept in #2 as it is today, and #3 packages it
declaratively and deletes the impure install chain.
