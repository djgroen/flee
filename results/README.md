# Fresh S1/S2 Experimental Results

**Created**: 2025-10-26 03:49:30
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
