# Legacy Topology Scripts (Archived)

These scripts were archived as part of the V3 topology consolidation. The canonical topology chain is:

- **Generator**: `generate_nuclear_topologies.py` → `topologies/{ring,linear,star}`
- **Configs**: `configs/{ring,linear,star}_topology.yml`
- **Runner**: `run_nuclear_parameter_sweep.py`

## Archived Scripts

| Script | Reason |
|--------|--------|
| topology_generator.py | NetworkX-based; different format; used by systematic_experiments |
| comprehensive_topology_builder.py | Outputs to comprehensive_topologies/ |
| comprehensive_topology_s1s2_experiments.py | In-memory topologies; old S1/S2 API |
| simple_topology_s1s2_experiments.py | Legacy experiment runner |
| topology_s1s2_experiments.py | Legacy experiment runner |
| systematic_topology_experiments.py | Uses topology_generator.py |
| improved_topologies_for_movies.py | One-off movie topologies |
| cleanup_and_start_fresh.py | Ad-hoc cleanup script |
| validate_topology_experiments.py | Validates comprehensive_topology |
| comprehensive_topology_paper_experiments.py | Paper-specific; uses comprehensive_topology |
