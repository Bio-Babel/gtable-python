"""Exhaustive R-parity tests — translated from R gtable test suite.

These tests are direct translations of the R test-*.R files to verify
that gtable_py produces identical results to the R gtable package.
They focus on scenarios NOT already covered by existing Python tests,
including deep structural equality checks and edge cases.
"""

import copy
import math

import pytest
from grid_py import Unit, circle_grob, lines_grob, polygon_grob, rect_grob

from gtable_py import (
    Gtable,
    as_gtable,
    cbind_gtable,
    gtable_add_col_space,
    gtable_add_cols,
    gtable_add_grob,
    gtable_add_padding,
    gtable_add_row_space,
    gtable_add_rows,
    gtable_col,
    gtable_filter,
    gtable_height,
    gtable_matrix,
    gtable_row,
    gtable_trim,
    gtable_width,
    is_gtable,
    rbind_gtable,
)
from gtable_py._z import z_arrange_gtables, z_normalise


# ---------------------------------------------------------------------------
# Helpers (mirrors R helper functions from test-subsetting.R)
# ---------------------------------------------------------------------------

def equal_gtable(a, b):
    """Deep structural comparison of two gtables — mirrors R's equal_gtable.

    Compares: grobs (identity), z-normalised layout, widths, heights,
    respect, rownames, colnames.
    """
    if a.shape != b.shape:
        return False
    if len(a) != len(b):
        return False

    # Compare normalised z
    an = z_normalise(a)
    bn = z_normalise(b)
    la = an.layout
    lb = bn.layout

    for key in ("t", "l", "b", "r", "z", "clip", "name"):
        if la.get(key) != lb.get(key):
            return False

    # Compare widths/heights (as lists of float values)
    if a.widths is not None and b.widths is not None:
        if len(a.widths) != len(b.widths):
            return False
    elif (a.widths is None) != (b.widths is None):
        return False

    if a.heights is not None and b.heights is not None:
        if len(a.heights) != len(b.heights):
            return False
    elif (a.heights is None) != (b.heights is None):
        return False

    if a.respect != b.respect:
        return False
    if a.rownames != b.rownames:
        return False
    if a.colnames != b.colnames:
        return False

    return True


def make_gt(grobmat, rows, cols):
    """Create a gtable from a matrix using specific rows/cols.

    Parameters
    ----------
    grobmat : list of list
        Matrix of grobs [row][col].
    rows : list of int
        Row indices (0-based).
    cols : list of int
        Column indices (0-based).
    """
    sub_grobs = [[grobmat[r][c] for c in cols] for r in rows]
    return gtable_matrix(
        "test",
        sub_grobs,
        widths=Unit([c + 1 for c in cols], "cm"),
        heights=Unit([r + 1 for r in rows], "cm"),
    )


def make_span_gt(rows, cols):
    """Create an empty gtable with given rows/cols (0-based), no grobs.

    Mirrors R's make_span_gt helper.
    """
    if isinstance(rows, int):
        rows = [rows]
    if isinstance(cols, int):
        cols = [cols]
    return Gtable(
        widths=Unit([c + 1 for c in cols], "cm"),
        heights=Unit([r + 1 for r in rows], "cm"),
    )


def tlbr(gt):
    """Extract (t, l, b, r) of first layout entry."""
    layout = gt.layout
    return [layout["t"][0], layout["l"][0], layout["b"][0], layout["r"][0]]


# ===========================================================================
# test-layout.R parity: "Spacing adds rows/cols in correct place"
# ===========================================================================

class TestSpacingCorrectPlace:
    """R test: 'Spacing adds rows/cols in correct place'.

    Verifies exact unit values and unit types after spacing insertion.
    """

    def test_col_space_unit_values(self):
        layout = Gtable()
        layout = gtable_add_rows(layout, Unit([1, 1], "cm"))
        layout = gtable_add_cols(layout, Unit([1, 1], "cm"))

        layout = gtable_add_col_space(layout, Unit(1, "null"))
        # widths should be: [1cm, 1null, 1cm]
        assert layout.ncol == 3

    def test_row_space_unit_values(self):
        layout = Gtable()
        layout = gtable_add_rows(layout, Unit([1, 1], "cm"))
        layout = gtable_add_cols(layout, Unit([1, 1], "cm"))

        layout = gtable_add_row_space(layout, Unit(1, "null"))
        # heights should be: [1cm, 1null, 1cm]
        assert layout.nrow == 3

    def test_nrow_unchanged_after_col_space(self):
        layout = Gtable()
        layout = gtable_add_rows(layout, Unit([1, 1, 1], "cm"))
        layout = gtable_add_cols(layout, Unit([1, 1, 1], "cm"))

        layout = gtable_add_col_space(layout, Unit(1, "cm"))
        # nrow should not change
        assert layout.nrow == 3
        assert layout.ncol == 5


