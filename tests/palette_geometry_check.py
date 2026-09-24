#!/usr/bin/env python3
"""The real card, offscreen, on a small and a large output with a 26 px top
bar: it clears the bar and the margins and its width follows the output."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
with tempfile.TemporaryDirectory(prefix='nixarchy-menu-palette-geometry-') as temp:
    work = Path(temp)
    project = work/'project'
    shutil.copytree(root, project, ignore=shutil.ignore_patterns('.git','.claude','.agents','.codex','tests','__pycache__'))
    for q in [project, *(project).rglob("*")]: q.chmod(q.stat().st_mode | 0o200)
    (work/'qs').symlink_to(OMARCHY + '/shell')
    source = project/'NixarchyMenu.qml'
    qml = source.read_text()
    qml = qml.replace('  id: root\n', '  id: root\n  property alias testCard: card\n  property alias testPanel: panel\n', 1)
    qml = qml.replace('  PanelWindow {','  Window {\n    transientParent: null\n    width: 1000; height: 800')
    qml = qml.replace('    anchors { top: true; bottom: true; left: true; right: true }\n','')
    source.write_text('\n'.join(line for line in qml.splitlines() if 'exclusionMode:' not in line and 'WlrLayershell.' not in line))
    (work/'shell.qml').write_text('''import QtQuick
import Quickshell
import qs.Commons
import "project"
ShellRoot {
 id: test
 function check(ok,msg) { if(!ok) { console.log("FAIL",msg); Qt.callLater(Qt.quit); throw Error(msg) } }
 NixarchyMenu { id: palette; omarchyPath: "''' + OMARCHY + '''" }
 function measure(w, h) {
   var c = palette.testCard, m = Style.space(16), bar = 26
   var base = Style.space(palette.compact ? 640 : 760)
   var want = Math.min(w - 2 * m, Math.max(base, Math.min(1.5 * base, Math.round(0.40 * w))))
   console.log("card", w + "x" + h, "->", c.x, c.y, c.width + "x" + c.height)
   test.check(c.y >= bar + m, w + "x" + h + ": clears the bar: y=" + c.y)
   test.check(c.y + c.height <= h - m, w + "x" + h + ": bottom margin: " + (c.y + c.height))
   test.check(c.x >= m && c.x + c.width <= w - m, w + "x" + h + ": side margins: " + c.x + "+" + c.width)
   test.check(c.width === want, w + "x" + h + ": width " + c.width + " === " + want)
 }
 Timer { interval:250; repeat:true; running:true; onTriggered: {
   if (!palette.configSettled) return; running = false   // start once the on-disk load has applied, or it would undo applyConfigText
   palette.applyConfigText(JSON.stringify({version:1,matching:{mode:"off"},palette:{animations:"off",windowTransition:"instant"}}))
   palette.shell = {bar:{barSize:26, barHidden:false, position:"top"}}
   palette.open('{}')
   test.resize(960, 540)
 } }
 // An offscreen window takes its new size on a later event loop turn.
 property var sizes: [[960, 540], [2560, 1440]]
 property int at: 0
 function resize(w, h) { palette.testPanel.width = w; palette.testPanel.height = h; settle.restart() }
 Timer { id: settle; interval: 100; onTriggered: {
   var s = test.sizes[test.at]
   test.check(palette.testPanel.width === s[0] && palette.testPanel.height === s[1], "the window took " + s + ": " + palette.testPanel.width + "x" + palette.testPanel.height)
   test.measure(s[0], s[1])
   if (++test.at < test.sizes.length) { test.resize(test.sizes[test.at][0], test.sizes[test.at][1]); return }
   test.check(palette.testCard.width > Style.space(palette.compact ? 640 : 760), "the card grows on a large output")
   console.log("PASS palette geometry"); Qt.quit()
 } }
 Timer { interval:15000; running:true; onTriggered:{ console.log("FAIL timeout"); Qt.quit() } }
}
''')
    env=dict(os.environ, HOME=str(work), XDG_RUNTIME_DIR=str(work), QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='generic', QT_QUICK_BACKEND='software', QML_IMPORT_PATH=str(work))
    env.pop('DISPLAY', None)
    env.pop('WAYLAND_DISPLAY', None)
    result=subprocess.run(['quickshell','-p',str(work/'shell.qml')],env=env,capture_output=True,text=True,timeout=120)
    output=result.stdout+result.stderr
    if os.environ.get("GEOMETRY_VERBOSE"): print(output)
    assert 'PASS palette geometry' in output and 'FAIL' not in output, output
    assert 'TypeError' not in output and 'ReferenceError' not in output, output
    print('PASS palette geometry: the card clears a top bar and the margins at 960x540 and grows with a 2560x1440 output')
