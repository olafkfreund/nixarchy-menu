.pragma library

// Hand a query to the user's default coding agent, to Nixi, or to Google.
// Nothing here runs at query time except string building; activation is always
// an explicit Enter, and every agent hand-off asks first (see agentRow).

var MAX_PROMPT = 2000

// Every id omarchy-agent launches ($OMARCHY_PATH/bin/omarchy-agent), with the
// binary it runs. Antigravity is launched without the prompt (`agy` alone).
var AGENTS = {
  "claude":       { name: "Claude Code", bin: "claude" },
  "codex":        { name: "Codex", bin: "codex" },
  "opencode":     { name: "OpenCode", bin: "opencode" },
  "gemini":       { name: "Gemini CLI", bin: "gemini" },
  "copilot":      { name: "GitHub Copilot", bin: "copilot" },
  "crush":        { name: "Crush", bin: "crush" },
  "grok":         { name: "Grok", bin: "grok" },
  "pi":           { name: "Pi", bin: "pi" },
  "omp":          { name: "Oh My Pi", bin: "omp" },
  "antigravity":  { name: "Antigravity", bin: "agy", promptless: true },
  "cursor-agent": { name: "Cursor CLI", bin: "cursor-agent" },
  "hermes":       { name: "Hermes", bin: "hermes" },
  "muse":         { name: "Muse Code", bin: "muse" },
  "openclaw":     { name: "OpenClaw", bin: "omarchy-launch-openclaw" }
}

// omarchy-agent refuses to launch unless the agent's id is itself a command
// (`omarchy-cmd-missing "$agent"`), whatever binary it then runs, so an agent
// counts as installed only when both are on PATH. For antigravity (agy) and
// openclaw that shows "not installed" instead of a launch that fails
// (nixarchy#949).
function commandsFor(agentId) {
  var agent = AGENTS[agentId]
  if (!agent) return []
  return agent.bin === agentId ? [agentId] : [agentId, agent.bin]
}

// found: command name -> true, for the commands commandsFor() listed.
function isInstalled(agentId, found) {
  var commands = commandsFor(agentId)
  return commands.length > 0 && commands.every(function(c) { return found && found[c] === true })
}

var PICKER = { type: "navigate", scope: "omarchy/setup.default.agent", title: "Default Agent" }

// Trimmed and bounded. A leading "/" would be a slash command and a leading "-"
// an option to crush and pi (nixarchy#949), so both are padded with a space.
function clip(prompt) {
  var text = String(prompt === undefined || prompt === null ? "" : prompt).trim().slice(0, MAX_PROMPT)
  return /^[\/-]/.test(text) ? " " + text : text
}

function googleUrl(query) { return "https://www.google.com/search?q=" + encodeURIComponent(String(query || "").trim()).replace(/%20/g, "+") }

// The "Ask <agent>" row's own fields; the provider adds section, tier and score.
function agentRow(agentId, installed, text) {
  var id = String(agentId || "").trim()
  if (!id)
    return { title: "Choose a default agent", subtitle: "Pick the coding agent that answers from here", verb: "Open", action: PICKER }
  var agent = AGENTS[id]
  if (!agent)
    return { title: "Default agent “" + id + "” is not supported here", subtitle: "Choose another in Setup › Default Agent", disabled: true }
  if (!installed)
    return { title: agent.name + " is not installed", subtitle: "Choose an installed agent", verb: "Open", action: PICKER }
  var prompt = clip(text)
  return {
    title: "Ask " + agent.name,
    subtitle: "Opens " + agent.name + " in a terminal · " + (agent.promptless ? "opens without your text" : "runs without asking"),
    verb: "Open " + agent.name,
    action: agent.promptless ? { type: "exec", argv: ["omarchy-agent"] } : { type: "exec", argv: ["omarchy-agent-prompt", prompt] },
    confirm: "Ask " + agent.name + "?",
    confirmDetail: (agent.promptless ? agent.name + " opens without your text." : prompt) + "\n\n" + agent.name + " starts with automatic approval and can run commands without asking.",
    confirmText: "Open " + agent.name
  }
}

// `nixi --ask` needs nixi-nixarchy#37. Without it (canAsk false), open Nixi
// with the question on the clipboard and say so.
function nixiRow(text, canAsk) {
  var prompt = clip(text)
  return {
    title: "Ask Nixi",
    subtitle: canAsk ? "Nixi asks before it runs anything" : "Opens Nixi with your question on the clipboard",
    verb: "Ask",
    action: canAsk ? { type: "exec", argv: ["nixi", "--ask", prompt] } : { type: "compound", actions: [
      { type: "copy", text: prompt },
      { type: "exec", argv: ["nixi"] },
      { type: "notify", glyph: "󰅍", headline: "Question copied", body: "Paste it into Nixi with Ctrl+V" } ] }
  }
}
