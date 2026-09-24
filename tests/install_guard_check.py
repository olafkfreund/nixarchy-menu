#!/usr/bin/env python3
"""Checks that bin/nixarchy-menu leaves a nixarchy-managed plugin alone (#20).

A managed target is Home Manager's symlink into /nix/store. install and
uninstall must refuse before touching anything; every other target state goes
through as before. Runs against a temp $HOME with logging stubs for nix and the
omarchy CLI. Stdlib only.

Run: python3 tests/install_guard_check.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "nixarchy-menu")
# Any real /nix/store path works as the "managed" link target.
STORE_PATH = os.path.realpath(sys.executable)
failures = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        failures.append(what)


def run(verb, make_target):
    home = tempfile.mkdtemp(prefix="nm-guard-")
    stubs = os.path.join(home, "stubs")
    os.makedirs(stubs)
    log = os.path.join(home, "calls.log")
    # nix exits 1: an empty store path would make stage_plugin copy "/.".
    for name, code in (("nix", 1), ("omarchy", 0), ("omarchy-shell", 0), ("omarchy-plugin-list", 0)):
        path = os.path.join(stubs, name)
        with open(path, "w") as f:
            f.write(f'#!/bin/sh\necho "{name} $*" >> "{log}"\nexit {code}\n')
        os.chmod(path, 0o755)
    plugins = os.path.join(home, ".config", "omarchy", "plugins")
    os.makedirs(plugins)
    target = os.path.join(plugins, "nixarchy.menu")
    make_target(target, home)
    before = os.readlink(target) if os.path.islink(target) else None
    env = dict(os.environ, HOME=home, PATH=stubs + os.pathsep + os.environ.get("PATH", ""))
    proc = subprocess.run(["bash", SCRIPT, verb], env=env, capture_output=True, text=True)
    calls = open(log).read() if os.path.exists(log) else ""
    after = os.readlink(target) if os.path.islink(target) else None
    staging = [n for n in os.listdir(plugins) if n.startswith(".nixarchy-menu.")]
    shutil.rmtree(home)
    return proc, calls, before, after, staging


def managed(target, _home):
    os.symlink(STORE_PATH, target)


def real_dir(target, _home):
    os.makedirs(target)


def elsewhere(target, home):
    src = os.path.join(home, "src-checkout")
    os.makedirs(src)
    os.symlink(src, target)


for verb in ("install", "uninstall"):
    proc, calls, before, after, staging = run(verb, managed)
    check(proc.returncode == 1, f"managed {verb}: exits 1 (got {proc.returncode})")
    check("defaultPlugins.menu" in proc.stderr, f"managed {verb}: says what manages it")
    check(calls == "", f"managed {verb}: runs nothing (calls: {calls.strip()!r})")
    check(before == after == STORE_PATH, f"managed {verb}: the link is untouched")
    check(staging == [], f"managed {verb}: leaves no staging directory")

for name, make in (("real directory", real_dir), ("symlink outside the store", elsewhere)):
    proc, calls, _, _, _ = run("install", make)
    first = calls.splitlines()[0] if calls else ""
    check(first.startswith("nix build"), f"{name}: install goes on to build (first call: {first!r})")
    check("defaultPlugins.menu" not in proc.stderr, f"{name}: not refused")

if failures:
    print(f"FAIL install guard: {len(failures)} check(s)")
    sys.exit(1)
print("PASS install guard: managed install/uninstall refused, hand installs unchanged")
