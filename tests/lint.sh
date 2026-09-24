#!/usr/bin/env bash
# qmllint with the `qs` module (Omarchy's shell Commons/Ui) made importable.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHIM="$(mktemp -d)"
trap 'rm -rf "$SHIM"' EXIT
ln -s "${OMARCHY_PATH:-/usr/share/omarchy}/shell" "$SHIM/qs"
# Qt and Quickshell modules: every QML2_IMPORT_PATH entry becomes an -I, so
# the Nix sandbox (no system Qt) resolves QtQuick and Quickshell imports.
imports=(-I "$SHIM")
IFS=: read -ra extra <<< "${QML2_IMPORT_PATH:-}"
for dir in "${extra[@]}"; do [[ -n $dir ]] && imports+=(-I "$dir"); done
status=0
while IFS= read -r file; do
  if ! qmllint "${imports[@]}" "$file"; then status=1; fi
done < <(rg --files "$ROOT" -g '*.qml' -g '!**/tests/**' | sort)
exit $status
