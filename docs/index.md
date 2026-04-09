# gtable_py

Python port of the R **gtable** package.

`gtable_py` provides tools for creating and manipulating tables of grid graphical objects (grobs)
arranged in a layout grid. It is a faithful port of the R
[gtable](https://gtable.r-lib.org) package, built on top of
[grid_py](https://github.com/r-lib/grid_py) as its rendering backend.

## Features

- Create grob tables with row and column layout (`Gtable`)
- Add grobs with row/column spanning (`gtable_add_grob`)
- Insert rows and columns (`gtable_add_rows`, `gtable_add_cols`)
- Row-bind and column-bind tables (`rbind_gtable`, `cbind_gtable`)
- Filter, trim, and pad tables
- Convenience constructors: `gtable_col`, `gtable_row`, `gtable_matrix`
- Full z-order control for layered rendering

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from grid_py import Unit, rect_grob, Gpar
from gtable_py import Gtable, gtable_add_grob

# Create a 2x2 table
gt = Gtable(Unit([1, 2], "cm"), Unit([3, 4], "cm"))

# Add a grob to cell (1, 1)
rect = rect_grob(gp=Gpar(fill="steelblue"))
gt = gtable_add_grob(gt, rect, t=1, l=1)

# Draw it
gt.plot()
```

## Dependencies

- [grid_py](https://github.com/r-lib/grid_py) >= 0.1.0
- numpy >= 1.24
