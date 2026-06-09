"""Smoke test for gtable_py._biobabel.

Exercises the core public API (construction, functional add, query) without
opening a rendering device, so it runs headless.
"""

from __future__ import annotations

from grid_py import Unit, gpar, rect_grob, text_grob

from gtable_py import (
    Gtable,
    gtable_add_grob,
    gtable_filter,
    gtable_matrix,
    is_gtable,
)


def main() -> None:
    # Pattern 1: matrix construction.
    mat = gtable_matrix(
        name="grid",
        grobs=[
            [rect_grob(gp=gpar(fill="#fee")), rect_grob(gp=gpar(fill="#efe"))],
            [text_grob("A"), text_grob("B")],
        ],
        widths=Unit([1, 1], "null"),
        heights=Unit([2, 1], "null"),
    )
    assert is_gtable(mat)
    assert mat.shape == (2, 2)
    assert len(mat) == 4  # four grobs placed

    # Pattern 2: empty Gtable + functional, named gtable_add_grob.
    tab = Gtable(
        widths=Unit([1], "null"),
        heights=Unit([1, 6, 1], "null"),
        name="composite",
    )
    tab = gtable_add_grob(tab, text_grob("title"), t=1, l=1, name="title")
    tab = gtable_add_grob(tab, rect_grob(), t=2, l=1, name="plot")
    tab = gtable_add_grob(tab, text_grob("legend"), t=3, l=1, name="legend")
    assert len(tab) == 3
    assert tab.layout["t"] == [1, 2, 3]  # stored positions are 1-based

    # Functional API: the input is unchanged by a non-captured call.
    before = len(tab)
    gtable_add_grob(tab, rect_grob(), t=1, l=1)  # return value discarded
    assert len(tab) == before

    # Filter by cell name.
    only_plot = gtable_filter(tab, "plot")
    assert is_gtable(only_plot)

    print("gtable_py smoke OK")


if __name__ == "__main__":
    main()
