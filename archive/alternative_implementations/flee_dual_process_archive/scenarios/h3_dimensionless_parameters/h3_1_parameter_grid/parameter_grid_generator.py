"""
H3.1 Parameter Grid Generator

Generates systematic parameter combinations for testing dimensionless parameter scaling laws.
Creates 175 parameter combinations across conflict_intensity × recovery_period × connectivity_rate space.
"""

import itertools
import numpy as np
from typing import List, Dict, Tuple
import json
import os


class ParameterGridGenerator:
    """Generates parameter grids for H3.1 dimensionless parameter testing."""
    
    def __init__(self):
        # Base parameter ranges
        self.conflict_intensities = [0.1, 0.3, 0.5, 0.7, 0.9]
        self.recovery_periods = [10, 20, 30, 40, 50]  # days
        self.connectivity_rates = [0.0, 2.0, 4.0, 6.0, 8.0]
        
        # Edge case parameters for phase boundary exploration
        self.edge_conflict_intensities = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85]
        self.edge_recovery_periods = [15, 25, 35, 45]
        self.edge_connectivity_rates = [1.0, 3.0, 5.0, 7.0]
    
    def calculate_cognitive_pressure(self, conflict_intensity: float, 
                                   recovery_period: float, 
                                   connectivity_rate: float) -> float:
        """
        Calculate the dimensionless cognitive pressure parameter.
        
        cognitive_pressure = (conflict_intensity × connectivity_rate) / (recovery_period / 30.0)
        
        Args:
            conflict_intensity: Conflict intensity level (0.0-1.0)
            recovery_period: Recovery period in days
            connectivity_rate: Social connectivity rate
            
        Returns:
            Dimensionless cognitive pressure value
        """
        return (conflict_intensity * connectivity_rate) / (recovery_period / 30.0)
    
    def generate_base_grid(self) -> List[Dict]:
        """Generate the base 5x5x5 parameter grid (125 combinations)."""
        combinations = []
        
        for conflict, recovery, connectivity in itertools.product(
            self.conflict_intensities, 
            self.recovery_periods, 
            self.connectivity_rates
        ):
            cognitive_pressure = self.calculate_cognitive_pressure(
                conflict, recovery, connectivity
            )
            
            combinations.append({
                'conflict_intensity': conflict,
                'recovery_period': recovery,
                'connectivity_rate': connectivity,
                'cognitive_pressure': cognitive_pressure,
                'experiment_type': 'base_grid'
            })
        
        return combinations
    
    def generate_edge_cases(self) -> List[Dict]:
        """Generate edge case combinations near predicted phase boundaries."""
        combinations = []
        
        # Target cognitive pressure ranges for edge exploration
        target_pressures = [0.4, 0.6, 1.4, 1.6]  # Around predicted transitions
        
        for target_pressure in target_pressures:
            # Generate combinations that produce cognitive pressure near target
            for conflict in self.edge_conflict_intensities:
                for connectivity in self.edge_connectivity_rates:
                    # Calculate required recovery period for target pressure
                    if connectivity > 0:  # Avoid division by zero
                        required_recovery = (conflict * connectivity * 30.0) / target_pressure
                        
                        # Use closest available recovery period
                        closest_recovery = min(self.edge_recovery_periods, 
                                             key=lambda x: abs(x - required_recovery))
                        
                        actual_pressure = self.calculate_cognitive_pressure(
                            conflict, closest_recovery, connectivity
                        )
                        
                        # Only include if reasonably close to target
                        if abs(actual_pressure - target_pressure) < 0.3:
                            combinations.append({
                                'conflict_intensity': conflict,
                                'recovery_period': closest_recovery,
                                'connectivity_rate': connectivity,
                                'cognitive_pressure': actual_pressure,
                                'experiment_type': 'edge_case',
                                'target_pressure': target_pressure
                            })
        
        # Remove duplicates and limit to 50 combinations
        unique_combinations = []
        seen = set()
        
        for combo in combinations:
            key = (combo['conflict_intensity'], combo['recovery_period'], combo['connectivity_rate'])
            if key not in seen:
                seen.add(key)
                unique_combinations.append(combo)
        
        return unique_combinations[:50]
    
    def generate_full_grid(self) -> List[Dict]:
        """Generate the complete 175-combination parameter grid."""
        base_combinations = self.generate_base_grid()
        edge_combinations = self.generate_edge_cases()
        
        all_combinations = base_combinations + edge_combinations
        
        # Add experiment IDs
        for i, combo in enumerate(all_combinations):
            combo['experiment_id'] = f"h3_1_grid_{i+1:03d}"
        
        return all_combinations
    
    def analyze_pressure_distribution(self, combinations: List[Dict]) -> Dict:
        """Analyze the distribution of cognitive pressure values."""
        pressures = [combo['cognitive_pressure'] for combo in combinations]
        
        return {
            'min_pressure': min(pressures),
            'max_pressure': max(pressures),
            'mean_pressure': np.mean(pressures),
            'std_pressure': np.std(pressures),
            'pressure_ranges': {
                'low (< 0.5)': len([p for p in pressures if p < 0.5]),
                'medium (0.5-1.5)': len([p for p in pressures if 0.5 <= p <= 1.5]),
                'high (> 1.5)': len([p for p in pressures if p > 1.5])
            }
        }
    
    def save_parameter_grid(self, output_dir: str) -> str:
        """Save the parameter grid to JSON file."""
        combinations = self.generate_full_grid()
        analysis = self.analyze_pressure_distribution(combinations)
        
        output_data = {
            'metadata': {
                'total_combinations': len(combinations),
                'base_grid_size': 125,
                'edge_cases': len([c for c in combinations if c['experiment_type'] == 'edge_case']),
                'generation_date': str(np.datetime64('now')),
                'cognitive_pressure_formula': '(conflict_intensity × connectivity_rate) / (recovery_period / 30.0)'
            },
            'pressure_analysis': analysis,
            'parameter_combinations': combinations
        }
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'h3_1_parameter_grid.json')
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        return output_file
    
    def get_combinations_by_pressure_range(self, combinations: List[Dict], 
                                         min_pressure: float, 
                                         max_pressure: float) -> List[Dict]:
        """Filter combinations by cognitive pressure range."""
        return [
            combo for combo in combinations 
            if min_pressure <= combo['cognitive_pressure'] <= max_pressure
        ]


def main():
    """Generate and save the H3.1 parameter grid."""
    generator = ParameterGridGenerator()
    
    # Generate full grid
    combinations = generator.generate_full_grid()
    
    print(f"Generated {len(combinations)} parameter combinations")
    
    # Analyze distribution
    analysis = generator.analyze_pressure_distribution(combinations)
    print(f"Cognitive pressure range: {analysis['min_pressure']:.3f} - {analysis['max_pressure']:.3f}")
    print(f"Pressure distribution: {analysis['pressure_ranges']}")
    
    # Save to file
    output_dir = os.path.dirname(__file__)
    output_file = generator.save_parameter_grid(output_dir)
    print(f"Parameter grid saved to: {output_file}")


if __name__ == "__main__":
    main()