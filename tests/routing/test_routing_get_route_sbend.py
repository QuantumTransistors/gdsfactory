from functools import partial

import gdsfactory as gf


def test_get_route_sbend():
    c = gf.Component("demo_route_sbend")
    mmi1 = c << gf.components.mmi1x2()
    mmi2 = c << gf.components.mmi1x2()
    mmi2.move((100, 50))
    route = gf.routing.get_route_sbend(mmi1.ports["o3"], mmi2.ports["o1"])
    c.add(route.references)
    assert len(route.references) == 1
    assert route.length > 0
    assert route.ports == (mmi1.ports["o3"], mmi2.ports["o1"])


def test_get_route_sbend_custom_factory():
    c = gf.Component("demo_route_sbend_custom_factory")
    mmi1 = c << gf.components.mmi1x2()
    mmi2 = c << gf.components.mmi1x2()
    mmi2.move((100, 50))
    # does not make sense physically but gdsfactory should still generate this
    route = gf.routing.get_route_sbend(
        mmi1.ports["o3"],
        mmi2.ports["o1"],
        bend_s=partial(gf.components.bend_s, cross_section="xs_sc"),
    )
    c.add(route.references)
    assert len(route.references) == 1
    assert route.length > 0
    assert route.ports == (mmi1.ports["o3"], mmi2.ports["o1"])
