---
status: draft
issue: 5
intent: intent/2026-09-24-5-plugin-help-rows.md
---

# Spec: Surface nixarchy plugins, Nixi and skill-backed help as palette rows

The palette-side half is in this repo. The menu-data half (Ask-topic aliases
and a guarded Nixi row in nixarchy `modules/apps.nix`) is nixarchy#961, with
its own artifacts. This spec does not depend on #961 landing: the palette
changes are correct with or without that data.

## Design

### 1. Hidden parents stay hidden in search (`providers/OmarchyMenu.qml`)
- **Extract the ancestor walk.** It already lives inside `catalogVisible()`
  (~:333-340): walk `parent` and require `whenResults[id] === true` for every
  ancestor with a `when`. It becomes `ancestorsVisible(entry)`, and
  `catalogVisible()` calls it, so there is one implementation.
- **Search mode** (~:392) requires
  `root.isVisible(entry) && root.ancestorsVisible(entry)`.
- **Browsing** (~:382) is unchanged: it only lists children of an already
  visible parent.

### 2. Ask topics that launch an agent ask first
- `rowFor()` sets a confirm when the row's action runs an agent:
  - the action contains a `nixarchy-ask` command word
  - or it starts with `omarchy-agent`/`omarchy-agent-prompt`

  That is a small explicit pattern list, commented with its reason.
- **Confirm text:** `confirm: "Ask your default agent?"` with
  `confirmDetail: "<row label>\n\nThe agent starts with automatic approval and can run commands without asking."`,
  in the same form as #4. The destructive-action confirm is unchanged, and
  takes precedence if both apply.

### 3. A bare `?` offers Ask Nixi (`providers/AiWeb.qml`)
- **Today:** `if (!q) return []` returns nothing for a lone `?`.
- **New:** a lone `?`, with the query exactly `?` after trimming and Nixi
  enabled, returns one "Ask Nixi" row, tier `answer`, subtitle "Open Nixi",
  effect `{type:"exec", argv:["nixi"]}`.
- **Unchanged:** an empty query without `?` still returns nothing.

## Alternatives rejected

- **A generic "every enabled plugin is a row" provider:** it duplicates the
  curated menu rows and loses their labels, aliases and fallbacks. The
  intent decided against it.
- **A second parent-guard implementation in search:** `catalogVisible`
  already has one.
- **Confirming every menu action:** only agent-launching rows share #4's
  auto-approve risk.
- **Parsing "help \<topic\>" in the palette:** plain-word matching is menu
  data (nixarchy#961), and free text already reaches Ask Nixi and the agent
  row.

## Risks

- **The pattern list could miss a future agent-launching row.** It is
  documented next to the list, and the fallback is today's behaviour, no
  confirm.
- **`ancestorsVisible` costs a parent walk per search leaf.** It is bounded
  (≤ 32 levels, the same cap as `catalogVisible`) and uses the cached
  `whenResults`.

## Verification

1. **QML and harness tests:**
   - With the Ask folder's `when` false (no default agent), searching
     "faster" returns no Ask topic. With it true, it does.
   - An Ask topic row carries the confirm fields, and a non-agent action row
     does not.
   - A lone `?` with Nixi enabled gives exactly one Ask Nixi row; with Nixi
     disabled, none.
   - These go in the existing `tests/catalog_check.py` / menu harness style
     where they need the menu model, and `tst_ai.qml` for the AiWeb pure
     parts.
2. **`nix flake check`,** plus a forced `--rebuild` of `quickshell`.
3. **razer:**
   - With no default agent, "faster" finds no Ask row.
   - With one set, "faster" asks for confirmation before `nixarchy-ask`.
   - A lone `?` offers Ask Nixi.
