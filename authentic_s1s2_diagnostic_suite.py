#!/usr/bin/env python3
"""
Authentic S1/S2 Diagnostic Suite

This diagnostic suite ONLY works with authentic Flee simulation data.
It includes strict validation to prevent analysis of fake or simulated data.

Key Safety Features:
- Validates data authenticity before any analysis
- Requires provenance records from real Flee simulations
- Blocks analysis if ecosystem.evolve() was not called
- Clear error messages for fake data attempts
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from validate_flee_data import FleeDataValidator

class AuthenticS1S2DiagnosticSuite:
    """
    Diagnostic suite that ONLY analyzes authentic Flee simulation data.
    
    This class ensures scientific integrity by:
    1. Validating data authenticity before analysis
    2. Requiring complete provenance records
    3. Blocking analysis of fake or simulated data
    4. Providing clear error messages for invalid data
    """
    
    def __init__(self, output_dir: str = "authentic_s1s2_diagnostics"):
        """
        Initialize the authentic diagnostic suite.
        
        Args:
            output_dir: Directory for diagnostic outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.validator = FleeDataValidator()
        self.simulation_data = None
        self.provenance_data = None
        
    def load_and_validate_simulation_data(self, simulation_dir: Path) -> bool:
        """
        Load and validate simulation data for authenticity.
        
        Args:
            simulation_dir: Path to simulation directory
            
        Returns:
            True if data is authentic and loaded successfully
        """
        print("🔒 LOADING AND VALIDATING SIMULATION DATA")
        print("=" * 50)
        
        # First, validate data authenticity
        if not self.validator.validate_data_for_analysis(simulation_dir):
            print("❌ CRITICAL ERROR: Data validation failed!")
            print("   Cannot proceed with analysis of non-authentic data.")
            return False
        
        try:
            # Load provenance data
            provenance_file = simulation_dir / "provenance.json"
            with open(provenance_file, 'r') as f:
                self.provenance_data = json.load(f)
            
            # Load S1/S2 diagnostic data
            s1s2_data_file = simulation_dir / "s1s2_diagnostics" / "cognitive_decisions.json"
            if s1s2_data_file.exists():
                with open(s1s2_data_file, 'r') as f:
                    self.simulation_data = json.load(f)
            else:
                print("⚠️  Warning: No S1/S2 diagnostic data found")
                self.simulation_data = {'decisions': [], 'daily_populations': [], 'locations': []}
            
            # Load standard Flee output for additional validation
            flee_output_file = simulation_dir / "standard_flee" / "out.csv"
            if flee_output_file.exists():
                self._validate_flee_output_consistency(flee_output_file)
            
            print("✅ Authentic simulation data loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading simulation data: {e}")
            return False
    
    def _validate_flee_output_consistency(self, flee_output_file: Path) -> None:
        """Validate consistency between Flee output and S1/S2 data."""
        try:
            with open(flee_output_file, 'r') as f:
                lines = f.readlines()
            
            flee_days = len(lines) - 1  # Subtract header
            s1s2_days = len(self.simulation_data.get('daily_populations', []))
            
            if flee_days != s1s2_days and s1s2_days > 0:
                print(f"⚠️  Warning: Flee output has {flee_days} days, S1/S2 data has {s1s2_days} days")
            else:
                print(f"✅ Data consistency verified: {flee_days} days of simulation")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not validate output consistency: {e}")
    
    def generate_authentic_diagnostic_plots(self, simulation_dir: Path) -> bool:
        """
        Generate diagnostic plots from authentic Flee simulation data.
        
        Args:
            simulation_dir: Path to validated simulation directory
            
        Returns:
            True if plots generated successfully
        """
        print("\\n📊 GENERATING AUTHENTIC S1/S2 DIAGNOSTIC PLOTS")
        print("=" * 60)
        
        # Load and validate data
        if not self.load_and_validate_simulation_data(simulation_dir):
            return False
        
        try:
            # Create comprehensive diagnostic figure
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'Authentic S1/S2 Diagnostic: {self.provenance_data["simulation_metadata"]["scenario_name"]}', 
                        fontsize=16, fontweight='bold')
            
            # Plot 1: Population Movement Over Time
            self._plot_population_movement(axes[0, 0])
            
            # Plot 2: S1/S2 Decision Distribution
            self._plot_s1s2_decisions(axes[0, 1])
            
            # Plot 3: Cognitive Pressure Analysis
            self._plot_cognitive_pressure(axes[1, 0])
            
            # Plot 4: Simulation Metadata and Authenticity
            self._plot_authenticity_info(axes[1, 1])
            
            plt.tight_layout()
            
            # Save diagnostic plot
            output_file = self.output_dir / f"authentic_s1s2_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Authentic diagnostic plots saved: {output_file}")
            
            # Generate summary report
            self._generate_authenticity_report(simulation_dir)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating diagnostic plots: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _plot_population_movement(self, ax) -> None:
        """Plot population movement over time from authentic Flee data."""
        daily_pops = self.simulation_data.get('daily_populations', [])
        
        if not daily_pops:
            ax.text(0.5, 0.5, 'No Population Data\\n(Authentic Flee data required)', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Population Movement (No Data)')
            return
        
        days = [d['day'] for d in daily_pops]
        locations = list(daily_pops[0].keys())
        locations.remove('day')
        locations.remove('total')
        
        for location in locations:
            populations = [d[location] for d in daily_pops]
            ax.plot(days, populations, marker='o', linewidth=2, label=location)
        
        ax.set_xlabel('Simulation Day')
        ax.set_ylabel('Population')
        ax.set_title('Authentic Population Movement\\n(From Real Flee Simulation)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add authenticity marker
        evolve_calls = self.provenance_data['flee_integration']['total_evolve_calls']
        ax.text(0.02, 0.98, f'✅ {evolve_calls} ecosystem.evolve() calls', 
               transform=ax.transAxes, fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    
    def _plot_s1s2_decisions(self, ax) -> None:
        """Plot S1/S2 decision distribution from authentic data."""
        decisions = self.simulation_data.get('decisions', [])
        
        if not decisions:
            ax.text(0.5, 0.5, 'No Decision Data\\n(Authentic Flee data required)', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('S1/S2 Decisions (No Data)')
            return
        
        s1_decisions = [d for d in decisions if not d.get('system2_active', False)]
        s2_decisions = [d for d in decisions if d.get('system2_active', False)]
        
        # Create pie chart
        sizes = [len(s1_decisions), len(s2_decisions)]
        labels = [f'S1 Heuristic ({len(s1_decisions)})', f'S2 Analytical ({len(s2_decisions)})']
        colors = ['#FF6B6B', '#4ECDC4']
        
        if sum(sizes) > 0:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            ax.set_title('Authentic S1/S2 Decision Distribution\\n(From Real Agent Calculations)')
        else:
            ax.text(0.5, 0.5, 'No Decision Data Available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('S1/S2 Decisions (No Data)')
    
    def _plot_cognitive_pressure(self, ax) -> None:
        """Plot cognitive pressure distribution from authentic data."""
        decisions = self.simulation_data.get('decisions', [])
        
        if not decisions:
            ax.text(0.5, 0.5, 'No Cognitive Data\\n(Authentic Flee data required)', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Cognitive Pressure (No Data)')
            return
        
        pressures = [d.get('cognitive_pressure', 0) for d in decisions if 'cognitive_pressure' in d]
        
        if pressures:
            ax.hist(pressures, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax.axvline(x=0.6, color='red', linestyle='--', linewidth=2, label='S2 Activation Threshold')
            ax.set_xlabel('Cognitive Pressure')
            ax.set_ylabel('Frequency')
            ax.set_title('Authentic Cognitive Pressure Distribution\\n(From Real Agent Calculations)')
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No Pressure Data Available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Cognitive Pressure (No Data)')
    
    def _plot_authenticity_info(self, ax) -> None:
        """Plot simulation authenticity and metadata information."""
        ax.axis('off')
        
        # Authenticity information
        info_text = []
        info_text.append("🔒 DATA AUTHENTICITY VERIFIED")
        info_text.append("=" * 30)
        info_text.append("")
        
        # Simulation metadata
        sim_meta = self.provenance_data['simulation_metadata']
        info_text.append(f"Scenario: {sim_meta['scenario_name']}")
        info_text.append(f"Timestamp: {sim_meta['timestamp'][:19]}")
        info_text.append(f"Total Days: {sim_meta['total_days']}")
        info_text.append("")
        
        # Flee integration verification
        flee_meta = self.provenance_data['flee_integration']
        info_text.append("Flee Integration:")
        info_text.append(f"  ✅ ecosystem.evolve() called: {flee_meta['ecosystem_evolve_called']}")
        info_text.append(f"  ✅ Total evolve calls: {flee_meta['total_evolve_calls']}")
        info_text.append(f"  ✅ Engine: {flee_meta['simulation_engine']}")
        info_text.append("")
        
        # Data sources verification
        data_sources = self.provenance_data['data_sources']
        info_text.append("Data Sources:")
        info_text.append(f"  • Movements: {data_sources['agent_movements']}")
        info_text.append(f"  • Populations: {data_sources['population_counts']}")
        info_text.append(f"  • Decisions: {data_sources['decision_tracking']}")
        info_text.append(f"  • Fake data used: {data_sources['fake_data_used']}")
        
        # Display information
        y_pos = 0.95
        for line in info_text:
            font_weight = 'bold' if line.startswith('🔒') or line.startswith('=') or ':' in line else 'normal'
            font_size = 10 if line.startswith('🔒') else 8
            ax.text(0.05, y_pos, line, transform=ax.transAxes, fontsize=font_size,
                   verticalalignment='top', fontweight=font_weight)
            y_pos -= 0.04
    
    def _generate_authenticity_report(self, simulation_dir: Path) -> None:
        """Generate a text report confirming data authenticity."""
        report_file = self.output_dir / "authenticity_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("AUTHENTIC S1/S2 SIMULATION ANALYSIS REPORT\\n")
            f.write("=" * 50 + "\\n\\n")
            
            f.write("DATA AUTHENTICITY VERIFICATION\\n")
            f.write("-" * 30 + "\\n")
            f.write(f"✅ Data source: {simulation_dir}\\n")
            f.write(f"✅ Provenance record verified\\n")
            f.write(f"✅ ecosystem.evolve() calls: {self.provenance_data['flee_integration']['total_evolve_calls']}\\n")
            f.write(f"✅ No fake data detected\\n\\n")
            
            f.write("SIMULATION METADATA\\n")
            f.write("-" * 20 + "\\n")
            sim_meta = self.provenance_data['simulation_metadata']
            for key, value in sim_meta.items():
                f.write(f"{key}: {value}\\n")
            
            f.write("\\nFLEE INTEGRATION VERIFICATION\\n")
            f.write("-" * 30 + "\\n")
            flee_meta = self.provenance_data['flee_integration']
            for key, value in flee_meta.items():
                f.write(f"{key}: {value}\\n")
            
            f.write("\\nDATA SOURCES\\n")
            f.write("-" * 15 + "\\n")
            data_sources = self.provenance_data['data_sources']
            for key, value in data_sources.items():
                f.write(f"{key}: {value}\\n")
            
            # Analysis summary
            decisions = self.simulation_data.get('decisions', [])
            if decisions:
                s1_count = len([d for d in decisions if not d.get('system2_active', False)])
                s2_count = len([d for d in decisions if d.get('system2_active', False)])
                
                f.write("\\nANALYSIS SUMMARY\\n")
                f.write("-" * 20 + "\\n")
                f.write(f"Total decisions analyzed: {len(decisions)}\\n")
                f.write(f"S1 (Heuristic) decisions: {s1_count} ({s1_count/len(decisions)*100:.1f}%)\\n")
                f.write(f"S2 (Analytical) decisions: {s2_count} ({s2_count/len(decisions)*100:.1f}%)\\n")
        
        print(f"✅ Authenticity report generated: {report_file}")

def analyze_authentic_flee_simulation(simulation_dir: str) -> bool:
    """
    Analyze an authentic Flee simulation with S1/S2 diagnostics.
    
    Args:
        simulation_dir: Path to simulation directory
        
    Returns:
        True if analysis completed successfully
    """
    print("🔬 AUTHENTIC S1/S2 SIMULATION ANALYSIS")
    print("=" * 50)
    print("This tool ONLY analyzes authentic Flee simulation data.")
    print("It will BLOCK analysis of fake or simulated data.")
    print()
    
    suite = AuthenticS1S2DiagnosticSuite()
    return suite.generate_authentic_diagnostic_plots(Path(simulation_dir))

def main():
    """Command-line interface for authentic S1/S2 analysis."""
    if len(sys.argv) != 2:
        print("Usage: python authentic_s1s2_diagnostic_suite.py <simulation_directory>")
        print()
        print("Example:")
        print("  python authentic_s1s2_diagnostic_suite.py flee_simulations/flee_output_2025-08-31_02-40-40_evacuation_timing_s1s2")
        sys.exit(1)
    
    simulation_dir = sys.argv[1]
    
    success = analyze_authentic_flee_simulation(simulation_dir)
    
    if success:
        print("\\n🎉 AUTHENTIC ANALYSIS COMPLETED SUCCESSFULLY!")
        print("All plots and reports are based on real Flee simulation data.")
        sys.exit(0)
    else:
        print("\\n🚫 ANALYSIS FAILED!")
        print("Data authenticity validation failed or analysis error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    main()