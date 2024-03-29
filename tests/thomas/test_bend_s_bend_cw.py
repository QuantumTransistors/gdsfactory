import gdsfactory as gf
from gdsfactory.components import bend_straight_bend

c = gf.Component("TOP")
b = c << bend_straight_bend(direction="ccw")
b.mirror()
c.add_port("o1", port=b.ports["o1"])
c.add_port("o2", port=b.ports["o2"])
c.show(show_ports=True, show_subports=True)
