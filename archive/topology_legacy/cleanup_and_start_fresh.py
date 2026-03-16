#!/usr/bin/env python3
"""
Clean up old results and prepare for fresh, systematic experiments.

This script:
1. Archives old results (doesn't delete, just moves to archive)
2. Creates clean directory structure
3. Prepares for fresh experiments
"""

import shutil
from pathlib import Path
from datetime import datetime


def archive_old_results():
    """Archive old results to a timestamped directory."""
    
    print("=" * 70)
    print("🧹 CLEANING UP OLD RESULTS")
    print("=" * 70)
    print()
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = Path("archive") / "old_results" / f"archived_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Archive directory: {archive_dir}")
    print()
    
    # Directories to archive
    dirs_to_archive = [
        "results",
        "proper_10k_agent_experiments",
        "final_agent_flow_graphs",
        "complete_analysis_results",
        "organized_s1s2_results",
        "cognition_results"
    ]
    
    archived_count = 0
    
    for dir_name in dirs_to_archive:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   📁 Archiving: {dir_name}/")
            dest = archive_dir / dir_name
            shutil.move(str(dir_path), str(dest))
            archived_count += 1
            print(f"      ✅ Moved to: {dest}")
    
    # Archive individual result files
    result_files = [
        "test_5parameter_results.json",
        "experiment_results.json",
        "all_10k_agent_results.json",
        "parameter_sensitivity_analysis.png",
        "population_scaling_analysis.png",
        "s2_threshold_sensitivity_test.png"
    ]
    
    for file_name in result_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"   📄 Archiving: {file_name}")
            dest = archive_dir / file_name
            shutil.move(str(file_path), str(dest))
            archived_count += 1
            print(f"      ✅ Moved to: {dest}")
    
    print()
    print(f"✅ Archived {archived_count} items to: {archive_dir}")
    print()


def create_fresh_structure():
    """Create clean directory structure for new experiments."""
    
    print("=" * 70)
    print("🆕 CREATING FRESH DIRECTORY STRUCTURE")
    print("=" * 70)
    print()
    
    # Create clean results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    subdirs = [
        "results/figures",
        "results/data",
        "results/reports"
    ]
    
    for subdir in subdirs:
        Path(subdir).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {subdir}/")
    
    print()
    print("✅ Fresh directory structure ready")
    print()


def create_fresh_readme():
    """Create a README for the new results."""
    
    readme_content = """# Fresh S1/S2 Experimental Results

**Created**: {timestamp}
**Status**: Clean slate - ready for systematic experiments

## Directory Structure

```
results/
├── figures/          # All visualization outputs
├── data/            # Raw data and analysis results
└── reports/         # Summary reports and documentation
```

## Experimental Plan

### Phase 1: Mathematical Validation (CURRENT)
- Validate 5-parameter model in isolation
- Verify all outputs are properly bounded
- Test parameter sensitivity

### Phase 2: Integration Testing
- Test with Flee simulation (1,000 agents, 3 experiments)
- Verify S2 activation rates (expect 10-50%)
- Check for integration issues

### Phase 3: Full Experiments
- Run 27 experiments (3 topologies × 3 sizes × 3 scenarios)
- 10,000 agents per experiment
- 20 days simulation

### Phase 4: Analysis & Visualization
- Generate comparison figures
- Perform sensitivity analysis
- Create publication-ready visualizations

## Notes

- All old results archived to: `archive/old_results/archived_TIMESTAMP/`
- Starting fresh with systematic, well-documented approach
- Focus on robust, reproducible results
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    readme_path = Path("results") / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"📝 Created: {readme_path}")
    print()


def main():
    """Main cleanup and setup function."""
    
    print()
    print("=" * 70)
    print("🔄 FRESH START: CLEANUP AND SETUP")
    print("=" * 70)
    print()
    print("This script will:")
    print("  1. Archive all old results (safe, not deleted)")
    print("  2. Create clean directory structure")
    print("  3. Prepare for fresh, systematic experiments")
    print()
    
    # Archive old results
    archive_old_results()
    
    # Create fresh structure
    create_fresh_structure()
    
    # Create README
    create_fresh_readme()
    
    # Summary
    print("=" * 70)
    print("✅ CLEANUP COMPLETE - READY FOR FRESH START")
    print("=" * 70)
    print()
    print("📊 What's Next:")
    print("  1. Run: python demonstrate_5parameter_model.py")
    print("     → Validates mathematical model")
    print()
    print("  2. Run: python test_5parameter_integration.py")
    print("     → Tests integration with Flee (1,000 agents)")
    print()
    print("  3. Run: python run_fresh_experiments.py")
    print("     → Runs full systematic experiments (10,000 agents)")
    print()
    print("  4. Run: python generate_fresh_figures.py")
    print("     → Creates all publication-ready figures")
    print()
    print("📁 Old results safely archived in:")
    print(f"   archive/old_results/archived_*")
    print()
    print("🎯 You now have a clean slate for systematic, robust results!")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()




