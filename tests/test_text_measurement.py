"""Tests for text/grob size measurement through gtable.

These tests verify that gtable_py correctly measures grob sizes
(width_cm, height_cm) and uses them in auto-sizing layouts
(gtable_col, gtable_row, as_gtable). This is the key code path
for text measurement in gtable.
"""

import pytest
from grid_py import Unit, circle_grob, rect_grob, text_grob

from gtable_py import as_gtable, gtable_col, gtable_row, is_gtable
from gtable_py._utils import height_cm, width_cm


# ---------------------------------------------------------------------------
# width_cm / height_cm — the core measurement functions
# ---------------------------------------------------------------------------

class TestWidthCm:
    def test_text_grob_nonzero(self):
        tg = text_grob("Hello World")
        w = width_cm(tg)
        assert isinstance(w, float)
        assert w > 0

    def test_unit_returns_value(self):
        u = Unit(3.5, "cm")
        assert width_cm(u) == pytest.approx(3.5)

    def test_list_of_grobs_returns_max(self):
        short = text_grob("Hi")
        long = text_grob("Hello World, this is a longer string")
        w = width_cm([short, long])
        w_short = width_cm(short)
        w_long = width_cm(long)
        assert w == pytest.approx(max(w_short, w_long))

    def test_empty_list_returns_zero(self):
        assert width_cm([]) == 0.0

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            width_cm(42)


class TestHeightCm:
    def test_text_grob_nonzero(self):
        tg = text_grob("Hello World")
        h = height_cm(tg)
        assert isinstance(h, float)
        assert h > 0

    def test_unit_returns_value(self):
        u = Unit(2.0, "cm")
        assert height_cm(u) == pytest.approx(2.0)

    def test_list_of_grobs_returns_max(self):
        t1 = text_grob("A")
        t2 = text_grob("B")
        h = height_cm([t1, t2])
        h1 = height_cm(t1)
        h2 = height_cm(t2)
        assert h == pytest.approx(max(h1, h2))

    def test_empty_list_returns_zero(self):
        assert height_cm([]) == 0.0

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            height_cm("bad")


# ---------------------------------------------------------------------------
# gtable_col / gtable_row auto-sizing from grob measurements
# ---------------------------------------------------------------------------

class TestGtableColAutoWidth:
    """When width=None, gtable_col should compute width from grobs."""

    def test_text_grob_auto_width(self):
        grobs = [text_grob("Hello"), text_grob("World!")]
        col = gtable_col("test", grobs)
        # Width should be auto-computed, not fallback 1.0
        expected_max = max(width_cm(g) for g in grobs)
        actual = width_cm(col.widths)
        assert actual == pytest.approx(expected_max, rel=1e-3)

    def test_explicit_width_overrides(self):
        grobs = [text_grob("Hello")]
        col = gtable_col("test", grobs, width=Unit(5, "cm"))
        assert width_cm(col.widths) == pytest.approx(5.0)

    def test_auto_width_not_one(self):
        """Regression test: auto-width must NOT be the old fallback 1.0."""
        grobs = [text_grob("This is a moderately long piece of text")]
        col = gtable_col("test", grobs)
        w = width_cm(col.widths)
        # A long text should produce a width much larger than 1.0cm
        assert w > 1.5


class TestGtableRowAutoHeight:
    """When height=None, gtable_row should compute height from grobs."""

    def test_text_grob_auto_height(self):
        grobs = [text_grob("Hello"), text_grob("World!")]
        row = gtable_row("test", grobs)
        expected_max = max(height_cm(g) for g in grobs)
        actual = height_cm(row.heights)
        assert actual == pytest.approx(expected_max, rel=1e-3)

    def test_explicit_height_overrides(self):
        grobs = [text_grob("Hello")]
        row = gtable_row("test", grobs, height=Unit(3, "cm"))
        assert height_cm(row.heights) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# as_gtable — grob conversion with auto width/height
# ---------------------------------------------------------------------------

class TestAsGtableTextGrob:
    def test_text_grob_produces_gtable(self):
        tg = text_grob("Test")
        result = as_gtable(tg)
        assert is_gtable(result)
        assert result.shape == (1, 1)
        assert len(result) == 1

    def test_text_grob_auto_dimensions(self):
        tg = text_grob("Test")
        result = as_gtable(tg)
        # Width and height should reflect text measurement
        w = width_cm(result.widths)
        h = height_cm(result.heights)
        assert w > 0
        assert h > 0


# ---------------------------------------------------------------------------
# Multiple text grobs with different sizes
# ---------------------------------------------------------------------------

class TestTextSizeVariation:
    def test_longer_text_wider(self):
        short = text_grob("Hi")
        long = text_grob("Hello World, this is long")
        assert width_cm(long) > width_cm(short)

    def test_col_width_tracks_widest(self):
        short = text_grob("Hi")
        long = text_grob("Hello World, this is long")
        col = gtable_col("test", [short, long])
        # Width should match the longer text
        assert width_cm(col.widths) == pytest.approx(width_cm(long), rel=1e-3)
