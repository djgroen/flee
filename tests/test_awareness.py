from flee import flee, moving

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_awareness():

    print("Testing basic data handling and simulation kernel.")
    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0

    for level in range (0,5):

      flee.SimulationSettings.move_rules["AwarenessLevel"] = level

      end_time = 5
      e = flee.Ecosystem()

      l1 = e.addLocation(name="A", movechance=0.3)
      _ = e.addLocation(name="B", movechance=0.3)
      _ = e.addLocation(name="C", movechance=0.3)
      _ = e.addLocation(name="D", movechance=0.3)
      _ = e.addLocation(name="C2", movechance=0.3)
      _ = e.addLocation(name="D2", movechance=0.3)
      _ = e.addLocation(name="D3", location_type="camp")

      e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
      e.linkUp(endpoint1="A", endpoint2="C", distance=834.0)
      e.linkUp(endpoint1="A", endpoint2="D", distance=834.0)
      e.linkUp(endpoint1="C", endpoint2="C2", distance=834.0)
      e.linkUp(endpoint1="C", endpoint2="D2", distance=834.0)
      e.linkUp(endpoint1="D", endpoint2="D2", distance=834.0)
      e.linkUp(endpoint1="D2", endpoint2="D3", distance=834.0)
      e.linkUp(endpoint1="C2", endpoint2="D3", distance=834.0)

      e.addAgent(location=l1, attributes={})

      moving.selectRoute(e.agents[0], time=0, debug=True)

      for t in range(0,end_time):
        e.evolve()

      print("Test successful!")


def test_marker_location():

    print("Testing basic data handling and simulation kernel.")
    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0

    flee.SimulationSettings.move_rules["AwarenessLevel"] = 5

    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=0.3)
    _ = e.addLocation(name="B", movechance=0.3)
    _ = e.addLocation(name="C", location_type="marker")
    _ = e.addLocation(name="D", movechance=0.3, location_type="camp")

    e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=834.0)
    e.linkUp(endpoint1="B", endpoint2="D", distance=834.0)
    e.linkUp(endpoint1="C", endpoint2="D", distance=834.0)

    e.addAgent(location=l1, attributes={})

    w, r = moving.selectRoute(e.agents[0], time=0, debug=True, return_all_routes=True)

    assert len(r) == 4
    # should return four routes, although order may vary.

    wts, rts = moving.calculateLinkWeight(e.agents[0], l1.links[0], 0.0, ['A'], 0, 0, True)
    #should return rts = [['A', 'B'], ['A', 'B', 'D']]

    for i in rts:
        assert i[-1] in ['B','D']

    wts2, rts2 = moving.calculateLinkWeight(e.agents[0], l1.links[1], 0.0, ['A'], 0, 0, True)
    #should return rts = [['A', 'C', 'D'], ['A', 'C', 'D', 'B']] 

    for i in rts2:
        assert i[-1] in ['B','D']

    print("Test successful!")



if __name__ == "__main__":
    test_awareness()
    test_marker_location()
