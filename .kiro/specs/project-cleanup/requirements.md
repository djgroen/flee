# Project Cleanup Specification

## Overview
This specification defines the systematic cleanup of the S1/S2 refugee simulation project after successful completion of authentic Flee integration and comprehensive figure generation. The project has accumulated numerous experimental files, test scripts, and development artifacts that need organized cleanup.

## Background
The project has successfully achieved:
- ✅ 21 authentic figures from real Flee simulations
- ✅ Complete S1/S2 diagnostic suite
- ✅ Dimensionless scaling law analysis
- ✅ Spatial network visualization suite
- ✅ Full authenticity validation framework

The workspace now contains ~150+ files across multiple development phases that need systematic organization.

## User Stories

### US-1: As a researcher, I want essential production files preserved
**Story**: As a researcher using this codebase, I need all production-ready analysis tools and authentic simulation data preserved so I can reproduce results and conduct further research.

**Acceptance Criteria**:
- All authentic analysis suites are preserved
- All generated figure directories are preserved
- All authentic simulation data is preserved
- All validation and runner scripts are preserved
- Documentation files are preserved

### US-2: As a developer, I want development artifacts archived
**Story**: As a developer maintaining this codebase, I need development and experimental files archived (not deleted) so I can reference the development process while keeping the workspace clean.

**Acceptance Criteria**:
- Experimental scripts are moved to archive directory
- Test files are organized in archive
- Development versions of scripts are archived
- Archive maintains original directory structure
- Archive includes metadata about what was moved

### US-3: As a maintainer, I want obsolete files removed
**Story**: As a project maintainer, I need truly obsolete files (temporary fixes, duplicates, failed experiments) removed to reduce workspace clutter and confusion.

**Acceptance Criteria**:
- One-time fix scripts are removed
- Duplicate files are removed
- Failed experiment artifacts are removed
- Temporary files are removed
- Removal is logged for audit trail

### US-4: As a user, I want clear organization
**Story**: As someone using this project, I need the remaining files clearly organized with obvious purposes so I can quickly find what I need.

**Acceptance Criteria**:
- Production files are in logical directories
- Clear naming conventions are maintained
- README files explain directory purposes
- File relationships are documented
- Navigation is intuitive

### US-5: As a researcher, I want cleanup to be reversible
**Story**: As a researcher, I need the cleanup process to be reversible in case archived files are needed later.

**Acceptance Criteria**:
- Complete manifest of all moves/deletions
- Archive structure allows easy restoration
- Backup of current state before cleanup
- Clear instructions for reversal
- No data loss occurs

## Success Criteria

### Primary Success Criteria
1. **Workspace Reduction**: Reduce active workspace files by 60-70%
2. **Organization**: Clear separation of production vs development files
3. **Preservation**: Zero loss of essential functionality or data
4. **Documentation**: Complete audit trail of all changes
5. **Reversibility**: Ability to restore any archived content

### Secondary Success Criteria
1. **Performance**: Faster file navigation and search
2. **Clarity**: New users can quickly understand project structure
3. **Maintenance**: Easier to identify what needs updating
4. **Compliance**: Follows software engineering best practices

## Constraints

### Technical Constraints
- Must preserve all authentic simulation data
- Must maintain all working analysis pipelines
- Must preserve figure generation capabilities
- Must maintain git history

### Business Constraints
- Cannot break existing workflows
- Must complete cleanup in single session
- Must provide rollback capability
- Must maintain scientific reproducibility

## Assumptions
- Current workspace contains ~150+ files
- Most experimental files are no longer needed
- Archive storage is available
- Git repository can handle file moves
- No external dependencies on file locations

## Dependencies
- Git version control system
- File system with archive directory capability
- Backup storage for safety
- Documentation system for audit trail

## Risks and Mitigations

### Risk: Accidental deletion of important files
**Mitigation**: Create complete backup before any operations, use archive-first approach

### Risk: Breaking existing scripts that reference moved files
**Mitigation**: Analyze file dependencies before moving, update import paths

### Risk: Loss of development history
**Mitigation**: Preserve files in archive with original timestamps and metadata

### Risk: Confusion about what was moved where
**Mitigation**: Generate detailed manifest and update documentation

## Out of Scope
- Refactoring existing code functionality
- Changing file formats or data structures
- Optimizing algorithm performance
- Adding new features during cleanup