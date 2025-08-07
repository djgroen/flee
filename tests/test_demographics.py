from flee import flee, demographics

def setup(yaml="empty.yml"):
    flee.SimulationSettings.ReadFromYML(yaml)

    e = flee.Ecosystem()
    e.demographics_test_prefix = "test_data/test_data_idp"

    e.addLocation(name="A", x=0.0, y=0.0, movechance=1.0, foreign=False)
    e.addLocation(name="B", x=1.0, y=1.0, movechance=1.0, foreign=False)
    e.addLocation(name="C", x=100.0, y=100.0, movechance=1.0, foreign=False)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="B", endpoint2="C", distance=100.0)

    return e


def test_get_attribute_ratio():
    e = setup()

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="B", endpoint2="C", distance=100.0)

    # Insert refugee agents
    for _ in range(0, 1):
        e.addAgent(location=e.locations[0], attributes={})

    e.locations[0].pop = 1000
    e.locations[0].attributes["british"] = 20

    assert demographics.get_attribute_ratio(e.locations[0], "british") == 0.02


def test_load_demographics_csv():
    e = setup()

    demographics._read_demographic_csv(e, "test_data/test_data_idp/input_csv/demographics_religion.csv")

    #print(demographics.__demographics)
    #print(demographics.get_attribute_values("religion"))

    assert len(demographics.get_attribute_values("religion")) == 3
    assert not demographics.__demographics["religion"].isnull().values.any()
