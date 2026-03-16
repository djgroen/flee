# Fixes: Safe Zones and Input File Tracking

## Issues Identified

1. **Agents leaving safe zones**: Safe zones were not properly designated as camps
2. **Input files not tracked**: Config, locations, and routes files were not saved for each run

## Fixes Applied

### 1. Safe Zones Properly Designated as Camps

**Problem**: Safe zones were created with `'type': 'camp'` in the locations dictionary, but when calling `ecosystem.addLocation()`, the `location_type` parameter was not being passed. This meant locations were treated as default/town locations instead of camps.

**Solution**: Modified `nuclear_evacuation_simulations.py` to pass `location_type` parameter:

```python
# Before (line 401-407):
location = ecosystem.addLocation(
    name=loc['name'],
    x=loc['x'], y=loc['y'],
    movechance=loc['movechance'],
    capacity=loc['capacity'],
    pop=0
)

# After:
location_type = loc.get('type', 'town')
location = ecosystem.addLocation(
    name=loc['name'],
    x=loc['x'], y=loc['y'],
    location_type=location_type,  # Pass type so camps are properly designated
    movechance=loc['movechance'],
    capacity=loc['capacity'],
    pop=0
)
```

**Verification**: Tested that passing `location_type='camp'` properly sets:
- `location.camp = True`
- `location.movechance = SimulationSettings.move_rules["CampMoveChance"]` (0.001)

This ensures agents have a very low probability (0.001) of leaving safe zones, making them effectively sinks.

### 2. Input Files Saved for Each Run

**Problem**: Input files (config YAML, locations CSV, routes CSV) were created temporarily and deleted after simulation, making it impossible to reproduce runs.

**Solution**: Created a run-specific directory for each simulation that saves all input files:

```python
# Create run-specific directory for input files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = self.output_dir / f'run_{topology_name}_{timestamp}'
run_dir.mkdir(exist_ok=True)

# Save config
config_file = run_dir / f'config_{topology_name}.yml'
with open(config_file, 'w') as f:
    yaml.dump(config, f)

# Save locations as CSV (Flee format)
locations_csv = run_dir / f'locations_{topology_name}.csv'
with open(locations_csv, 'w') as f:
    f.write('name,region,x,y,location_type,movechance,capacity,pop,country,conflict,conflict_date,attributes\n')
    for loc in locations:
        f.write(f"{loc['name']},unknown,{loc['x']},{loc['y']},{loc.get('type', 'town')},"
               f"{loc['movechance']},{loc['capacity']},0,unknown,{loc.get('conflict', 0.0)},0,{{}}\n")

# Save routes as CSV (Flee format)
routes_csv = run_dir / f'routes_{topology_name}.csv'
with open(routes_csv, 'w') as f:
    f.write('from,to,distance\n')
    for route in routes:
        f.write(f"{route['from']},{route['to']},{route['distance']}\n")
```

**Result**: Each simulation run now has:
- `run_{topology}_{timestamp}/config_{topology}.yml` - Full simulation configuration
- `run_{topology}_{timestamp}/locations_{topology}.csv` - Location definitions
- `run_{topology}_{timestamp}/routes_{topology}.csv` - Route definitions

These paths are stored in the results JSON under `input_files`:
```json
{
  "input_files": {
    "config": "nuclear_evacuation_results/run_Ring_20240101_120000/config_Ring.yml",
    "locations": "nuclear_evacuation_results/run_Ring_20240101_120000/locations_Ring.csv",
    "routes": "nuclear_evacuation_results/run_Ring_20240101_120000/routes_Ring.csv",
    "run_directory": "nuclear_evacuation_results/run_Ring_20240101_120000"
  }
}
```

## Impact

1. **Agents stay in safe zones**: With `movechance=0.001` and proper camp designation, agents have a 0.1% chance per timestep of leaving safe zones, making them effectively permanent destinations.

2. **Reproducibility**: All input files are now saved, allowing exact reproduction of any simulation run.

3. **Traceability**: Each run has a timestamped directory with all configuration and topology data.

## Files Modified

- `nuclear_evacuation_simulations.py`:
  - Line ~403: Added `location_type` parameter to `addLocation()` call
  - Lines 378-408: Added input file saving to run-specific directories
  - Lines 578-603: Added `input_files` to result dictionary

## Testing

Verified that:
- ✅ Camp locations are properly designated (`location.camp = True`)
- ✅ Camp movechance is set correctly (`movechance = 0.001`)
- ✅ Input files are saved to timestamped directories
- ✅ Input file paths are stored in results JSON

