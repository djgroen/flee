import sys
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

    print(routes, file=sys.stderr)

    assert "E" not in routes

    assert "A" not in routes

    assert "B" in routes

    assert "C" in routes

    assert "D" in routes

    assert "B" in routes["D"][1]

    for key in routes:
        assert routes[key][0] > 0.0
        assert len(routes[key][1]) > 0

    # Check location end point score function.
    assert crawling.getLocationCrawlEndPointScore(l1.links[0], 0) == 1.0

    # Manually insert a major route for testing.
    l1.major_routes = [["B","D","E"]]
    """ 
    NOTE: in files major routes contain the source location ("A" in this case).
    But when loaded in the code, the source location is already implied by the 
    Location object it is attached to, so it is omitted from the list.

    Hence a major route specified as A,B,D,E in a file, will show as ["B","D","E"]
    in the major_routes list for Location "A".
    """

    dest_list = crawling.compileDestList(l1)

    # Insert major routes for location l1 test. Since the context is l1 here, there is no prior_route.
    crawling.insertMajorRoutesForLocation(l1, l1, [], dest_list, 0)

    #print("routes A:", l1.routes, l1.major_routes, file=sys.stderr)
    assert "E" in l1.routes.keys()
    assert l1.routes["E"][1][0] == "D"
    assert l1.routes["E"][2].name == "E"
    
