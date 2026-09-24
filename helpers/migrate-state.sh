#!/bin/sh
# One-time copy of Keystroke's user state to the nixarchy-menu paths. Run by
# NixarchyMenu.qml at load. Each new path is derived the way its reader
# derives it; the old paths are never modified, so going back to Keystroke
# finds everything as it was. Not copied: share/keystroke/matching (the
# engine and models ship with the package) and share/keystroke/voxtype
# (upstream's own).

failed=""

# m OLD NEW: copy OLD to NEW unless NEW exists or OLD is absent. The copy
# lands in a sibling and is renamed into place, so an interrupted copy never
# leaves a partial NEW that later runs would skip.
m() {
  [ -e "$2" ] || [ -L "$2" ] && return 0
  [ -e "$1" ] || [ -L "$1" ] || return 0
  tmp="$2.migrating.$$"
  if mkdir -p "$(dirname "$2")" && cp -a "$1" "$tmp" && mv -T "$tmp" "$2"; then
    return 0
  fi
  rm -rf "$tmp"
  echo "$1" >&2
  failed="$failed $1"
}

notify() {
  if [ -n "$OMARCHY_PATH" ] && [ -x "$OMARCHY_PATH/bin/omarchy-notification-send" ]; then
    "$OMARCHY_PATH/bin/omarchy-notification-send" -g "󰵅" "$1" "$2"
  else
    notify-send "$1" "$2"
  fi
}

state=${XDG_STATE_HOME:-$HOME/.local/state}
cache=${XDG_CACHE_HOME:-$HOME/.cache}

m "$HOME/.config/omarchy/keystroke.json" "$HOME/.config/omarchy/nixarchy-menu.json"
m "$HOME/.local/state/keystroke" "$HOME/.local/state/nixarchy-menu"
# The currency extension alone reads $XDG_STATE_HOME.
if [ "$state" != "$HOME/.local/state" ]; then
  m "$state/keystroke/currency" "$state/nixarchy-menu/currency"
fi
m "$cache/keystroke" "$cache/nixarchy-menu"
m "$HOME/.local/share/keystroke/extensions" "$HOME/.local/share/nixarchy-menu/extensions"

# Only after the copies: created first, it would make the migration skip it.
mkdir -p "$HOME/.local/state/nixarchy-menu"

# An enabled evindor.keystroke wins every omarchy.menu call. Only say so.
plugins=$(omarchy-shell shell listPlugins 2>/dev/null) || plugins=""
if [ -n "$plugins" ]; then
  if command -v jq >/dev/null 2>&1; then
    old=$(printf '%s' "$plugins" | jq -r 'map(select(.id == "evindor.keystroke" and .enabled == true)) | length' 2>/dev/null)
  else
    # ponytail: assumes the flat object shape listPlugins prints; jq is the real parser.
    old=$(printf '%s' "$plugins" | tr -d ' \n\t' | grep -c '"id":"evindor\.keystroke"[^}]*"enabled":true')
  fi
  if [ "${old:-0}" -gt 0 ] 2>/dev/null; then
    notify "nixarchy-menu" "Keystroke is still enabled and keeps the menu. Run: omarchy plugin disable evindor.keystroke"
  fi
fi

if [ -n "$failed" ]; then
  notify "nixarchy-menu" "Could not copy Keystroke data from:$failed. The old data is untouched; the copy is retried at the next start."
  exit 1
fi
exit 0
