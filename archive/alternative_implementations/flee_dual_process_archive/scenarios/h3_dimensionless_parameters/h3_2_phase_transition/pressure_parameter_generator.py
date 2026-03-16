"""
H3.2 Pressure Parameter Generator

Generates parameter combinations for fixed cognitive pressure values.
Creates 50 scenarios with cognitive_pressure from 0 to 2 for precise phase transition identification.
"""

import numpy as np
import itertools
from typing import List, Dict, Tuple, Optional
import json
import os


class PressureParameterGenerator:
    """Generates parameter combinations for fixed cognitive pressure values."""
    
    def __init__(self):
        # Base parameter ranges for combination generation
        self.base_conflict_intensities = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        self.base_connectivity_rates = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        
        # Constraints for realistic parameter values
        self.min_recovery_period = 5
        self.max_recovery_period = 60
        self.min_conflict_intensity = 0.05
        self.max_conflict_intensity = 1.0
        self.min_connectivity_rate = 0.0
        self.max_connectivity_rate = 10.0
    
    def calculate_required_recovery_period(self, cognitive_pressure: float,
                                         conflict_intensity: float,
                                         connectivity_rate: float) -> float:
        """
        Calculate required recovery period for target cognitive pressure.
        
        cognitive_pressure = (conflict_intensity × connectivity_rate) / (recovery_period / 30.0)
        => recovery_period = (conflict_intensity × connectivity_rate × 30.0) / cognitive_pressure
        
        Args:
            cognitive_pressure: Target cognitive pressure value
            conflict_intensity: Conflict intensity level
            connectivity_rate: Social connectivity rate
            
        Returns:
            Required recovery period in days
        """
        if cognitive_pressure <= 0:
            return float('inf')  # Infinite recovery period for zero pressure
        
        return (conflict_intensity * connectivity_rate * 30.0) / cognitive_pressure
    
    def generate_combinations_for_pressure(self, target_pressure: float,
                                         max_combinations: int = 5) -> List[Dict]:
        """
        Generate parameter combinations for a specific cognitive pressure value.
        
        Args:
            target_pressure: Target cognitive pressure value
            max_combinations: Maximum number of combinations to generate
            
        Returns:
            List of parameter combination dictionaries
        """
        combinations = []
        
        # Special case for zero pressure
        if target_pressure == 0.0:
            return [{
                'conflict_intensity': 0.0,
                'recovery_period': 30.0,  # Default recovery period
                'connectivity_rate': 0.0,
                'cognitive_pressure': 0.0,
                'generation_method': 'zero_pressure'
            }]
        
        # Generate combinations using different conflict/connectivity pairs
        for conflict in self.base_conflict_intensities:
            for connectivity in self.base_connectivity_rates:
                # Skip zero connectivity for non-zero pressure
                if connectivity == 0.0 and target_pressure > 0:
                    continue
                
                # Calculate required recovery period
                required_recovery = self.calculate_required_recovery_period(
                    target_pressure, conflict, connectivity
                )
                
                # Check if recovery period is within realistic bounds
                if (self.min_recovery_period <= required_recovery <= self.max_recovery_period):
                    # Verify the cognitive pressure calculation
                    actual_pressure = (conflict * connectivity) / (required_recovery / 30.0)
                    
                    # Only include if pressure is close to target (within 1% tolerance)
                    if abs(actual_pressure - target_pressure) / target_pressure < 0.01:
                        combinations.append({
                            'conflict_intensity': conflict,
                            'recovery_period': required_recovery,
                            'connectivity_rate': connectivity,
                            'cognitive_pressure': actual_pressure,
                            'generation_method': 'calculated',
                            'pressure_error': abs(actual_pressure - target_pressure)
                        })
                
                # Stop if we have enough combinations
                if len(combinations) >= max_combinations:
                    break
            
            if len(combinations) >= max_combinations:
                break
        
        # If we don't have enough combinations, try with intermediate values
        if len(combinations) < max_combinations:
            additional_combinations = self._generate_intermediate_combinations(
                target_pressure, max_combinations - len(combinations)
            )
            combinations.extend(additional_combinations)
        
        # Sort by pressure error (best matches first)
        combinations.sort(key=lambda x: x.get('pressure_error', float('inf')))
        
        return combinations[:max_combinations]
    
    def _generate_intermediate_combinations(self, target_pressure: float,
                                          needed_combinations: int) -> List[Dict]:
        """Generate additional combinations using intermediate parameter values."""
        combinations = []
        
        # Use finer-grained parameter values
        fine_conflicts = np.linspace(0.1, 0.9, 17)  # 17 values
        fine_connectivity = np.linspace(0.5, 8.0, 16)  # 16 values
        
        for conflict in fine_conflicts:
            for connectivity in fine_connectivity:
                required_recovery = self.calculate_required_recovery_period(
                    target_pressure, conflict, connectivity
                )
                
                if (self.min_recovery_period <= required_recovery <= self.max_recovery_period):
                    actual_pressure = (conflict * connectivity) / (required_recovery / 30.0)
                    
                    if abs(actual_pressure - target_pressure) / target_pressure < 0.02:  # 2% tolerance
                        combinations.append({
                            'conflict_intensity': conflict,
                            'recovery_period': required_recovery,
                            'connectivity_rate': connectivity,
                            'cognitive_pressure': actual_pressure,
                            'generation_method': 'intermediate',
                            'pressure_error': abs(actual_pressure - target_pressure)
                        })
                
                if len(combinations) >= needed_combinations:
                    break
            
            if len(combinations) >= needed_combinations:
                break
        
        return combinations
    
    def generate_pressure_series(self, n_scenarios: int = 50,
                               pressure_range: Tuple[float, float] = (0.0, 2.0)) -> List[Dict]:
        """
        Generate complete series of scenarios with evenly distributed cognitive pressure values.
        
        Args:
            n_scenarios: Number of scenarios to generate
            pressure_range: (min_pressure, max_pressure) tuple
            
        Returns:
            List of all parameter combinations for the pressure series
        """
        min_pressure, max_pressure = pressure_range
        
        # Generate evenly spaced pressure values
        pressure_values = np.linspace(min_pressure, max_pressure, n_scenarios)
        
        all_combinations = []
        
        for i, pressure in enumerate(pressure_values):
            # Generate combinations for this pressure value
            combinations = self.generate_combinations_for_pressure(pressure, max_combinations=1)
            
            if combinations:
                # Take the best combination and add scenario info
                best_combo = combinations[0]
                best_combo['scenario_id'] = f"h3_2_pressure_{i+1:02d}"
                best_combo['target_pressure'] = pressure
                best_combo['scenario_index'] = i
                
                all_combinations.append(best_combo)
            else:
                # If no valid combination found, create a warning entry
                print(f"Warning: No valid parameter combination found for pressure {pressure:.3f}")
                
                # Create a fallback combination
                fallback_combo = {
                    'scenario_id': f"h3_2_pressure_{i+1:02d}",
                    'target_pressure': pressure,
                    'scenario_index': i,
                    'conflict_intensity': 0.5,  # Default values
                    'recovery_period': 30.0,
                    'connectivity_rate': pressure * 2.0,  # Approximate
                    'cognitive_pressure': pressure,
                    'generation_method': 'fallback',
                    'pressure_error': 0.0
                }
                all_combinations.append(fallback_combo)
        
        return all_combinations
    
    def analyze_pressure_coverage(self, combinations: List[Dict]) -> Dict:
        """
        Analyze the coverage and quality of generated pressure combinations.
        
        Args:
            combinations: List of parameter combinations
            
        Returns:
            Dictionary with coverage analysis
        """
        if not combinations:
            return {'error': 'No combinations provided'}
        
        pressures = [combo['cognitive_pressure'] for combo in combinations]
        target_pressures = [combo['target_pressure'] for combo in combinations]
        errors = [combo.get('pressure_error', 0) for combo in combinations]
        
        # Calculate coverage statistics
        analysis = {
            'total_scenarios': len(combinations),
            'pressure_range': {
                'min_actual': min(pressures),
                'max_actual': max(pressures),
                'min_target': min(target_pressures),
                'max_target': max(target_pressures)
            },
            'pressure_accuracy': {
                'mean_error': np.mean(errors),
                'max_error': max(errors),
                'std_error': np.std(errors),
                'scenarios_within_1pct': sum(1 for e in errors if e < 0.01),
                'scenarios_within_5pct': sum(1 for e in errors if e < 0.05)
            },
            'generation_methods': {}
        }
        
        # Count generation methods
        for combo in combinations:
            method = combo.get('generation_method', 'unknown')
            analysis['generation_methods'][method] = analysis['generation_methods'].get(method, 0) + 1
        
        # Check for gaps in coverage
        sorted_pressures = sorted(pressures)
        gaps = []
        for i in range(1, len(sorted_pressures)):
            gap = sorted_pressures[i] - sorted_pressures[i-1]
            if gap > 0.1:  # Gap larger than 0.1 pressure units
                gaps.append({
                    'start': sorted_pressures[i-1],
                    'end': sorted_pressures[i],
                    'size': gap
                })
        
        analysis['coverage_gaps'] = gaps
        analysis['coverage_quality'] = 'excellent' if len(gaps) == 0 and np.mean(errors) < 0.01 else \
                                     'good' if len(gaps) <= 2 and np.mean(errors) < 0.05 else \
                                     'moderate'
        
        return analysis
    
    def save_pressure_series(self, output_dir: str, n_scenarios: int = 50) -> str:
        """
        Generate and save complete H3.2 pressure series.
        
        Args:
            output_dir: Directory to save the pressure series
            n_scenarios: Number of scenarios to generate
            
        Returns:
            Path to saved pressure series file
        """
        # Generate pressure series
        combinations = self.generate_pressure_series(n_scenarios)
        
        # Analyze coverage
        analysis = self.analyze_pressure_coverage(combinations)
        
        # Create output data
        output_data = {
            'metadata': {
                'scenario_type': 'h3_2_phase_transition',
                'total_scenarios': len(combinations),
                'pressure_range': [0.0, 2.0],
                'generation_date': str(np.datetime64('now')),
                'cognitive_pressure_formula': '(conflict_intensity × connectivity_rate) / (recovery_period / 30.0)'
            },
            'coverage_analysis': analysis,
            'parameter_combinations': combinations
        }
        
        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'h3_2_pressure_series.json')
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        return output_file
    
    def get_critical_region_scenarios(self, combinations: List[Dict],
                                    critical_pressure: float = 1.0,
                                    region_width: float = 0.4) -> List[Dict]:
        """
        Extract scenarios in the critical transition region.
        
        Args:
            combinations: List of all parameter combinations
            critical_pressure: Expected critical pressure value
            region_width: Width of critical region around critical pressure
            
        Returns:
            List of combinations in critical region
        """
        min_critical = critical_pressure - region_width / 2
        max_critical = critical_pressure + region_width / 2
        
        critical_scenarios = [
            combo for combo in combinations
            if min_critical <= combo['cognitive_pressure'] <= max_critical
        ]
        
        return critical_scenarios


