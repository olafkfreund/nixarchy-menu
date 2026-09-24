#!/usr/bin/env python3
"""Checks helpers/migrate-state.sh against a temp $HOME. Stdlib only.

Run: python3 tests/migrate_state_check.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "helpers", "migrate-state.sh")
failures = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        failures.append(what)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def read(path):
    with open(path, "rb") as f:
        return f.read()


def snapshot(root):
    out = {}
    for d, _, files in os.walk(root):
        for n in files:
            p = os.path.join(d, n)
            out[os.path.relpath(p, root)] = read(p)
    return out


def leftovers(root):
    return [os.path.join(d, n) for d, dirs, files in os.walk(root) for n in dirs + files if ".migrating." in n]


def stubs(bindir, log, plugins_json):
    os.makedirs(bindir, exist_ok=True)
    shell = os.path.join(bindir, "omarchy-shell")
    with open(shell, "w") as f:
        f.write("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\n" % plugins_json)
    notif = os.path.join(bindir, "notify-send")
    with open(notif, "w") as f:
        f.write('#!/bin/sh\nprintf "%%s|" "$@" >> "%s"\necho >> "%s"\n' % (log, log))
    for p in (shell, notif):
        os.chmod(p, 0o755)


def run(home, extra_env=None, plugins_json="[]", nojq=False):
    bindir = os.path.join(home, "stubbin")
    log = os.path.join(home, "notify.log")
    stubs(bindir, log, plugins_json)
    path = os.environ.get("PATH", "")
    if nojq:
        # A PATH without jq: only the tools the script needs, to exercise grep.
        path = os.path.join(home, "tools")
        os.makedirs(path)
        for t in ("dirname", "mkdir", "cp", "mv", "rm", "tr", "grep", "cat"):  # cat: the stub
            os.symlink(shutil.which(t), os.path.join(path, t))
    env = {"HOME": home, "PATH": bindir + ":" + path}
    env.update(extra_env or {})
    r = subprocess.run([shutil.which("sh"), SCRIPT], env=env, capture_output=True, text=True)
    notes = read(log).decode().splitlines() if os.path.exists(log) else []
    return r, notes


def seed(home, state=None, cache=None):
    state = state or os.path.join(home, ".local/state")
    cache = cache or os.path.join(home, ".cache")
    write(os.path.join(home, ".config/omarchy/keystroke.json"), b'{"providers":{"ai":{"provider":"claude"}}}')
    write(os.path.join(home, ".local/state/keystroke/usage.json"), b'{"a":1}')
    write(os.path.join(home, ".local/state/keystroke/questions/q.json"), b"q")
    write(os.path.join(state, "keystroke/currency/rates.json"), b"cur")
    write(os.path.join(cache, "keystroke/currency/rates.json"), b"cache")
    write(os.path.join(home, ".local/share/keystroke/extensions/ext/extension.json"), b"{}")
    write(os.path.join(home, ".local/share/keystroke/voxtype/v"), b"vox")


def case_defaults():
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        seed(home)
        before = snapshot(home)
        r, notes = run(home)
        check(r.returncode == 0, "defaults: exit 0 (%s)" % r.stderr.strip())
        n = lambda p: os.path.join(home, p)
        check(read(n(".config/omarchy/nixarchy-menu.json")) == before[".config/omarchy/keystroke.json"], "config copied")
        check(read(n(".local/state/nixarchy-menu/usage.json")) == b'{"a":1}', "state dir copied")
        check(os.path.exists(n(".local/state/nixarchy-menu/questions/q.json")), "state subdirs copied")
        check(read(n(".cache/nixarchy-menu/currency/rates.json")) == b"cache", "cache copied")
        check(os.path.exists(n(".local/share/nixarchy-menu/extensions/ext/extension.json")), "extensions copied")
        check(not os.path.exists(n(".local/share/nixarchy-menu/voxtype")), "voxtype skipped")
        after = snapshot(home)
        check(all(after.get(k) == v for k, v in before.items()), "old files byte-identical")
        check(not leftovers(home), "no .migrating leftovers")
        check(notes == [], "no notice without evindor.keystroke enabled")


def case_no_overwrite_and_mkdir():
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        seed(home)
        write(os.path.join(home, ".config/omarchy/nixarchy-menu.json"), b"mine")
        r, _ = run(home)
        check(read(os.path.join(home, ".config/omarchy/nixarchy-menu.json")) == b"mine", "existing new path not overwritten")
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        r, notes = run(home)
        check(r.returncode == 0 and os.path.isdir(os.path.join(home, ".local/state/nixarchy-menu")), "fresh home: state dir created")
        check(notes == [], "fresh home: no notice")


def case_failure():
    if os.geteuid() == 0:
        print("SKIP failure case (root ignores file modes)")
        return
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        seed(home)
        bad = os.path.join(home, ".local/state/keystroke/usage.json")
        os.chmod(bad, 0o000)
        try:
            r, notes = run(home)
        finally:
            os.chmod(bad, 0o644)
        new = os.path.join(home, ".local/state/nixarchy-menu")
        check(r.returncode == 1, "failure: exit 1")
        check(os.path.join(home, ".local/state/keystroke") in r.stderr, "failure: old path on stderr")
        check(os.listdir(new) == [], "failure: no partial new state (only the empty mkdir)")
        check(not leftovers(home), "failure: no .migrating leftovers")
        check(len(notes) == 1 and "untouched" in notes[0], "failure: one notice saying old data is untouched")
        check(os.path.exists(os.path.join(home, ".config/omarchy/nixarchy-menu.json")), "failure: other pairs still copied")


def case_xdg():
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        data, state, cache = (os.path.join(home, x) for x in ("xdata", "xstate", "xcache"))
        seed(home, state, cache)
        r, _ = run(home, {"XDG_DATA_HOME": data, "XDG_STATE_HOME": state, "XDG_CACHE_HOME": cache})
        check(r.returncode == 0, "xdg: exit 0 (%s)" % r.stderr.strip())
        check(os.path.exists(os.path.join(home, ".local/share/nixarchy-menu/extensions/ext/extension.json")), "xdg: extensions stay under $HOME")
        check(read(os.path.join(state, "nixarchy-menu/currency/rates.json")) == b"cur", "xdg: currency under XDG_STATE_HOME")
        check(os.path.exists(os.path.join(home, ".local/state/nixarchy-menu/usage.json")), "xdg: state dir stays under $HOME")
        check(read(os.path.join(cache, "nixarchy-menu/currency/rates.json")) == b"cache", "xdg: cache under XDG_CACHE_HOME")


def case_old_plugin():
    enabled = '[{"id":"evindor.keystroke","name":"Keystroke","kinds":["menu","bar-widget"],"enabled":true,"active":false},' \
              '{"id":"nixarchy.menu","name":"nixarchy-menu","kinds":["menu"],"enabled":true,"active":false}]'
    disabled = enabled.replace('"enabled":true', '"enabled":false', 1)
    for nojq in (False, True):
        label = "grep" if nojq else "jq"
        with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
            r, notes = run(home, plugins_json=enabled, nojq=nojq)
            check(len(notes) == 1 and "omarchy plugin disable evindor.keystroke" in notes[0], "old plugin enabled (%s): one notice" % label)
        with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
            r, notes = run(home, plugins_json=disabled, nojq=nojq)
            check(notes == [], "old plugin disabled (%s): no notice" % label)


def case_omarchy_notification_send():
    with tempfile.TemporaryDirectory(prefix="nixarchy-menu-migrate-") as home:
        op = os.path.join(home, "omarchy")
        log = os.path.join(home, "omarchy.log")
        write(os.path.join(op, "bin/omarchy-notification-send"), ('#!/bin/sh\nprintf "%%s|" "$@" >> "%s"\necho >> "%s"\n' % (log, log)).encode())
        os.chmod(os.path.join(op, "bin/omarchy-notification-send"), 0o755)
        r, notes = run(home, {"OMARCHY_PATH": op}, '[{"id":"evindor.keystroke","enabled":true}]')
        sent = read(log).decode().splitlines() if os.path.exists(log) else []
        check(len(sent) == 1 and notes == [], "OMARCHY_PATH set: notice goes through omarchy-notification-send once")


for case in (case_defaults, case_no_overwrite_and_mkdir, case_failure, case_xdg, case_old_plugin, case_omarchy_notification_send):
    case()

print("FAIL: %d check(s)" % len(failures) if failures else "PASS: all checks")
sys.exit(1 if failures else 0)
