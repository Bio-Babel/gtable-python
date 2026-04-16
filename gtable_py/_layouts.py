"""Convenience constructors for common gtable layouts."""

from __future__ import annotations

import math
from typing import Any, List, Optional, Union

from grid_py import Unit, grid_show_layout, null_grob

from ._add_grob import gtable_add_grob
from ._gtable import Gtable, _gtable_layout
from ._utils import check_gtable, height_cm, width_cm

__all__ = [
    "gtable_col",
    "gtable_row",
    "gtable_matrix",
    "gtable_row_spacer",
    "gtable_col_spacer",
    "gtable_show_layout",
]


def gtable_col(
    name: str,
    grobs: List[Any],
    width: Optional[Unit] = None,
    heights: Optional[Unit] = None,
    z: Optional[List[float]] = None,
    vp: Any = None,
    clip: str = "inherit",
) -> Gtable:
    """Create a single-column gtable.

    Parameters
    ----------
    name : str
        Table name.
    grobs : list of Grob
        Grobs to stack vertically.
    width : Unit or None
        Column width. Defaults to max grob width in cm.
    heights : Unit or None
        Row heights. Defaults to ``1 null`` per grob.
    z : list of float or None
        Z-order per grob.
    vp : Viewport or None
        Optional viewport.
    clip : str
        Clipping mode.

    Returns
    -------
    Gtable
        Single-column table.
    """
    if width is None:
        max_w = max(width_cm(g) for g in grobs) if grobs else 1.0
        width = Unit(max_w, "cm")
    if heights is None:
        heights = Unit([1] * len(grobs), "null")

    if z is not None and len(z) != len(grobs):
        raise ValueError("`z` must be None or the same length as `grobs`")
    if z is None:
        z_val: Union[float, List[float]] = math.inf
    else:
        z_val = z

    # Use names of grobs as rownames if available
    rnames = None
    if isinstance(grobs, dict):
        rnames = list(grobs.keys())
        grobs = list(grobs.values())

    table = Gtable(
        widths=width,
        heights=heights,
        name=name,
        vp=vp,
        rownames=rnames,
    )
    table = gtable_add_grob(
        table,
        grobs,
        t=list(range(1, len(grobs) + 1)),
        l=1,
        z=z_val,
        clip=clip,
    )
    return table


def gtable_row(
    name: str,
    grobs: List[Any],
    height: Optional[Unit] = None,
    widths: Optional[Unit] = None,
    z: Optional[List[float]] = None,
    vp: Any = None,
    clip: str = "inherit",
) -> Gtable:
    """Create a single-row gtable.

    Parameters
    ----------
    name : str
        Table name.
    grobs : list of Grob
        Grobs to place side-by-side.
    height : Unit or None
        Row height. Defaults to max grob height in cm.
    widths : Unit or None
        Column widths. Defaults to ``1 null`` per grob.
    z : list of float or None
        Z-order per grob.
    vp : Viewport or None
        Optional viewport.
    clip : str
        Clipping mode.

    Returns
    -------
    Gtable
        Single-row table.
    """
    if height is None:
        max_h = max(height_cm(g) for g in grobs) if grobs else 1.0
        height = Unit(max_h, "cm")
    if widths is None:
        widths = Unit([1] * len(grobs), "null")

    if z is not None and len(z) != len(grobs):
        raise ValueError("`z` must be None or the same length as `grobs`")
    if z is None:
        z_val: Union[float, List[float]] = math.inf
    else:
        z_val = z

    cnames = None
    if isinstance(grobs, dict):
        cnames = list(grobs.keys())
        grobs = list(grobs.values())

    table = Gtable(
        widths=widths,
        heights=height,
        name=name,
        vp=vp,
        colnames=cnames,
    )
    table = gtable_add_grob(
        table,
        grobs,
        l=list(range(1, len(grobs) + 1)),
        t=1,
        z=z_val,
        clip=clip,
    )
    return table


def gtable_matrix(
    name: str,
    grobs: List[List[Any]],
    widths: Unit,
    heights: Unit,
    z: Optional[List[List[float]]] = None,
    respect: bool = False,
    clip: str = "on",
    vp: Any = None,
) -> Gtable:
    """Create a gtable from a matrix (list of lists) of grobs.

    Parameters
    ----------
    name : str
        Table name.
    grobs : list of list of Grob
        Matrix of grobs. ``grobs[row][col]``.
    widths : Unit
        Column widths.
    heights : Unit
        Row heights.
    z : list of list of float or None
        Z-order matrix.
    respect : bool
        Whether to respect aspect ratio.
    clip : str
        Clipping mode.
    vp : Viewport or None
        Optional viewport.

    Returns
    -------
    Gtable
        Matrix table.
    """
    nrow = len(grobs)
    ncol = len(grobs[0]) if nrow > 0 else 0

    if len(widths) != ncol:
        raise ValueError("`widths` must match the number of columns in `grobs`")
    if len(heights) != nrow:
        raise ValueError("`heights` must match the number of rows in `grobs`")
    if z is not None:
        if len(z) != nrow or any(len(row) != ncol for row in z):
            raise ValueError("`z` must have the same dimensions as `grobs`")

    # Flatten grobs and positions (column-major like R)
    flat_grobs = []
    flat_t = []
    flat_l = []
    flat_z: List[float] = []

    for col_idx in range(ncol):
        for row_idx in range(nrow):
            flat_grobs.append(grobs[row_idx][col_idx])
            flat_t.append(row_idx + 1)
            flat_l.append(col_idx + 1)
            if z is not None:
                flat_z.append(z[row_idx][col_idx])

    if z is None:
        z_val: Union[float, List[float]] = math.inf
    else:
        z_val = flat_z

    table = Gtable(
        widths=widths,
        heights=heights,
        name=name,
        respect=respect,
        vp=vp,
    )
    table = gtable_add_grob(
        table,
        flat_grobs,
        t=flat_t,
        l=flat_l,
        z=z_val,
        clip=clip,
    )
    return table


def gtable_row_spacer(widths: Unit) -> Gtable:
    """Create a zero-row gtable with given widths (row spacer).

    Parameters
    ----------
    widths : Unit
        Column widths.

    Returns
    -------
    Gtable
        Spacer table.
    """
    from ._add_rows_cols import gtable_add_cols
    return gtable_add_cols(Gtable(), widths)


def gtable_col_spacer(heights: Unit) -> Gtable:
    """Create a zero-column gtable with given heights (column spacer).

    Parameters
    ----------
    heights : Unit
        Row heights.

    Returns
    -------
    Gtable
        Spacer table.
    """
    from ._add_rows_cols import gtable_add_rows
    return gtable_add_rows(Gtable(), heights)


def gtable_show_layout(x: Gtable, **kwargs: Any) -> None:
    """Visualise the layout of a gtable.

    Parameters
    ----------
    x : Gtable
        Target table.
    **kwargs
        Passed to ``grid_py.grid_show_layout``.
    """
    check_gtable(x)
    grid_show_layout(_gtable_layout(x), **kwargs)
