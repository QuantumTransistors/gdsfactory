from __future__ import annotations

import pytest

import gdsfactory as gf
from gdsfactory.components import cells

skip_test = {
    "component_sequence",
    "extend_port",
    "extend_ports_list",
    "add_grating_couplers",
    "add_grating_couplers_fiber_array",
    "add_grating_couplers_with_loopback_fiber_array",
    "add_grating_couplers_with_loopback_fiber_single",
}
cells_to_test = set(cells.keys()) - skip_test


@pytest.fixture(params=cells_to_test, scope="function")
def component_name(request) -> str:
    return request.param


def test_components_serialize(component_name: str) -> None:
    """Avoid regressions in GDS geometry shapes and layers."""
    c1 = cells[component_name]()
    settings = c1.settings
    cell_name = c1.function_name
    c2 = gf.get_component({"component": cell_name, "settings": settings})
    assert c2


if __name__ == "__main__":
    # import json
    # c1 = gf.components.mmi1x2()
    # settings = c1.settings.full
    # settings_string = json.dumps(settings)
    # settings2 = json.loads(settings_string)
    # cell_name = c1.settings.function_name
    # c2 = gf.get_component({"component": cell_name, "settings": settings2})

    import json

    import orjson

    c1 = gf.components.cutback_splitter()
    settings = c1.settings
    settings_string = json.dumps(dict(settings))
    settings2 = orjson.loads(settings_string)
    cell_name = c1.function_name
    c2 = gf.get_component({"component": cell_name, "settings": settings2})
