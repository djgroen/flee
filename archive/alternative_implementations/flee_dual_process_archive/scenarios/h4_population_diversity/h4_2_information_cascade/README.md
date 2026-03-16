# H4.2: Information Cascade Test Scenario

## Overview

This scenario tests **Hypothesis 4.2**: S1 agents serve as "scouts" whose discoveries benefit S2 "followers" in mixed populations, creating information cascades that improve collective outcomes.

## Scenario Design

### Information Asymmetry Network

The scenario creates destinations with varying visibility and discovery difficulty:

```
Origin (40k pop) → Information_Hub (8k pop) → [Multiple Destinations]
     ↓                                              ↓
[Direct routes to obvious destinations]    [Hidden high-quality destinations]
```

### Destination Types

1. **Obvious_Camp**: High visibility (1.0), moderate quality (0.6), easy discovery
2. **Hidden_Good_Camp**: Low visibility (0.2), high quality (0.9), difficult discovery  
3. **Moderate_Camp**: Medium visibility (0.6), good quality (0.7), moderate discovery
4. **Late_Discovery_Camp**: Very low visibility (0.1), high quality (0.8), very difficult discovery

### Scout-Follower Dynamics

- **S1 "Scouts"**: Fast exploration, high discovery capability, information sharing
- **S2 "Followers"**: Deliberative processing, high information receptivity, network-based decisions

## Expected Information Cascade Pattern

### Phase 1: Scout Discovery (Days 1-15)
- S1 scouts rapidly explore and discover destinations
- Early discovery of obvious destinations by multiple scouts
- Gradual discovery of hidden high-quality destinations by persistent scouts

### Phase 2: Information Sharing (Days 5-25)
- Scouts share discovery information through social networks
- Information flows from S1 discoverers to connected S2 agents
- Network effects amplify information spread

### Phase 3: Follower Adoption (Days 8-35)
- S2 followers receive and process scout information
- Deliberative evaluation of destination options
- Adoption decisions based on processed information

### Phase 4: Cascade Effects (Days 15-45)
- Information cascades create correlated destination choices
- Mixed populations achieve better collective outcomes
- Optimal utilization of high-quality hidden destinations

## Key Metrics

### Discovery Rate
- Speed of destination discovery by S1 scouts
- Diversity of destinations discovered
- Time to discover hidden high-quality options

### Adoption Lag
- Time delay between S1 discovery and S2 adoption
- Variation in adoption lag by destination quality
- Network effects on adoption timing

### Information Correlation
- Correlation between S1 discovery patterns and S2 adoption patterns
- Strength of information cascade effects
- Network-mediated information flow

### Cascade Efficiency
- Ratio of S2 adoptions to S1 discoveries
- Speed of information propagation
- Overall cascade effectiveness

### Collective Optimality
- Population-level destination choice quality
- Utilization of high-quality hidden destinations
- Comparison with random or individual decision-making

## Usage

### Generate Scenario
```python
from h4_2_information_cascade import InformationCascadeScenario

scenario = InformationCascadeScenario()
files = scenario.create_scenario(
    output_dir="./h4_2_output",
    scout_ratio=0.3,
    information_sharing_rate=0.7
)
```

### Track Scout-Follower Behavior
```python
from h4_2_information_cascade.scout_follower_tracker import ScoutFollowerTracker

tracker = ScoutFollowerTracker(scenario_config)
tracker.initialize_agents(agent_data)

# During simulation
tracker.track_discovery_event(day=15, agent_id=1, destination="Hidden_Good_Camp")
tracker.track_information_sharing(day=16, sender_id=1, information="Hidden_Good_Camp", recipients=[10, 11, 12])
tracker.track_adoption_event(day=19, agent_id=10, destination="Hidden_Good_Camp")

# Generate report
report = tracker.generate_tracking_report()
```

### Analyze Cascade Metrics
```python
from h4_2_information_cascade.cascade_metrics import analyze_h4_2_scenario

results = analyze_h4_2_scenario(
    output_dir="./h4_2_output",
    scout_ratio=0.3
)

print(f"Discovery Rate: {results.discovery_rate:.3f}")
print(f"Adoption Lag: {results.adoption_lag:.1f} days")
print(f"Information Correlation: {results.information_correlation:.3f}")
print(f"Cascade Efficiency: {results.cascade_efficiency:.3f}")
```

### Analyze Information Flow
```python
from h4_2_information_cascade.information_flow_analyzer import InformationFlowAnalyzer

analyzer = InformationFlowAnalyzer("./h4_2_output")
analyzer.build_information_network(scout_data, follower_data)

flow_metrics = analyzer.analyze_information_flow()
dynamics = analyzer.analyze_scout_follower_dynamics()

# Export analysis
analyzer.export_network_analysis("./h4_2_analysis")
```

## Files Generated

- **locations.csv**: Network with varying destination visibility
- **routes.csv**: Connections with discovery difficulty parameters
- **conflicts.csv**: Gradual conflict escalation (60-day scenario)
- **discovery_timeline.csv**: Expected S1 discovery timeline
- **agent_config.yml**: Scout-follower population configuration
- **sim_period.csv**: 60-day simulation period
- **scenario_metadata.yml**: Complete scenario documentation

## Expected Findings

### Scout Performance
- **High Discovery Rate**: S1 scouts discover destinations quickly
- **Exploration Diversity**: Scouts explore multiple destination options
- **Information Sharing**: Active sharing of discovery information

### Follower Performance  
- **Informed Decisions**: S2 followers make better destination choices
- **Network Benefits**: Benefit from scout information through social networks
- **Quality Optimization**: Higher utilization of high-quality destinations

### Cascade Dynamics
- **Information Flow**: Clear information flow from scouts to followers
- **Adoption Patterns**: Correlated adoption following scout discoveries
- **Collective Benefits**: Mixed populations outperform homogeneous populations

### Network Effects
- **Broker Identification**: Key agents facilitating information flow
- **Cascade Reach**: Extent of information spread through population
- **Temporal Patterns**: Evolution of information cascades over time

## Validation

The scenario validates H4.2 predictions:

- **H4.2a**: S1 scouts discover high-quality destinations first
- **H4.2b**: Information flows from S1 to S2 through social networks
- **H4.2c**: S2 adoption correlates with S1 discovery patterns
- **H4.2d**: Mixed populations achieve better collective outcomes than homogeneous populations

## Research Applications

This scenario enables research into:

- Information cascade dynamics in crisis situations
- Scout-follower roles in collective decision-making
- Network effects in information diffusion
- Cognitive diversity benefits in exploration-exploitation trade-offs
- Social learning in refugee movement patterns