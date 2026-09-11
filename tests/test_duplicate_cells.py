from __future__ import annotations

import warnings

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


def test_derived_name_held_by_a_live_component_is_refused() -> None:
    """A ``$k`` name a duplicate is holding is refused like any other held name.

    How the holder came by the name does not matter: it is live and it has it.
    """
    c0 = gf.Component("derived_probe")
    c1 = gf.Component("derived_probe")
    assert c1.name == "derived_probe$1", c1.name

    with pytest.warns(UserWarning, match="Cell name collision"):
        c2 = gf.Component("derived_probe$1")
    assert c2.name == "derived_probe$1$1", c2.name
    assert len({c0.name, c1.name, c2.name}) == 3


def test_duplicate_cell_name_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    holder = gf.Component("error_probe$1")
    first = gf.Component("error_probe")
    with pytest.raises(ValueError, match="Cell name collision"):
        gf.Component("error_probe")
    assert (holder.name, first.name) == ("error_probe$1", "error_probe")


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
    try:
        with pytest.warns(UserWarning, match="Cell name collision"):
            c = gf.Component("dollar_zero_probe")
        assert c.name == "dollar_zero_probe$1", c.name
    finally:
        # The fork's tests/conftest.py resets no caches, so leaving this behind
        # would leak into whatever runs next.
        del CACHE["dollar_zero_probe"]


def test_a_vacated_name_is_not_reused(recwarn: pytest.WarningsRecorder) -> None:
    """Leaving a name does not wind the derivation index back, exactly as before.

    ``name_counters`` says where the next ``$k`` starts and nothing else; rewinding
    it would re-mint a suffix a live component still holds, which is how two
    components ended up on one name.
    """
    c = gf.Component("vacated_probe$1")
    c.name = "vacated_probe_moved"

    c2 = gf.Component("vacated_probe$1")
    assert c2.name == "vacated_probe$1$1", c2.name
    assert [str(w.message) for w in recwarn] == []


def test_rename_onto_a_vacated_name_keeps_components_distinct() -> None:
    """Two components swapping names stay on two names."""
    a = gf.Component("swap_probe")
    b = gf.Component("swap_probe$1")

    b.name = "swap_probe"
    a.name = "swap_probe$1"

    assert a.name != b.name, (a.name, b.name)


def test_a_name_no_live_component_holds_is_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A counter above zero is not a holder, and must not be reported as one.

    Under ``error`` -- the mode the tapeout audit runs in -- reporting a free name
    aborts the build.
    """
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    a = gf.Component("freed_probe$1")
    b = gf.Component("freed_probe$1")
    assert b.name == "freed_probe$1$1", b.name
    a.name = "freed_probe_moved"

    c = gf.Component("freed_probe")
    d = gf.Component("freed_probe")
    assert (c.name, d.name) == ("freed_probe", "freed_probe$1"), (c.name, d.name)


def test_a_vacated_base_name_is_reusable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Having served as a derivation base does not burn a name."""
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    c = gf.Component("burned_probe")
    c.name = "burned_probe_moved"

    d = gf.Component("burned_probe")
    assert d.name == "burned_probe$1", d.name


def _sequences(depth: int):
    """Every construct/rename sequence of ``depth`` steps over three names.

    A step is either building a new component on one of the names, or assigning
    one of them to a component built earlier. Yields ``(op, index_or_name, ...)``
    tuples; the name set is per-sequence, so no global reset is needed.
    """

    def rec(prefix: list, live: int):
        if len(prefix) == depth:
            yield tuple(prefix)
            return
        ops = [("new", k) for k in range(3)]
        ops += [("ren", i, k) for i in range(live) for k in range(3)]
        for op in ops:
            prefix.append(op)
            yield from rec(prefix, live + (1 if op[0] == "new" else 0))
            prefix.pop()

    yield from rec([], 0)


def test_no_sequence_puts_two_live_components_on_one_name() -> None:
    """Every construct/rename sequence over one name set leaves distinct names.

    Bounded enumeration -- the property is what the change is for, and the only
    one a test can assert without a second gdsfactory to compare against. Renames
    are in scope because they go through the same probe as construction; what is
    out of scope is ``cache=False`` and ``clear_cache``, which record nothing and
    forget everything respectively.
    """
    for i, seq in enumerate(_sequences(4)):
        prefix = f"enum_probe_{i}"
        names = [prefix, f"{prefix}$1", f"{prefix}$2"]
        components: list[gf.Component] = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for op in seq:
                if op[0] == "new":
                    components.append(gf.Component(names[op[1]]))
                else:
                    components[op[1]].name = names[op[2]]
                held = [c.name for c in components]
                assert len(set(held)) == len(held), (seq, held)
                # $0 is a suffix gdsfactory has never minted. Nothing special-cases
                # it any more -- the index is always past the name just refused --
                # so this is the only thing standing behind that claim.
                assert not any(n.endswith("$0") for n in held), (seq, held)


