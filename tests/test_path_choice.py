from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_path_choice():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0

    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0)
    _ = e.addLocation(name="B", movechance=1.0)
    _ = e.addLocation(name="C1", movechance=1.0)
    _ = e.addLocation(name="C2", movechance=1.0)
    _ = e.addLocation(name="D1", movechance=1.0)
    _ = e.addLocation(name="D2", movechance=1.0)
    _ = e.addLocation(name="D3", movechance=1.0)
    # l2 = e.addLocation(name="B", movechance=1.0)
    # l3 = e.addLocation(name="C1", movechance=1.0)
    # l4 = e.addLocation(name="C2", movechance=1.0)
    # l5 = e.addLocation(name="D1", movechance=1.0)
    # l6 = e.addLocation(name="D2", movechance=1.0)
    # l7 = e.addLocation(name="D3", movechance=1.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=10.0)
    e.linkUp(endpoint1="A", endpoint2="C1", distance=10.0)
    e.linkUp(endpoint1="A", endpoint2="D1", distance=10.0)
    e.linkUp(endpoint1="C1", endpoint2="C2", distance=10.0)
    e.linkUp(endpoint1="D1", endpoint2="D2", distance=10.0)
    e.linkUp(endpoint1="D2", endpoint2="D3", distance=10.0)

    e.addAgent(location=l1, age=20, gender="", attributes={})

    print("Test successful!")


if __name__ == "__main__":
    test_path_choice()
