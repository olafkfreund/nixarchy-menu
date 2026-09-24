<!-- For a change to nixarchy-menu itself, describe what changed and why, and paste what you ran (bin/nixarchy-menu test). Delete the checklist below. -->

## New or updated extension

Folder: `extensions/<id>`

What it does, in one paragraph, with two or three example queries.

- [ ] `bin/nixarchy-menu check-extensions extensions/<id>` passes (or `python3 tools/check_extensions.py extensions/<id>`).
- [ ] The folder is self-contained: no imports from outside it, no symlinks, no `manifest.json`.
- [ ] Everything the extension runs, reads, writes or downloads is listed in its README under *Limits and dependencies*. A setup script pins and verifies anything it downloads.
- [ ] No network call, process or file write happens before the user turns the extension on, and none happens on every keystroke that the README does not explain.
- [ ] Tried in the real palette from `~/.local/share/nixarchy-menu/extensions/<id>`.
- [ ] I am the author of this code or the README says where it came from and under which license.
