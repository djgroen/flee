from flee import flee, demographics

def test_get_attribute_ratio():
    flee.SimulationSettings.ReadFromYML("empty.yml")

    e = flee.Ecosystem()
    e.demographics_test_prefix = "test_data/test_data_idp"

    l1 = e.addLocation(name="A", x=0.0, y=0.0, movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", x=1.0, y=1.0, movechance=1.0, foreign=False)
    l3 = e.addLocation(name="C", x=100.0, y=100.0, movechance=1.0, foreign=False)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="B", endpoint2="C", distance=100.0)

    # Insert refugee agents
    for _ in range(0, 1):
        e.addAgent(location=l1, attributes={})

    l1.pop = 1000
    l1.attributes["british"] = 20

    assert demographics.get_attribute_ratio(l1, "british") == 0.02

