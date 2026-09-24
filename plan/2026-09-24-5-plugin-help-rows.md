---
status: approved
issue: 5
spec: spec/2026-09-24-5-plugin-help-rows.md
---

# Plan: Surface nixarchy plugins, Nixi and skill-backed help as palette rows

## Approved decisions
- **`providers/OmarchyMenu.qml`:**
  - Extract the ancestor-`when` walk out of `catalogVisible()` into
    `ancestorsVisible(entry)`, with the 32-level cap and `whenResults`, and
    have `catalogVisible()` call it.
  - Search mode (~:392) requires `isVisible(entry) && ancestorsVisible(entry)`.
  - Browsing is unchanged.
- **`rowFor()` confirm for agent-launching rows:**
  - It applies when the action contains a `nixarchy-ask` command word, or
    starts with `omarchy-agent`/`omarchy-agent-prompt`. Keep this as an
    explicit, commented pattern list.
  - The fields are `confirm: "Ask your default agent?"`,
    `confirmDetail: "<label>\n\nThe agent starts with automatic approval and can run commands without asking."`
    and `confirmText: "Ask"`.
  - The destructive-action confirm takes precedence.
- **`providers/AiWeb.qml`:** a lone `?` with Nixi enabled gives one "Ask Nixi"
  row (tier `answer`, subtitle "Open Nixi", `exec ["nixi"]`). An empty query
  still gives nothing.
- **The menu data** (aliases and the Nixi row) is nixarchy#961, not this repo.
- **No generic plugin provider.**

## Steps (one implementer)
1. **`ancestorsVisible`:** extract it, reuse it in `catalogVisible` and in
   search.
   → Verify: `catalog_check.py` still passes, and the new menu test (step 4)
   shows "faster" hidden with the Ask `when` false and shown with it true.
2. **`rowFor` agent confirm.**
   → Verify: an Ask topic row has the confirm fields and a non-agent action
   row doesn't.
3. **AiWeb bare `?`.**
   → Verify: a `tst_ai` or harness case gives one Ask Nixi row with Nixi
   enabled and none when it's disabled.
4. **Tests:** extend the menu harness (`tests/catalog_check.py` style, the
   real `OmarchyMenu` with a fixture jsonc and `whenResults`) for steps 1 and
   2, and `tst_ai.qml` (or an AiWeb harness) for step 3.
   → Verify: the QML suite passes, and the harness passes locally in
   `nix develop`.
   *Deviation:* the cases extend `tests/catalog_check.py` itself, with the
   fixture set inline as `items` (as its existing case does) instead of a
   jsonc file, and the AiWeb `?` case runs the real provider in the same
   harness. No new harness, so the flake and `bin` lists are unchanged.
5. **Lead:**
   - commit
   - `nix flake check` plus a forced `--rebuild` of `quickshell`
   - razer, after claiming it on the bus and with a shell restart:
     - with no default agent, "faster" shows no Ask row
     - with one set, "faster" asks for confirmation
     - a lone `?` shows Ask Nixi
   - Codex review
   - PR, merged when CI is green and the user agrees

## Tests
- QML suite, `nix flake check`, and a forced `--rebuild` of `quickshell`.
- The razer checks in step 5.

## Rollback
Revert the commit. The menu shows today's rows.
