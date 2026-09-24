import QtQuick
import QtTest
import "../core/Geometry.js" as Geometry

TestCase {
    name: "Geometry"
    readonly property var topBar: ({ barHidden: false, barSize: 26, position: "top" })
    function rect(w, h, bar) { return Geometry.cardRect(w, h, bar === undefined ? topBar : bar, 760, 580, 16, -1) }

    function test_1080p_barely_changes() {
        var r = rect(1920, 1080)
        compare([r.width, r.height], [768, 583])
        compare(r.x, 576)
        compare(r.y, 42 + Math.round((1022 - 583) * 0.38))
    }
    function test_1440p_grows() {
        var r = rect(2560, 1440)
        compare([r.width, r.height], [1024, 778])
    }
    function test_4k_is_capped_at_one_and_a_half() {
        var r = rect(3840, 2160)
        compare([r.width, r.height], [1140, 870])
    }
    function test_small_output_stays_clear_of_the_bar() {
        var r = rect(960, 540)
        compare([r.width, r.height], [760, 482])
        verify(r.y >= 42, "below the bar and margin: " + r.y)
        verify(r.y + r.height <= 524, "above the bottom margin: " + (r.y + r.height))
        compare(r.x, 16 + Math.round((928 - 760) / 2))
    }
    function test_bottom_bar_reserves_the_bottom() {
        var r = rect(960, 540, { barHidden: false, barSize: 26, position: "bottom" })
        compare(r.y, 16)
        verify(r.y + r.height <= 540 - 26 - 16)
    }
    function test_left_bar_reserves_the_left() {
        var r = rect(960, 540, { barHidden: false, barSize: 28, position: "left" })
        verify(r.x >= 28 + 16, "right of the bar: " + r.x)
        verify(r.x + r.width <= 960 - 16)
        compare(r.height, 540 - 32)   // nothing reserved vertically
    }
    function test_hidden_bar_reserves_nothing() {
        var r = rect(960, 540, { barHidden: true, barSize: 26, position: "top" })
        compare([r.y, r.height], [16, 508])
    }
    function test_no_bar_reserves_nothing() {
        var r = rect(960, 540, null)
        compare([r.y, r.height], [16, 508])
    }
    function test_dmenu_keeps_its_width_and_content_height_and_centres() {
        var r = Geometry.cardRect(1920, 1080, topBar, 300, 580, 16, 200)
        compare([r.width, r.height], [300, 200])
        compare(r.y, 42 + Math.round((1022 - 200) / 2))
        var tall = Geometry.cardRect(960, 540, topBar, 300, 580, 16, 5000)
        compare(tall.height, 482)
        compare(tall.y, 42)
    }
}
