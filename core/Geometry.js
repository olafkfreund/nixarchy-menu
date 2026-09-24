.pragma library

// The palette card's rectangle on an output of outW×outH logical px. It grows
// with the output (40% × 54%, today's 760/1920 and 580/1080) between the base
// size and 1.5× it, and never covers the bar or the margin around the edges.
// dmenuContentH >= 0 is a dmenu picker: it keeps its requested width (baseW)
// and content height, and centres vertically.
function cardRect(outW, outH, bar, baseW, baseH, margin, dmenuContentH) {
  function reserve(edge) { return bar && !bar.barHidden && bar.position === edge ? bar.barSize : 0 }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }
  var dmenu = dmenuContentH >= 0
  var availW = outW - reserve("left") - reserve("right") - 2 * margin
  var availH = outH - reserve("top") - reserve("bottom") - 2 * margin
  var width = Math.min(availW, dmenu ? baseW : clamp(Math.round(0.40 * outW), baseW, 1.5 * baseW))
  var height = Math.min(availH, dmenu ? dmenuContentH : clamp(Math.round(0.54 * outH), baseH, 1.5 * baseH))
  return {
    x: reserve("left") + margin + Math.round((availW - width) / 2),
    y: reserve("top") + margin + Math.round((availH - height) * (dmenu ? 0.5 : 0.38)),
    width: width,
    height: height
  }
}
