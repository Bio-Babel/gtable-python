---
name: use-gtable-py
description: A grob-based tabular layout primitive — build composite figures (title + plot + legend, multi-panel grids) on top of grid_py.
---

# gtable-python

Python port of [r-lib/gtable](https://github.com/r-lib/gtable) (v0.3.6.9000). A Gtable is a grob that lays out *other* grobs in cells of an R×C table. ggplot2 internally is all gtable — every panel, axis, strip, and legend is a named cell.

## Mental model — 60 seconds

1. **`Gtable` is a grob.** You can `grid_draw(my_gtable)` directly.

2. **Cells are placements.** Each placement has `(t, l, b, r)` indices (1-based, inclusive), a `name`, a `z` for stacking, and a grob to render.

3. **Widths and heights are `Unit` vectors.** Mix fixed sizes (`Unit([2], "cm")`) with proportional ones (`Unit([1, 6, 1], "null")` — like CSS `1fr 6fr 1fr`).

4. **The API is functional, not in-place.** `gtable_add_grob(tab, g, t=1, l=1)` returns a *new* Gtable. Capture the return value or your edit is a no-op.

## Cardinal idioms

- **Build from a matrix**: `gtable_matrix(name, grobs=[[g11, g12], [g21, g22]], widths=..., heights=...)`
- **Build iteratively**: `Gtable(widths=..., heights=..., name=...)` + chained `gtable_add_grob` with named cells
- **Compose existing gtables**: `rbind_gtable(top, bottom)` / `cbind_gtable(left, right)`
- **Surgical edits**: `gtable_filter(tab, regex)` to keep only matching cells; `gtable_trim(tab)` to drop empty boundary rows/cols

## When NOT to reach for gtable

- **Single-panel plot** — push a viewport directly in `grid_py` and draw; gtable is overkill.
- **You want a data table, not a layout** — pandas/polars are for data.
- **You're using patchwork-python already** — patchwork wraps gtable; one or the other.

## Quick reference

```python
from grid_py import Unit, rect_grob, text_grob, gpar, grid_draw
from gtable_py import Gtable, gtable_add_grob, gtable_matrix

# Pattern 1: matrix
tab = gtable_matrix(
    name="grid",
    grobs=[[rect_grob(gp=gpar(fill="#fee")), rect_grob(gp=gpar(fill="#efe"))],
           [text_grob("A"),                   text_grob("B")]],
    widths=Unit([1, 1], "null"),
    heights=Unit([2, 1], "null"),
)

# Pattern 2: iterative with named cells
tab = Gtable(widths=Unit([1], "null"), heights=Unit([1, 6, 1], "null"))
tab = gtable_add_grob(tab, title_grob,  t=1, l=1, name="title")
tab = gtable_add_grob(tab, plot_grob,   t=2, l=1, name="plot")
tab = gtable_add_grob(tab, legend_grob, t=3, l=1, name="legend")

grid_draw(tab)
```

For more: `biobabel.list_idioms(package="gtable_py")` and `biobabel.describe_concept("gtable_py.Gtable")`.
