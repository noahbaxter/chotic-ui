"""The line editor: keys in, text and a correctly placed cursor out, including
once the text has wrapped onto a second row."""

import re

from chotic_ui.primitives import line_editor as le
from chotic_ui.primitives.line_editor import LineEditor, parse_chunk


class Screen:
    """Just enough of a terminal to replay what the editor writes: wrapping
    (with the deferred wrap at the last column), \\r, \\b and the CSI
    sequences the editor uses."""

    def __init__(self, cols, rows=10):
        self.cols, self.rows = cols, rows
        self.grid = [[" "] * cols for _ in range(rows)]
        self.r = self.c = 0
        self.pending = False

    def write(self, text):
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "\x1b":
                m = re.compile(r"\[(\d*)([A-Za-z])").match(text, i + 1)
                n, final = m.group(1), m.group(2)
                self._csi(int(n) if n else None, final)
                i = m.end()
                continue
            self._char(ch)
            i += 1

    def _char(self, ch):
        if ch == "\r":
            self.c, self.pending = 0, False
        elif ch == "\n":
            self.r, self.c, self.pending = self.r + 1, 0, False
        elif ch == "\b":
            self.c, self.pending = max(0, self.c - 1), False
        else:
            if self.pending:
                self.r, self.c, self.pending = self.r + 1, 0, False
            self.grid[self.r][self.c] = ch
            if self.c == self.cols - 1:
                self.pending = True
            else:
                self.c += 1

    def _csi(self, n, final):
        if final == "A":
            self.r, self.pending = max(0, self.r - (n or 1)), False
        elif final == "G":
            self.c, self.pending = (n or 1) - 1, False
        elif final == "J":
            self.grid[self.r][self.c:] = [" "] * (self.cols - self.c)
            for row in range(self.r + 1, self.rows):
                self.grid[row] = [" "] * self.cols
        else:
            raise AssertionError(f"unexpected CSI {final}")

    def lines(self):
        return ["".join(row).rstrip() for row in self.grid]


def type_into(editor, screen, keys, cols):
    editor.feed(keys)
    screen.write(editor.render(cols))


class TestKeys:
    def test_typing_and_backspace(self):
        e = LineEditor("> ")
        e.feed("abc")
        e.feed([le.BACKSPACE])
        assert (e.text, e.pos) == ("ab", 2)

    def test_arrows_edit_in_the_middle(self):
        e = LineEditor()
        e.feed("ace")
        e.feed([le.LEFT, le.LEFT, "b"])
        e.feed([le.RIGHT, "d"])
        assert e.text == "abcde"

    def test_home_end_delete(self):
        e = LineEditor()
        e.feed("abc")
        e.feed([le.HOME, le.DELETE])
        assert (e.text, e.pos) == ("bc", 0)
        e.feed([le.END, "!"])
        assert e.text == "bc!"

    def test_backspace_at_start_and_delete_at_end_do_nothing(self):
        e = LineEditor()
        e.feed("a")
        e.feed([le.DELETE])
        e.feed([le.HOME, le.BACKSPACE])
        assert e.text == "a"

    def test_enter_and_esc(self):
        e = LineEditor()
        e.feed(["a", le.ENTER, "b"])
        assert (e.text, e.done, e.cancelled) == ("a", True, False)
        e = LineEditor()
        e.feed(["a", le.ESC])
        assert (e.done, e.cancelled) == (True, True)

    def test_ctrl_v_pastes_the_clipboard_as_one_line(self, monkeypatch):
        monkeypatch.setattr(le.clipboard, "read_text",
                            lambda: "https://drive.google.com/x\r\nsecond\n")
        e = LineEditor()
        e.feed(["a", "\x16", "b"])
        assert e.text == "ahttps://drive.google.com/xsecondb"

    def test_control_characters_are_not_typed(self):
        e = LineEditor()
        e.feed(["\x03", "\t", "a"])
        assert e.text == "a"


class TestParseChunk:
    def test_plain_text_and_arrows(self):
        assert parse_chunk("ab\x1b[Dc") == ["a", "b", le.LEFT, "c"]

    def test_home_end_delete_spellings(self):
        assert parse_chunk("\x1b[H\x1b[1~\x1bOH") == [le.HOME] * 3
        assert parse_chunk("\x1b[F\x1b[4~\x1bOF") == [le.END] * 3
        assert parse_chunk("\x1b[3~") == [le.DELETE]

    def test_a_lone_escape_is_the_esc_key(self):
        assert parse_chunk("\x1b") == [le.ESC]

    def test_unknown_sequences_are_dropped(self):
        assert parse_chunk("a\x1b[5~b\x1b[1;5Cc") == ["a", "b", "c"]

    def test_trailing_escape_does_not_crash(self):
        assert parse_chunk("ab\x1b") == ["a", "b"]


class TestWrapping:
    COLS = 10

    def test_text_wraps_and_the_cursor_follows(self):
        s, e = Screen(self.COLS), LineEditor("> ")
        type_into(e, s, "abcdefghijklmno", self.COLS)  # 17 columns: two rows
        assert s.lines()[:2] == ["> abcdefgh", "ijklmno"]
        assert (s.r, s.c) == (1, 7)

    def test_backspace_crosses_back_over_the_wrap(self):
        s, e = Screen(self.COLS), LineEditor("> ")
        type_into(e, s, "abcdefghij", self.COLS)  # 12 columns
        type_into(e, s, [le.BACKSPACE] * 4, self.COLS)
        assert s.lines()[:2] == ["> abcdef", ""]
        assert (s.r, s.c) == (0, 8)

    def test_arrows_cross_the_wrap_in_both_directions(self):
        s, e = Screen(self.COLS), LineEditor("> ")
        type_into(e, s, "abcdefghij", self.COLS)
        type_into(e, s, [le.LEFT] * 3, self.COLS)  # onto the first row
        assert (s.r, s.c) == (0, 9)
        type_into(e, s, "X", self.COLS)
        assert s.lines()[:2] == ["> abcdefgX", "hij"]
        type_into(e, s, [le.RIGHT] * 3, self.COLS)
        assert (s.r, s.c) == (1, 3)

    def test_text_ending_exactly_on_the_last_column(self):
        s, e = Screen(self.COLS), LineEditor("> ")
        type_into(e, s, "abcdefgh", self.COLS)  # fills row 0 exactly
        assert s.lines()[0] == "> abcdefgh"
        assert (s.r, s.c) == (1, 0)
        type_into(e, s, [le.BACKSPACE], self.COLS)
        assert s.lines()[:2] == ["> abcdefg", ""]
        assert (s.r, s.c) == (0, 9)

    def test_a_width_change_starts_the_redraw_from_the_reflowed_row(self):
        """The terminal re-wraps the line when the window resizes; the cursor
        row from the old width would start the redraw in the wrong place."""
        e = LineEditor("> ")
        e.feed("abcdefghijklmnopqrstuvwxyz")  # 28 columns
        e.render(10)  # cursor on row 2 at 10 wide
        out = e.render(5)  # re-wrapped: 28 // 5 = row 5
        assert out.startswith("\x1b[5A")

    def test_a_pasted_url_longer_than_three_rows(self, monkeypatch):
        url = "https://drive.google.com/drive/folders/" + "A" * 40
        monkeypatch.setattr(le.clipboard, "read_text", lambda: url)
        s, e = Screen(self.COLS), LineEditor("> ")
        type_into(e, s, ["\x16"], self.COLS)
        assert "".join(s.lines()).replace("> ", "", 1) == url
        type_into(e, s, [le.HOME], self.COLS)
        assert (s.r, s.c) == (0, 2)
