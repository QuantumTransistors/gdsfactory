from __future__ import annotations

import pytest

import gdsfactory as gf
from gdsfactory.cell import CACHE
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


def test_reserved_derived_name_is_not_reissued(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """Asking for a name a duplicate already derived gets a free one, quietly.

    Two components asking for the same name is the ordinary duplicate case
    whatever that name looks like, so this is as quiet as asking twice for ``x``.
    """
    gf.Component("derived_probe")
    c1 = gf.Component("derived_probe")
    assert c1.name == "derived_probe$1", c1.name

    c2 = gf.Component("derived_probe$1")
    assert c2.name == "derived_probe$1$1", c2.name
    assert [str(w.message) for w in recwarn] == []


def test_duplicate_cell_name_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    gf.Component("error_probe$1")
    gf.Component("error_probe")
    with pytest.raises(ValueError, match="Cell name collision"):
        gf.Component("error_probe")


def test_plain_duplicates_are_silent(recwarn: pytest.WarningsRecorder) -> None:
    """The ordinary duplicate case is not a collision and must stay quiet.

    The base name carries ``$`` on purpose: real GDS in the consuming tapeout
    holds cells called ``ec_alignment_ruler$10``, and duplicating one of those is
    as ordinary as duplicating any other name.
    """
    gf.Component("silent$probe$7")
    c1 = gf.Component("silent$probe$7")
    c2 = gf.Component("silent$probe$7")
    assert (c1.name, c2.name) == ("silent$probe$7$1", "silent$probe$7$2")
    assert [str(w.message) for w in recwarn] == []


def test_dollar_name_duplicate_does_not_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same case in ``error`` mode: a $-shaped name still duplicates."""
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    gf.Component("Ruler$50$to$-100")
    c1 = gf.Component("Ruler$50$to$-100")
    assert c1.name == "Ruler$50$to$-100$1", c1.name


def test_cache_only_name_never_mints_dollar_zero() -> None:
    """A bare name in CACHE whose counter is 0 resolves to ``$1``, never ``$0``.

    ``@cell`` keys CACHE on the signature name, which ``autoname=False`` and
    ``get_child_name`` leave uncounted, so this state is reachable.
    """
    CACHE["dollar_zero_probe"] = gf.Component("dollar_zero_probe_holder")

    with pytest.warns(UserWarning, match="Cell name collision"):
        c = gf.Component("dollar_zero_probe")
    assert c.name == "dollar_zero_probe$1", c.name


def test_reservation_released_on_rename_away(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """A component leaving a name gives that name's reservation back."""
    c = gf.Component("release_probe$1")
    c.name = "release_probe_moved"

    c2 = gf.Component("release_probe$1")
    assert c2.name == "release_probe$1", c2.name
    assert [str(w.message) for w in recwarn] == []


def test_release_declines_while_the_name_is_a_derivation_base() -> None:
    """A name other components derive suffixes from is not given back.

    ``rename``'s own derivation is unprobed, so releasing here would let a later
    rename re-derive a suffix a live component still holds.
    """
    a = gf.Component("base_probe")
    b = gf.Component("base_probe_other")
    b.name = "base_probe"
    assert b.name == "base_probe$1", b.name

    a.name = "base_probe_moved"

    c = gf.Component("base_probe_third")
    c.name = "base_probe"
    assert c.name == "base_probe$2", c.name
    assert c.name != b.name


def test_collision_warning_points_at_the_caller() -> None:
    """The report names the caller's line, not gdsfactory's own internals."""
    gf.Component("stacklevel_probe$1")
    gf.Component("stacklevel_probe")
    with pytest.warns(UserWarning, match="Cell name collision") as record:
        gf.Component("stacklevel_probe")

    assert record[0].filename == __file__, record[0].filename


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
