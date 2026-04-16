"""Core Gtable class — a table of grid grobs."""

from __future__ import annotations

import copy
import math
import re
import warnings
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from grid_py import (
    GList,
    GTree,
    Gpar,
    GridLayout,
    Grob,
    Unit,
    Viewport,
    VpStack,
    absolute_size,
    grid_draw,
    grid_grill,
    grid_newpage,
    grid_rect,
    grid_show_layout,
    grob_height,
    grob_tree,
    grob_width,
    is_grob,
    is_unit,
    null_grob,
    set_children,
    unit_c,
)

from ._utils import (
    check_gtable,
    check_unit_arg,
    insert_unit,
    layout_nrow,
    layout_subset,
    neg_to_pos,
    new_layout,
)

__all__ = [
    "Gtable",
    "is_gtable",
    "as_gtable",
    "gtable_height",
    "gtable_width",
]


class Gtable(GTree):
    """A table of grid grobs with row/column layout.

    A Gtable captures all the information needed to layout grobs in a
    table structure. It supports row and column spanning and makes it
    easy to align and combine multiple tables.

    Parameters
    ----------
    widths : Unit, optional
        Column widths.
    heights : Unit, optional
        Row heights.
    respect : bool
        Whether to respect aspect ratio of null units.
    name : str
        Name of the table (used for the layout viewport).
    rownames : list of str or None
        Row names for character subsetting.
    colnames : list of str or None
        Column names for character subsetting.
    vp : Viewport or None
        An optional outer viewport.
    """

    def __init__(
        self,
        widths: Optional[Unit] = None,
        heights: Optional[Unit] = None,
        respect: bool = False,
        name: str = "layout",
        rownames: Optional[List[str]] = None,
        colnames: Optional[List[str]] = None,
        vp: Optional[Viewport] = None,
    ) -> None:
        if widths is not None and len(widths) > 0:
            check_unit_arg(widths, arg="widths")
        if heights is not None and len(heights) > 0:
            check_unit_arg(heights, arg="heights")

        # Store table metadata
        self._grobs: List[Grob] = []
        self._layout: Dict[str, list] = new_layout()
        self._widths: Optional[Unit] = widths
        self._heights: Optional[Unit] = heights
        self._respect: bool = respect
        self._rownames: Optional[List[str]] = list(rownames) if rownames is not None else None
        self._colnames: Optional[List[str]] = list(colnames) if colnames is not None else None

        # Reconstruct viewport if one was provided (mirrors R's gtable())
        actual_vp = vp
        if vp is not None:
            actual_vp = Viewport(
                name=name,
                x=vp.x if hasattr(vp, 'x') else None,
                y=vp.y if hasattr(vp, 'y') else None,
                width=vp.width if hasattr(vp, 'width') else None,
                height=vp.height if hasattr(vp, 'height') else None,
                just=vp.justification if hasattr(vp, 'justification') else None,
                gp=vp.gp if hasattr(vp, 'gp') else None,
                xscale=vp.xscale if hasattr(vp, 'xscale') else None,
                yscale=vp.yscale if hasattr(vp, 'yscale') else None,
                angle=vp.angle if hasattr(vp, 'angle') else 0,
                clip=vp.clip if hasattr(vp, 'clip') else None,
            )

        super().__init__(name=name, vp=actual_vp)

    # -- Properties -----------------------------------------------------------

    @property
    def grobs(self) -> List[Grob]:
        """List of grobs in this table."""
        return self._grobs

    @grobs.setter
    def grobs(self, value: List[Grob]) -> None:
        self._grobs = list(value)

    @property
    def layout(self) -> Dict[str, list]:
        """Layout data (dict with keys t, l, b, r, z, clip, name)."""
        return self._layout

    @layout.setter
    def layout(self, value: Dict[str, list]) -> None:
        self._layout = value

    @property
    def widths(self) -> Optional[Unit]:
        """Column widths."""
        return self._widths

    @widths.setter
    def widths(self, value: Optional[Unit]) -> None:
        self._widths = value

    @property
    def heights(self) -> Optional[Unit]:
        """Row heights."""
        return self._heights

    @heights.setter
    def heights(self, value: Optional[Unit]) -> None:
        self._heights = value

    @property
    def respect(self) -> bool:
        """Whether to respect aspect ratio of null units."""
        return self._respect

    @respect.setter
    def respect(self, value: bool) -> None:
        self._respect = value

    @property
    def rownames(self) -> Optional[List[str]]:
        """Row names."""
        return self._rownames

    @rownames.setter
    def rownames(self, value: Optional[List[str]]) -> None:
        self._rownames = list(value) if value is not None else None

    @property
    def colnames(self) -> Optional[List[str]]:
        """Column names."""
        return self._colnames

    @colnames.setter
    def colnames(self, value: Optional[List[str]]) -> None:
        self._colnames = list(value) if value is not None else None

    # -- Dimension protocol ---------------------------------------------------

    @property
    def shape(self) -> Tuple[int, int]:
        """Return (nrow, ncol) like ``dim()`` in R.

        Returns
        -------
        tuple of int
            (number of rows, number of columns).
        """
        return (self.nrow, self.ncol)

    @property
    def ncol(self) -> int:
        """Number of columns."""
        return len(self._widths) if self._widths is not None else 0

    @property
    def nrow(self) -> int:
        """Number of rows."""
        return len(self._heights) if self._heights is not None else 0

    @property
    def dimnames(self) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """Return (rownames, colnames).

        Returns
        -------
        tuple
            (rownames, colnames).
        """
        return (self._rownames, self._colnames)

    @dimnames.setter
    def dimnames(self, value: Tuple[Optional[List[str]], Optional[List[str]]]) -> None:
        """Set (rownames, colnames).

        Parameters
        ----------
        value : tuple
            (rownames, colnames).
        """
        rn, cn = value
        if rn is not None:
            rn = list(rn)
            if len(set(rn)) != len(rn):
                raise ValueError("rownames must be distinct")
        if cn is not None:
            cn = list(cn)
            if len(set(cn)) != len(cn):
                raise ValueError("colnames must be distinct")
        self._rownames = rn
        self._colnames = cn

    def __len__(self) -> int:
        """Return number of grobs."""
        return len(self._grobs)

    # -- Repr / str -----------------------------------------------------------

    def to_string(self, zsort: bool = False) -> str:
        """Format the table as a human-readable string.

        Parameters
        ----------
        zsort : bool
            If True, sort output rows by z value (matches R's
            ``print.gtable(x, zsort=TRUE)``).

        Returns
        -------
        str
            Formatted string.
        """
        nrow, ncol = self.shape
        n_grobs = len(self._grobs)
        header = f'TableGrob ({nrow} x {ncol}) "{self.name}": {n_grobs} grobs'
        if layout_nrow(self._layout) == 0:
            return header

        lines = [header]
        layout = self._layout
        indices = list(range(layout_nrow(layout)))
        if zsort:
            indices.sort(key=lambda i: layout["z"][i])
        for i in indices:
            t, b = layout["t"][i], layout["b"][i]
            l, r = layout["l"][i], layout["r"][i]
            z = layout["z"][i]
            gname = layout["name"][i]
            grob_str = str(self._grobs[i]) if i < len(self._grobs) else "?"
            lines.append(
                f"  z={z}  ({t}-{b},{l}-{r})  {gname}  {grob_str}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.to_string(zsort=False)

    # -- Transpose ------------------------------------------------------------

    def transpose(self) -> "Gtable":
        """Transpose the table (swap rows and columns).

        Returns
        -------
        Gtable
            Transposed table.
        """
        new = copy.copy(self)
        layout = copy.deepcopy(self._layout)
        old_t = layout["t"][:]
        old_l = layout["l"][:]
        old_b = layout["b"][:]
        old_r = layout["r"][:]
        layout["t"] = old_l
        layout["l"] = old_t
        layout["b"] = old_r
        layout["r"] = old_b
        new._layout = layout
        new._widths = copy.copy(self._heights)
        new._heights = copy.copy(self._widths)
        new._rownames = copy.copy(self._colnames)
        new._colnames = copy.copy(self._rownames)
        new._grobs = list(self._grobs)
        return new

    # -- Subscript (R's [.gtable) ---------------------------------------------

    def __getitem__(self, key: Any) -> "Gtable":
        """Subset the table by row/column indices or names.

        Supports ``gt[rows, cols]`` where *rows* and *cols* can be
        integers (0-based), slices, lists of ints, or lists of names.

        Parameters
        ----------
        key : tuple
            ``(row_selector, col_selector)``.

        Returns
        -------
        Gtable
            Subsetted table.
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise IndexError("Gtable requires 2-d indexing: gt[rows, cols]")

        row_sel, col_sel = key

        # Resolve to 1-based integer lists
        rows_1based = self._resolve_index(row_sel, self.nrow, self._rownames)
        cols_1based = self._resolve_index(col_sel, self.ncol, self._colnames)

        # Check monotonically increasing
        rows_valid = [r for r in rows_1based if r is not None]
        cols_valid = [c for c in cols_1based if c is not None]
        if len(rows_valid) > 1 and any(
            rows_valid[i + 1] <= rows_valid[i] for i in range(len(rows_valid) - 1)
        ):
            raise IndexError("`rows` and `cols` must be increasing sequences")
        if len(cols_valid) > 1 and any(
            cols_valid[i + 1] <= cols_valid[i] for i in range(len(cols_valid) - 1)
        ):
            raise IndexError("`rows` and `cols` must be increasing sequences")

        x = copy.copy(self)
        x._grobs = list(self._grobs)
        x._layout = copy.deepcopy(self._layout)
        x._heights = copy.copy(self._heights)
        x._widths = copy.copy(self._widths)
        x._rownames = copy.copy(self._rownames)
        x._colnames = copy.copy(self._colnames)

        # Boolean masks for which original rows/cols are kept
        row_set = set(rows_valid)
        col_set = set(cols_valid)

        # Subset heights/widths/names
        x._heights = _unit_subset(self._heights, rows_valid)
        x._widths = _unit_subset(self._widths, cols_valid)
        if self._rownames is not None:
            x._rownames = [self._rownames[r - 1] for r in rows_valid]
        if self._colnames is not None:
            x._colnames = [self._colnames[c - 1] for c in cols_valid]

        layout = x._layout

        # Keep grobs whose full extent is within the selected rows/cols
        keep = []
        for i in range(layout_nrow(layout)):
            t, b = layout["t"][i], layout["b"][i]
            l, r = layout["l"][i], layout["r"][i]
            if t in row_set and b in row_set and l in col_set and r in col_set:
                keep.append(True)
            else:
                keep.append(False)
        x._grobs = [g for g, k in zip(x._grobs, keep) if k]

        # Compute row/col adjustments (cumulative count of removed rows before each pos)
        all_rows = list(range(1, self.nrow + 1))
        row_keep = [r in row_set for r in all_rows]
        adj_rows = _cumsum_not(row_keep)

        all_cols = list(range(1, self.ncol + 1))
        col_keep = [c in col_set for c in all_cols]
        adj_cols = _cumsum_not(col_keep)

        # Adjust layout positions
        for i in range(layout_nrow(layout)):
            layout["t"][i] = layout["t"][i] - adj_rows[layout["t"][i] - 1]
            layout["b"][i] = layout["b"][i] - adj_rows[layout["b"][i] - 1]
            layout["l"][i] = layout["l"][i] - adj_cols[layout["l"][i] - 1]
            layout["r"][i] = layout["r"][i] - adj_cols[layout["r"][i] - 1]

        x._layout = layout_subset(layout, keep)

        # Handle NA rows (names not found) — add zero-height rows
        from ._add_rows_cols import gtable_add_cols, gtable_add_rows
        for idx, val in enumerate(rows_1based):
            if val is None:
                x = gtable_add_rows(x, Unit(0, "mm"), pos=idx)
        for idx, val in enumerate(cols_1based):
            if val is None:
                x = gtable_add_cols(x, Unit(0, "mm"), pos=idx)

        return x

    def _resolve_index(
        self,
        sel: Any,
        size: int,
        names: Optional[List[str]],
    ) -> List[Optional[int]]:
        """Resolve a selector to a list of 1-based indices.

        Parameters
        ----------
        sel : int, slice, list, or str
            Selector.
        size : int
            Dimension size.
        names : list of str or None
            Dimension names.

        Returns
        -------
        list of int or None
            1-based indices (None for missing names).
        """
        if isinstance(sel, slice):
            start, stop, step = sel.indices(size)
            return [i + 1 for i in range(start, stop, step or 1)]
        if isinstance(sel, int):
            if sel < 0:
                sel = size + sel
            return [sel + 1]
        if isinstance(sel, (list, tuple)):
            result = []
            for item in sel:
                if isinstance(item, str):
                    if names is not None and item in names:
                        result.append(names.index(item) + 1)
                    else:
                        result.append(None)
                elif isinstance(item, int):
                    idx = item if item >= 0 else size + item
                    result.append(idx + 1)
                else:
                    raise IndexError(f"Invalid index type: {type(item)}")
            return result
        raise IndexError(f"Invalid selector type: {type(sel)}")

    # -- Plot -----------------------------------------------------------------

    def plot(self, bg: Optional[str] = None, grill: Optional[str] = None) -> None:
        """Draw the table.

        Parameters
        ----------
        bg : str or None
            Background fill colour.
        grill : str or None
            Grid line colour.
        """
        grid_newpage()
        if bg is not None:
            grid_rect(gp=Gpar(fill=bg))
        if grill is not None:
            grill_seq = [i / 19.0 for i in range(20)]  # seq(0, 1, length.out=20)
            grid_grill(h=grill_seq, v=grill_seq, gp=Gpar(col=grill))
        grid_draw(self)

    # -- Grid hooks (override GTree methods) ----------------------------------

    def width_details(self) -> Unit:
        """Return absolute width for grid rendering.

        Returns
        -------
        Unit
            Absolute width.
        """
        return absolute_size(gtable_width(self))

    def height_details(self) -> Unit:
        """Return absolute height for grid rendering.

        Returns
        -------
        Unit
            Absolute height.
        """
        return absolute_size(gtable_height(self))

    def make_context(self) -> "Gtable":
        """Set up viewport with layout for rendering.

        Returns
        -------
        Gtable
            Self with viewport configured.
        """
        layout_vp = Viewport(
            layout=_gtable_layout(self),
            name=self.name,
        )
        if self.vp is None:
            self.vp = layout_vp
        else:
            self.vp = VpStack(self.vp, layout_vp)
        return self

    def make_content(self) -> "Gtable":
        """Prepare children for rendering.

        Mirrors R's ``makeContent.gtable`` (gtable-package.R):
        wraps each grob in a grobTree with its own child viewport,
        ordered by z.

        Returns
        -------
        Gtable
            Self with children set.
        """
        # --- Wrap children with layout-positioned viewports
        layout = self._layout
        n = layout_nrow(layout)
        children = []
        for i in range(n):
            vp_name = (
                f"{layout['name'][i]}."
                f"{layout['t'][i]}-{layout['r'][i]}-"
                f"{layout['b'][i]}-{layout['l'][i]}"
            )
            child_viewport = Viewport(
                name=vp_name,
                layout_pos_row=(layout["t"][i], layout["b"][i]),
                layout_pos_col=(layout["l"][i], layout["r"][i]),
                clip=layout["clip"][i],
            )
            children.append((layout["z"][i], i, vp_name, child_viewport))

        # Sort by z
        children.sort(key=lambda c: c[0])
        grob_trees = []
        for z_val, idx, vp_name, child_vp in children:
            gt = grob_tree(self._grobs[idx], name=vp_name, vp=child_vp)
            grob_trees.append(gt)

        gl = GList(*grob_trees)
        self = set_children(self, gl)
        return self

    # -- Copy support ---------------------------------------------------------

    def __copy__(self) -> "Gtable":
        new = Gtable.__new__(Gtable)
        new._grobs = list(self._grobs)
        new._layout = copy.deepcopy(self._layout)
        new._widths = copy.copy(self._widths)
        new._heights = copy.copy(self._heights)
        new._respect = self._respect
        new._rownames = list(self._rownames) if self._rownames is not None else None
        new._colnames = list(self._colnames) if self._colnames is not None else None
        new.name = self.name
        new.vp = self.vp
        new.gp = self.gp
        return new


# ---------------------------------------------------------------------------
# Module-level functions
# ---------------------------------------------------------------------------


def is_gtable(x: Any) -> bool:
    """Check if *x* is a Gtable.

    Parameters
    ----------
    x : Any
        Object to test.

    Returns
    -------
    bool
        True if *x* is a Gtable instance.
    """
    return isinstance(x, Gtable)


def as_gtable(
    x: Any,
    *,
    widths: Optional[Unit] = None,
    heights: Optional[Unit] = None,
) -> Gtable:
    """Convert an object to a Gtable.

    Parameters
    ----------
    x : Gtable, Grob, or other
        Object to convert.
    widths : Unit or None
        Width for single-cell wrapping (Grob only).
    heights : Unit or None
        Height for single-cell wrapping (Grob only).

    Returns
    -------
    Gtable
        Resulting table.

    Raises
    ------
    TypeError
        If *x* cannot be converted.
    """
    if isinstance(x, Gtable):
        return x
    if is_grob(x):
        if widths is not None and len(widths) > 1:
            widths = widths[0:1]
            warnings.warn("`widths` truncated to length 1.", stacklevel=2)
        if heights is not None and len(heights) > 1:
            heights = heights[0:1]
            warnings.warn("`heights` truncated to length 1.", stacklevel=2)
        w = widths if widths is not None else grob_width(x)
        h = heights if heights is not None else grob_height(x)
        from ._add_grob import gtable_add_grob
        table = Gtable(widths=w, heights=h)
        return gtable_add_grob(table, x, t=1, l=1, b=1, r=1)
    raise TypeError(f"Cannot convert {type(x).__name__} to a Gtable.")


def gtable_height(x: Gtable) -> Unit:
    """Return the total height of a gtable.

    Parameters
    ----------
    x : Gtable
        A gtable object.

    Returns
    -------
    Unit
        Sum of row heights.
    """
    if x.heights is None or len(x.heights) == 0:
        return Unit(0, "cm")
    return sum(x.heights)


def gtable_width(x: Gtable) -> Unit:
    """Return the total width of a gtable.

    Parameters
    ----------
    x : Gtable
        A gtable object.

    Returns
    -------
    Unit
        Sum of column widths.
    """
    if x.widths is None or len(x.widths) == 0:
        return Unit(0, "cm")
    return sum(x.widths)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _gtable_layout(x: Gtable) -> GridLayout:
    """Create a grid.layout from a Gtable.

    Parameters
    ----------
    x : Gtable
        A gtable object.

    Returns
    -------
    GridLayout
        Grid layout object.
    """
    nrow = x.nrow
    ncol = x.ncol
    heights = x.heights if x.heights is not None else Unit(1, "null")
    widths = x.widths if x.widths is not None else Unit(1, "null")
    return GridLayout(
        nrow=nrow,
        heights=heights,
        ncol=ncol,
        widths=widths,
        respect=x.respect,
    )


def _unit_subset(u: Unit, indices_1based: List[int]) -> Unit:
    """Subset a Unit by 1-based indices.

    Parameters
    ----------
    u : Unit
        Input unit vector.
    indices_1based : list of int
        1-based indices to select.

    Returns
    -------
    Unit
        Subsetted unit vector.
    """
    if not indices_1based:
        return Unit([], "cm")
    # Convert to 0-based for Python indexing
    parts = [u[i - 1:i] for i in indices_1based]
    if len(parts) == 1:
        return parts[0]
    return unit_c(*parts)


def _cumsum_not(mask: List[bool]) -> List[int]:
    """Cumulative sum of ``not mask``.

    Parameters
    ----------
    mask : list of bool
        Boolean mask.

    Returns
    -------
    list of int
        Cumulative count of False values.
    """
    result = []
    total = 0
    for m in mask:
        if not m:
            total += 1
        result.append(total)
    return result