def main():
    """Generate and analyze H3.2 pressure parameter series."""
    generator = PressureParameterGenerator()
    
    # Generate pressure series
    print("Generating H3.2 pressure parameter series...")
    combinations = generator.generate_pressure_series(n_scenarios=50)
    
    print(f"Generated {len(combinations)} scenarios")
    
    # Analyze coverage
    analysis = generator.analyze_pressure_coverage(combinations)
    print(f"Coverage quality: {analysis['coverage_quality']}")
    print(f"Mean pressure error: {analysis['pressure_accuracy']['mean_error']:.4f}")
    print(f"Scenarios within 1% error: {analysis['pressure_accuracy']['scenarios_within_1pct']}/50")
    
    # Show pressure distribution
    pressures = [combo['cognitive_pressure'] for combo in combinations]
    print(f"Pressure range: {min(pressures):.3f} - {max(pressures):.3f}")
    
    # Save to file
    output_dir = os.path.dirname(__file__)
    output_file = generator.save_pressure_series(output_dir)
    print(f"Pressure series saved to: {output_file}")
    
    # Show critical region scenarios
    critical_scenarios = generator.get_critical_region_scenarios(combinations)
    print(f"Critical region scenarios (0.8-1.2): {len(critical_scenarios)}")


if __name__ == "__main__":
    main()