#!/usr/bin/env python3
"""
Flee Data Authenticity Validator

This utility validates that simulation data comes from authentic Flee runs.
It prevents analysis of fake or simulated data by checking for proper provenance.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

class FleeDataValidator:
    """
    Validates the authenticity of Flee simulation data.
    
    This class ensures that:
    1. Data comes from real ecosystem.evolve() calls
    2. Proper provenance records exist
    3. Standard Flee output files are present
    4. No fake data is used in analysis
    """
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_simulation_directory(self, sim_dir: Path) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a complete simulation directory for authenticity.
        
        Args:
            sim_dir: Path to simulation directory
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        print(f"🔍 VALIDATING SIMULATION DIRECTORY: {sim_dir}")
        print("=" * 60)
        
        if not sim_dir.exists():
            self.validation_errors.append(f"Simulation directory does not exist: {sim_dir}")
            return False, self._create_validation_report()
        
        # Check directory structure
        self._validate_directory_structure(sim_dir)
        
        # Check provenance record
        provenance_data = self._validate_provenance_record(sim_dir)
        
        # Check standard Flee output
        self._validate_standard_flee_output(sim_dir)
        
        # Check for authenticity markers
        self._validate_authenticity_markers(provenance_data)
        
        # Create validation report
        is_valid = len(self.validation_errors) == 0
        report = self._create_validation_report()
        
        return is_valid, report
    
    def _validate_directory_structure(self, sim_dir: Path) -> None:
        """Validate expected directory structure."""
        expected_dirs = ["standard_flee", "s1s2_diagnostics"]
        
        for dir_name in expected_dirs:
            dir_path = sim_dir / dir_name
            if not dir_path.exists():
                self.validation_errors.append(f"Missing required directory: {dir_name}")
            else:
                print(f"✅ Found directory: {dir_name}")
    
    def _validate_provenance_record(self, sim_dir: Path) -> Dict[str, Any]:
        """Validate provenance record exists and contains required information."""
        provenance_file = sim_dir / "provenance.json"
        
        if not provenance_file.exists():
            self.validation_errors.append("Missing provenance.json file - cannot verify data authenticity")
            return {}
        
        try:
            with open(provenance_file, 'r') as f:
                provenance_data = json.load(f)
            
            print("✅ Found provenance.json file")
            
            # Check required provenance fields
            required_fields = [
                'simulation_metadata',
                'flee_integration', 
                'data_sources',
                'output_files'
            ]
            
            for field in required_fields:
                if field not in provenance_data:
                    self.validation_errors.append(f"Missing provenance field: {field}")
                else:
                    print(f"✅ Provenance field present: {field}")
            
            return provenance_data
            
        except json.JSONDecodeError as e:
            self.validation_errors.append(f"Invalid provenance.json format: {e}")
            return {}
    
    def _validate_standard_flee_output(self, sim_dir: Path) -> None:
        """Validate standard Flee output files exist and have proper format."""
        flee_dir = sim_dir / "standard_flee"
        out_csv = flee_dir / "out.csv"
        
        if not out_csv.exists():
            self.validation_errors.append("Missing standard Flee output file: out.csv")
            return
        
        try:
            with open(out_csv, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                self.validation_errors.append("out.csv file is too short - may be incomplete")
                return
            
            # Check header format
            header = lines[0].strip()
            if not header.startswith("Day,Date"):
                self.validation_warnings.append("out.csv header format may not be standard Flee format")
            else:
                print("✅ Standard Flee out.csv format detected")
            
            # Check for data rows
            data_rows = len(lines) - 1
            print(f"✅ Found {data_rows} days of simulation data in out.csv")
            
        except Exception as e:
            self.validation_errors.append(f"Error reading out.csv: {e}")
    
    def _validate_authenticity_markers(self, provenance_data: Dict[str, Any]) -> None:
        """Validate authenticity markers in provenance data."""
        if not provenance_data:
            return
        
        flee_integration = provenance_data.get('flee_integration', {})
        data_sources = provenance_data.get('data_sources', {})
        
        # Check ecosystem.evolve() calls
        evolve_called = flee_integration.get('ecosystem_evolve_called', False)
        evolve_calls = flee_integration.get('total_evolve_calls', 0)
        
        if not evolve_called or evolve_calls == 0:
            self.validation_errors.append("No ecosystem.evolve() calls detected - data may be fake")
        else:
            print(f"✅ Authentic Flee simulation detected: {evolve_calls} ecosystem.evolve() calls")
        
        # Check for fake data markers
        fake_data_used = data_sources.get('fake_data_used', True)  # Default to True for safety
        if fake_data_used:
            self.validation_errors.append("Provenance indicates fake data was used")
        else:
            print("✅ No fake data detected in provenance record")
        
        # Check simulation engine
        sim_engine = flee_integration.get('simulation_engine', 'Unknown')
        if sim_engine != 'Authentic Flee':
            self.validation_warnings.append(f"Simulation engine: {sim_engine} (expected: Authentic Flee)")
        else:
            print("✅ Authentic Flee simulation engine confirmed")
    
    def _create_validation_report(self) -> Dict[str, Any]:
        """Create a comprehensive validation report."""
        return {
            'is_valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings)
        }
    
    def validate_data_for_analysis(self, data_source: Path) -> bool:
        """
        Validate data before allowing analysis - this is the main safety check.
        
        Args:
            data_source: Path to simulation directory or data file
            
        Returns:
            True if data is safe to analyze, False otherwise
        """
        print("🛡️  FLEE DATA AUTHENTICITY CHECK")
        print("=" * 40)
        print("Validating data before analysis to prevent use of fake data...")
        
        if data_source.is_dir():
            # Validate simulation directory
            is_valid, report = self.validate_simulation_directory(data_source)
        else:
            # Check if it's part of a simulation directory
            sim_dir = data_source.parent
            while sim_dir != sim_dir.parent:
                if (sim_dir / "provenance.json").exists():
                    is_valid, report = self.validate_simulation_directory(sim_dir)
                    break
                sim_dir = sim_dir.parent
            else:
                print("❌ ERROR: Cannot find provenance record for data file")
                print(f"   Data file: {data_source}")
                print("   This data cannot be verified as authentic Flee simulation data.")
                return False
        
        # Display validation results
        if is_valid:
            print("\\n✅ DATA AUTHENTICITY VERIFIED")
            print("   This data comes from a real Flee simulation.")
            print("   Safe to proceed with analysis.")
            
            if report['warning_count'] > 0:
                print(f"\\n⚠️  {report['warning_count']} warnings:")
                for warning in report['warnings']:
                    print(f"   • {warning}")
            
            return True
        else:
            print("\\n❌ DATA AUTHENTICITY VALIDATION FAILED")
            print("   This data is NOT from an authentic Flee simulation.")
            print("   Analysis is BLOCKED to prevent use of fake data.")
            
            print(f"\\n🚨 {report['error_count']} critical errors:")
            for error in report['errors']:
                print(f"   • {error}")
            
            if report['warning_count'] > 0:
                print(f"\\n⚠️  {report['warning_count']} warnings:")
                for warning in report['warnings']:
                    print(f"   • {warning}")
            
            return False

def validate_flee_simulation_data(data_path: str) -> bool:
    """
    Convenience function to validate Flee simulation data.
    
    Args:
        data_path: Path to simulation directory or data file
        
    Returns:
        True if data is authentic and safe to analyze
    """
    validator = FleeDataValidator()
    return validator.validate_data_for_analysis(Path(data_path))

def main():
    """Command-line interface for data validation."""
    if len(sys.argv) != 2:
        print("Usage: python validate_flee_data.py <simulation_directory_or_data_file>")
        sys.exit(1)
    
    data_path = sys.argv[1]
    
    print("🔒 FLEE DATA AUTHENTICITY VALIDATOR")
    print("=" * 50)
    print("This tool validates that simulation data comes from real Flee runs.")
    print("It prevents analysis of fake or simulated data.")
    print()
    
    is_valid = validate_flee_simulation_data(data_path)
    
    if is_valid:
        print("\\n🎉 VALIDATION PASSED - Data is authentic and safe to use!")
        sys.exit(0)
    else:
        print("\\n🚫 VALIDATION FAILED - Data is NOT authentic or safe to use!")
        sys.exit(1)

if __name__ == "__main__":
    main()