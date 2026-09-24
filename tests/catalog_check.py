#!/usr/bin/env python3
"""Guarded Omarchy catalog uses actual provider code without executing commands."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
with tempfile.TemporaryDirectory(prefix='nixarchy-menu-catalog-') as temp:
    work=Path(temp)
    for folder in ['providers','core']:
        shutil.copytree(root/folder,work/folder)
        # The source may be a read-only store path; make the copy writable.
        for q in [work/folder, *(work/folder).rglob("*")]: q.chmod(q.stat().st_mode | 0o200)
    (work/'qs').symlink_to(OMARCHY + '/shell')
    (work/'shell.qml').write_text('''import QtQuick
import Quickshell
import "providers"
ShellRoot {
  OmarchyMenu { id: menu }
  AiWeb { id: ai }
  function check(ok,msg) { if(!ok) { console.log("FAIL",msg); Qt.callLater(Qt.quit); throw Error(msg) } }
  Timer { interval:100; running:true; onTriggered: {
    menu.items = {
      root:{id:"root",parent:"",kind:"menu",label:"Root",aliases:[]},
      group:{id:"group",parent:"root",kind:"menu",label:"Group",aliases:[],when:"guard-parent"},
      child:{id:"child",parent:"group",kind:"action",label:"Child",aliases:[],action:"never-run"},
      guarded:{id:"guarded",parent:"root",kind:"action",label:"Guarded",aliases:[],when:"guard-child",action:"never-run"},
      visible:{id:"visible",parent:"root",kind:"action",label:"Visible",aliases:[],action:"never-run"}
    }
    menu.itemOrder=["root","group","child","guarded","visible"]
    menu.pathCache=({}); menu.rowsLoaded=true; menu.whenResults=({})
    var ctx={scope:"",sub:"",settings:{confirmDestructive:true}}
    var rows=menu.catalog(ctx)
    check(rows.length===1 && rows[0].id==="visible","unknown guards and their descendants are excluded")
    menu.whenResults={group:true,guarded:false}
    rows=menu.catalog(ctx)
    check(rows.some(r=>r.id==="child") && !rows.some(r=>r.id==="guarded"),"resolved visibility respected")
    ctx.sub="group"
    rows=menu.catalog(ctx)
    check(rows.length===1 && rows[0].id==="child","subtree scope respected")
    menu.whenResults={group:false,guarded:true}
    check(menu.catalog(ctx).length===0,"ancestor becoming unavailable removes descendants")
    console.log("PASS catalog guards and scopes")

    // #5: search hides leaves under a hidden folder; agent-launching actions confirm.
    menu.items = {
      root:{id:"root",parent:"",kind:"menu",label:"Root",aliases:[]},
      ask:{id:"ask",parent:"root",kind:"menu",label:"Ask",aliases:[],when:"has-default-agent"},
      "ask.faster":{id:"ask.faster",parent:"ask",kind:"action",label:"Make my computer faster",aliases:["faster"],action:"nixarchy-ask performance"},
      "remove.ask":{id:"remove.ask",parent:"root",kind:"action",label:"Remove via agent",aliases:[],action:"nixarchy-ask remove"},
      plain:{id:"plain",parent:"root",kind:"action",label:"Plain",aliases:[],action:"echo nixarchy-asked"}
    }
    menu.itemOrder=["root","ask","ask.faster","remove.ask","plain"]
    menu.pathCache=({}); menu.whenResults={ask:false}
    var sctx={scope:"",sub:"",query:"faster",settings:{confirmDestructive:true},pending:function(){}}
    check(!menu.query(sctx).some(r=>r.id==="ask.faster"),"faster hidden while Ask's when is false")
    menu.whenResults={}
    check(!menu.query(sctx).some(r=>r.id==="ask.faster"),"faster hidden while Ask's when is unresolved")
    menu.whenResults={ask:true}
    var hit=menu.query(sctx).filter(r=>r.id==="ask.faster")
    check(hit.length===1,"faster shown once Ask's when is true")
    check(hit[0].confirm==="Ask your default agent?" && hit[0].confirmText==="Ask"
          && hit[0].confirmDetail==="Make my computer faster\n\nThe agent starts with automatic approval and can run commands without asking.","Ask topic confirms")
    var byId={}; menu.catalog(ctx).forEach(r=>byId[r.id]=r)
    check(byId.plain && !byId.plain.confirm && !byId.plain.confirmDetail,"non-agent action has no confirm")
    check(byId["remove.ask"].confirm==="Run “Remove via agent”?" && !byId["remove.ask"].confirmDetail,"destructive confirm wins")
    check(menu.launchesAgent("omarchy-agent-prompt hi") && menu.launchesAgent("omarchy-agent") && menu.launchesAgent("foo && nixarchy-ask x")
          && !menu.launchesAgent("omarchy-agents") && !menu.launchesAgent("echo nixarchy-ask-me") && !menu.launchesAgent(""),"agent pattern list")
    console.log("PASS search guards and agent confirm")

    // #5: a lone "?" offers Ask Nixi only when Nixi is enabled; empty gives nothing.
    var q=t=>ai.query({scope:"",query:t,rawQuery:t})
    ai.nixi=false
    check(q("?").length===0,"lone ? without Nixi gives nothing")
    ai.nixi=true
    var n=q("?")
    check(n.length===1 && n[0].title==="Ask Nixi" && n[0].subtitle==="Open Nixi" && n[0].tier==="answer"
          && JSON.stringify(n[0].action)==='{"type":"exec","argv":["nixi"]}',"lone ? gives one Ask Nixi row")
    check(q("").length===0 && q("  ").length===0,"empty query gives nothing")
    console.log("PASS bare question mark"); Qt.quit()
  } }
}
''')
    env=dict(os.environ,HOME=str(work),OMARCHY_PATH=str(work/'absent'),XDG_RUNTIME_DIR=str(work),QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_IMPORT_PATH=str(work))
    env.pop('DISPLAY',None);env.pop('WAYLAND_DISPLAY',None)
    result=subprocess.run(['quickshell','-p',str(work/'shell.qml')],env=env,capture_output=True,text=True,timeout=120)
    output=result.stdout+result.stderr
    for marker in ['PASS catalog guards and scopes','PASS search guards and agent confirm','PASS bare question mark']:
        assert marker in output and 'FAIL' not in output,output
    print('PASS catalog: unresolved guards, ancestor visibility, updates and scoped enumeration')
    print('PASS search: hidden folders hide their leaves; agent actions confirm; lone ? asks Nixi')