def test_collision_warning_points_at_the_caller() -> None:
    """The report names the caller's line, not gdsfactory's own internals."""
    holder = gf.Component("stacklevel_probe$1")
    first = gf.Component("stacklevel_probe")
    with pytest.warns(UserWarning, match="Cell name collision") as record:
        gf.Component("stacklevel_probe")

    assert record[0].filename == __file__, record[0].filename
    assert (holder.name, first.name) == ("stacklevel_probe$1", "stacklevel_probe")


def test_rename_onto_a_name_a_live_component_holds_is_refused() -> None:
    """``c.name = x`` goes through the same probe and the same report as ``Component(x)``.

    This is the path the consuming tapeout takes: ``qt01/dies/generate_test_die.py``
    assigns ``_c.name = name`` to every sub-block in the die loop.
    """
    holder = gf.Component("rename_probe$1")
    first = gf.Component("rename_probe")
    mover = gf.Component("rename_probe_elsewhere")

    with pytest.warns(UserWarning, match="Cell name collision"):
        mover.name = "rename_probe"

    assert mover.name == "rename_probe$2", mover.name
    assert len({holder.name, first.name, mover.name}) == 3


def test_renaming_a_component_onto_the_name_it_holds_is_a_no_op(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """A component is never a collision with itself, however the name is derived.

    The literal case is ``test_same_names``; this is the derived one. ``self$1`` is
    what the counter arithmetic hands out for ``self`` here, and the component
    asking for it is the one already holding it.
    """
    first = gf.Component("self_probe")
    mover = gf.Component("self_probe$1")

    mover.name = "self_probe"

    assert mover.name == "self_probe$1", mover.name
    assert first.name == "self_probe"
    assert [str(w.message) for w in recwarn] == []


def test_a_refused_rename_leaves_the_component_where_it_was(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Under ``error`` the raise happens before the old name is given up.

    Otherwise the component is live, keeps answering to its old name, and is
    recorded as holding nothing -- so the next build could be handed that name.
    """
    monkeypatch.setattr(CONF, "on_duplicate_cell_name", "error")
    # Bound to names: an unreferenced Component is collected at once, and a name
    # nothing holds is free, which is the point of the record.
    holder = gf.Component("refused_probe$1")
    first = gf.Component("refused_probe")
    mover = gf.Component("kept_probe$1")

    with pytest.raises(ValueError, match="Cell name collision"):
        mover.name = "refused_probe"

    assert mover.name == "kept_probe$1", mover.name
    assert (holder.name, first.name) == ("refused_probe$1", "refused_probe")
    # And it is still recorded as holding that name: the next derivation for
    # ``kept_probe`` lands on ``kept_probe$1``, and has to be refused rather than
    # handed out on top of a live component.
    bare = gf.Component("kept_probe")
    with pytest.raises(ValueError, match="Cell name collision"):
        gf.Component("kept_probe")
    assert bare.name == "kept_probe", bare.name


def test_rename_collision_warning_points_at_the_caller() -> None:
    """Both ways of renaming report the caller's line, not gdsfactory's own.

    The ``name`` setter is one frame deeper than ``rename()``, which is the whole
    reason ``rename`` takes a ``stacklevel``.
    """
    held = [
        gf.Component("setter_stacklevel_probe$1"),
        gf.Component("setter_stacklevel_probe"),
        gf.Component("call_stacklevel_probe$1"),
        gf.Component("call_stacklevel_probe"),
    ]
    through_setter = gf.Component("rename_stacklevel_a")
    through_call = gf.Component("rename_stacklevel_b")

    with pytest.warns(UserWarning, match="Cell name collision") as setter_record:
        through_setter.name = "setter_stacklevel_probe"
    with pytest.warns(UserWarning, match="Cell name collision") as call_record:
        through_call.rename("call_stacklevel_probe")

    assert setter_record[0].filename == __file__, setter_record[0].filename
    assert call_record[0].filename == __file__, call_record[0].filename
    assert len({c.name for c in held}) == len(held)


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
