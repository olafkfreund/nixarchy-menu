#!/usr/bin/env python3
"""A setting saved before the on-disk config has loaded must not overwrite it (#12).

Runs the real offscreen palette twice: once over a config file with
providers.open-url.prefix "zz", once with a HOME where the state migration fails.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")

SHELL = '''import QtQuick
import Quickshell
import "project"
ShellRoot {
 id: test
 property int failures: 0
 function check(ok, msg) { if (!ok) { failures++; console.log("FAIL", msg) } else console.log("ok", msg) }
 function set(path, key, value, schema) { palette.perform({type: "setting", path: path, key: key, value: value, schema: schema}, {}) }
 NixarchyMenu { id: palette; omarchyPath: "''' + OMARCHY + '''" }
 %s
 Timer { interval: 15000; running: true; onTriggered: { console.log("FAIL timeout", palette.configSettled, palette.stateReady, palette.errorMessage); Qt.quit() } }
}
'''

LOADS = '''
 // 1. Before settling: migrateState has not exited yet, so nothing has loaded.
 Component.onCompleted: {
   test.check(!palette.configSettled, "not settled at creation")
   test.set(["providers", "open-url"], "prefix", "yy", {key: "prefix", type: "string"})
   test.check(palette.errorMessage.indexOf("still loading") >= 0, "a save before the load is refused: " + palette.errorMessage)
 }
 Timer { interval: 50; repeat: true; running: true; onTriggered: {
   if (!palette.configSettled) return
   running = false
   // 2. Settled: the on-disk values, not the defaults and not the refused change.
   var p = palette.config.providers && palette.config.providers["open-url"]
   test.check(p && p.prefix === "zz", "settled config has the on-disk prefix: " + JSON.stringify(p))
   // 3. A save now goes through and keeps the other keys (checked on disk by Python).
   palette.errorMessage = ""
   test.set(["palette"], "density", "comfortable", {key: "density", type: "enum", options: ["compact", "comfortable"]})
   test.check(palette.errorMessage === "", "a save after settling is accepted: " + palette.errorMessage)
   console.log(test.failures ? "FAIL settle" : "PASS settle")
   Qt.callLater(Qt.quit)
 } }
'''

MIGRATION_FAILS = '''
 Timer { interval: 50; repeat: true; running: true; onTriggered: {
   if (!palette.configSettled) return
   running = false
   // 4. A failed migration still settles, with no state paths this session.
   test.check(!palette.stateReady, "migration failed: stateReady stays false")
   console.log(test.failures ? "FAIL settle" : "PASS settle")
   Qt.callLater(Qt.quit)
 } }
'''


def run(body, seed):
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-config-settle-") as temp:
        work = Path(temp)
        project = work / "project"
        shutil.copytree(root, project, ignore=shutil.ignore_patterns(
            ".git", ".claude", ".agents", ".codex", "tests", "__pycache__", "experiments"))
        # The source may be a read-only store path; make the copy writable.
        for q in [project, *project.rglob("*")]: q.chmod(q.stat().st_mode | 0o200)
        (work / "qs").symlink_to(OMARCHY + "/shell")
        source = project / "NixarchyMenu.qml"
        qml = source.read_text().replace("  PanelWindow {", "  Window {\n    transientParent: null\n    width: 1000; height: 800")
        qml = qml.replace("    anchors { top: true; bottom: true; left: true; right: true }\n", "")
        source.write_text("\n".join(line for line in qml.splitlines() if "exclusionMode:" not in line and "WlrLayershell." not in line))
        restore = seed(work)
        (work / "shell.qml").write_text(SHELL % body)
        env = dict(os.environ, HOME=str(work), XDG_RUNTIME_DIR=str(work),
                   QT_QPA_PLATFORM="offscreen", QT_QPA_PLATFORMTHEME="generic",
                   QT_QUICK_BACKEND="software", QML_IMPORT_PATH=str(work))
        env.pop("DISPLAY", None)
        env.pop("WAYLAND_DISPLAY", None)
        # migrate-state.sh notifies on failure: keep that off the real desktop.
        env.pop("OMARCHY_PATH", None)
        stubs = work / "bin"
        stubs.mkdir()
        for tool in ("notify-send", "omarchy-shell"):
            (stubs / tool).write_text("#!/bin/sh\nexit 0\n")
            (stubs / tool).chmod(0o755)
        env["PATH"] = f"{stubs}:{env.get('PATH', '')}"
        try:
            result = subprocess.run(["quickshell", "-p", str(work / "shell.qml")], env=env,
                                    capture_output=True, text=True, timeout=120)
        finally:
            if restore: restore()
        output = result.stdout + result.stderr
        assert "PASS settle" in output and "FAIL" not in output, output
        assert "TypeError" not in output and "ReferenceError" not in output, output
        config = work / ".config/omarchy/nixarchy-menu.json"
        return json.loads(config.read_text()) if config.exists() else None


def on_disk(work):
    config = work / ".config/omarchy/nixarchy-menu.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"version": 1, "matching": {"mode": "off"},
                                  "providers": {"open-url": {"prefix": "zz"}}}))


saved = run(LOADS, on_disk)
assert saved["providers"]["open-url"]["prefix"] == "zz", saved      # 1: the refused "yy" never reached disk
assert saved["palette"]["density"] == "comfortable", saved          # 3: the accepted save landed
assert saved["matching"] == {"mode": "off"}, saved                  # 3: and kept the other keys


def migration_fails(work):
    # The setup migrate_state_check.py uses: an unreadable old state file makes the copy fail.
    bad = work / ".local/state/keystroke/usage.json"
    bad.parent.mkdir(parents=True)
    bad.write_text('{"a":1}')
    bad.chmod(0o000)
    return lambda: bad.chmod(0o644)


if os.geteuid() == 0:
    print("SKIP migration-failure case (root ignores file modes)")
else:
    run(MIGRATION_FAILS, migration_fails)
print("PASS palette config settle: saves refused before load, on-disk values kept, later saves keep other keys, failed migration still settles")
