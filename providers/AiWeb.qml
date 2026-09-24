import QtQuick
import Quickshell
import Quickshell.Io
import "../core/AiTargets.js" as AiTargets

// Fallbacks for queries nothing else answers: ask Nixi, ask the default coding
// agent (Omarchy's Setup › Default Agent) in a terminal, or search Google.
// Typing never runs anything: the agent comes from a watched file, whether it
// is installed from one `command -v` re-run when the agent or the desktop
// entries change, and Nixi's state from one check per palette open. A leading
// "?" puts Ask Nixi first.
Item {
  id: root
  property var host: null
  property string agentId: ""
  property var found: ({ id: "", commands: ({}) })   // what the last check found on PATH, and for which agent
  property bool recheck: false
  property string detectFor: ""
  property bool nixi: false               // Nixi enabled and on PATH
  property bool nixiAsk: false            // and new enough for `nixi --ask`

  readonly property var provider: ({
    apiVersion: 1,
    id: "ai",
    name: "Agents & Web Search",
    icon: "✳",
    color: "#e79c85",
    description: "Continue any query in Nixi, your default coding agent or Google",
    settings: [],
    query: function(ctx) { return root.query(ctx) },
    opened: function() { agentFile.reload(); if (!nixiCheck.running) nixiCheck.running = true }
  })

  function requery() { if (root.host && root.host.opened) root.host.requery({ provider: root.provider.id }) }

  FileView {
    id: agentFile
    path: Quickshell.env("HOME") + "/.config/omarchy/defaults/agent"
    watchChanges: true
    printErrors: false
    onLoaded: root.agentId = text().split("\n")[0].trim()
    onLoadFailed: root.agentId = ""
    onFileChanged: reload()
  }

  onAgentIdChanged: checkAgent()

  function checkAgent() {
    if (detect.running) { root.recheck = true; return }
    var commands = AiTargets.commandsFor(root.agentId)
    if (!commands.length) return
    root.detectFor = root.agentId
    detect.command = ["sh", "-c", "PATH=\"$HOME/.local/share/mise/shims:$PATH\"; for c; do command -v \"$c\" >/dev/null && echo \"$c\"; done", "sh"].concat(commands)
    detect.running = true
  }

  // omarchy-agent looks in mise's shims too, so this does the same. It checks
  // the id and the binary; see AiTargets.commandsFor.
  Process {
    id: detect
    stdout: StdioCollector {
      onStreamFinished: {
        var commands = ({}), lines = text.split("\n")
        for (var i = 0; i < lines.length; i++) if (lines[i].trim()) commands[lines[i].trim()] = true
        root.found = { id: root.detectFor, commands: commands }
        root.requery()
      }
    }
    onRunningChanged: if (!running && root.recheck) { root.recheck = false; root.checkAgent() }
  }

  // Installing or removing an agent usually changes the desktop entries.
  Connections {
    target: DesktopEntries.applications
    function onValuesChanged() { root.checkAgent() }
  }

  // An older nixi lists no --ask in the usage line it prints for an unknown
  // flag (it exits without doing anything); nixi-nixarchy#37 adds it.
  Process {
    id: nixiCheck
    command: ["sh", "-c", "nixarchy-plugin --enabled io.github.olafkfreund.nixi >/dev/null 2>&1 && command -v nixi >/dev/null || exit 0; echo enabled; nixi --nixarchy-menu-probe 2>&1 | grep -q -- --ask && echo ask"]
    stdout: StdioCollector {
      onStreamFinished: {
        root.nixi = text.indexOf("enabled") >= 0
        root.nixiAsk = text.indexOf("ask") >= 0
        root.requery()
      }
    }
  }

  function row(fields, id, icon, tier, score, q) {
    fields.id = id
    fields.icon = icon
    fields.section = "Continue with"
    fields.tier = tier
    fields.score = score
    fields.preview = q
    fields.previewLabel = "PROMPT"
    return fields
  }

  function query(ctx) {
    if (ctx.scope) return []
    var raw = String(ctx.rawQuery === undefined ? ctx.query : ctx.rawQuery).trim()
    var asked = raw.charAt(0) === "?"
    var q = asked ? raw.slice(1).trim() : raw
    if (!q) return []
    var rows = []
    if (root.nixi) rows.push(row(AiTargets.nixiRow(q, root.nixiAsk), "nixi", "", asked ? "answer" : "fallback", 3.5, q))
    var installed = root.found.id === root.agentId && AiTargets.isInstalled(root.agentId, root.found.commands)
    rows.push(row(AiTargets.agentRow(root.agentId, installed, q), "agent", "󰚩", "fallback", 3, q))
    rows.push({ id: "google", title: "Search Google", subtitle: q, icon: "󰊭", section: "Continue with", verb: "Search", tier: "fallback", score: 2,
                action: { type: "url", url: AiTargets.googleUrl(q) } })
    return rows
  }
}
