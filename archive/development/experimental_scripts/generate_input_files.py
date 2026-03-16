#!/usr/bin/env python3
"""
Generate Input Files for Flee Simulations

This script generates the standard Flee CSV input files for each simulation
based on the scenario data stored in the provenance and S1/S2 diagnostics.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
import sys

def extract_scenario_data_from_simulation(sim_dir: Path) -> Dict[str, Any]:
    """Extract scenario data from simulation outputs."""
    
    # Load S1/S2 diagnostics to get location and network data
    s1s2_file = sim_dir / "s1s2_diagnostics" / "cognitive_decisions.json"
    if not s1s2_file.exists():
        print(f"❌ No S1/S2 data found in {sim_dir.name}")
        return None
    
    with open(s1s2_file, 'r') as f:
        s1s2_data = json.load(f)
    
    # Load provenance for metadata
    provenance_file = sim_dir / "provenance.json"
    with open(provenance_file, 'r') as f:
        provenance = json.load(f)
    
    return {
        'scenario_name': provenance['simulation_metadata']['scenario_name'],
        'total_days': provenance['simulation_metadata']['total_days'],
        'locations': s1s2_data['locations'],
        'decisions': s1s2_data['decisions'],
        'daily_populations': s1s2_data.get('daily_populations', [])
    }

def generate_locations_csv(scenario_data: Dict, output_dir: Path):
    """Generate locations.csv file."""
    locations_file = output_dir / "locations.csv"
    
    with open(locations_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'population'])
        
        for loc in scenario_data['locations']:
            # Convert x,y coordinates to approximate lat/lon (simplified)
            lat = loc['y'] / 111.0  # Rough conversion: 1 degree ≈ 111 km
            lon = loc['x'] / 111.0
            
            # Determine location type based on name and capacity
            if 'conflict' in loc['name'].lower() or 'origin' in loc['name'].lower():
                loc_type = 'conflict_zone'
                conflict_date = '2023-01-01'  # Default conflict start
            elif 'camp' in loc['name'].lower() or 'refugee' in loc['name'].lower():
                loc_type = 'camp'
                conflict_date = ''
            else:
                loc_type = 'town'
                conflict_date = ''
            
            writer.writerow([
                loc['name'],
                'Region1',  # Default region
                'Country1',  # Default country
                f"{lat:.6f}",
                f"{lon:.6f}",
                loc_type,
                conflict_date,
                0  # Initial population
            ])
    
    print(f"✅ Generated: {locations_file}")

def generate_routes_csv(scenario_data: Dict, output_dir: Path):
    """Generate routes.csv file based on network topology."""
    routes_file = output_dir / "routes.csv"
    
    locations = scenario_data['locations']
    
    with open(routes_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name1', 'name2', 'distance', 'forced_redirection'])
        
        # Generate routes based on scenario type
        scenario_name = scenario_data['scenario_name']
        
        if 'Evacuation' in scenario_name:
            # Linear evacuation route: Conflict_Zone -> Transit_Town -> Refugee_Camp
            if len(locations) >= 3:
                writer.writerow(['Conflict_Zone', 'Transit_Town', '75', '0'])
                writer.writerow(['Transit_Town', 'Refugee_Camp', '75', '0'])
        
        elif 'Bottleneck' in scenario_name:
            # Diamond network with bottleneck and alternative route
            if len(locations) >= 5:
                writer.writerow(['Origin', 'Bottleneck', '50', '0'])
                writer.writerow(['Origin', 'Alternative_Route', '80', '0'])
                writer.writerow(['Bottleneck', 'Destination', '50', '0'])
                writer.writerow(['Alternative_Route', 'Destination', '60', '0'])
                writer.writerow(['Bottleneck', 'Transit_Hub', '30', '0'])
                writer.writerow(['Transit_Hub', 'Destination', '30', '0'])
        
        elif 'Destination' in scenario_name:
            # Star network with multiple destination choices
            if len(locations) >= 5:
                writer.writerow(['Origin', 'Close_Safe_Camp', '30', '0'])
                writer.writerow(['Origin', 'Far_Excellent_Camp', '100', '0'])
                writer.writerow(['Origin', 'Medium_Good_Camp', '60', '0'])
                writer.writerow(['Origin', 'Risky_Nearby_Camp', '25', '0'])
        
        else:
            # Default: connect all locations in sequence
            for i in range(len(locations) - 1):
                loc1 = locations[i]['name']
                loc2 = locations[i + 1]['name']
                distance = ((locations[i+1]['x'] - locations[i]['x'])**2 + 
                           (locations[i+1]['y'] - locations[i]['y'])**2)**0.5
                writer.writerow([loc1, loc2, f"{distance:.1f}", '0'])
    
    print(f"✅ Generated: {routes_file}")

def generate_conflicts_csv(scenario_data: Dict, output_dir: Path):
    """Generate conflicts.csv file."""
    conflicts_file = output_dir / "conflicts.csv"
    
    with open(conflicts_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#Day', 'name', 'change'])
        
        # Add conflict events based on scenario
        scenario_name = scenario_data['scenario_name']
        total_days = scenario_data['total_days']
        
        if 'Evacuation' in scenario_name:
            # Escalating conflict in origin
            writer.writerow(['0', 'Conflict_Zone', '50'])  # Initial conflict
            if 'escalation' in scenario_name.lower():
                writer.writerow([f"{total_days//2}", 'Conflict_Zone', '100'])  # Mid-simulation escalation
        
        elif 'Bottleneck' in scenario_name:
            # Conflict that drives people to seek alternative routes
            writer.writerow(['0', 'Origin', '75'])
            writer.writerow([f"{total_days//3}", 'Bottleneck', '25'])  # Bottleneck becomes unsafe
        
        elif 'Destination' in scenario_name:
            # Conflict that forces destination choice
            writer.writerow(['0', 'Origin', '80'])
            writer.writerow([f"{total_days//2}", 'Risky_Nearby_Camp', '30'])  # Nearby camp becomes risky
    
    print(f"✅ Generated: {conflicts_file}")

def generate_sim_period_csv(scenario_data: Dict, output_dir: Path):
    """Generate sim_period.csv file."""
    sim_period_file = output_dir / "sim_period.csv"
    
    with open(sim_period_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['StartDate', 'Length'])
        writer.writerow(['2023-01-01', str(scenario_data['total_days'])])
    
    print(f"✅ Generated: {sim_period_file}")

def generate_closures_csv(scenario_data: Dict, output_dir: Path):
    """Generate closures.csv file (usually empty for our scenarios)."""
    closures_file = output_dir / "closures.csv"
    
    with open(closures_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#Day', 'name1', 'name2', 'closure_type'])
        # Most scenarios don't have closures, so leave empty
    
    print(f"✅ Generated: {closures_file}")

def generate_input_files_for_simulation(sim_dir: Path):
    """Generate all input files for a single simulation."""
    print(f"\\n📁 GENERATING INPUT FILES: {sim_dir.name}")
    print("=" * 60)
    
    # Extract scenario data
    scenario_data = extract_scenario_data_from_simulation(sim_dir)
    if not scenario_data:
        return False
    
    # Create input_files directory
    input_dir = sim_dir / "input_files"
    input_dir.mkdir(exist_ok=True)
    
    # Generate all CSV files
    generate_locations_csv(scenario_data, input_dir)
    generate_routes_csv(scenario_data, input_dir)
    generate_conflicts_csv(scenario_data, input_dir)
    generate_sim_period_csv(scenario_data, input_dir)
    generate_closures_csv(scenario_data, input_dir)
    
    # Generate README explaining the input files
    readme_file = input_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(f"# Input Files for {scenario_data['scenario_name']}\\n\\n")
        f.write(f"**Scenario**: {scenario_data['scenario_name']}\\n")
        f.write(f"**Duration**: {scenario_data['total_days']} days\\n")
        f.write(f"**Locations**: {len(scenario_data['locations'])} locations\\n\\n")
        
        f.write("## Files Generated\\n\\n")
        f.write("- **locations.csv**: Location definitions with coordinates and types\\n")
        f.write("- **routes.csv**: Network connections between locations\\n")
        f.write("- **conflicts.csv**: Conflict events over time\\n")
        f.write("- **sim_period.csv**: Simulation time period\\n")
        f.write("- **closures.csv**: Route closures (empty for this scenario)\\n\\n")
        
        f.write("## Location Details\\n\\n")
        for loc in scenario_data['locations']:
            f.write(f"- **{loc['name']}**: ({loc['x']}, {loc['y']}) - ")
            f.write(f"Conflict: {loc['conflict']:.2f}, Capacity: {loc['capacity']}\\n")
        
        f.write(f"\\n## Simulation Results\\n\\n")
        f.write(f"- **Total Decisions**: {len(scenario_data['decisions'])}\\n")
        f.write(f"- **Final Populations**: See standard_flee/out.csv\\n")
        f.write(f"- **S1/S2 Analysis**: See s1s2_diagnostics/\\n")
    
    print(f"✅ Generated: {readme_file}")
    print(f"✅ Input files completed for {scenario_data['scenario_name']}")
    
    return True

def main():
    """Generate input files for all simulations."""
    print("📁 FLEE INPUT FILE GENERATOR")
    print("=" * 50)
    print("Generating standard Flee CSV input files for each simulation.")
    print()
    
    # Find all simulation directories
    flee_sims_dir = Path("flee_simulations")
    
    if not flee_sims_dir.exists():
        print("❌ No flee_simulations directory found!")
        return
    
    # Get all simulation directories
    sim_dirs = [d for d in flee_sims_dir.iterdir() if d.is_dir() and d.name.startswith("flee_output_")]
    
    if not sim_dirs:
        print("❌ No simulation directories found!")
        return
    
    print(f"📂 Found {len(sim_dirs)} simulation directories")
    
    successful_generations = 0
    
    for sim_dir in sim_dirs:
        try:
            if generate_input_files_for_simulation(sim_dir):
                successful_generations += 1
        except Exception as e:
            print(f"❌ Error processing {sim_dir.name}: {e}")
    
    print(f"\\n📊 SUMMARY: {successful_generations}/{len(sim_dirs)} input file sets generated")
    
    if successful_generations > 0:
        print("\\n✅ Input file generation completed!")
        print("📁 Each simulation now has complete input_files/ directory")
        print("📄 Check input_files/README.md in each simulation for details")
    else:
        print("\\n❌ No input files generated successfully!")

if __name__ == "__main__":
    main()