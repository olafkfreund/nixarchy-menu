import QtQuick
import QtTest
import "../core/AiTargets.js" as Ai

TestCase {
    name: "AiTargets"

    function test_clip_bounds_pads_and_keeps_empty() {
        compare(Ai.clip(new Array(3000).join("a")).length, Ai.MAX_PROMPT)
        compare(Ai.clip("  hi  "), "hi")
        compare(Ai.clip("/clear"), " /clear")
        compare(Ai.clip("-h"), " -h")
        compare(Ai.clip(""), "")
        compare(Ai.clip("   "), "")
        compare(Ai.clip(undefined), "")
    }
    function test_no_agent_opens_the_default_agent_picker() {
        var r = Ai.agentRow("", false, "hello")
        compare(r.action, { type: "navigate", scope: "omarchy/setup.default.agent", title: "Default Agent" })
        verify(!r.confirm)
    }
    function test_uninstalled_agent_never_launches() {
        var r = Ai.agentRow("claude", false, "hello")
        compare(r.title, "Claude Code is not installed")
        compare(r.action.type, "navigate")
        compare(r.action.scope, "omarchy/setup.default.agent")
    }
    function test_installed_agent_gets_the_prompt_as_a_literal_argument_and_confirms() {
        var payload = "--help $(touch /tmp/no) `id` \"quoted\"\nsecond line"
        var r = Ai.agentRow("claude", true, payload)
        compare(r.title, "Ask Claude Code")
        compare(r.action.argv, ["omarchy-agent-prompt", " " + payload])        // leading "-" padded, nothing else touched
        compare(r.confirm, "Ask Claude Code?")
        compare(r.confirmText, "Open Claude Code")
        compare(r.confirmDetail, " " + payload + "\n\nClaude Code starts with automatic approval and can run commands without asking.")
        compare(Ai.agentRow("opencode", true, "hi").action.argv, ["omarchy-agent-prompt", "hi"])
    }
    function test_promptless_agent_opens_without_the_text() {
        var r = Ai.agentRow("antigravity", true, "hello")
        compare(r.action.argv, ["omarchy-agent"])
        verify(r.subtitle.indexOf("without your text") > 0)
        verify(r.confirm.length > 0)
        compare(Ai.AGENTS.antigravity.bin, "agy")
    }
    function test_installed_needs_the_id_and_the_binary_like_omarchy_agent() {
        compare(Ai.commandsFor("claude"), ["claude"])
        compare(Ai.commandsFor("antigravity"), ["antigravity", "agy"])
        verify(Ai.isInstalled("claude", { claude: true }))
        verify(!Ai.isInstalled("antigravity", { agy: true }))                 // omarchy-agent would refuse (nixarchy#949)
        verify(Ai.isInstalled("antigravity", { antigravity: true, agy: true }))
        verify(!Ai.isInstalled("openclaw", { "omarchy-launch-openclaw": true }))
        verify(!Ai.isInstalled("vim", { vim: true }))
        var r = Ai.agentRow("antigravity", Ai.isInstalled("antigravity", { agy: true }), "hello")
        compare(r.title, "Antigravity is not installed")
        compare(r.action, { type: "navigate", scope: "omarchy/setup.default.agent", title: "Default Agent" })
    }
    function test_unknown_agent_has_no_action() {
        var r = Ai.agentRow("vim", true, "hello")
        compare(r.action, undefined)
        verify(r.disabled)
    }
    function test_nixi_asks_with_the_text_or_falls_back_to_the_clipboard() {
        compare(Ai.nixiRow("how do I x?", true).action.argv, ["nixi", "--ask", "how do I x?"])
        var fallback = Ai.nixiRow("how do I x?", false).action
        compare(fallback.type, "compound")
        compare(fallback.actions[0], { type: "copy", text: "how do I x?" })
        compare(fallback.actions[1].argv, ["nixi"])
    }
    function test_lone_question_mark_opens_nixi() {
        var r = Ai.openNixiRow()
        compare(r.title, "Ask Nixi")
        compare(r.subtitle, "Open Nixi")
        compare(r.action, { type: "exec", argv: ["nixi"] })
    }
    function test_google_url() {
        compare(Ai.googleUrl("two words"), "https://www.google.com/search?q=two+words")
    }
}
