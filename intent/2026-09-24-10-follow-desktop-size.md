---
status: approved
issue: 10
author: olafkfreund
epic: 6
---

# Intent: Palette window follows the desktop size and stays clear of the bar

## Problem

The palette card is sized as if the screen were always a 1080p laptop with no bar.

- **Size today:** `NixarchyMenu.qml:1253-1258` sets the card to `min(Style.space(760|640), panel − 2·gapsOut)` wide and `min(Style.space(580|540), panel − 2·gapsOut)` tall.
- **`panel` includes the bar.** It is one full-screen `PanelWindow` with `exclusionMode: Ignore`, so the dimming scrim can cover the bar.
- **The only margin is `Style.gapsOut`, which is 5 px.** Measured on razer (#10 comments):
  - **1920×1080 at scale 1:** 760×580. Fine.
  - **2560×1440 and 3840×2160 at scale 1:** still 760×580. That's under a third of the width, and a lot of empty screen.
  - **1920×1080 at scale 2** (960×540 logical): 760×530 at y=5. It covers the bar and sits 5 px from the top and bottom.
- **What already works:**
  - Text and spacing follow the theme's `[font] base-size` and `[spacing] scale`, because `Style.space` and `Style.font` track them.
  - Hyprland's monitor scale applies through logical pixels.
  - On razer, text size 16 and 20 grew the card to about 850×720 and 1066×900.
- **Omarchy already gives plugins the bar's live size and position:** `shell.bar.{barSize, barHidden, position}`. Omarchy's notifications use them to stay clear of it (`plugins/notifications/Service.qml:48-52`).

## Proposed outcome

- **The card is a share of the output it opens on:** about 40% of the width and 54% of the height. Those are today's 1080p proportions, so 1080p barely changes.
- **It never goes smaller than today's size or larger than 1.5 times it,** so it doesn't get too big on 4K.
- **It always fits the area left after the bar and a 16 px margin,** wherever the bar is and whether or not it's hidden.

Worked through by hand at comfortable density, base-size 12, with a 26 px top bar:

| Output (logical) | Today | Proposed |
|---|---|---|
| 1920×1080 | 760×580 | about 768×583 |
| 2560×1440 | 760×580 | about 1024×778 |
| 3840×2160 | 760×580 | 1140×870 (the 1.5× cap) |
| 960×540 (1080p at scale 2) | 760×530, over the bar | about 760×482, clear of the bar |

- **Text size does not change with the screen size.** It keeps following base-size and monitor scale, the user's own settings. The larger card just shows more rows.
- **The dmenu-style pickers get the same bar-aware limit.**
- **Nixi's card gets the same rule:** nixi-nixarchy#38 uses a copy of the same small helper, because the two repos can't import each other.

## Affected users and systems

- **This repo:**
  - `NixarchyMenu.qml`: the card size and position.
  - A new `core/Geometry.js`: one pure function.
  - A new `tests/tst_geometry.qml`.
  - A palette check at real sizes.
- **Nixi:** `Conversation.qml`, at two sites. That is tracked in nixi#38 with its own artifacts.
- **Everyone's palette size changes on screens larger than 1080p, and on high-scale screens.**

## Constraints

- **The panel stays full-screen (`exclusionMode: Ignore`),** so the scrim still dims the bar and a click anywhere still cancels. The card itself avoids the bar.
- **No new multiplier on text or rows,** so the user's base-size and scale stay the single control.
- **Testable without a desktop:** the sizing is a pure function, and a palette check uses the existing offscreen window swap from `palette_motion_check.py`.

## Open questions

1. **Should text also grow on a large screen at scale 1,** for example 4K at scale 1?
   Proposed: **no**. That is what monitor scale or base-size is for, and a second multiplier would fight them.
2. **Should the numbers be user-adjustable,** as a Palette › Size setting (Auto / Compact / Comfortable)?
   Proposed: **not now**. Density already gives Compact and Comfortable, and Auto becomes the behaviour.
