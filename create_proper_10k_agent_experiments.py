#!/usr/bin/env python3
"""
Create Proper 10k Agent Experiments with Input Files
- Generate proper Flee input files for 10k agent experiments
- Save all input files for reproducibility
- Run with actual Flee framework using input files
"""

import sys
import os
import csv
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
import shutil
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

class Proper10kAgentExperiments:
    """Create proper 10k agent experiments with input files"""
    
    def __init__(self, output_dir="proper_10k_agent_experiments"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Test configurations for 10k agents - even numbers for better layouts
        # Geometric progression: 4, 8, 16 nodes
        # S1/S2 scenarios: low_s2, medium_s2, high_s2
        self.test_configs = []
        
        # FOR COLLEAGUE MEETING: 5 topologies × 4 scenarios = 20 experiments
        topologies = ['star', 'linear', 'grid']  # Add hierarchical, irregular_grid later if needed
        size = 8  # Fixed size for colleague meeting
        scenarios = ['baseline', 'low_s2', 'medium_s2', 'high_s2']  # Added baseline
        population = 5000  # Smaller population for faster runs
        
        for topology in topologies:
            for scenario in scenarios:
                self.test_configs.append({
                    'topology': topology,
                    'size': size,
                    'scenario': scenario,
                    'population': population
                })
        
    def create_all_10k_experiments(self):
        """Create all 10k agent experiments with proper input files"""
        
        print("🚀 Creating Proper 10k Agent Experiments with Input Files")
        print("=" * 70)
        
        for config in self.test_configs:
            print(f"\n🧪 Creating {config['topology']} n={config['size']} {config['scenario']} with {config['population']} agents...")
            self._create_single_10k_experiment(config)
        
        print(f"\n🎉 All 10k agent experiments created in {self.output_dir}")
        self._create_summary_report()
    
    def _create_single_10k_experiment(self, config):
        """Create a single 10k agent experiment with proper input files"""
        
        # Create experiment directory
        exp_name = f"{config['topology']}_n{config['size']}_{config['scenario']}_{config['population']}"
        exp_dir = self.output_dir / exp_name
        exp_dir.mkdir(exist_ok=True)
        
        # Create input_csv directory
        input_csv_dir = exp_dir / "input_csv"
        input_csv_dir.mkdir(exist_ok=True)
        
        # Create source_data directory
        source_data_dir = exp_dir / "source_data"
        source_data_dir.mkdir(exist_ok=True)
        
        # 1. Generate network topology
        topology_data = self._generate_network_topology(config['topology'], config['size'])
        
        # 2. Create locations.csv
        self._create_locations_csv(topology_data, input_csv_dir)
        
        # 3. Create routes.csv
        self._create_routes_csv(topology_data, input_csv_dir)
        
        # 4. Create conflicts.csv
        self._create_conflicts_csv(topology_data, input_csv_dir)
        
        # 5. Create closures.csv
        self._create_closures_csv(topology_data, input_csv_dir)
        
        # 6. Create simsetting.yml
        self._create_simsetting_yml(config, exp_dir)
        
        # 7. Create refugee data files
        self._create_refugee_data_files(config, topology_data, source_data_dir)
        
        # 8. Create sim_period.csv
        self._create_sim_period_csv(exp_dir)
        
        # 9. Save experiment metadata
        self._save_experiment_metadata(config, topology_data, exp_dir)
        
        print(f"  ✅ Input files created in {exp_dir}")
        print(f"  📁 Input files: locations.csv, routes.csv, conflicts.csv, closures.csv")
        print(f"  📁 Source data: data_layout.csv, refugees.csv")
        print(f"  📁 Config: simsetting.yml, sim_period.csv")
        print(f"  📁 Metadata: experiment_metadata.json")
    
    def _generate_network_topology(self, topology_type, n_nodes):
        """Generate network topology with proper star network setup"""
        
        locations = []
        routes = []
        
        if topology_type == 'linear':
            for i in range(n_nodes):
                if i == 0:
                    locations.append({
                        'name': f'Origin_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'conflict', 'pop': 10000, 'country': 'TestCountry'  # ALL agents start here
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'town', 'pop': 0, 'country': 'TestCountry'  # No initial population
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'camp', 'pop': 0, 'country': 'TestCountry'  # No initial population
                    })
            
            for i in range(n_nodes - 1):
                routes.append({
                    'from': locations[i]['name'],
                    'to': locations[i + 1]['name'],
                    'distance': 100.0
                })
        
        elif topology_type == 'star':
            # FIXED: All agents start at origin only
            locations.append({
                'name': f'Origin_{topology_type}_{n_nodes}',
                'x': 0.0, 'y': 0.0,
                'type': 'conflict', 'pop': 10000, 'country': 'TestCountry'  # ALL agents start here
            })
            
            # Hub
            locations.append({
                'name': f'Hub_{topology_type}_{n_nodes}',
                'x': 3.0, 'y': 0.0,
                'type': 'town', 'pop': 0, 'country': 'TestCountry'  # No initial population
            })
            
            # Camps in star pattern
            for i in range(2, n_nodes):
                angle = 2 * np.pi * (i - 2) / (n_nodes - 2)
                x = 6.0 * np.cos(angle)
                y = 6.0 * np.sin(angle)
                locations.append({
                    'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                    'x': x, 'y': y,
                    'type': 'camp', 'pop': 0, 'country': 'TestCountry'  # No initial population
                })
            
            # Create star connections
            routes.append({
                'from': locations[0]['name'],
                'to': locations[1]['name'],
                'distance': 100.0
            })
            
            for i in range(2, n_nodes):
                routes.append({
                    'from': locations[1]['name'],
                    'to': locations[i]['name'],
                    'distance': 100.0
                })
        
        elif topology_type == 'grid':
            grid_size = int(np.ceil(np.sqrt(n_nodes)))
            locations = []
            
            # Create grid locations
            for i in range(n_nodes):
                row = i // grid_size
                col = i % grid_size
                
                if i == 0:
                    locations.append({
                        'name': f'Origin_{topology_type}_{n_nodes}',
                        'x': float(col * 3), 'y': float(row * 3),
                        'type': 'conflict', 'pop': 10000, 'country': 'TestCountry'  # ALL agents start here
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 3), 'y': float(row * 3),
                        'type': 'town', 'pop': 0, 'country': 'TestCountry'  # No initial population
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 3), 'y': float(row * 3),
                        'type': 'camp', 'pop': 0, 'country': 'TestCountry'  # No initial population
                    })
            
            # Create grid routes
            for i in range(n_nodes):
                row = i // grid_size
                col = i % grid_size
                
                # Right neighbor
                if col < grid_size - 1 and i + 1 < n_nodes:
                    routes.append({
                        'from': locations[i]['name'],
                        'to': locations[i + 1]['name'],
                        'distance': 100.0
                    })
                
                # Bottom neighbor
                if row < grid_size - 1 and i + grid_size < n_nodes:
                    routes.append({
                        'from': locations[i]['name'],
                        'to': locations[i + grid_size]['name'],
                        'distance': 100.0
                    })
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'locations': locations,
            'routes': routes
        }
    
    def _create_locations_csv(self, topology_data, input_csv_dir):
        """Create locations.csv file"""
        
        locations_data = []
        for loc in topology_data['locations']:
            locations_data.append({
                'name': loc['name'],
                'region': 'TestRegion',
                'country': loc['country'],
                'gps_x': loc['x'],
                'gps_y': loc['y'],
                'location_type': loc['type'],
                'conflict_date': 0 if loc['type'] == 'conflict' else 0,
                'pop/cap': loc['pop']
            })
        
        df = pd.DataFrame(locations_data)
        # Add # prefix to header for proper parsing
        with open(input_csv_dir / "locations.csv", 'w') as f:
            f.write('#')
            df.to_csv(f, index=False)
    
    def _create_routes_csv(self, topology_data, input_csv_dir):
        """Create routes.csv file"""
        
        routes_data = []
        for route in topology_data['routes']:
            routes_data.append({
                'name1': route['from'],
                'name2': route['to'],
                'distance': route['distance'],
                'forced_redirection': '',
                'blocked': 0
            })
        
        df = pd.DataFrame(routes_data)
        # Add # prefix to header for proper parsing
        with open(input_csv_dir / "routes.csv", 'w') as f:
            f.write('#')
            df.to_csv(f, index=False)
    
    def _create_conflicts_csv(self, topology_data, input_csv_dir):
        """Create conflicts.csv file"""
        
        # Create conflicts.csv with time-based format
        conflict_locations = [loc['name'] for loc in topology_data['locations'] if loc['type'] == 'conflict']
        
        if conflict_locations:
            # Create time series data (20 days)
            conflicts_data = {'Day': list(range(21))}  # 0 to 20 days
            
            for loc in conflict_locations:
                # Start with no conflict for first 2 days, then ramp up
                conflict_values = [0.0, 0.0] + [1.0] * 19  # No conflict days 0-1, then high conflict
                conflicts_data[loc] = conflict_values
            
            df = pd.DataFrame(conflicts_data)
            # Add # prefix to header for proper parsing
            with open(input_csv_dir / "conflicts.csv", 'w') as f:
                f.write('#')
                df.to_csv(f, index=False)
        else:
            # Empty conflicts file
            df = pd.DataFrame(columns=['Day'])
            # Add # prefix to header for proper parsing
            with open(input_csv_dir / "conflicts.csv", 'w') as f:
                f.write('#')
                df.to_csv(f, index=False)
    
    def _create_closures_csv(self, topology_data, input_csv_dir):
        """Create closures.csv file"""
        
        # Empty closures file
        df = pd.DataFrame(columns=['name1', 'name2', 'closure_start', 'closure_end'])
        # Add # prefix to header for proper parsing
        with open(input_csv_dir / "closures.csv", 'w') as f:
            f.write('#')
            df.to_csv(f, index=False)
    
    def _create_simsetting_yml(self, config, exp_dir):
        """Create simsetting.yml file"""
        
        # Determine S2 threshold based on scenario
        s2_thresholds = {
            'baseline': 0.0,    # No S2 switching
            'low_s2': 0.3,
            'medium_s2': 0.5,
            'high_s2': 0.7
        }
        s2_threshold = s2_thresholds.get(config['scenario'], 0.5)
        
        simsetting_content = f"""log_levels:
  agent: 1
  link: 1
  camp: 0
  conflict: 0
  init: 0
  granularity: location
spawn_rules:
  take_from_population: False
  insert_day0: True
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 0.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  weight_power: 1.0
  movechance_pop_base: 10000.0
  movechance_pop_scale_factor: 0.5
  two_system_decision_making: {s2_threshold}
optimisations:
  hasten: 1
"""
        
        with open(exp_dir / "simsetting.yml", "w") as f:
            f.write(simsetting_content)
    
    def _create_refugee_data_files(self, config, topology_data, source_data_dir):
        """Create refugee data files"""
        
        # Create data_layout.csv
        data_layout = {
            'Location': [loc['name'] for loc in topology_data['locations'] if loc['type'] in ['camp', 'conflict']],
            'refugees.csv': ['refugees.csv'] * len([loc for loc in topology_data['locations'] if loc['type'] in ['camp', 'conflict']])
        }
        df_layout = pd.DataFrame(data_layout)
        df_layout.to_csv(source_data_dir / "data_layout.csv", index=False)
        
        # Create refugees.csv with initial data (20 days)
        # Format: Date,Location1,Location2,Location3,...
        # Include both camps and conflict locations
        refugee_locations = [loc['name'] for loc in topology_data['locations'] if loc['type'] in ['camp', 'conflict']]
        
        refugees_data = {'Date': []}
        for loc in refugee_locations:
            refugees_data[loc] = []
        
        for day in range(21):  # 0 to 20 days
            refugees_data['Date'].append(f'2023-01-{day+1:02d}')
            for loc in refugee_locations:
                refugees_data[loc].append(0)  # Start with 0, will be populated by simulation
        
        df_refugees = pd.DataFrame(refugees_data)
        df_refugees.to_csv(source_data_dir / "refugees.csv", index=False)
    
    def _create_sim_period_csv(self, exp_dir):
        """Create sim_period.csv file"""
        
        sim_period_data = [
            ['startdate', '2013-01-01'],
            ['length', '20']  # 20 days
        ]
        
        with open(exp_dir / "sim_period.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(sim_period_data)
    
    def _save_experiment_metadata(self, config, topology_data, exp_dir):
        """Save experiment metadata"""
        
        metadata = {
            'experiment_name': f"{config['topology']}_n{config['size']}_{config['scenario']}_10k",
            'topology': config['topology'],
            'network_size': config['size'],
            'scenario': config['scenario'],
            'population_size': config['population'],
            'simulation_days': 20,
            'created_at': datetime.now().isoformat(),
            'topology_data': topology_data,
            'input_files': [
                'input_csv/locations.csv',
                'input_csv/routes.csv',
                'input_csv/conflicts.csv',
                'input_csv/closures.csv',
                'source_data/data_layout.csv',
                'source_data/refugees.csv',
                'simsetting.yml',
                'sim_period.csv'
            ]
        }
        
        with open(exp_dir / "experiment_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def _create_summary_report(self):
        """Create summary report"""
        
        summary = {
            'total_experiments': len(self.test_configs),
            'experiments': [],
            'created_at': datetime.now().isoformat()
        }
        
        for config in self.test_configs:
            exp_name = f"{config['topology']}_n{config['size']}_{config['scenario']}_10k"
            exp_dir = self.output_dir / exp_name
            
            summary['experiments'].append({
                'name': exp_name,
                'topology': config['topology'],
                'network_size': config['size'],
                'scenario': config['scenario'],
                'population': config['population'],
                'directory': str(exp_dir),
                'input_files_created': [
                    'input_csv/locations.csv',
                    'input_csv/routes.csv',
                    'input_csv/conflicts.csv',
                    'input_csv/closures.csv',
                    'source_data/data_layout.csv',
                    'source_data/refugees.csv',
                    'simsetting.yml',
                    'sim_period.csv',
                    'experiment_metadata.json'
                ]
            })
        
        with open(self.output_dir / "experiments_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Create markdown summary
        md_summary = f"""# Proper 10k Agent Experiments - Summary

**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Experiments Created

**Total**: {len(self.test_configs)} experiments with 10,000 agents each

### Experiment List:

"""
        
        for config in self.test_configs:
            exp_name = f"{config['topology']}_n{config['size']}_{config['scenario']}_10k"
            md_summary += f"""#### {exp_name}
- **Topology**: {config['topology'].title()}
- **Network Size**: {config['size']} nodes
- **Scenario**: {config['scenario']}
- **Population**: {config['population']:,} agents
- **Directory**: `{exp_name}/`

**Input Files Created:**
- `input_csv/locations.csv` - Network locations
- `input_csv/routes.csv` - Network connections
- `input_csv/conflicts.csv` - Conflict zones
- `input_csv/closures.csv` - Route closures
- `source_data/data_layout.csv` - Refugee data layout
- `source_data/refugees.csv` - Refugee data
- `simsetting.yml` - Simulation settings
- `sim_period.csv` - Simulation period
- `experiment_metadata.json` - Experiment metadata

"""
        
        md_summary += f"""
## 📁 Directory Structure

```
{self.output_dir.name}/
"""
        
        for config in self.test_configs:
            exp_name = f"{config['topology']}_n{config['size']}_{config['scenario']}_10k"
            md_summary += f"""├── {exp_name}/
│   ├── input_csv/
│   │   ├── locations.csv
│   │   ├── routes.csv
│   │   ├── conflicts.csv
│   │   └── closures.csv
│   ├── source_data/
│   │   ├── data_layout.csv
│   │   └── refugees.csv
│   ├── simsetting.yml
│   ├── sim_period.csv
│   └── experiment_metadata.json
"""
        
        md_summary += f"""└── experiments_summary.json
```

## 🎯 Next Steps

1. **Run Flee simulations** using the created input files
2. **Compare results** with smaller population experiments
3. **Validate stochastic stability** with 10k agents
4. **Generate visualizations** from the results

## 🔬 Scientific Value

- **Stochastic stability**: 10k agents provide robust statistical results
- **Input file preservation**: All input files saved for reproducibility
- **Proper Flee integration**: Uses actual Flee input file format
- **Metadata tracking**: Complete experiment documentation

**Ready for proper Flee execution with 10,000 agents!** 🚀
"""
        
        with open(self.output_dir / "EXPERIMENTS_SUMMARY.md", 'w') as f:
            f.write(md_summary)
        
        print(f"  📊 Summary report created: {self.output_dir}/EXPERIMENTS_SUMMARY.md")

def main():
    """Main function"""
    
    # Create and run experiments
    creator = Proper10kAgentExperiments()
    creator.create_all_10k_experiments()

if __name__ == "__main__":
    main()
