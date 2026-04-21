"""
gtable_py — Python port of the R gtable package.

A gtable is a table of grid grobs (graphical objects) arranged in
a layout grid, supporting row/column spanning and composition.
"""

from ._add_grob import gtable_add_grob
from ._add_rows_cols import gtable_add_cols, gtable_add_rows
from ._add_space import gtable_add_col_space, gtable_add_row_space
from ._bind import cbind_gtable, rbind_gtable
from ._filter import gtable_filter
from ._gtable import Gtable, as_gtable, gtable_height, gtable_width, is_gtable
from ._layouts import (
    gtable_col,
    gtable_col_spacer,
    gtable_matrix,
    gtable_row,
    gtable_row_spacer,
    gtable_show_layout,
)
from ._padding import gtable_add_padding
from ._trim import gtable_trim

__version__ = "0.3.6.9000"
__r_commit__ = "c017439"

__all__ = [
    # Core class
    "Gtable",
    "is_gtable",
    "as_gtable",
    # Dimension queries
    "gtable_height",
    "gtable_width",
    # Manipulation
    "gtable_add_grob",
    "gtable_add_rows",
    "gtable_add_cols",
    "gtable_add_row_space",
    "gtable_add_col_space",
    "gtable_add_padding",
    # Construction
    "gtable_col",
    "gtable_row",
    "gtable_matrix",
    "gtable_row_spacer",
    "gtable_col_spacer",
    # Filtering & trimming
    "gtable_filter",
    "gtable_trim",
    # Layout visualisation
    "gtable_show_layout",
    # Binding
    "rbind_gtable",
    "cbind_gtable",
]
