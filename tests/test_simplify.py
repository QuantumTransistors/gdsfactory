import warnings

import numpy as np

import gdsfactory as gf
from gdsfactory import component, component_layout

points = np.array([[0.0, 0], [1, 0.001], [2, 0]])


def test_line_distances_no_2d_cross() -> None:
    """numpy 2.0 deprecated np.cross on 2-D vectors and later numpy raises."""
    for module in (component, component_layout):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            d = module._line_distances(points, points[0], points[-1])
            simplified = module._simplify(points, 1e-2)
            kept = module._simplify(points, 1e-4)
        np.testing.assert_allclose(d, [0, 0.001, 0], atol=1e-12)
        np.testing.assert_array_equal(simplified, points[[0, -1]])
        np.testing.assert_array_equal(kept, points)


def test_component_simplify() -> None:
    c = gf.components.bend_circular()
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        s = c.simplify(tolerance=0.05)
    n_before = sum(len(p) for p in c.get_polygons())
    n_after = sum(len(p) for p in s.get_polygons())
    assert 0 < n_after < n_before
