#!/usr/bin/env python3
"""
Refugee Movement Simulations: Context-Dependent Decision-Making

Four scenarios designed to demonstrate:
1. System 1 vs System 2 route choices
2. Social connection effects on S2 activation
3. Context-dependent processing (high conflict → S1, recovery → S2)
4. Agent transitions between cognitive states

Author: Michael Puma
Date: 2024
"""

import numpy as np
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

from flee import flee
from flee.SimulationSettings import SimulationSettings

# Import experience index calculation
try:
    from flee.s1s2_model import calculate_experience_index
except ImportError:
    # Fallback if s1s2_model not available
    def calculate_experience_index(agent, time):
        """Calculate experience index for agent."""
        connections = agent.attributes.get("connections", 0)
        timesteps = getattr(agent, 'timesteps_since_departure', 0)
        education = agent.attributes.get('education_level', 0.5)
        
        # Simple experience index
        x = (connections / 10.0) * 0.4 + (min(timesteps, 30) / 30.0) * 0.4 + education * 0.2
        return max(0.0, min(1.0, x))


class RefugeeSimulator:
    """Simulator for refugee movement scenarios with S1/S2 decision-making."""
    
    def __init__(self, output_dir="refugee_simulation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def create_scenario_1_nearest_border(self):
        """
        Scenario 1: Nearest Border (System 1 Demonstration)
        
        Two safe borders at different distances:
        - Border A: 300 units away (nearest) - System 1 heuristic
        - Border B: 600 units away (farther) - System 2 may choose this
        
        Expected: System 1 agents head to Border A (nearest)
        
        Dimensionless parameters:
        - Characteristic distance: D_char = 100 units
        - Characteristic time: T_char = 10 timesteps
        - Normalized distances: d_A = 3.0, d_B = 6.0
        - Normalized speeds: v = 10 units/timestep (typical)
        """
        locations = []
        routes = []
        
        # Characteristic scales for dimensionless analysis
        D_char = 100.0  # Characteristic distance (units)
        T_char = 10.0   # Characteristic time (timesteps)
        v_char = D_char / T_char  # Characteristic speed = 10 units/timestep
        
        # Origin: High conflict zone (agents start here)
        locations.append({
            'name': 'ConflictZone',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.9,  # High conflict
            'movechance': 1.0,  # Always try to leave
            'capacity': -1
        })
        
        # Route 1: Nearest border (System 1 heuristic)
        # Distance: 3.0 * D_char = 300 units
        locations.append({
            'name': 'Town1',
            'x': 150.0, 'y': 0.0,  # Halfway point
            'type': 'town',
            'conflict': 0.3,
            'movechance': 0.3,  # Reduced to slow movement
            'capacity': 5000
        })
        
        locations.append({
            'name': 'BorderA',
            'x': 300.0, 'y': 0.0,  # 3.0 * D_char
            'type': 'camp',  # Safe zone
            'conflict': 0.0,
            'movechance': 0.001,  # Stay in safe zone
            'capacity': 10000
        })
        
        # Route 2: Farther border (System 2 may choose this)
        # Distance: 6.0 * D_char = 600 units
        locations.append({
            'name': 'Town2',
            'x': 0.0, 'y': 300.0,  # Halfway point
            'type': 'town',
            'conflict': 0.3,
            'movechance': 0.6,  # Increased for reasonable movement speed
            'capacity': 5000
        })
        
        locations.append({
            'name': 'BorderB',
            'x': 0.0, 'y': 600.0,  # 6.0 * D_char
            'type': 'camp',  # Safe zone
            'conflict': 0.0,
            'movechance': 0.001,  # Stay in safe zone
            'capacity': 10000
        })
        
        # Routes with increased distances
        routes.append({'from': 'ConflictZone', 'to': 'Town1', 'distance': 150.0})  # 1.5 * D_char
        routes.append({'from': 'Town1', 'to': 'BorderA', 'distance': 150.0})  # Total: 3.0 * D_char = 300
        
        routes.append({'from': 'ConflictZone', 'to': 'Town2', 'distance': 300.0})  # 3.0 * D_char
        routes.append({'from': 'Town2', 'to': 'BorderB', 'distance': 300.0})  # Total: 6.0 * D_char = 600
        
        return locations, routes, "Nearest Border"
    
    def create_scenario_2_multiple_routes(self):
        """
        Scenario 2: Multiple Routes (System 2 Demonstration)
        
        Two routes with different characteristics:
        - Route 1: Short (100 units) but passes through high-conflict town
        - Route 2: Longer (200 units) but passes through low-conflict town
        
        Expected: System 1 chooses Route 1 (shorter), System 2 may choose Route 2 (safer)
        """
        locations = []
        routes = []
        
        # Origin: High conflict zone
        locations.append({
            'name': 'ConflictZone',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.9,
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Route 1: Short but risky
        locations.append({
            'name': 'Town1',
            'x': 50.0, 'y': 0.0,
            'type': 'town',
            'conflict': 0.6,  # High conflict
            'movechance': 0.5,
            'capacity': 5000
        })
        
        locations.append({
            'name': 'SafeZoneA',
            'x': 100.0, 'y': 0.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Route 2: Longer but safer
        locations.append({
            'name': 'Town2',
            'x': 0.0, 'y': 50.0,
            'type': 'town',
            'conflict': 0.2,  # Low conflict
            'movechance': 0.5,
            'capacity': 5000
        })
        
        locations.append({
            'name': 'SafeZoneB',
            'x': 0.0, 'y': 200.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Routes
        routes.append({'from': 'ConflictZone', 'to': 'Town1', 'distance': 50.0})
        routes.append({'from': 'Town1', 'to': 'SafeZoneA', 'distance': 50.0})  # Route 1: 100 total
        
        routes.append({'from': 'ConflictZone', 'to': 'Town2', 'distance': 50.0})
        routes.append({'from': 'Town2', 'to': 'SafeZoneB', 'distance': 150.0})  # Route 2: 200 total
        
        return locations, routes, "Multiple Routes"
    
    def create_scenario_3_social_connections(self):
        """
        Scenario 3: Social Connections (Connection Effects)
        
        Two routes:
        - Route A: Passes through recovery camp (builds connections)
        - Route B: Direct route (no recovery, stays isolated)
        
        Expected: Route A agents build connections → higher S2 activation
        """
        locations = []
        routes = []
        
        # Origin: High conflict zone
        locations.append({
            'name': 'ConflictZone',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.9,
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Route A: With recovery camp (builds connections)
        locations.append({
            'name': 'Town',
            'x': 50.0, 'y': 0.0,
            'type': 'town',
            'conflict': 0.3,
            'movechance': 0.5,
            'capacity': 5000
        })
        
        locations.append({
            'name': 'RecoveryCamp',
            'x': 100.0, 'y': 0.0,
            'type': 'camp',  # Recovery camp (builds connections)
            'conflict': 0.0,  # Zero conflict to maximize S2 activation (Ω → 1)
            'movechance': 0.2,  # Stay longer to build connections and activate S2
            'capacity': 8000
        })
        
        locations.append({
            'name': 'SafeZone',
            'x': 200.0, 'y': 0.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Route B: Direct route (no recovery)
        locations.append({
            'name': 'DirectRoute',
            'x': 0.0, 'y': 50.0,
            'type': 'town',
            'conflict': 0.4,
            'movechance': 0.6,
            'capacity': 5000
        })
        
        locations.append({
            'name': 'SafeZoneDirect',
            'x': 150.0, 'y': 50.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Routes
        routes.append({'from': 'ConflictZone', 'to': 'Town', 'distance': 50.0})
        routes.append({'from': 'Town', 'to': 'RecoveryCamp', 'distance': 50.0})
        routes.append({'from': 'RecoveryCamp', 'to': 'SafeZone', 'distance': 100.0})
        
        routes.append({'from': 'ConflictZone', 'to': 'DirectRoute', 'distance': 50.0})
        routes.append({'from': 'DirectRoute', 'to': 'SafeZoneDirect', 'distance': 100.0})
        
        return locations, routes, "Social Connections"
    
    def create_scenario_4_context_transition(self):
        """
        Scenario 4: Context Transition (S1 → S2 Switch)
        
        Clear conflict gradient: High → Moderate → Low
        Agents start in high conflict (S1), move to recovery (S2 possible)
        
        Expected: S2 activation increases as agents move through zones
        """
        locations = []
        routes = []
        
        # High conflict zone (origin)
        locations.append({
            'name': 'ConflictZone',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.9,  # High conflict
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Transit zone (moderate conflict)
        locations.append({
            'name': 'TransitZone',
            'x': 50.0, 'y': 0.0,
            'type': 'town',
            'conflict': 0.4,  # Moderate conflict
            'movechance': 0.5,
            'capacity': 5000
        })
        
        # Recovery zone (low conflict)
        locations.append({
            'name': 'RecoveryZone',
            'x': 100.0, 'y': 0.0,
            'type': 'town',
            'conflict': 0.05,  # Very low conflict to encourage S2 activation
            'movechance': 0.3,  # Stay longer to allow S2 activation
            'capacity': 5000
        })
        
        # Safe zone
        locations.append({
            'name': 'SafeZone',
            'x': 200.0, 'y': 0.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Routes (linear progression)
        routes.append({'from': 'ConflictZone', 'to': 'TransitZone', 'distance': 50.0})
        routes.append({'from': 'TransitZone', 'to': 'RecoveryZone', 'distance': 50.0})
        routes.append({'from': 'RecoveryZone', 'to': 'SafeZone', 'distance': 100.0})
        
        return locations, routes, "Context Transition"
    
    def run_simulation(self, scenario_name, locations, routes, num_agents=500, 
                      num_timesteps=60, s1s2_enabled=True):  # Increased to 60 for longer journeys
        """
        Run a single simulation scenario.
        
        Returns:
            dict: Simulation results including metrics and agent data
        """
        print(f"\n{'='*60}")
        print(f"Running Scenario: {scenario_name}")
        print(f"{'='*60}")
        
        # Create run-specific directory for input files (timestamped like nuclear simulations)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scenario_name_clean = scenario_name.replace(" ", "_")
        run_dir = self.output_dir / f'run_{scenario_name_clean}_{timestamp}'
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config file (complete config like nuclear simulations)
        import yaml
        config = {
            'log_levels': {
                'agent': 1,  # Enable agent logging for individual trajectories
                'link': 0, 'camp': 0, 'conflict': 0,
                'init': 0, 'granularity': 'location'
            },
            'spawn_rules': {
                'take_from_population': False,
                'insert_day0': True
            },
            'move_rules': {
                'max_move_speed': 20.0,  # Increased from 15.0 - faster movement (was 360.0 originally)
                'max_walk_speed': 8.0,   # Increased from 5.0 - faster walking (was 35.0 originally)
                'foreign_weight': 1.0,
                'camp_weight': 3.0,
                'conflict_weight': 0.25,
                'conflict_movechance': 1.0,
                'camp_movechance': 0.001,
                'default_movechance': 0.5,
                'awareness_level': 1,
                'capacity_scaling': 1.0,
                'avoid_short_stints': False,
                'start_on_foot': False,
                'weight_power': 1.0,
                'movechance_pop_base': 10000.0,
                'movechance_pop_scale_factor': 0.5,
                'two_system_decision_making': s1s2_enabled,
                'conflict_threshold': 0.5,
                'connectivity_mode': 'baseline',
                'steepness': 6.0,
                's1s2_model': {
                    'enabled': s1s2_enabled,
                    'alpha': 1.0,  # Further reduced - much easier S2 activation
                    'beta': 1.0,   # Further reduced - much easier S2 activation
                    'p_s2': 0.9,
                },
                'awareness_level': 2,
                # Add required settings that SimulationSettings expects
                'match_camp_religion': False,
                'match_camp_ethnicity': False,
                'match_town_ethnicity': False,
                'match_conflict_ethnicity': False,
                'children_avoid_hazards': False,
                'boys_take_risk': False
            },
            'optimisations': {'hasten': 1}
        }
        
        config_file = run_dir / f'config_{scenario_name_clean}.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Save locations as CSV (Flee format - matching nuclear simulations)
        locations_csv = run_dir / f'locations_{scenario_name_clean}.csv'
        with open(locations_csv, 'w') as f:
            # Header: name,region,x,y,location_type,movechance,capacity,pop,country,conflict,conflict_date,attributes
            f.write('name,region,x,y,location_type,movechance,capacity,pop,country,conflict,conflict_date,attributes\n')
            for loc in locations:
                f.write(f"{loc['name']},unknown,{loc['x']},{loc['y']},{loc.get('type', 'town')},"
                       f"{loc['movechance']},{loc['capacity']},0,unknown,{loc.get('conflict', 0.0)},0,{{}}\n")
        
        # Save routes as CSV (Flee format)
        routes_csv = run_dir / f'routes_{scenario_name_clean}.csv'
        with open(routes_csv, 'w') as f:
            # Header: from,to,distance
            f.write('from,to,distance\n')
            for route in routes:
                f.write(f"{route['from']},{route['to']},{route['distance']}\n")
        
        print(f"📁 Input files saved to: {run_dir}")
        print(f"   - Config: {config_file.name}")
        print(f"   - Locations: {locations_csv.name}")
        print(f"   - Routes: {routes_csv.name}")
        
        try:
            # Initialize simulation
            SimulationSettings.ReadFromYML(str(config_file))
            ecosystem = flee.Ecosystem()
            
            # Set output directory for agent logs (Flee writes to current directory)
            # IMPORTANT: Change to run_dir so each simulation saves its own agents.out.0
            import os
            original_dir = os.getcwd()
            os.chdir(str(run_dir))  # Change to run-specific directory
            
            # Clean up any existing agents.out.0 from this run directory
            agents_out_0 = run_dir / 'agents.out.0'
            if agents_out_0.exists():
                agents_out_0.unlink()
            
            # Add locations
            location_map = {}
            for loc in locations:
                location = ecosystem.addLocation(
                    name=loc['name'],
                    x=loc['x'], y=loc['y'],
                    location_type=loc['type'],
                    movechance=loc['movechance'],
                    capacity=loc['capacity'],
                    pop=0
                )
                location.conflict = loc['conflict']
                location_map[loc['name']] = location
            
            # Add routes
            for route in routes:
                ecosystem.linkUp(route['from'], route['to'], route['distance'])
            
            # Find origin (highest conflict location)
            origin = max(location_map.values(), key=lambda l: getattr(l, 'conflict', 0.0))
            
            # Create agents with varied attributes
            for i in range(num_agents):
                # Varied experience profiles - adjusted to enable more S2 activation
                attributes = {
                    'connections': np.random.choice([0, 1, 2, 3], p=[0.2, 0.3, 0.3, 0.2]),  # More connected agents
                    'education_level': np.random.uniform(0.4, 0.8),  # Higher education (was 0.3-0.7)
                    'stress_tolerance': np.random.uniform(0.5, 0.9),  # Higher stress tolerance (was 0.4-0.8)
                    's2_threshold': np.random.uniform(0.4, 0.6),  # Varied thresholds (was fixed 0.5)
                }
                
                ecosystem.addAgent(
                    location=origin,  # Pass Location object, not string
                    attributes=attributes
                )
            
            # Get agents from ecosystem (after they're added)
            agents = ecosystem.agents
            
            # Track metrics over time
            metrics = {
                'timesteps': [],
                's2_activation_by_location': {},
                'population_by_location': {},
                'population_by_type': {},
                'route_choices': {},
                'connection_stats': {},
                'agent_states': [],  # For detailed agent tracking
            }
            
            # Initialize location tracking
            for loc_name in location_map.keys():
                metrics['s2_activation_by_location'][loc_name] = []
                metrics['population_by_location'][loc_name] = []
            
            # Log initial state (before first evolve)
            # IMPORTANT: Log BEFORE evolve() so agents are at their starting location
            agent_states = []
            for idx, agent in enumerate(agents):
                if agent.location and not agent.travelling:  # Only log if at a location, not on a route
                    loc_x = agent.location.x
                    loc_y = agent.location.y
                    location_name = agent.location.name if agent.location else 'Unknown'
                    
                    # Add DETERMINISTIC jitter based on agent ID and location
                    # Same agent at same location = same offset every timestep
                    # Different agents at same location = different offsets (no overlap)
                    # Apply to all locations (including safe zones) to prevent overlap
                    offset_radius = 20.0  # Increased to prevent overlap (was 10.0)
                    import hashlib
                    hash_input = f"{idx}_{location_name}".encode('utf-8')
                    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                    # Use different seeds for x and y to ensure better distribution
                    np.random.seed(hash_value % (2**32))  # Seed from hash
                    offset_x = np.random.uniform(-offset_radius, offset_radius)
                    np.random.seed((hash_value + 12345) % (2**32))  # Different seed for y
                    offset_y = np.random.uniform(-offset_radius, offset_radius)
                    
                    agent_states.append({
                        'id': f'agent_{idx}',
                        'location': location_name,
                        'cognitive_state': getattr(agent, 'cognitive_state', 'S1'),
                        'connections': agent.attributes.get('connections', 0),
                        'timesteps_since_departure': getattr(agent, 'timesteps_since_departure', 0),
                        'x': loc_x + offset_x,
                        'y': loc_y + offset_y,
                    })
            metrics['agent_states'].append({
                'timestep': 0,
                'agents': agent_states
            })
            
            # Run simulation
            for t in range(1, num_timesteps + 1):  # Start from 1, since we logged t=0 above
                # Evolve ecosystem
                ecosystem.evolve()
                
                # Collect metrics (include t in timesteps list)
                metrics['timesteps'].append(t)  # t is now 1, 2, 3, ... (t=0 added separately)
                
                # Population by location
                pop_by_loc = {}
                pop_by_type = {'camp': 0, 'town': 0, 'conflict': 0, 'unknown': 0}
                s2_by_loc = {}
                s2_count_by_loc = {}
                total_by_loc = {}
                
                for loc_name, location in location_map.items():
                    pop = location.numAgents
                    pop_by_loc[loc_name] = pop
                    metrics['population_by_location'][loc_name].append(pop)
                    
                    # Track by type
                    loc_type = location.location_type if hasattr(location, 'location_type') else 'unknown'
                    if loc_type == 'camp':
                        pop_by_type['camp'] += pop
                    elif loc_type == 'town':
                        pop_by_type['town'] += pop
                    elif loc_type == 'conflict':
                        pop_by_type['conflict'] += pop
                    else:
                        pop_by_type['unknown'] += pop
                    
                    # S2 activation by location
                    s2_count = 0
                    total_agents = 0
                    for agent in agents:
                        if agent is not None and hasattr(agent, 'location') and agent.location == location:
                            total_agents += 1
                            cognitive_state = getattr(agent, 'cognitive_state', 'S1')
                            if cognitive_state == 'S2':
                                s2_count += 1
                    
                    if total_agents > 0:
                        s2_rate = s2_count / total_agents
                    else:
                        s2_rate = 0.0
                    
                    s2_by_loc[loc_name] = s2_rate
                    s2_count_by_loc[loc_name] = s2_count
                    total_by_loc[loc_name] = total_agents
                    metrics['s2_activation_by_location'][loc_name].append(s2_rate)
                
                # Track agent states (ALL agents at ALL timesteps, like nuclear simulations)
                agent_states = []
                for idx, agent in enumerate(agents):
                    if agent.location is None:
                        continue
                    
                    # Skip agents that are travelling (on routes) - they'll be handled by agent logs
                    if agent.travelling:
                        continue
                    
                    # Get location coordinates (agents are at discrete locations)
                    loc_x = agent.location.x if agent.location else 0.0
                    loc_y = agent.location.y if agent.location else 0.0
                    
                    # Check if agent is in a safe zone (camp) - still need jitter to prevent overlap!
                    location_name = agent.location.name if agent.location else 'Unknown'
                    is_safe_zone = (agent.location.camp or 
                                   'border' in location_name.lower() or 
                                   'safezone' in location_name.lower())
                    
                    # Add DETERMINISTIC jitter for ALL locations (including safe zones)
                    # Same agent at same location = same offset every timestep
                    # Different agents at same location = different offsets (no overlap)
                    # Safe zones get slightly smaller radius but still need jitter
                    offset_radius = 25.0 if not is_safe_zone else 20.0  # Slightly smaller for safe zones
                    import hashlib
                    hash_input = f"{idx}_{location_name}".encode('utf-8')
                    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                    # Use different seeds for x and y to ensure better distribution
                    np.random.seed(hash_value % (2**32))  # Seed from hash
                    offset_x = np.random.uniform(-offset_radius, offset_radius)
                    np.random.seed((hash_value + 12345) % (2**32))  # Different seed for y
                    offset_y = np.random.uniform(-offset_radius, offset_radius)
                    
                    # Get actual cognitive state (agents in safe zones can be S2)
                    cognitive_state = getattr(agent, 'cognitive_state', 'S1')
                    
                    agent_states.append({
                        'id': f'agent_{idx}',  # Use consistent ID format
                        'location': location_name,
                        'cognitive_state': cognitive_state,  # Use actual state, not default
                        'connections': agent.attributes.get('connections', 0),
                        'timesteps_since_departure': getattr(agent, 'timesteps_since_departure', 0),
                        'x': loc_x + offset_x,  # Store actual coordinates with offset
                        'y': loc_y + offset_y,
                    })
                metrics['agent_states'].append({
                    'timestep': t,  # t is now 1, 2, 3, ... (t=0 was logged before loop)
                    'agents': agent_states
                })
                
                # Connection statistics
                connections = [a.attributes.get('connections', 0) for a in agents]
                metrics['connection_stats'][t] = {
                    'mean': np.mean(connections),
                    'std': np.std(connections),
                    'min': np.min(connections),
                    'max': np.max(connections),
                }
                
                # Print progress
                if t % 10 == 0 or t == num_timesteps:
                    total_s2 = sum(s2_count_by_loc.values())
                    total_agents_active = sum(total_by_loc.values())
                    overall_s2_rate = total_s2 / total_agents_active if total_agents_active > 0 else 0.0
                    print(f"  Timestep {t:3d}: S2 rate = {overall_s2_rate:.1%}, "
                          f"Pop in camps = {pop_by_type['camp']}, "
                          f"Avg connections = {np.mean(connections):.1f}")
            
            # Final route choice analysis (for scenarios with multiple routes)
            route_choices = {}
            for agent in agents:
                if agent is not None and hasattr(agent, 'location') and agent.location:
                    loc_name = agent.location.name
                    if 'Border' in loc_name or 'SafeZone' in loc_name:
                        if loc_name not in route_choices:
                            route_choices[loc_name] = {'S1': 0, 'S2': 0, 'total': 0}
                        cognitive_state = getattr(agent, 'cognitive_state', 'S1')
                        route_choices[loc_name][cognitive_state] += 1
                        route_choices[loc_name]['total'] += 1
            
            metrics['route_choices'] = route_choices
            
            # Restore directory
            os.chdir(original_dir)
            
            # Save results
            result = {
                'scenario_name': scenario_name,
                'num_agents': num_agents,
                'num_timesteps': num_timesteps,
                'locations': locations,
                'routes': routes,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat(),
                'run_directory': str(run_dir),  # Save reference to input files
            }
            
            # Save to JSON in run directory
            result_file = run_dir / f"{scenario_name_clean}_results.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n✅ Scenario complete: {scenario_name}")
            print(f"   Results saved to: {result_file}")
            print(f"   Input files in: {run_dir}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Error running scenario {scenario_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_all_scenarios(self, num_agents=500, num_timesteps=60):  # Increased to 60 for longer journeys
        """Run all four scenarios."""
        scenarios = [
            self.create_scenario_1_nearest_border(),
            self.create_scenario_2_multiple_routes(),
            self.create_scenario_3_social_connections(),
            self.create_scenario_4_context_transition(),
        ]
        
        all_results = []
        for locations, routes, scenario_name in scenarios:
            result = self.run_simulation(
                scenario_name=scenario_name,
                locations=locations,
                routes=routes,
                num_agents=num_agents,
                num_timesteps=num_timesteps,
                s1s2_enabled=True
            )
            if result:
                all_results.append(result)
                self.results.append(result)
        
        # Save summary
        summary_file = self.output_dir / "all_scenarios_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'scenarios': [r['scenario_name'] for r in all_results],
                'num_agents': num_agents,
                'num_timesteps': num_timesteps,
                'timestamp': datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"All scenarios complete!")
        print(f"Summary saved to: {summary_file}")
        print(f"{'='*60}\n")
        
        return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run refugee movement simulations")
    parser.add_argument("--scenario", type=str, choices=['1', '2', '3', '4', 'all'],
                       default='all', help="Which scenario to run")
    parser.add_argument("--agents", type=int, default=500, help="Number of agents")
    parser.add_argument("--timesteps", type=int, default=40, help="Number of timesteps")
    
    args = parser.parse_args()
    
    simulator = RefugeeSimulator()
    
    if args.scenario == 'all':
        simulator.run_all_scenarios(num_agents=args.agents, num_timesteps=args.timesteps)
    else:
        scenario_map = {
            '1': simulator.create_scenario_1_nearest_border,
            '2': simulator.create_scenario_2_multiple_routes,
            '3': simulator.create_scenario_3_social_connections,
            '4': simulator.create_scenario_4_context_transition,
        }
        
        locations, routes, scenario_name = scenario_map[args.scenario]()
        simulator.run_simulation(
            scenario_name=scenario_name,
            locations=locations,
            routes=routes,
            num_agents=args.agents,
            num_timesteps=args.timesteps,
            s1s2_enabled=True
        )

