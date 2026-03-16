#!/usr/bin/env python3
"""
Simple Project Cleanup Script

Focus on main workspace files only, ignoring virtual environments and deep subdirectories.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_archive_structure():
    """Create the archive directory structure."""
    archive_dirs = [
        "archive",
        "archive/development",
        "archive/development/experimental_scripts",
        "archive/development/test_files", 
        "archive/development/demo_scripts",
        "archive/development/superseded_versions",
        "archive/research_notes",
        "archive/research_notes/frameworks",
        "archive/research_notes/hypotheses",
        "archive/alternative_implementations",
        "archive/result_directories"
    ]
    
    for dir_path in archive_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Archive structure created")

def get_main_workspace_files():
    """Get main workspace files, excluding deep subdirectories."""
    
    # Files to KEEP (production)
    keep_files = [
        # Core analysis tools
        "authentic_flee_runner.py",
        "authentic_s1s2_diagnostic_suite.py", 
        "authentic_dimensionless_analysis.py",
        "authentic_spatial_visualization_suite.py",
        "validate_flee_data.py",
        
        # Essential docs and config
        "README.md",
        "requirements.txt",
        "requirements_dev.txt", 
        "setup.py",
        "setup.cfg",
        "LICENSE",
        "Makefile",
        ".gitignore",
        ".gitattributes",
        "versioneer.py",
        "MANIFEST.in",
        "mkdocs.yml",
        
        # Final summaries
        "FINAL_COMPLETE_FIGURES_SUMMARY.md",
    ]
    
    # Directories to KEEP (production)
    keep_dirs = [
        "flee/",
        "authentic_s1s2_diagnostics/",
        "dimensionless_analysis/", 
        "spatial_network_analysis/",
        "flee_simulations/",
        ".kiro/",
        "docs/",
        "conflict_input/",
        "conflict_validation/"
    ]
    
    # Files to ARCHIVE (development)
    archive_files = [
        # Test files
        "test_flee_basic.py",
        "test_bottleneck_scenario.py",
        "test_evacuation_timing_scenario.py",
        "test_multi_destination_scenario.py",
        "test_cognitive_demo_clean.py",
        "test_cognitive_differences_demo.py",
        "test_cognitive_modes_direct.py",
        "test_cognitive_system_working.py",
        "test_existing_cognitive_system.py",
        "test_flee_direct.py",
        "test_flee_installed.py",
        "test_flee_simple.py",
        "test_minimal_flee_scenario.py",
        "test_native_flee_simulation.py",
        "test_native_flee_with_agents.py",
        "test_refugee_integration.py",
        "test_s1_vs_s2_demo.py",
        "test_s1s2_tracking.py",
        "test_working_cognitive_demo.py",
        "test_basic.py",
        "test_simple_cognitive.py",
        "test_simple_integration.py",
        
        # Development scripts
        "run_s1s2_with_diagnostics.py",
        "run_multiple_flee_scenarios.py",
        "standard_s1s2_diagnostic_suite.py",
        "comprehensive_s1s2_refugee_validation.py",
        "create_s1s2_refugee_plots.py",
        "create_clean_s1s2_plots.py",
        "generate_all_scenario_diagnostics.py",
        "s1s2_plotting_functions.py",
        "s1s2_decision_tracker.py",
        "topology_test_implementation.py",
        
        # Research documentation
        "aspirations_capabilities_s1s2_framework.md",
        "core_experimental_design.md",
        "flee_capability_analysis.md",
        "flee_s1s2_actual_implementation.md",
        "parsimonious_s1s2_refugee_framework.md",
        "s1_s2_hypothesis_framework.md",
        "DIMENSIONLESS_SCALING_FRAMEWORK.md",
        "S1S2_SCIENTIFIC_INTERPRETATION.md",
        "S1S2_REFUGEE_FRAMEWORK_OUTPUT_GUIDE.md",
        
        # Status files (archive for history)
        "CLEAN_PROJECT_SUMMARY.md",
        "COMPLETE_FIGURES_INVENTORY.md",
        "COMPLETE_OUTPUT_LOCATIONS.md",
        "DIAGNOSTIC_FIGURES_SUMMARY.md",
        "FINAL_CLEAN_STATUS.md",
        "AUTHENTIC_FLEE_SOLUTION_SUMMARY.md",
    ]
    
    # Directories to ARCHIVE
    archive_dirs = [
        "scripts/",
        "flee_dual_process/",
        "latex_paper/",
        "tests/",
        "tests_mpi/",
        "flee_benchmark_tests/",
        "multiscale/",
        "runscripts/",
        
        # Result directories
        "bottleneck_results/",
        "evacuation_timing_results/",
        "multi_destination_results/",
        "comprehensive_validation/",
        "comprehensive_validation_results/",
        "s1s2_diagnostics/",
        "s1s2_refugee_plots/",
        "s1s2_visualizations/",
        "spatial_analysis/",
        "dimensionless_figures/",
        "native_flee_output/",
        "output/",
        "test_data/",
        "test_evacuation_timing/",
        "test_minimal_scenario/",
        "test_refugee_output/",
        "test_topologies/",
        "flee_dual_process_archive/",
    ]
    
    # Files to DELETE
    delete_files = [
        "fix_all_csv_files.py",
        "fix_csv_formatting.py", 
        "output.txt",
        "empty.yml",
        ".DS_Store",
        "cleanup_classifier.py",
        "cleanup_classification.json",
        "cleanup_classification_report.md",
    ]
    
    # Directories to DELETE
    delete_dirs = [
        "__pycache__/",
        ".pytest_cache/",
        "build/",
        "dist/",
        "flee.egg-info/",
        "backup_pre_cleanup_20250831/",
    ]
    
    return {
        'keep_files': keep_files,
        'keep_dirs': keep_dirs,
        'archive_files': archive_files,
        'archive_dirs': archive_dirs,
        'delete_files': delete_files,
        'delete_dirs': delete_dirs
    }

def execute_cleanup():
    """Execute the cleanup operations."""
    print("🧹 STARTING PROJECT CLEANUP")
    print("=" * 50)
    
    # Create archive structure
    create_archive_structure()
    
    # Get file lists
    file_lists = get_main_workspace_files()
    
    # Track operations
    operations = {
        'kept': [],
        'archived': [],
        'deleted': [],
        'errors': []
    }
    
    # Archive files
    print("\\n📦 ARCHIVING FILES...")
    for file_name in file_lists['archive_files']:
        if Path(file_name).exists():
            try:
                # Determine archive subdirectory
                if file_name.startswith('test_'):
                    dest_dir = "archive/development/test_files"
                elif 'demo' in file_name or 'cognitive' in file_name:
                    dest_dir = "archive/development/demo_scripts"
                elif any(x in file_name for x in ['run_', 'create_', 'generate_']):
                    dest_dir = "archive/development/experimental_scripts"
                elif file_name.endswith('.md'):
                    if any(x in file_name for x in ['framework', 'hypothesis']):
                        dest_dir = "archive/research_notes/frameworks"
                    else:
                        dest_dir = "archive/research_notes"
                else:
                    dest_dir = "archive/development/superseded_versions"
                
                dest_path = Path(dest_dir) / file_name
                shutil.move(file_name, str(dest_path))
                operations['archived'].append(f"{file_name} -> {dest_path}")
                print(f"  📦 {file_name} -> {dest_dir}/")
            except Exception as e:
                operations['errors'].append(f"Error archiving {file_name}: {e}")
                print(f"  ❌ Error archiving {file_name}: {e}")
    
    # Archive directories
    for dir_name in file_lists['archive_dirs']:
        if Path(dir_name).exists():
            try:
                dest_path = Path("archive/alternative_implementations") / dir_name.rstrip('/')
                if "result" in dir_name or "output" in dir_name or "validation" in dir_name:
                    dest_path = Path("archive/result_directories") / dir_name.rstrip('/')
                
                shutil.move(dir_name, str(dest_path))
                operations['archived'].append(f"{dir_name} -> {dest_path}")
                print(f"  📦 {dir_name} -> {dest_path}")
            except Exception as e:
                operations['errors'].append(f"Error archiving {dir_name}: {e}")
                print(f"  ❌ Error archiving {dir_name}: {e}")
    
    # Delete files
    print("\\n🗑️ DELETING OBSOLETE FILES...")
    for file_name in file_lists['delete_files']:
        if Path(file_name).exists():
            try:
                Path(file_name).unlink()
                operations['deleted'].append(file_name)
                print(f"  🗑️ {file_name}")
            except Exception as e:
                operations['errors'].append(f"Error deleting {file_name}: {e}")
                print(f"  ❌ Error deleting {file_name}: {e}")
    
    # Delete directories
    for dir_name in file_lists['delete_dirs']:
        if Path(dir_name).exists():
            try:
                shutil.rmtree(dir_name)
                operations['deleted'].append(dir_name)
                print(f"  🗑️ {dir_name}")
            except Exception as e:
                operations['errors'].append(f"Error deleting {dir_name}: {e}")
                print(f"  ❌ Error deleting {dir_name}: {e}")
    
    # Generate manifest
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'operations': operations,
        'summary': {
            'kept': len(operations['kept']),
            'archived': len(operations['archived']),
            'deleted': len(operations['deleted']),
            'errors': len(operations['errors'])
        }
    }
    
    # Save manifest
    with open("archive/CLEANUP_MANIFEST.md", 'w') as f:
        f.write(f"# Project Cleanup Manifest\\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        
        f.write(f"## Summary\\n")
        f.write(f"- Archived: {len(operations['archived'])} items\\n")
        f.write(f"- Deleted: {len(operations['deleted'])} items\\n")
        f.write(f"- Errors: {len(operations['errors'])} items\\n\\n")
        
        if operations['archived']:
            f.write(f"## Archived Items\\n")
            for item in operations['archived']:
                f.write(f"- {item}\\n")
            f.write("\\n")
        
        if operations['deleted']:
            f.write(f"## Deleted Items\\n")
            for item in operations['deleted']:
                f.write(f"- {item}\\n")
            f.write("\\n")
        
        if operations['errors']:
            f.write(f"## Errors\\n")
            for error in operations['errors']:
                f.write(f"- {error}\\n")
    
    print(f"\\n✅ CLEANUP COMPLETE!")
    print(f"📦 Archived: {len(operations['archived'])} items")
    print(f"🗑️ Deleted: {len(operations['deleted'])} items")
    print(f"❌ Errors: {len(operations['errors'])} items")
    print(f"📄 Manifest: archive/CLEANUP_MANIFEST.md")
    
    return operations

if __name__ == "__main__":
    execute_cleanup()