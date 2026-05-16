"""Recipe: title + plot + legend in a 3-row Gtable.

Demonstrates the `build_then_add_grob` idiom: start from an empty gtable
sized by `Unit([1, 6, 1], "null")` rows (so the middle plot row takes 6×
the space of the strips), then add three named grobs.
"""

from __future__ import annotations

from pathlib import Path

from grid_py import (
    CairoRenderer,
    Unit,
    get_state,
    gpar,
    grid_draw,
    grid_newpage,
    rect_grob,
    text_grob,
)
from gtable_py import Gtable, gtable_add_grob


def main(out_path: Path = Path("title_plot_legend.png")) -> Path:
    title = text_grob("My Composite Figure", gp=gpar(fontsize=16))
    plot = rect_grob(gp=gpar(fill="#eef", col="#446"))
    legend = text_grob("legend goes here", gp=gpar(fontsize=10))

    tab = Gtable(
        widths=Unit([1], "null"),
        heights=Unit([1, 6, 1], "null"),
        name="composite",
    )
    tab = gtable_add_grob(tab, title, t=1, l=1, name="title")
    tab = gtable_add_grob(tab, plot, t=2, l=1, name="plot")
    tab = gtable_add_grob(tab, legend, t=3, l=1, name="legend")

    renderer = CairoRenderer(width=4, height=4, dpi=150, bg="white")
    get_state().init_device(renderer)
    grid_newpage()
    grid_draw(tab)
    renderer.write_to_png(str(out_path))
    return out_path


if __name__ == "__main__":
    print(f"wrote {main().resolve()}")
