import itertools
from pathlib import Path

import pytest

from gdsfactory.difftest import diff

_gds_dir = Path(__file__).parent / "gds"


def assert_xor_fails(ref_gds, run_gds, test_name, capsys, layers_with_xor):
    assert diff(ref_gds, run_gds, xor=True, test_name=test_name, show=False) is True
    captured = capsys.readouterr()
    for layer in layers_with_xor:
        assert f"XOR difference on layer {layer}" in captured.out


def test_xor1(capsys):
    # assert that the XOR flags the layer with A not B differences
    ref_gds = _gds_dir / "big_rect.gds"
    run_gds = _gds_dir / "small_rect.gds"
    assert_xor_fails(
        ref_gds=ref_gds,
        run_gds=run_gds,
        test_name="test_xor1",
        capsys=capsys,
        layers_with_xor=["2/0"],
    )


def test_xor2(capsys):
    # assert that the XOR flags the layer with B not A differences
    ref_gds = _gds_dir / "small_rect.gds"
    run_gds = _gds_dir / "big_rect.gds"
    assert_xor_fails(
        ref_gds=ref_gds,
        run_gds=run_gds,
        test_name="test_xor2",
        capsys=capsys,
        layers_with_xor=["2/0"],
    )


@pytest.mark.parametrize(["xor"], [[True], [False]])
def test_cell_name_changed_fails(xor: bool):
    ref_gds = _gds_dir / "big_rect.gds"
    run_gds = _gds_dir / "big_rect_named_bob.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_cell_name_changed_fails_xor{int(xor)}",
        ignore_cell_name_differences=False,
        xor=xor,
        show=False,
    )
    assert has_diff


@pytest.mark.parametrize(["xor"], [[True], [False]])
def test_cell_name_changed_ignored_passes(xor: bool):
    ref_gds = _gds_dir / "big_rect.gds"
    run_gds = _gds_dir / "big_rect_named_bob.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_cell_name_changed_ignored_passes_xor{int(xor)}",
        ignore_cell_name_differences=True,
        xor=xor,
        show=False,
    )
    assert not has_diff


@pytest.mark.parametrize(["xor"], [[True], [False]])
def test_sliver_xor_fails(xor: bool):
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "almost_big_rect_named_bob.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_sliver_xor_fails_xor{int(xor)}",
        ignore_cell_name_differences=True,
        xor=xor,
        ignore_sliver_differences=False,
        show=False,
    )
    assert has_diff


def test_sliver_xor_ignored_passes():
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "almost_big_rect_named_bob.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name="test_sliver_xor_ignored_passes",
        ignore_cell_name_differences=True,
        xor=True,
        ignore_sliver_differences=True,
        show=False,
    )
    assert not has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences"],
    itertools.product([True, False], repeat=2),
)
def test_non_xor_diff_fails_no_xor(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool
):
    ref_gds = _gds_dir / "big_rect.gds"
    run_gds = _gds_dir / "big_rect_in_spirit.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_non_xor_diff_fails_no_xor_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=False,
        ignore_sliver_differences=ignore_sliver_differences,
        show=False,
    )
    assert has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences"],
    itertools.product([True, False], repeat=2),
)
def test_non_xor_diff_passes_xor(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool
):
    ref_gds = _gds_dir / "big_rect.gds"
    run_gds = _gds_dir / "big_rect_in_spirit.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_non_xor_diff_passes_xor_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=True,
        ignore_sliver_differences=ignore_sliver_differences,
        show=False,
    )
    assert not has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences", "xor"],
    itertools.product([True, False], repeat=3),
)
def test_label_diff_fails(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool, xor: bool
):
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "bob_with_nametag.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_label_diff_fails_xor{int(xor)}_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=xor,
        ignore_sliver_differences=ignore_sliver_differences,
        ignore_label_differences=False,
        show=False,
    )
    assert has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences"],
    itertools.product([True, False], repeat=2),
)
def test_label_diff_ignored_xor_passes(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool
):
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "bob_with_nametag.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_label_diff_ignored_xor_passes_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=True,
        ignore_sliver_differences=ignore_sliver_differences,
        ignore_label_differences=True,
        show=False,
    )
    assert not has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences"],
    itertools.product([True, False], repeat=2),
)
def test_label_diff_ignored_new_layer_xor_fails(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool
):
    # the behavior here is arguable.. right now, it will still fail if a layer is added/removed due to a label only
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "bob_with_nametag_different_layer.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_label_diff_ignored_new_layer_xor_passes_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=True,
        ignore_sliver_differences=ignore_sliver_differences,
        ignore_label_differences=True,
        show=False,
    )
    assert has_diff


@pytest.mark.parametrize(
    ["ignore_cell_name_differences", "ignore_sliver_differences"],
    itertools.product([True, False], repeat=2),
)
def test_label_diff_ignored_no_xor_fails(
    ignore_cell_name_differences: bool, ignore_sliver_differences: bool
):
    # when xor=False, we are essentially running "strict mode, and the diff will fail regardless"
    ref_gds = _gds_dir / "big_rect_named_bob.gds"
    run_gds = _gds_dir / "bob_with_nametag.gds"
    has_diff = diff(
        ref_file=ref_gds,
        run_file=run_gds,
        test_name=f"test_label_diff_ignored_no_xor_passes_cellnames{int(ignore_cell_name_differences)}_slivers{int(ignore_sliver_differences)}",
        ignore_cell_name_differences=ignore_cell_name_differences,
        xor=False,
        ignore_sliver_differences=ignore_sliver_differences,
        ignore_label_differences=True,
        show=False,
    )
    assert has_diff


def test_show_failure_cannot_change_the_verdict():
    """A broken viewer must not turn a geometry difference into an unrelated error.

    Every other test in this file passes ``show=False``, but ``difftest`` -- the only
    production caller -- uses the default ``show=True``. That gap hid a defect: ``c`` was
    built in the process-global ``KCLayout`` and ``show()`` writes layouts, so a single pair
    of same-named cells anywhere in the process raised ``cell name(s) are used for more than
    one cell`` *before* ``diff`` returned. The geometry answer was replaced by an error about
    the viewer, and tests that were about to pass failed instead.

    Duplicate names are reachable in normal use: rebuilding modules in one process produces
    two generations of a cell under one name.
    """
    from kfactory import KCell, KCLayout

    stale = KCLayout(name="test_show_failure_stale_layout")
    KCell(name="dupe", kcl=stale)
    shadow = KCell(name="not_yet_dupe", kcl=stale)
    shadow.name = "dupe"
    assert [c.name for c in stale.layout.each_cell()] == ["dupe", "dupe"]

    has_diff = diff(
        ref_file=_gds_dir / "big_rect.gds",
        run_file=_gds_dir / "small_rect.gds",
        test_name="test_show_failure_cannot_change_the_verdict",
        xor=True,
        show=True,
    )
    assert has_diff is True
