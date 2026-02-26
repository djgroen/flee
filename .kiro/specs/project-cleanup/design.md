# Project Cleanup Design

## Architecture Overview

The cleanup process follows a three-tier classification system:
1. **KEEP**: Essential production files that remain in workspace
2. **ARCHIVE**: Development files moved to organized archive structure  
3. **DELETE**: Obsolete files that can be safely removed

## File Classification Framework

### Classification Criteria

#### KEEP Criteria
- ✅ Production-ready analysis tools
- ✅ Authentic simulation data and results
- ✅ Generated figures and visualizations
- ✅ Core documentation and specifications
- ✅ Essential configuration files
- ✅ Working validation and runner scripts

#### ARCHIVE Criteria  
- 📦 Experimental and development scripts
- 📦 Test files and demonstrations
- 📦 Superseded versions of tools
- 📦 Development documentation
- 📦 Alternative implementations
- 📦 Research notes and frameworks

#### DELETE Criteria
- 🗑️ One-time fix scripts (already applied)
- 🗑️ Duplicate files
- 🗑️ Failed experiments with no value
- 🗑️ Temporary files and artifacts
- 🗑️ Build artifacts that can be regenerated

## Directory Structure Design

### Current Workspace (Post-Cleanup)
```
flee-s1s2-project/
├── 📁 authentic_analysis/           # Core analysis tools
│   ├── authentic_flee_runner.py
│   ├── authentic_s1s2_diagnostic_suite.py
│   ├── authentic_dimensionless_analysis.py
│   ├── authentic_spatial_network_suite.py
│   └── validate_flee_data.py
├── 📁 flee_simulations/            # Authentic simulation data
│   ├── flee_output_*/
│   └── [preserved as-is]
├── 📁 figures/                     # All generated figures
│   ├── authentic_s1s2_diagnostics/
│   ├── dimensionless_analysis/
│   └── spatial_network_analysis/
├── 📁 flee/                        # Core Flee package
├── 📁 docs/                        # Documentation
├── 📁 .kiro/                       # Kiro specifications
├── 📊 FINAL_COMPLETE_FIGURES_SUMMARY.md
├── 📋 requirements.txt
├── 🔧 setup.py
└── 📖 README.md
```

### Archive Structure
```
archive/
├── 📁 development/                 # Development scripts
│   ├── experimental_scripts/
│   ├── test_files/
│   ├── demo_scripts/
│   └── superseded_versions/
├── 📁 research_notes/              # Research documentation
│   ├── frameworks/
│   ├── hypotheses/
│   └── design_docs/
├── 📁 alternative_implementations/ # Other approaches tried
├── 📁 build_artifacts/            # Generated files
└── 📄 ARCHIVE_MANIFEST.md         # What was moved when
```

## Implementation Strategy

### Phase 1: Safety Preparation
1. **Create complete backup**
   - Full workspace snapshot
   - Git commit current state
   - Document current file count

2. **Analyze dependencies**
   - Scan for import statements
   - Identify file references
   - Map critical dependencies

### Phase 2: Classification Execution
1. **Automated classification**
   - Run classification script
   - Generate move/delete lists
   - Create safety reports

2. **Manual review**
   - Review edge cases
   - Validate classifications
   - Approve final lists

### Phase 3: Organized Migration
1. **Create archive structure**
   - Set up archive directories
   - Prepare manifest tracking

2. **Execute moves**
   - Move ARCHIVE files first
   - Update any broken references
   - Delete obsolete files last

3. **Validation**
   - Test remaining functionality
   - Verify figure generation works
   - Confirm no broken imports

### Phase 4: Documentation
1. **Update documentation**
   - Revise README files
   - Update file references
   - Document new structure

2. **Create audit trail**
   - Complete manifest
   - Change log
   - Rollback instructions

## File Classification Rules

### Production Analysis Tools (KEEP)
```python
KEEP_PATTERNS = [
    "authentic_*.py",           # All authentic analysis tools
    "validate_flee_data.py",    # Data validation
    "flee/",                    # Core Flee package
    "*_analysis/",              # Figure directories
    "flee_simulations/",        # Simulation data
    "requirements*.txt",        # Dependencies
    "setup.py",                 # Package setup
    "README.md",                # Main documentation
    "FINAL_*.md",              # Final summaries
    ".kiro/specs/",            # Specifications
    "docs/",                   # Documentation
]
```

### Development Files (ARCHIVE)
```python
ARCHIVE_PATTERNS = [
    "test_*.py",               # Test files
    "*_demo*.py",              # Demo scripts
    "comprehensive_*.py",      # Superseded versions
    "standard_*.py",           # Non-authentic versions
    "run_s1s2_*.py",          # Development runners
    "create_*.py",            # One-off creators
    "*_framework.md",         # Research frameworks
    "*_hypothesis*.md",       # Research notes
    "scripts/",               # Development scripts
    "flee_dual_process/",     # Alternative implementation
]
```

### Obsolete Files (DELETE)
```python
DELETE_PATTERNS = [
    "fix_*.py",               # One-time fixes (already applied)
    "test_native_flee_*.py",  # Superseded tests
    "output.txt",             # Temporary output
    "__pycache__/",           # Python cache
    "*.pyc",                  # Compiled Python
    ".DS_Store",              # macOS artifacts
]
```

## Safety Mechanisms

### Backup Strategy
1. **Pre-cleanup snapshot**
   - Complete workspace copy
   - Git tag for current state
   - File manifest with checksums

2. **Incremental backups**
   - Backup before each phase
   - Track all file operations
   - Maintain rollback points

### Validation Checks
1. **Functionality tests**
   - Run authentic analysis suite
   - Generate sample figures
   - Verify data validation works

2. **Dependency checks**
   - Scan for broken imports
   - Test critical workflows
   - Validate file references

### Rollback Capability
1. **Complete restoration**
   - Restore from pre-cleanup backup
   - Reset git to tagged state
   - Verify full functionality

2. **Selective restoration**
   - Restore individual files from archive
   - Maintain archive structure
   - Update documentation

## Quality Assurance

### Automated Checks
- File count verification
- Import statement validation
- Figure generation testing
- Data integrity checks

### Manual Verification
- Spot check moved files
- Test key workflows
- Review documentation accuracy
- Validate archive organization

## Success Metrics

### Quantitative Metrics
- **File Reduction**: Target 60-70% reduction in workspace files
- **Directory Count**: Reduce from ~15 to ~8 top-level directories
- **Test Coverage**: Maintain 100% of authentic analysis functionality
- **Performance**: <2 second file search in cleaned workspace

### Qualitative Metrics
- **Clarity**: New users can understand structure in <5 minutes
- **Maintainability**: Easy to identify what needs updates
- **Reproducibility**: All figures can still be generated
- **Reversibility**: Any archived file can be restored in <1 minute