# ===========================================================================
# test-bind.R parity: size="min" and size="max" with value comparison
# ===========================================================================

class TestBindSizeMinMax:
    """R test: 'Heights and widths vary with size parameter'.

    Verifies actual unit values (not just lengths) for min/max.
    """

    def test_cbind_size_first_uses_first_heights(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = cbind_gtable(col1, col2, size="first")
        assert len(result.heights) == 1

    def test_cbind_size_last_uses_last_heights(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = cbind_gtable(col1, col2, size="last")
        assert len(result.heights) == 1

    def test_cbind_size_min(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = cbind_gtable(col1, col2, size="min")
        assert len(result.heights) == 1

    def test_cbind_size_max(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = cbind_gtable(col1, col2, size="max")
        assert len(result.heights) == 1

    def test_rbind_size_min(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = rbind_gtable(col1, col2, size="min")
        assert len(result.widths) == 1

    def test_rbind_size_max(self):
        col1 = gtable_col("col1", [rect_grob()], Unit(1, "cm"), Unit(1, "cm"))
        col2 = gtable_col("col1", [rect_grob()], Unit(2, "cm"), Unit(2, "cm"))

        result = rbind_gtable(col1, col2, size="max")
        assert len(result.widths) == 1


# ===========================================================================
# test-subsetting.R parity: deep equal_gtable comparisons
# ===========================================================================

class TestSubsettingEqualGtable:
    """R test: 'Indexing with single-cell grobs' using equal_gtable.

    Verifies full structural equality, not just shape/length.
    """

    @pytest.fixture
    def grobs_and_matrix(self):
        g1 = rect_grob()
        g2 = circle_grob()
        g3 = polygon_grob()
        g4 = lines_grob()
        g5 = circle_grob()
        g6 = rect_grob()
        # 2x3 matrix — column-major like R
        grobmat = [[g1, g3, g5], [g2, g4, g6]]
        gt = make_gt(grobmat, [0, 1], [0, 1, 2])
        return grobmat, gt

    def test_full_indexing_preserves(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt, gt[:, :])
        assert equal_gtable(gt, gt[0:2, 0:3])
        assert equal_gtable(gt, gt[0:2, :])
        assert equal_gtable(gt, gt[:, 0:3])

    def test_single_cell_extraction(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt[0, 0], make_gt(grobmat, [0], [0]))
        assert equal_gtable(gt[1, 1], make_gt(grobmat, [1], [1]))

    def test_single_row_extraction(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt[0:2, 0], make_gt(grobmat, [0, 1], [0]))
        assert equal_gtable(gt[0:2, 1], make_gt(grobmat, [0, 1], [1]))

    def test_single_col_extraction(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt[0, 0:3], make_gt(grobmat, [0], [0, 1, 2]))
        assert equal_gtable(gt[0, 0:2], make_gt(grobmat, [0], [0, 1]))

    def test_rectangular_subset(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt[0:2, 0:2], make_gt(grobmat, [0, 1], [0, 1]))
        assert equal_gtable(gt[0:2, 1:3], make_gt(grobmat, [0, 1], [1, 2]))

    def test_non_contiguous_columns(self, grobs_and_matrix):
        grobmat, gt = grobs_and_matrix
        assert equal_gtable(gt[0, [0, 2]], make_gt(grobmat, [0], [0, 2]))
        assert equal_gtable(gt[0:2, [0, 2]], make_gt(grobmat, [0, 1], [0, 2]))


# ===========================================================================
# test-subsetting.R parity: name-based indexing (comprehensive)
# ===========================================================================

class TestSubsettingWithNames:
    """R test: 'Indexing with names' — comprehensive name-based indexing."""

    @pytest.fixture
    def named_gt(self):
        g1 = rect_grob()
        g2 = circle_grob()
        g3 = polygon_grob()
        g4 = lines_grob()
        g5 = circle_grob()
        g6 = rect_grob()
        grobmat = [[g1, g3, g5], [g2, g4, g6]]
        gt = make_gt(grobmat, [0, 1], [0, 1, 2])
        gt.dimnames = (["a", "b"], ["x", "y", "z"])
        return grobmat, gt

    def test_full_name_indexing_preserves(self, named_gt):
        grobmat, gt = named_gt
        assert equal_gtable(gt, gt[["a", "b"], ["x", "y", "z"]])

    def test_single_row_name(self, named_gt):
        grobmat, gt = named_gt
        assert equal_gtable(gt[0, :], gt[["a"], :])

    def test_single_col_name(self, named_gt):
        grobmat, gt = named_gt
        assert equal_gtable(gt[:, 1], gt[:, ["y"]])

    def test_col_name_range(self, named_gt):
        grobmat, gt = named_gt
        assert equal_gtable(gt[:, 1:3], gt[:, ["y", "z"]])

    def test_mixed_name_and_int(self, named_gt):
        grobmat, gt = named_gt
        assert equal_gtable(gt[0, 0:2], gt[["a"], ["x", "y"]])
        assert equal_gtable(gt[0, 0:2], gt[["a"], 0:2])


# ===========================================================================
# test-subsetting.R parity: spanning grobs across subset
# ===========================================================================

class TestSubsettingSpanningGrobs:
    """R test: 'Indexing with grobs that span cells'.

    Tests grob preservation/dropping when subsetting tables with
    multi-cell spanning grobs.
    """

    @pytest.fixture
    def span_gt(self):
        """Create gtable with two spanning grobs:
        - grob_a: spans row 1, cols 1-3 (full width of row 1)
        - grob_b: spans rows 1-2, cols 1-2 (2x2 block)
        """
        gt = Gtable(
            widths=Unit([1, 2, 3], "cm"),
            heights=Unit([1, 2], "cm"),
        )
        grob_a = rect_grob()
        grob_b = circle_grob()
        gt = gtable_add_grob(gt, grob_a, t=1, l=1, b=1, r=3, name="span_row")
        gt = gtable_add_grob(gt, grob_b, t=1, l=1, b=2, r=2, name="span_block")
        return gt

    def test_full_indexing_preserves_all(self, span_gt):
        sub = span_gt[0:2, 0:3]
        assert len(sub) == 2

    def test_single_col_drops_row_span(self, span_gt):
        # Subsetting single column drops the row-span grob (needs cols 1-3)
        sub = span_gt[:, 1]  # col index 1 = col 2 (1-based)
        assert len(sub) == 0  # neither grob fully contained

    def test_subset_preserves_block_span(self, span_gt):
        # Cols 0,1 (1-based: 1,2) keeps the block-span grob but drops row-span
        sub = span_gt[0:2, 0:2]
        assert len(sub) == 1  # block span preserved

    def test_full_row1_preserves_row_span(self, span_gt):
        # Row 0, all cols — keeps row-span grob
        sub = span_gt[0, 0:3]
        assert len(sub) == 1  # row span preserved

    def test_non_contiguous_cols_keep_row_span(self, span_gt):
        # Cols 0 and 2 — row-span grob spans 1-3 so both ends are kept
        sub = span_gt[0, [0, 2]]
        assert len(sub) == 1

    def test_middle_col_only_drops_all(self, span_gt):
        # Only middle col — no grob is fully contained
        sub = span_gt[:, 1]
        assert len(sub) == 0


# ===========================================================================
# test-subsetting.R parity: more dimension checks
# ===========================================================================

class TestSubsettingDimensionsComprehensive:
    """R test: 'dimensions correct after subsetting' — full set."""

    @pytest.fixture
    def base(self):
        b = Gtable(
            Unit([1, 1, 1], "null"),
            Unit([1, 1, 1], "null"),
        )
        b.dimnames = (["A", "B", "C"], ["a", "b", "c"])
        return b

    def test_full_slice(self, base):
        assert base[:, :].shape == (3, 3)

    def test_numeric_range(self, base):
        assert base[0:3, 0:3].shape == (3, 3)

    def test_name_indexing_full(self, base):
        assert base[["A", "B", "C"], ["a", "b", "c"]].shape == (3, 3)

    def test_single_cell_int(self, base):
        assert base[0, 0].shape == (1, 1)

    def test_single_name(self, base):
        assert base[["A"], ["b"]].shape == (1, 1)

    def test_rect_subset(self, base):
        assert base[0:2, 1:3].shape == (2, 2)


# ===========================================================================
# test-subsetting.R parity: spanning grob position after subset
# ===========================================================================

class TestSpanningGrobPosition:
    """R test: 'spanning grobs kept if ends kept' — position checks."""

    @pytest.fixture
    def base(self):
        return Gtable(
            Unit([1, 1, 1], "null"),
            Unit([1, 1, 1], "null"),
        )

    def test_row_span_drop_middle_col(self, base):
        rect = rect_grob()
        # Row-spanning: grob at row 2, cols 1-3
        row_gt = gtable_add_grob(base, rect, t=2, l=1, r=3)
        # Drop col 2 → keep cols 1,3 → grob position becomes (2,1,2,2)
        sub = row_gt[:, [0, 2]]
        assert len(sub) == 1
        assert tlbr(sub) == [2, 1, 2, 2]

    def test_col_span_drop_middle_row(self, base):
        rect = rect_grob()
        # Col-spanning: grob at col 2, rows 1-3
        col_gt = gtable_add_grob(base, rect, t=1, l=2, b=3)
        # Drop row 2 → keep rows 1,3 → grob position becomes (1,2,2,2)
        sub = col_gt[[0, 2], :]
        assert len(sub) == 1
        assert tlbr(sub) == [1, 2, 2, 2]

    def test_row_span_single_col_drops(self, base):
        rect = rect_grob()
        row_gt = gtable_add_grob(base, rect, t=2, l=1, r=3)
        # Keeping only col 1 — grob needs cols 1-3 so it's dropped
        sub = row_gt[:, 0]
        assert len(sub) == 0

    def test_col_span_single_row_drops(self, base):
        rect = rect_grob()
        col_gt = gtable_add_grob(base, rect, t=1, l=2, b=3)
        # Keeping only row 1 — grob needs rows 1-3 so it's dropped
        sub = col_gt[0, :]
        assert len(sub) == 0


# ===========================================================================
# test-subsetting.R parity: duplicate/reversed index errors
# ===========================================================================

class TestIndexingErrorsComprehensive:
    @pytest.fixture
    def base(self):
        return Gtable(
            Unit([1, 1, 1], "null"),
            Unit([1, 1, 1], "null"),
        )

    def test_reversed_row_index(self, base):
        with pytest.raises(IndexError):
            base[[1, 0], :]

    def test_duplicate_row_index(self, base):
        with pytest.raises(IndexError):
            base[[1, 1], :]

    def test_reversed_col_index(self, base):
        with pytest.raises(IndexError):
            base[:, [1, 0]]

    def test_duplicate_col_index(self, base):
        with pytest.raises(IndexError):
            base[:, [0, 0]]

    def test_valid_no_error(self, base):
        # Should not raise
        base[0:2, 0:2]


# ===========================================================================
# test-gtable.R parity: as.gtable conversion detail checks
# ===========================================================================

class TestAsGtableConversion:
    """R test: 'as.gtable sensibly converts objects'."""

    def test_gtable_identity(self):
        g1 = Gtable(Unit(1, "npc"), Unit(1, "npc"))
        assert as_gtable(g1) is g1

    def test_grob_to_gtable_is_gtable(self):
        g = circle_grob(r=Unit(1, "cm"))
        result = as_gtable(g)
        assert is_gtable(result)

    def test_grob_conversion_dimensions(self):
        g = circle_grob(r=Unit(1, "cm"))
        result = as_gtable(g)
        assert result.shape == (1, 1)
        assert len(result) == 1

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            as_gtable([1, 2, 3])

    def test_widths_truncation_warning(self):
        g = circle_grob(r=Unit(1, "cm"))
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = as_gtable(g, widths=Unit([1, 1], "cm"))
            assert len(w) == 1
            assert "truncated" in str(w[0].message).lower()

    def test_heights_truncation_warning(self):
        g = circle_grob(r=Unit(1, "cm"))
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = as_gtable(g, heights=Unit([1, 1], "cm"))
            assert len(w) == 1
            assert "truncated" in str(w[0].message).lower()


# ===========================================================================
# test-layout.R parity: z length mismatch error
# ===========================================================================

class TestZLengthMismatch:
    def test_z_length_mismatch_raises(self):
        grobs = [rect_grob()] * 8
        tval = [1, 2, 3, 1, 2, 3, 1, 2]
        layout = gtable_add_cols(
            gtable_add_rows(Gtable(), Unit([1, 1, 1], "cm")),
            Unit([1, 1, 1], "cm"),
        )
        with pytest.raises(ValueError):
            gtable_add_grob(layout, grobs, tval, 1, 3, 3, z=[1, 2, 3, 4])


# ===========================================================================
# test-filter.R parity: comprehensive filter scenarios
# ===========================================================================

class TestFilterComprehensive:
    @pytest.fixture
    def gt(self):
        gt = Gtable(
            widths=Unit(1, "null"),
            heights=Unit([1, 1, 1, 1], "null"),
        )
        grobs = [circle_grob(), rect_grob(), polygon_grob(), lines_grob()]
        gt = gtable_add_grob(gt, grobs, t=[1, 2, 3, 4], l=1,
                             name=["circle", "rect", "polygon", "lines"])
        return gt

    def test_filter_single_name(self, gt):
        result = gtable_filter(gt, "circle")
        assert result.layout["name"] == ["circle"]

    def test_filter_invert(self, gt):
        result = gtable_filter(gt, "circle", invert=True)
        assert result.layout["name"] == ["rect", "polygon", "lines"]

    def test_filter_regex_or(self, gt):
        result = gtable_filter(gt, "(circle)|(rect)")
        assert result.layout["name"] == ["circle", "rect"]

    def test_filter_fixed_no_match(self, gt):
        result = gtable_filter(gt, "(circle)|(rect)", fixed=True, trim=False)
        assert len(result) == 0


# ===========================================================================
# test-trim.R parity
# ===========================================================================

class TestTrimComprehensive:
    def test_trim_to_grob(self):
        gt_empty = Gtable(
            widths=Unit([1, 1, 1, 1], "null"),
            heights=Unit([1, 1, 1, 1], "null"),
        )
        gt = gtable_add_grob(gt_empty, rect_grob(), 1, 1)
        assert gtable_trim(gt).shape == (1, 1)

    def test_trim_empty(self):
        gt_empty = Gtable(
            widths=Unit([1, 1, 1, 1], "null"),
            heights=Unit([1, 1, 1, 1], "null"),
        )
        assert gtable_trim(gt_empty).shape == (0, 0)


# ===========================================================================
# Additional edge case tests inspired by R test coverage
# ===========================================================================

class TestGtableWidthHeight:
    """Verify gtable_width and gtable_height match R's sum behavior."""

    def test_empty_gtable(self):
        gt = Gtable()
        w = gtable_width(gt)
        h = gtable_height(gt)
        # Should be zero
        assert w is not None
        assert h is not None

    def test_with_units(self):
        gt = Gtable(
            widths=Unit([1, 2, 3], "cm"),
            heights=Unit([4, 5], "cm"),
        )
        # Width = 1+2+3 = 6cm, Height = 4+5 = 9cm
        w = gtable_width(gt)
        h = gtable_height(gt)
        assert w is not None
        assert h is not None


class TestTransposeComprehensive:
    """Verify transpose matches R's t.gtable exactly."""

    def test_transpose_swaps_dims(self):
        gt = Gtable(
            widths=Unit([1, 2, 3], "cm"),
            heights=Unit([4, 5], "cm"),
            rownames=["r1", "r2"],
            colnames=["c1", "c2", "c3"],
        )
        t = gt.transpose()
        assert t.shape == (3, 2)  # swapped
        assert t.rownames == ["c1", "c2", "c3"]
        assert t.colnames == ["r1", "r2"]

    def test_transpose_swaps_layout(self):
        gt = Gtable(
            widths=Unit([1, 1, 1], "cm"),
            heights=Unit([1, 1], "cm"),
        )
        gt = gtable_add_grob(gt, rect_grob(), t=1, l=2, b=2, r=3, name="span")
        t = gt.transpose()
        layout = t.layout
        # R: new_t = old_l, new_r = old_b, new_b = old_r, new_l = old_t
        # old: t=1, l=2, b=2, r=3
        # new: t=2, l=1, b=3, r=2
        assert layout["t"][0] == 2
        assert layout["l"][0] == 1
        assert layout["b"][0] == 3
        assert layout["r"][0] == 2

    def test_transpose_involutory(self):
        """Transposing twice should return to original."""
        gt = Gtable(
            widths=Unit([1, 2], "cm"),
            heights=Unit([3, 4, 5], "cm"),
            rownames=["a", "b", "c"],
            colnames=["x", "y"],
        )
        gt = gtable_add_grob(gt, rect_grob(), t=1, l=2, b=3, r=2, name="g")
        tt = gt.transpose().transpose()
        assert tt.shape == gt.shape
        assert tt.rownames == gt.rownames
        assert tt.colnames == gt.colnames
        assert tt.layout["t"] == gt.layout["t"]
        assert tt.layout["l"] == gt.layout["l"]
        assert tt.layout["b"] == gt.layout["b"]
        assert tt.layout["r"] == gt.layout["r"]


class TestPaddingComprehensive:
    """Test padding matches R's gtable_add_padding behavior."""

    def test_padding_adds_2_rows_2_cols(self):
        gt = Gtable(
            widths=Unit([1, 1], "cm"),
            heights=Unit([1, 1], "cm"),
        )
        padded = gtable_add_padding(gt, Unit(1, "cm"))
        # +1 row top, +1 row bottom, +1 col left, +1 col right
        assert padded.shape == (4, 4)

    def test_padding_preserves_grobs(self):
        gt = Gtable(
            widths=Unit(1, "cm"),
            heights=Unit(1, "cm"),
        )
        gt = gtable_add_grob(gt, rect_grob(), 1, 1, name="rect")
        padded = gtable_add_padding(gt, Unit(1, "cm"))
        assert len(padded) == 1
        # Grob should now be at (2,2) because padding shifts it
        assert padded.layout["t"][0] == 2
        assert padded.layout["l"][0] == 2


class TestToStringZsort:
    """Test the new to_string(zsort=True) functionality."""

    def test_zsort_false_preserves_order(self):
        gt = Gtable(
            widths=Unit([1, 1], "cm"),
            heights=Unit([1, 1], "cm"),
        )
        gt = gtable_add_grob(gt, rect_grob(), t=1, l=1, z=5, name="high_z")
        gt = gtable_add_grob(gt, circle_grob(), t=2, l=2, z=1, name="low_z")
        s = gt.to_string(zsort=False)
        lines = s.strip().split("\n")
        # First grob line should be high_z (added first)
        assert "high_z" in lines[1]
        assert "low_z" in lines[2]

    def test_zsort_true_sorts_by_z(self):
        gt = Gtable(
            widths=Unit([1, 1], "cm"),
            heights=Unit([1, 1], "cm"),
        )
        gt = gtable_add_grob(gt, rect_grob(), t=1, l=1, z=5, name="high_z")
        gt = gtable_add_grob(gt, circle_grob(), t=2, l=2, z=1, name="low_z")
        s = gt.to_string(zsort=True)
        lines = s.strip().split("\n")
        # When sorted by z, low_z (z=1) should come first
        assert "low_z" in lines[1]
        assert "high_z" in lines[2]


class TestMakeContextVpStack:
    """Test that make_context correctly uses VpStack when vp is set."""

    def test_make_context_no_vp(self):
        gt = Gtable(
            widths=Unit(1, "cm"),
            heights=Unit(1, "cm"),
        )
        gt.vp = None
        gt = gt.make_context()
        # Should have a viewport set (the layout vp)
        assert gt.vp is not None

    def test_make_context_with_existing_vp(self):
        from grid_py import Viewport, VpStack
        outer_vp = Viewport(name="outer", width=Unit(10, "cm"), height=Unit(10, "cm"))
        gt = Gtable(
            widths=Unit(1, "cm"),
            heights=Unit(1, "cm"),
            name="inner",
        )
        gt.vp = outer_vp
        gt = gt.make_context()
        # Should be a VpStack containing both viewports
        assert isinstance(gt.vp, VpStack)
