"""Widths in terminal columns: CJK takes two, combining marks none."""

from chotic_ui.primitives.terminal import (display_width, pad_right, truncate_ansi,
                                           truncate_text, visible_len)


def test_wide_glyphs_count_two_columns():
    assert display_width("abc") == 3
    assert display_width("マクロス") == 8
    assert display_width("é") == 1  # e + combining acute


def test_visible_len_ignores_colour_and_counts_columns():
    assert visible_len("\x1b[31mマクロス\x1b[0m") == 8


def test_truncate_text_cuts_by_columns_not_characters():
    out = truncate_text("マクロスマクロス", 9)
    assert out.endswith("...") and display_width(out) <= 9


def test_truncate_text_never_splits_a_wide_glyph():
    assert truncate_text("aマ", 2, suffix="") == "a"


def test_truncate_ansi_fits_the_columns_it_was_given():
    out = truncate_ansi("\x1b[2mマクロス MACROSS\x1b[0m", 9)
    assert visible_len(out) <= 9 and out.count("…") == 1


def test_pad_right_pads_to_columns():
    assert visible_len(pad_right("マクロス", 12)) == 12
