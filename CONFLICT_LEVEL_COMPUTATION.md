# How Conflict Level is Computed in Flee

## 🔍 Key Finding: Conflict is NOT Computed - It's a Static Attribute

**Important**: Conflict intensity is **not dynamically computed** in Flee. It's a **static attribute** of each location that is set when the location is created or updated.

## 📊 How Conflict is Set

### 1. **Location Initialization** (`flee/flee.py` line 744-766)

When a `Location` object is created:
- Default: `self.conflict = -1.0` (no conflict)
- If `location_type = "conflict"`: 
  ```python
  self.conflict = float(self.attributes.get("conflict_intensity", 1.0))
  ```
  - Reads from `attributes["conflict_intensity"]` if provided
  - Defaults to `1.0` if not provided

### 2. **In Our Nuclear Evacuation Simulations** (`nuclear_evacuation_simulations.py`)

We set conflict values directly in the location data dictionary:
```python
locations.append({
    'name': 'Facility',
    'type': 'conflict',
    'conflict': 0.95,  # High conflict
    ...
})
```

Then after creating the location:
```python
location = ecosystem.addLocation(...)
location.conflict = loc['conflict']  # Direct assignment (line 438)
```

### 3. **From Input Files** (`flee/InputGeography.py`)

When reading from CSV files:
- Conflict values can be read from `conflicts.csv` (time-series data)
- Or from `locations.csv` via the `conflict_intensity` attribute column
- Updated over time via `AddNewConflictZones()` method

### 4. **Dynamic Updates** (`flee/flee.py`)

Conflict can be updated during simulation:
- `add_conflict_zone(name, conflict_intensity)` - Adds/updates conflict zone
- `set_conflict_intensity(name, conflict_intensity)` - Sets conflict intensity
- `remove_conflict_zone(name)` - Removes conflict (sets to -1.0)

## 🎯 Conflict Value Ranges

| Value | Meaning | Usage |
|-------|---------|-------|
| `-1.0` | No conflict (default) | Location has no conflict |
| `0.0` | No conflict (explicit) | Location explicitly has no conflict |
| `0.0 < conflict ≤ 0.5` | Moderate conflict | Allows S1/S2 modification |
| `conflict > 0.5` | High conflict | **Hard constraint applied** (our fix) |
| `1.0` | Maximum conflict | Extreme danger zone |

## ✅ Our Hard Constraint Implementation

Our fix checks:
```python
conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
if conflict > 0.5:  # High conflict threshold
    return a.location.movechance, current_s2  # Hard constraint
```

**This is correct because:**
- `conflict = -1.0` → `max(0.0, -1.0) = 0.0` → Won't trigger (no conflict)
- `conflict = 0.0` → `max(0.0, 0.0) = 0.0` → Won't trigger (no conflict)
- `conflict = 0.5` → `max(0.0, 0.5) = 0.5` → Won't trigger (exactly at threshold)
- `conflict = 0.51` → `max(0.0, 0.51) = 0.51` → **Will trigger** (high conflict)
- `conflict = 0.95` → `max(0.0, 0.95) = 0.95` → **Will trigger** (high conflict)

## 📝 Summary

1. **Conflict is static**: Set when location is created, not computed dynamically
2. **Sources**: 
   - Direct assignment (our simulations)
   - Input files (`conflicts.csv`, `locations.csv`)
   - Dynamic updates via `add_conflict_zone()` or `set_conflict_intensity()`
3. **Our threshold (`conflict > 0.5`) is correct**: 
   - Only triggers for high-conflict zones
   - Ignores locations with no conflict (`-1.0` or `0.0`)
   - Allows S1/S2 modification for moderate conflict (`≤ 0.5`)

## 🔧 Example from Our Simulations

**Ring Topology:**
- `Facility`: `conflict = 0.95` → **Hard constraint** (always try to leave)
- `Ring1`: `conflict = 0.70` → **Hard constraint** (always try to leave)
- `Ring2`: `conflict = 0.45` → **S1/S2 modification allowed** (moderate conflict)
- `Ring3`: `conflict = 0.20` → **S1/S2 modification allowed** (moderate conflict)
- `SafeZone`: `conflict = 0.0` → **No conflict** (camp hard constraint applies)

This ensures:
- Extreme danger zones → panic response (always try to leave)
- Moderate danger zones → deliberation possible (S1/S2 can modify)
- Safe zones → stay (camp hard constraint)





