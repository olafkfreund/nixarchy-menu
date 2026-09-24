---
status: approved
issue: 10
spec: spec/2026-09-24-10-follow-desktop-size.md
---

# Plan: Palette window follows the desktop size and stays clear of the bar

## Approved decisions
- **New `core/Geometry.js`:** `cardRect(outW, outH, bar, baseW, baseH, margin, dmenuContentH)`.
  - **Reserved edges:** `reserve[edge] = barSize` when not hidden and at that
    edge.
  - **Available area:** `availW/H` is the output minus the reserved edges
    minus `2·margin`.
  - **Width:** `min(availW, clamp(round(0.40·outW), baseW, 1.5·baseW))`.
    For dmenu it is `min(availW, baseW)`, with `baseW = Style.space(dmenuWidth)`,
    so a picker keeps the width its caller asked for. (Implementation note: the
    spec's formula did not say how dmenu width is chosen, and growing it would
    override the caller's `width`.)
  - **Height:** `min(availH, clamp(round(0.54·outH), baseH, 1.5·baseH))`.
    For dmenu it is `min(availH, dmenuContentH)`.
  - **Position:** `x` is centred in the available area. `y` is `0.38`, or
    `0.5` for dmenu, of the remaining height.
- **`NixarchyMenu.qml`:** the card geometry (:1253-1258) comes from `cardRect`.
  - `bar` is `root.shell.bar`, falling back to
    `{barHidden:false, barSize:Style.bar.sizeHorizontal, position:"top"}`.
  - `margin` is `Style.space(16)`.
  - `baseW/H` are `Style.space(760|640)` and `Style.space(580|540)`.
  - The Motion slide offset is kept.
  - The panel keeps `exclusionMode: Ignore`.
- **Not changed:** text scale, a size setting, and Nixi (nixi#38 is separate).

## Steps (one implementer)
1. **`core/Geometry.js`** plus **`tests/tst_geometry.qml`**, covering:
   - 1920×1080 gives about 768×583
   - 2560×1440 gives about 1024×778
   - 3840×2160 gives 1140×870
   - 960×540 gives about 760×482 with `y ≥ 42` and a bottom `≤ 524`
   - a bottom bar, a left bar, a hidden bar, and no shell
   - dmenu

   → Verify: the QML suite passes.
2. **`NixarchyMenu.qml`:** wire `cardRect`, keeping the Motion offset and the
   dmenu path.
   → Verify: qmllint shows no new warning, and `palette_motion_check`,
   `palette_dmenu_check` and the other palette checks pass.
3. **New `tests/palette_geometry_check.py`,** from `palette_motion_check.py`'s
   offscreen window swap:
   - set `palette.shell = {bar:{barSize:26, barHidden:false, position:"top"}}`
   - use 960×540 and 2560×1440
   - assert the bar clearance, the margins and the width

   Wire it into the flake `quickshell` list and bin.
   → Verify: it passes.
4. **Lead:**
   - commit
   - `nix flake check` plus a forced `--rebuild` of `quickshell`
   - razer, after claiming it on the bus and with a shell restart: screenshots
     at the current scale, and at scale 2 set temporarily with
     `hyprctl keyword monitor` and then restored
   - Codex review
   - PR, merged when CI is green and the user agrees

## Tests
- QML suite (`tst_geometry`), `nix flake check`, and a forced `--rebuild` of
  `quickshell`.
- razer screenshots at scale 1 and 2, compared with #10's measurements.

## Rollback
Revert the commit. Geometry returns to today's fixed size.

## Razer results (2026-09-24, eDP-1 1920×1080, compact density, 26px top bar)
- **Scale 1:** the card measured about 766×581 at (577, 210). `cardRect` gives 768×583 at (576, 209), so it matches within the 1px border.
- **Scale 2** (logical 960×540): the card measured 1280×963 physical at y=85, which is 640×482 logical at y≈42, bottom 524. That's exactly the compact `cardRect`. It clears the bar, and the text scales with the output.
- **Gotcha:** Hyprland 0.56 with Lua config has no `hyprctl keyword monitor`. The scale was set with `hyprctl eval 'hl.monitor({...})'` and restored to 1.

## Deviation at merge (rebase onto #12)
#12 (merged first) gates every palette harness on `palette.configSettled`. The
new `tests/palette_geometry_check.py` predates that, so on rebase it gets the
same repeating-check gate as `palette_motion_check.py`.
