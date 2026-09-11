from __future__ import annotations

import pytest

import gdsfactory as gf
from gdsfactory.config import CONF


def test_duplicated_cells_error() -> None:
    w = h = 10
    points = [
        [-w / 2.0, -h / 2.0],
        [-w / 2.0, h / 2],
        [w / 2, h / 2],
        [w / 2, -h / 2.0],
    ]
    c1 = gf.Component("test_duplicated_cells_error")
    c1.add_polygon(points, layer=(1, 0))

    w = h = 20
    points = [
        [-w / 2.0, -h / 2.0],
        [-w / 2.0, h / 2],
        [w / 2, h / 2],
        [w / 2, -h / 2.0],
    ]

    c2 = gf.Component()
    c2._cell.name = "test_duplicated_cells_error"
    c2.add_polygon(points, layer=(2, 0))

    c3 = gf.Component()
    c3 << c1
    c3 << c2

    with pytest.raises(ValueError):
        c3.write_gds("rectangles.gds", on_duplicate_cell="error")


def test_duplicated_cells_pass() -> None:
    gf.Component("duplicated_cells_pass")
    c1 = gf.Component("duplicated_cells_pass")
    assert c1.name == "duplicated_cells_pass$1", c1.name
    c2 = gf.Component("duplicated_cells_pass")
    assert c2.name == "duplicated_cells_pass$2", c2.name


def test_same_names() -> None:
    c = gf.Component("test_same_names")
    c.name = "test_same_names"
    c.name = "test_same_names"
    assert c.name == "test_same_names", c.name


def test_reserved_name_is_not_reissued() -> None:
    """A name already taken by a live Component is never handed out again.

    The derived ``$k`` name has to be probed, not just computed from the counter
    for the bare name: here ``reissue_probe$1`` exists before anything asks for
    ``reissue_probe``, so the second duplicate has to skip to ``$2``.
    """
    c0 = gf.Component("reissue_probe$1")
    c1 = gf.Component("reissue_probe")
    with pytest.warns(UserWarning, match="Cell name collision"):
        c2 = gf.Component("reissue_probe")

    assert c2.name == "reissue_probe$2", c2.name
    assert len({c0.name, c1.name, c2.name}) == 3, (c0.name, c1.name, c2.name)


def test_reserved_derived_name_is_not_reissued() -> None:
    """Same in the other direction: asking for a name a duplicate already derived."""
    gf.Component("derived_probe")
    c1 = gf.Component("derived_probe")
    assert c1.name == "derived_probe$1", c1.name

    with pytest.warns(UserWarning, match="Cell name collision"):
        c2 = gf.Component("derived_probe$1")

    assert c2.name == "derived_probe$1$1", c2.name


def test_duplicate_cell_name_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    gf.Component("error_probe$1")
    gf.Component("error_probe")
    with pytest.raises(ValueError, match="Cell name collision"):
        gf.Component("error_probe")


def test_plain_duplicates_are_silent(recwarn: pytest.WarningsRecorder) -> None:
    """The ordinary duplicate case is not a collision and must stay quiet."""
    gf.Component("silent_probe")
    c1 = gf.Component("silent_probe")
    c2 = gf.Component("silent_probe")
    assert (c1.name, c2.name) == ("silent_probe$1", "silent_probe$2")
    assert [str(w.message) for w in recwarn] == []


if __name__ == "__main__":
    test_same_names()
    # c1 = gf.Component("h")
    # c2 = gf.Component("h")
    # c3 = gf.Component("h")
    # print(c1.name)
    # print(c2.name)
    # print(c3.name)
    # test_duplicated_cells_pass()
    # test_duplicated_cells_error()
    # test_duplicated_cells_pass()

    # w = h = 10
    # points = [
    #     [-w / 2.0, -h / 2.0],
    #     [-w / 2.0, h / 2],
    #     [w / 2, h / 2],
    #     [w / 2, -h / 2.0],
    # ]
    # c1 = gf.Component("test_duplicated_cells_error")
    # c1.add_polygon(points, layer=(1, 0))

    # w = h = 20
    # points = [
    #     [-w / 2.0, -h / 2.0],
    #     [-w / 2.0, h / 2],
    #     [w / 2, h / 2],
    #     [w / 2, -h / 2.0],
    # ]

    # c2 = gf.Component()
    # c2.name = "test_duplicated_cells_error"
    # c2.add_polygon(points, layer=(2, 0))

    # c3 = gf.Component("top")
    # c3 << c1
    # c3 << c2
    # c3.show()
