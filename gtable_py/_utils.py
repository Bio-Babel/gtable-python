"""Internal utility functions for gtable_py."""

from __future__ import annotations

import copy
import re
import warnings
from typing import Any, Dict, List, Optional, Sequence, Union

from grid_py import (
    Grob,
    Unit,
    convert_height,
    convert_width,
    grob_height,
    grob_width,
    is_grob,
    is_unit,
    unit_c,
    unit_pmax,
    unit_pmin,
)

__all__: list[str] = []


# ---------------------------------------------------------------------------
# Layout (lightweight data-frame substitute)
# ---------------------------------------------------------------------------

def new_layout(
    t: Optional[List[int]] = None,
    l: Optional[List[int]] = None,
    b: Optional[List[int]] = None,
    r: Optional[List[int]] = None,
    z: Optional[List[float]] = None,
    clip: Optional[List[str]] = None,
    name: Optional[List[str]] = None,
) -> Dict[str, list]:
    """Create a layout dict (analogue of R's layout data.frame).

    All position values are **1-based** to match R semantics.

    Parameters
    ----------
    t, l, b, r : list of int, optional
        Top, left, bottom, right extents.
    z : list of float, optional
        Z-ordering values.
    clip : list of str, optional
        Clip mode per grob ("on", "off", "inherit").
    name : list of str, optional
        Grob names.

    Returns
    -------
    dict
        Layout with keys ``t``, ``l``, ``b``, ``r``, ``z``, ``clip``, ``name``.
    """
    return {
        "t": list(t) if t is not None else [],
        "l": list(l) if l is not None else [],
        "b": list(b) if b is not None else [],
        "r": list(r) if r is not None else [],
        "z": list(z) if z is not None else [],
        "clip": list(clip) if clip is not None else [],
        "name": list(name) if name is not None else [],
    }


def layout_nrow(layout: Dict[str, list]) -> int:
    """Return number of rows in a layout."""
    return len(layout["t"])


def layout_subset(layout: Dict[str, list], mask: List[bool]) -> Dict[str, list]:
    """Subset layout by boolean mask.

    Parameters
    ----------
    layout : dict
        Layout dict.
    mask : list of bool
        Boolean mask.

    Returns
    -------
    dict
        Filtered layout.
    """
    return {
        k: [v for v, m in zip(vals, mask) if m]
        for k, vals in layout.items()
    }


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def check_gtable(x: Any, *, arg: str = "x") -> None:
    """Raise TypeError if *x* is not a Gtable instance.

    Parameters
    ----------
    x : Any
        Object to check.
    arg : str
        Argument name for error messages.
    """
    # Avoid circular import — use duck-typing check.
    if not _is_gtable(x):
        raise TypeError(f"`{arg}` must be a Gtable object, got {type(x).__name__}")


def check_unit_arg(x: Any, *, arg: str = "x") -> None:
    """Raise TypeError if *x* is not a grid_py Unit.

    Parameters
    ----------
    x : Any
        Object to check.
    arg : str
        Argument name for error messages.
    """
    if not is_unit(x):
        raise TypeError(f"`{arg}` must be a Unit vector, got {type(x).__name__}")


def _is_gtable(x: Any) -> bool:
    """Check if *x* is a Gtable (duck-typed to avoid circular import)."""
    return hasattr(x, "_layout") and hasattr(x, "_widths") and hasattr(x, "_heights")


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------

def neg_to_pos(x: int, max_val: int) -> int:
    """Convert negative index to positive (R-style).

    In R gtable, ``-1`` means "at the end" (after last element).
    ``0`` means "before first element".

    Parameters
    ----------
    x : int
        Index (may be negative).
    max_val : int
        Maximum dimension.

    Returns
    -------
    int
        Positive index.
    """
    if x >= 0:
        return x
    return max_val + 1 + x


def neg_to_pos_vec(xs: List[int], max_val: int) -> List[int]:
    """Vectorised version of :func:`neg_to_pos`.

    Parameters
    ----------
    xs : list of int
        Indices.
    max_val : int
        Maximum dimension.

    Returns
    -------
    list of int
        Positive indices.
    """
    return [neg_to_pos(x, max_val) for x in xs]


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def insert_unit(x: Any, values: Any, after: Optional[int] = None) -> Unit:
    """Insert *values* into unit vector *x* after position *after*.

    Parameters
    ----------
    x : Unit or None
        Original unit vector.
    values : Unit or None
        Units to insert.
    after : int or None
        0-based insertion point. ``None`` means append.

    Returns
    -------
    Unit
        Combined unit vector.
    """
    x_len = len(x) if x is not None else 0
    v_len = len(values) if values is not None else 0
    if x_len == 0:
        return values
    if v_len == 0:
        return x
    if after is None:
        after = x_len
    if after <= 0:
        return unit_c(values, x)
    if after >= x_len:
        return unit_c(x, values)
    return unit_c(x[0:after], values, x[after:x_len])


def compare_unit(x: Unit, y: Unit, comp: str) -> Unit:
    """Element-wise min/max of two unit vectors.

    Parameters
    ----------
    x, y : Unit
        Unit vectors of the same length.
    comp : str
        ``"min"`` or ``"max"``.

    Returns
    -------
    Unit
        Result of element-wise comparison.
    """
    y_len = len(y) if y is not None else 0
    x_len = len(x) if x is not None else 0
    if y_len == 0:
        return x
    if x_len == 0:
        return y
    if comp == "min":
        return unit_pmin(x, y)
    if comp == "max":
        return unit_pmax(x, y)
    raise ValueError(f"comp must be 'min' or 'max', got {comp!r}")


def width_cm(x: Any) -> float:
    """Convert grob or unit to width in cm.

    Parameters
    ----------
    x : Grob or Unit or list
        Input.

    Returns
    -------
    float
        Width in cm.
    """
    if is_grob(x):
        val = convert_width(grob_width(x), "cm", valueOnly=True)
        return float(val[0]) if hasattr(val, '__len__') else float(val)
    if isinstance(x, (list, tuple)):
        return max(width_cm(item) for item in x) if x else 0.0
    if is_unit(x):
        val = convert_width(x, "cm", valueOnly=True)
        return float(val[0]) if hasattr(val, '__len__') else float(val)
    raise TypeError(f"Cannot compute width_cm for {type(x).__name__}")


def height_cm(x: Any) -> float:
    """Convert grob or unit to height in cm.

    Parameters
    ----------
    x : Grob or Unit or list
        Input.

    Returns
    -------
    float
        Height in cm.

    Notes
    -----
    R's ``height_cm`` uses ``convertWidth`` (not ``convertHeight``) for the
    grob branch.  For absolute units (cm, inches, …) the result is identical,
    but we mirror R exactly.
    """
    if is_grob(x):
        # R uses convertWidth(grobHeight(x), "cm", TRUE) — not convertHeight
        val = convert_width(grob_height(x), "cm", valueOnly=True)
        return float(val[0]) if hasattr(val, '__len__') else float(val)
    if isinstance(x, (list, tuple)):
        return max(height_cm(item) for item in x) if x else 0.0
    if is_unit(x):
        val = convert_height(x, "cm", valueOnly=True)
        return float(val[0]) if hasattr(val, '__len__') else float(val)
    raise TypeError(f"Cannot compute height_cm for {type(x).__name__}")


def len_same_or_1(x: Sequence, n: int) -> bool:
    """Check that *x* has length 1 or *n*.

    Parameters
    ----------
    x : Sequence
        Input.
    n : int
        Target length.

    Returns
    -------
    bool
        True if length is 1 or n.
    """
    return len(x) == 1 or len(x) == n
