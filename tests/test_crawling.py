from flee import flee, crawling

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_location_crawling_2loc():
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["AwarenessLevel"] = 1

    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", movechance=0.0, foreign=True)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    # Insert refugee agents
    for _ in range(0, 1):
        e.addAgent(location=l1, attributes={})

    routes = crawling.generateLocationRoutes(l1, 0)

    assert routes == None


if __name__ == "__main__":
    test_camp_sink()
