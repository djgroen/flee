from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_close_location():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    # end_time = 80
    e = flee.Ecosystem()

    _ = e.addLocation(name="A", movechance=0.3)
    _ = e.addLocation(name="B", movechance=0.0)
    _ = e.addLocation(name="C", movechance=0.0)
    _ = e.addLocation(name="D", movechance=0.0)
    # l1 = e.addLocation(name="A", movechance=0.3)
    # l2 = e.addLocation(name="B", movechance=0.0)
    # l3 = e.addLocation(name="C", movechance=0.0)
    # l4 = e.addLocation(name="D", movechance=0.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=1368.0)
    e.linkUp(endpoint1="A", endpoint2="D", distance=536.0)

    assert e.close_location(location_name="C")

    print("Test successful!")


if __name__ == "__main__":
    test_close_location()
