---
status: approved
issue: 10
intent: intent/2026-09-24-10-follow-desktop-size.md
---

# Spec: Palette window follows the desktop size and stays clear of the bar

## Design

### 1. `core/Geometry.js`, a new pure function (about 20 lines)
`cardRect(outW, outH, bar, baseW, baseH, margin, dmenuContentH)` returns
`{x, y, width, height}` in logical px:
```
reserve[edge] = bar && !bar.barHidden && bar.position === edge ? bar.barSize : 0
availW = outW - reserve.left - reserve.right - 2·margin
availH = outH - reserve.top  - reserve.bottom - 2·margin
width  = min(availW, clamp(round(0.40·outW), baseW, 1.5·baseW))
height = dmenuContentH >= 0 ? min(availH, dmenuContentH)
                            : min(availH, clamp(round(0.54·outH), baseH, 1.5·baseH))
x = reserve.left + margin + round((availW - width) / 2)
y = reserve.top  + margin + round((availH - height) · (dmenu ? 0.5 : 0.38))
```
- 0.40 and 0.54 are today's 760/1920 and 580/1080, so 1080p barely changes.
- `baseW` and `baseH` are passed in already scaled: `Style.space(760|640)`
  and `Style.space(580|540)`. That keeps base-size and density as they are.

### 2. `NixarchyMenu.qml`
- **Bar state.** The card reads
  `bar = root.shell && root.shell.bar ? root.shell.bar : { barHidden: false, barSize: Style.bar.sizeHorizontal, position: "top" }`.
  This is the same live API and fallback as Omarchy's notifications
  (`plugins/notifications/Service.qml:48-52`).
- **Card geometry.** The card's `width`, `height`, `x` and `y` (:1253-1258)
  come from one `cardRect(panel.width, panel.height, bar, …, Style.space(16), …)`
  binding. The existing Motion slide offset is still added to `y`.
- **Unchanged:** the panel keeps `exclusionMode: Ignore`, so the scrim still
  dims the bar and a click anywhere cancels. Text and row sizes don't change;
  the list shows more rows in a taller card.

### 3. Nixi (nixi-nixarchy#38, separate artifacts in the Nixi repo)
It uses the same rule, with a copy of `Geometry.js` and a 540×560 base,
applied at both `Conversation.qml` sites. It is **not** part of this change.

## Alternatives rejected

- **`exclusionMode: Normal` so the compositor shrinks the panel:** the scrim
  would stop dimming the bar, and a click there would no longer cancel.
- **Scale text with the output size:** that is a second multiplier fighting
  base-size and monitor scale. The intent answered: no.
- **A Size setting (Auto / Compact / Comfortable):** density already exists.
  The intent answered: not now.
- **One `Geometry.js` shared across repos:** there is no import path between
  plugins, and 20 duplicated lines is cheaper than a shared package.

## Risks

- **Everyone's card grows on screens larger than 1080p.** That is the point,
  and the 1.5× cap limits it.
- **An unusual bar** (vertical, or a hidden one reappearing) is covered by the
  `position` and `barHidden` cases in the tests.

## Verification

1. **`tests/tst_geometry.qml`** (runs in the existing `qml-unit` check),
   comfortable density with a 26 px top bar and a 16 px margin:
   - 1920×1080 → about 768×583
   - 2560×1440 → about 1024×778
   - 3840×2160 → 1140×870, the cap
   - 960×540 → about 760×482 with y ≥ 42, bottom ≤ 524, not over the bar
   - a bar at the bottom, a bar on the left, a hidden bar, and no shell
     (fallback)
   - the dmenu height rule
2. **`tests/palette_geometry_check.py`,** built on `palette_motion_check.py`'s
   offscreen window swap: the real card at 960×540 and 2560×1440, with
   `shell.bar` set, asserting the bar clearance and width.
3. **razer, at scale 1 and 2,** after claiming it on the agent bus and with a
   shell restart: screenshots, as in #10's comments.
