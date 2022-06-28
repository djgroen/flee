from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable

__refugees_raw = 0
__refugee_debt = 0

def spawn_daily_displaced(e, t, d):
    global __refugees_raw, __refugee_debt
    """
    t = time
    e = Ecosystem object
    d = DataTable object
    refugees_raw = raw refugee count
    """

    insert_day0_refugees_in_camps = True

    # Determine number of new refugees to insert into the system.
    new_refs = d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False) - __refugee_debt
    __refugees_raw += d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False)

    #Refugees are pre-placed in Mali, so set new_refs to 0 on Day 0.
    if insert_day0_refugees_in_camps:
        if t == 0:
            new_refs = 0
            #refugees_raw = 0

    if new_refs < 0:
      __refugee_debt = -new_refs
      new_refs = 0
    elif __refugee_debt > 0:
      __refugee_debt = 0

    #Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(e.pick_conflict_location())

    return new_refs, __refugees_raw, __refugee_debt
