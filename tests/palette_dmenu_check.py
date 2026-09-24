#!/usr/bin/env python3
"""Dmenu sizing on the real palette keeps its empty state visible."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
with tempfile.TemporaryDirectory(prefix="nixarchy-menu-palette-dmenu-") as temp:
    work = Path(temp)
    project = work / "project"
    shutil.copytree(root, project, ignore=shutil.ignore_patterns(".git", ".claude", ".agents", ".codex", "tests", "__pycache__"))
    # The source may be a read-only store path; make the copy writable.
    for q in [project, *(project).rglob("*")]: q.chmod(q.stat().st_mode | 0o200)
    (work / "qs").symlink_to(OMARCHY + "/shell")
    source = project / "NixarchyMenu.qml"
    qml = source.read_text()
    qml = qml.replace("  id: root\n", "  id: root\n  property alias testCard: card\n  property alias testContent: content\n  property alias testEmptyState: emptyState\n", 1)
    qml = qml.replace("  PanelWindow {", "  Window {\n    transientParent: null\n    width: 1000; height: 800")
    qml = qml.replace("    anchors { top: true; bottom: true; left: true; right: true }\n", "")
    source.write_text("\n".join(line for line in qml.splitlines() if "exclusionMode:" not in line and "WlrLayershell." not in line))
    (work / "shell.qml").write_text('''import QtQuick
import Quickshell
import "project"
ShellRoot {
  id: test
  property real oneRowHeight: 0
  function check(ok, msg) { if (!ok) { console.log("FAIL", msg); Qt.callLater(Qt.quit); throw Error(msg) } }
  NixarchyMenu { id: palette; omarchyPath: "''' + OMARCHY + '''" }
  Timer { interval: 250; running: true; onTriggered: {
    palette.open(JSON.stringify({ mode: "select", prompt: "Keybindings", options: ["Super + K → Keybindings"], width: 800, maxHeight: 500 }))
    test.check(palette.rows.length === 1, "the picker begins with one row")
    test.oneRowHeight = palette.testCard.height
    palette.setQuery("tiltet")
    palette.runQuery()
    Qt.callLater(function() {
      test.check(palette.rows.length === 0, "the filter has no matches")
      test.check(palette.testContent.height >= palette.testEmptyState.implicitHeight,
                 "the empty message fits: " + palette.testContent.height + " >= " + palette.testEmptyState.implicitHeight)
      test.check(palette.testCard.height > test.oneRowHeight, "the empty picker reserves more room than one result row")
      palette.cancel()
      console.log("PASS palette dmenu")
      Qt.quit()
    })
  } }
  Timer { interval: 8000; running: true; onTriggered: { console.log("FAIL timeout"); Qt.quit() } }
}
''')
    env = dict(os.environ, HOME=str(work), XDG_RUNTIME_DIR=str(work), QT_QPA_PLATFORM="offscreen", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_BACKEND="software", QML_IMPORT_PATH=str(work))
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    result = subprocess.run(["quickshell", "-p", str(work / "shell.qml")], env=env, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    assert "PASS palette dmenu" in output and "FAIL" not in output, output
    assert "TypeError" not in output and "ReferenceError" not in output, output
    print("PASS palette dmenu: an empty filtered picker keeps its message visible")
