from flee import flee, crawling

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_location_crawling_4loc():
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["AwarenessLevel"] = 2

    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", movechance=0.0, foreign=True)
    l3 = e.addLocation(name="C", movechance=0.0, foreign=True)
    l4 = e.addLocation(name="D", movechance=0.0, foreign=True)
    l5 = e.addLocation(name="E", movechance=0.0, foreign=True)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=200.0)
    e.linkUp(endpoint1="B", endpoint2="D", distance=100.0)
    e.linkUp(endpoint1="C", endpoint2="D", distance=100.0)
    e.linkUp(endpoint1="D", endpoint2="E", distance=100.0)
    # Insert refugee agents
    for _ in range(0, 1):
        e.addAgent(location=l1, attributes={})

    routes = crawling.generateLocationRoutes(l1, 0)

    assert "E" not in routes

    assert "A" not in routes

    assert "B" in routes

    assert "C" in routes

    assert "D" in routes

    assert "B" in routes["D"][1]

    for key in routes:
        assert routes[key][0] > 0.0
        assert len(routes[key][1]) > 0

