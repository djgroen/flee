#!/usr/bin/env python3
"""
Idealized Nuclear Evacuation Simulations with Dual-Process S1/S2 Model

Three topologies most relevant for nuclear-related evacuations:
1. **Ring/Circular**: Evacuation zones (circular danger zones around facility)
2. **Star/Hub-and-Spoke**: Central facility with evacuation routes radiating outward
3. **Linear**: Single evacuation corridor along major road/route

Uses the aligned parsimonious dual-process model (P_S2 = Ψ × Ω).
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import yaml

sys.path.insert(0, '.')

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee.moving import calculateMoveChance
from flee.flee import Person


class NuclearEvacuationSimulator:
    """Simulator for nuclear evacuation scenarios with S1/S2 decision-making."""
    
    def __init__(self, output_dir="data/nuclear_evacuation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def create_ring_topology(self, n_locations=12, radius=100.0, decision_rich=False):
        """
        Create ring/circular topology (evacuation zones).
        
        Relevant for: Circular danger zones around nuclear facility
        - Locations arranged in concentric rings
        - Inner ring: high danger (conflict zone)
        - Outer rings: progressively safer
        - Agents start at center, evacuate outward
        
        If decision_rich=True: Creates multiple route choices and safe zones
        """
        locations = []
        routes = []
        
        # Center location (nuclear facility - highest danger)
        locations.append({
            'name': 'Facility',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.95,  # Extreme danger
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Create rings at different distances (more spread out for visibility)
        n_rings = 3
        if decision_rich:
            locations_per_ring = 6  # More locations = more choices
        else:
            locations_per_ring = 4  # Fixed to 4 for clearer visualization
        
        for ring in range(1, n_rings + 1):
            ring_radius = radius * ring / n_rings
            angle_step = 2 * np.pi / locations_per_ring
            
            for i in range(locations_per_ring):
                angle = i * angle_step
                x = ring_radius * np.cos(angle)
                y = ring_radius * np.sin(angle)
                
                # Conflict decreases with distance
                conflict = max(0.1, 0.95 - (ring * 0.25))
                
                loc_name = f'Ring{ring}_Loc{i+1}'
                locations.append({
                    'name': loc_name,
                    'x': x, 'y': y,
                    'type': 'town',
                    'conflict': conflict,
                    'movechance': 0.3,
                    'capacity': -1
                })
                
                # Connect to previous ring or center
                if ring == 1:
                    # Connect to center
                    routes.append({
                        'from': 'Facility',
                        'to': loc_name,
                        'distance': ring_radius
                    })
                else:
                    # Connect to nearest location in previous ring
                    prev_ring = ring - 1
                    prev_angle = angle
                    prev_loc_name = f'Ring{prev_ring}_Loc{(i % locations_per_ring) + 1}'
                    routes.append({
                        'from': prev_loc_name,
                        'to': loc_name,
                        'distance': radius / n_rings
                    })
                    
                    # DECISION-RICH: Add alternative path (adjacent location)
                    if decision_rich:
                        adj_i = (i + 1) % locations_per_ring
                        adj_loc_name = f'Ring{prev_ring}_Loc{adj_i+1}'
                        routes.append({
                            'from': adj_loc_name,
                            'to': loc_name,
                            'distance': radius / n_rings * 1.5  # Longer but alternative
                        })
                
                # ADD: Connect adjacent locations in same ring (creates circular paths)
                # This adds decision complexity: go around ring or go outward?
                if ring > 1:  # Only for outer rings to avoid too many connections
                    next_i = (i + 1) % locations_per_ring
                    next_loc_name = f'Ring{ring}_Loc{next_i + 1}'
                    routes.append({
                        'from': loc_name,
                        'to': next_loc_name,
                        'distance': 2 * ring_radius * np.sin(angle_step / 2)  # Arc distance
                    })
        
        # Add safe zone(s) at outer edge
        if decision_rich:
            # MULTIPLE safe zones at different angles (creates destination choice)
            n_safe_zones = 3
            for i in range(n_safe_zones):
                angle = i * 2 * np.pi / n_safe_zones
                safe_x = radius * 1.5 * np.cos(angle)
                safe_y = radius * 1.5 * np.sin(angle)
                
                safe_name = f'SafeZone{i+1}'
                locations.append({
                    'name': safe_name,
                    'x': safe_x, 'y': safe_y,
                    'type': 'camp',
                    'conflict': 0.0,
                    'movechance': 0.001,
                    'capacity': 10000
                })
                
                # Connect ALL outer ring locations to ALL safe zones (ensures all 3 safe zones are accessible)
                for j in range(locations_per_ring):
                    ring3_loc = f'Ring{n_rings}_Loc{j+1}'
                    ring3_angle = j * angle_step
                    dist_to_safe = np.sqrt(
                        (ring_radius * np.cos(ring3_angle) - safe_x)**2 + 
                        (ring_radius * np.sin(ring3_angle) - safe_y)**2
                    )
                    # Connect ALL safe zones to ALL Ring3 locations (removed i < 2 restriction)
                    routes.append({
                        'from': ring3_loc,
                        'to': safe_name,
                        'distance': dist_to_safe
                    })
        else:
            # Single safe zone (original)
            safe_zone = {
                'name': 'SafeZone',
                'x': radius * 1.5, 'y': 0.0,
                'type': 'camp',
                'conflict': 0.0,
                'movechance': 0.001,
                'capacity': 10000
            }
            locations.append(safe_zone)
            
            # Connect ALL outer ring locations to safe zone (fixes bottleneck)
            for i in range(locations_per_ring):
                routes.append({
                    'from': f'Ring{n_rings}_Loc{i+1}',
                    'to': 'SafeZone',
                    'distance': radius * 0.5
                })
        
        return locations, routes
    
    def create_star_topology(self, n_spokes=6, spoke_length=200.0):
        """
        Create star/hub-and-spoke topology.
        
        Relevant for: Central nuclear facility with evacuation routes radiating outward
        - Center: nuclear facility (high danger)
        - Spokes: evacuation routes in different directions
        - Endpoints: safe zones/camps
        """
        locations = []
        routes = []
        
        # Center location (nuclear facility)
        locations.append({
            'name': 'Facility',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.95,
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Create spokes (evacuation routes)
        angle_step = 2 * np.pi / n_spokes
        
        for i in range(n_spokes):
            angle = i * angle_step
            
            # Intermediate town along route
            mid_x = spoke_length * 0.5 * np.cos(angle)
            mid_y = spoke_length * 0.5 * np.sin(angle)
            
            mid_name = f'Route{i+1}_Mid'
            locations.append({
                'name': mid_name,
                'x': mid_x, 'y': mid_y,
                'type': 'town',
                'conflict': 0.4,  # Moderate danger
                'movechance': 0.3,
                'capacity': -1
            })
            
            # Safe zone at end of route
            end_x = spoke_length * np.cos(angle)
            end_y = spoke_length * np.sin(angle)
            
            end_name = f'SafeZone{i+1}'
            locations.append({
                'name': end_name,
                'x': end_x, 'y': end_y,
                'type': 'camp',
                'conflict': 0.0,
                'movechance': 0.001,
                'capacity': 5000
            })
            
            # Routes: Facility -> Mid -> SafeZone
            routes.append({
                'from': 'Facility',
                'to': mid_name,
                'distance': spoke_length * 0.5
            })
            routes.append({
                'from': mid_name,
                'to': end_name,
                'distance': spoke_length * 0.5
            })
        
        return locations, routes
    
    def create_linear_topology(self, n_locations=8, total_length=300.0):
        """
        Create linear topology (single evacuation corridor).
        
        Relevant for: Evacuation along major road/route away from facility
        - Linear chain of locations
        - High conflict at start (near facility)
        - Decreasing conflict along route
        - Safe zone at end
        """
        locations = []
        routes = []
        
        # Start location (near facility - high danger)
        locations.append({
            'name': 'NearFacility',
            'x': 0.0, 'y': 0.0,
            'type': 'conflict',
            'conflict': 0.9,
            'movechance': 1.0,
            'capacity': -1
        })
        
        # Intermediate locations along route
        step_length = total_length / (n_locations - 1)
        
        for i in range(1, n_locations - 1):
            x = i * step_length
            conflict = max(0.1, 0.9 - (i * 0.15))  # Decreasing conflict
            
            loc_name = f'Location{i}'
            locations.append({
                'name': loc_name,
                'x': x, 'y': 0.0,
                'type': 'town',
                'conflict': conflict,
                'movechance': 0.3,
                'capacity': -1
            })
            
            # Connect to previous location
            prev_name = 'NearFacility' if i == 1 else f'Location{i-1}'
            routes.append({
                'from': prev_name,
                'to': loc_name,
                'distance': step_length
            })
        
        # Safe zone at end
        safe_zone = {
            'name': 'SafeZone',
            'x': total_length, 'y': 0.0,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        }
        locations.append(safe_zone)
        
        # Connect last location to safe zone
        routes.append({
            'from': f'Location{n_locations-2}',
            'to': 'SafeZone',
            'distance': step_length
        })
        
        return locations, routes
    
    def run_simulation(self, topology_name, locations, routes, num_agents=100, 
                      num_timesteps=30, s1s2_enabled=True):
        """Run a single simulation with given topology."""
        
        print(f"\n{'='*60}")
        print(f"🧪 {topology_name} Topology Simulation")
        print(f"{'='*60}")
        print(f"Locations: {len(locations)}, Routes: {len(routes)}")
        print(f"Agents: {num_agents}, Timesteps: {num_timesteps}")
        
        # Create configuration
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
                'max_move_speed': 360.0,
                'max_walk_speed': 35.0,
                'foreign_weight': 1.0,
                'camp_weight': 3.0,  # Increased to 3.0 to make safe zones highly attractive
                'conflict_weight': 0.25,
                'conflict_movechance': 1.0,  # HIGH movechance to escape danger zones
                'camp_movechance': 0.001,
                'default_movechance': 0.3,
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
                    'alpha': 2.0,
                    'beta': 2.0,
                    'p_s2': 0.9  # Increased from 0.8 to make S2 decisions more visible
                },
                'awareness_level': 2  # Increased from 1 to give S2 agents more route visibility
            },
            'optimisations': {'hasten': 1}
        }
        
        # Create run-specific directory for input files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / f'run_{topology_name}_{timestamp}'
        run_dir.mkdir(exist_ok=True)
        
        # Write config to run directory
        config_file = run_dir / f'config_{topology_name}.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Save locations as CSV (Flee format)
        locations_csv = run_dir / f'locations_{topology_name}.csv'
        with open(locations_csv, 'w') as f:
            # Header: name,region,x,y,location_type,movechance,capacity,pop,country,conflict,conflict_date,attributes
            f.write('name,region,x,y,location_type,movechance,capacity,pop,country,conflict,conflict_date,attributes\n')
            for loc in locations:
                f.write(f"{loc['name']},unknown,{loc['x']},{loc['y']},{loc.get('type', 'town')},"
                       f"{loc['movechance']},{loc['capacity']},0,unknown,{loc.get('conflict', 0.0)},0,{{}}\n")
        
        # Save routes as CSV (Flee format)
        routes_csv = run_dir / f'routes_{topology_name}.csv'
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
            import os
            original_dir = os.getcwd()
            os.chdir(str(self.output_dir))
            
            # Clean up any existing agents.out.0 from previous topology (but keep topology-specific ones)
            agents_out_0 = self.output_dir / 'agents.out.0'
            if agents_out_0.exists():
                agents_out_0.unlink()
            
            # Add locations
            location_map = {}
            for loc in locations:
                # IMPORTANT: Pass location_type to properly designate camps
                # This ensures safe zones are marked as camps and agents don't leave them
                location_type = loc.get('type', 'town')
                location = ecosystem.addLocation(
                    name=loc['name'],
                    x=loc['x'], y=loc['y'],
                    location_type=location_type,  # Pass type so camps are properly designated
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
            
            # Create agents with varied experience
            agents = []
            for i in range(num_agents):
                # Varied experience profiles
                attributes = {
                    'education_level': np.random.uniform(0.3, 0.9),
                    'local_knowledge': np.random.uniform(0.0, 1.0),
                    'conflict_exposure': np.random.uniform(0.0, 0.8),
                    'connections': np.random.randint(0, 8),
                    'age_factor': np.random.uniform(0.2, 0.9)
                }
                
                agent = Person(origin, attributes)
                ecosystem.agents.append(agent)
                agents.append(agent)
            
            # Run simulation
            s2_activations_by_time = []
            agents_at_safe_by_time = []
            avg_pressure_by_time = []
            agent_s2_states_by_time = {}  # Track individual agent S2 states
            population_by_type_time = []  # Track population by location type over time
            
            for t in range(num_timesteps):
                # Track metrics
                s2_count = 0
                total_decisions = 0
                total_pressure = 0.0
                agents_at_safe = 0
                agent_states = {}  # agent_id -> {'s2_active': bool, 'x': float, 'y': float, 'location': str, 'cognitive_state': str}
                
                # Track population by location type (initialize each timestep)
                pop_by_type = {'camp': 0, 'town': 0, 'conflict': 0, 'unknown': 0}
                
                for idx, agent in enumerate(agents):
                    if agent.location is None:
                        continue
                    
                    # Calculate cognitive pressure
                    pressure = agent.calculate_cognitive_pressure(t)
                    total_pressure += pressure
                    
                    # Calculate move chance (triggers S1/S2)
                    move_chance, s2_weight = calculateMoveChance(agent, ForceTownMove=False, time=t)
                    s2_active = s2_weight > 0.5  # V3: threshold for "S2 dominant" (backward compat)
                    
                    cognitive_state = "S2" if s2_active else "S1"
                    
                    # Store agent state for visualization
                    # Use agent index as ID for consistency
                    agent_id = f"agent_{idx}"
                    
                    # Get location coordinates (agents are at discrete locations)
                    loc_x = agent.location.x if agent.location else 0.0
                    loc_y = agent.location.y if agent.location else 0.0
                    
                    # Add random offset for agents at same location (so we can see them individually)
                    # This simulates agents being spread around a location
                    import random
                    offset_radius = 10.0  # Increased offset to reduce marker overlap
                    offset_x = random.uniform(-offset_radius, offset_radius)
                    offset_y = random.uniform(-offset_radius, offset_radius)
                    
                    experience_index = getattr(agent, 'experience_index', 0.5)
                    
                    agent_states[agent_id] = {
                        's2_active': s2_active,
                        's2_weight': s2_weight,
                        'x': loc_x + offset_x,
                        'y': loc_y + offset_y,
                        'location': agent.location.name if agent.location else 'Unknown',
                        'cognitive_state': cognitive_state,
                        'agent_index': idx,
                        'experience_index': experience_index
                    }
                    
                    if s2_active:
                        s2_count += 1
                    total_decisions += 1
                    
                    # Check if at safe zone
                    if agent.location and agent.location.name.startswith('SafeZone'):
                        agents_at_safe += 1
                    
                    # Track population by location type
                    if agent.location:
                        # Get location type from location_map
                        loc_name = agent.location.name
                        loc_type = 'unknown'
                        for loc in locations:
                            if loc['name'] == loc_name:
                                loc_type = loc.get('type', 'town')
                                break
                        pop_by_type[loc_type] = pop_by_type.get(loc_type, 0) + 1
                
                # Store agent states for this timestep
                agent_s2_states_by_time[t] = agent_states
                
                # Store population by type for this timestep
                population_by_type_time.append(pop_by_type.copy())
                
                s2_rate = (s2_count / total_decisions * 100) if total_decisions > 0 else 0.0
                avg_pressure = total_pressure / len(agents) if agents else 0.0
                
                s2_activations_by_time.append(s2_rate)
                agents_at_safe_by_time.append(agents_at_safe)
                avg_pressure_by_time.append(avg_pressure)
                
                # Evolve ecosystem
                ecosystem.evolve()
                
                if t % 5 == 0 or t == num_timesteps - 1:
                    print(f"  t={t:2d}: S2 rate={s2_rate:5.1f}%, Safe={agents_at_safe:3d}, "
                          f"Avg pressure={avg_pressure:.3f}")
            
            # Save agent log file BEFORE returning (ensure it's saved for this topology)
            # IMPORTANT: We're in self.output_dir, so use current directory paths
            import shutil
            import os
            agent_log = Path('agents.out.0')  # Current directory (we're in output_dir)
            topology_log = Path(f'agents_{topology_name.lower()}.out')
            
            if agent_log.exists():
                if topology_log.exists():
                    topology_log.unlink()
                try:
                    shutil.copy2(agent_log, topology_log)
                    file_size_mb = agent_log.stat().st_size / 1024 / 1024
                    print(f"📝 Agent logs saved to: {topology_log.name} ({file_size_mb:.1f} MB)")
                except Exception as e:
                    print(f"⚠️  Warning: Could not copy agent logs: {e}")
            else:
                print(f"⚠️  Warning: agents.out.0 not found for {topology_name} topology (current dir: {os.getcwd()})")
            
            # Final statistics
            final_s2_rate = s2_activations_by_time[-1]
            final_safe = agents_at_safe_by_time[-1]
            avg_s2_rate = np.mean(s2_activations_by_time)
            max_s2_rate = np.max(s2_activations_by_time)
            
            result = {
                'topology': topology_name,
                'num_agents': num_agents,
                'num_timesteps': num_timesteps,
                'num_locations': len(locations),
                'num_routes': len(routes),
                'final_s2_rate': final_s2_rate,
                'avg_s2_rate': avg_s2_rate,
                'max_s2_rate': max_s2_rate,
                'final_agents_at_safe': final_safe,
                'final_agents_at_safe_pct': (final_safe / num_agents * 100),
                'avg_pressure': np.mean(avg_pressure_by_time),
                's2_activations_by_time': s2_activations_by_time,
                'agents_at_safe_by_time': agents_at_safe_by_time,
                'avg_pressure_by_time': avg_pressure_by_time,
                'population_by_type_time': population_by_type_time,  # Track population by location type
                'agent_logs_file': str(self.output_dir / topology_log) if topology_log.exists() else None,
                # Store topology structure for visualization (INCLUDE CAPACITY)
                'locations': [{'name': loc['name'], 'x': loc['x'], 'y': loc['y'], 
                              'conflict': loc.get('conflict', 0.0), 'type': loc.get('type', 'town'),
                              'capacity': loc.get('capacity', -1)} 
                             for loc in locations],
                'routes': [{'from': route['from'], 'to': route['to'], 'distance': route['distance']} 
                          for route in routes],
                # Store individual agent S2 states for visualization
                'agent_s2_states_by_time': agent_s2_states_by_time,
                # Input files (will be added in finally block)
                'input_files': {
                    'config': str(config_file),
                    'locations': str(locations_csv),
                    'routes': str(routes_csv),
                    'run_directory': str(run_dir)
                }
            }
            
            self.results.append(result)
            
            print(f"\n📊 Results:")
            print(f"   Final S2 rate: {final_s2_rate:.1f}%")
            print(f"   Average S2 rate: {avg_s2_rate:.1f}%")
            print(f"   Agents at safe zones: {final_safe}/{num_agents} ({final_safe/num_agents*100:.1f}%)")
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Save agent log file with topology-specific name (preserve for each topology)
            if 'original_dir' in locals():
                agent_log = self.output_dir / 'agents.out.0'
                if agent_log.exists():
                    # Use topology-specific name to avoid overwriting between topologies
                    topology_log = self.output_dir / f'agents_{topology_name.lower()}.out'
                    if topology_log.exists():
                        topology_log.unlink()  # Remove old file if exists (from previous run)
                    
                    # Copy instead of rename, so we can keep both if needed
                    import shutil
                    shutil.copy2(agent_log, topology_log)
                    print(f"📝 Agent logs saved to: {topology_log.name} ({agent_log.stat().st_size} bytes)")
                    
                    # Keep agents.out.0 for now (will be overwritten by next topology, but that's OK)
                    # The topology-specific copy is what we use for visualization
                
                # Restore original directory
                os.chdir(original_dir)
            
            # Update result with input files if result exists
            if 'result' in locals() and result:
                result['input_files'] = {
                    'config': str(config_file),
                    'locations': str(locations_csv),
                    'routes': str(routes_csv),
                    'run_directory': str(run_dir)
                }
            
            # Don't remove config file - it's now saved in run directory
    
    def run_all_topologies(self, num_agents=100, num_timesteps=30, decision_rich=False):
        """Run simulations for all three topologies.
        
        Args:
            num_agents: Number of agents per simulation
            num_timesteps: Number of timesteps
            decision_rich: If True, use topologies with multiple route choices
        """
        
        print("\n" + "="*60)
        print("NUCLEAR EVACUATION SIMULATIONS")
        print("Dual-Process S1/S2 Model (P_S2 = Ψ × Ω)")
        if decision_rich:
            print("🎯 DECISION-RICH MODE: Multiple route choices enabled")
        print("="*60)
        
        # 1. Ring topology
        ring_locs, ring_routes = self.create_ring_topology(n_locations=12, radius=100.0, decision_rich=decision_rich)
        self.run_simulation("Ring", ring_locs, ring_routes, num_agents, num_timesteps)
        
        # 2. Star topology
        star_locs, star_routes = self.create_star_topology(n_spokes=6, spoke_length=200.0)
        self.run_simulation("Star", star_locs, star_routes, num_agents, num_timesteps)
        
        # 3. Linear topology
        linear_locs, linear_routes = self.create_linear_topology(n_locations=8, total_length=300.0)
        self.run_simulation("Linear", linear_locs, linear_routes, num_agents, num_timesteps)
        
        # Save results
        self.save_results()
        
    def save_results(self):
        """Save results to CSV and JSON."""
        if not self.results:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary CSV
        summary_data = []
        for r in self.results:
            summary_data.append({
                'topology': r['topology'],
                'num_agents': r['num_agents'],
                'num_timesteps': r['num_timesteps'],
                'num_locations': r['num_locations'],
                'num_routes': r['num_routes'],
                'final_s2_rate': r['final_s2_rate'],
                'avg_s2_rate': r['avg_s2_rate'],
                'max_s2_rate': r['max_s2_rate'],
                'final_agents_at_safe': r['final_agents_at_safe'],
                'final_agents_at_safe_pct': r['final_agents_at_safe_pct'],
                'avg_pressure': r['avg_pressure']
            })
        
        df = pd.DataFrame(summary_data)
        csv_file = self.output_dir / f'nuclear_evacuation_summary_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        print(f"\n📊 Summary saved to: {csv_file}")
        
        # Save detailed JSON
        import json
        json_file = self.output_dir / f'nuclear_evacuation_detailed_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📊 Detailed results saved to: {json_file}")


if __name__ == "__main__":
    import sys
    
    simulator = NuclearEvacuationSimulator()
    
    # Check for decision-rich mode
    decision_rich = '--decision-rich' in sys.argv or '-d' in sys.argv
    
    # Run simulations
    # Using 1,000 agents for better flocking visualization (faster than 10,000)
    # Check for longer simulation flag
    longer_sim = '--longer' in sys.argv or '-l' in sys.argv
    num_timesteps = 60 if longer_sim else 30
    if longer_sim:
        print(f"⏱️  Running LONGER simulations: {num_timesteps} timesteps")
    simulator.run_all_topologies(num_agents=1000, num_timesteps=num_timesteps, decision_rich=decision_rich)
    
    if decision_rich:
        print("\n" + "="*60)
        print("✅ Decision-rich simulations complete!")
        print("   Topologies now have multiple route choices")
        print("   S1 vs S2 decisions should be more visible in animations")
        print("="*60)

