#!/usr/bin/env python3
"""
Improved Topologies for More Interesting Agent Decisions

These topologies create decision points where S1 vs S2 choices lead to 
different outcomes, making the animations more visually interesting.
"""

import numpy as np


def create_decision_rich_ring_topology(n_rings=3, radius=100.0):
    """
    Ring topology with multiple route choices at each level.
    
    Key improvements:
    - Multiple paths between rings (not just nearest neighbor)
    - Some routes are shorter but more dangerous
    - Some routes are longer but safer
    - Agents can choose to go around ring or directly outward
    """
    locations = []
    routes = []
    
    # Center location (nuclear facility - highest danger)
    locations.append({
        'name': 'Facility',
        'x': 0.0, 'y': 0.0,
        'type': 'conflict',
        'conflict': 0.95,
        'movechance': 1.0,
        'capacity': -1
    })
    
    locations_per_ring = 6  # More locations = more choices
    n_rings = 3
    
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
            
            # Connect to previous ring - MULTIPLE CHOICES
            if ring == 1:
                # Connect to center
                routes.append({
                    'from': 'Facility',
                    'to': loc_name,
                    'distance': ring_radius
                })
            else:
                # Connect to MULTIPLE locations in previous ring (creates choices)
                prev_ring = ring - 1
                
                # Option 1: Direct path (nearest neighbor) - SHORTER but same conflict
                prev_i = i
                prev_loc_name = f'Ring{prev_ring}_Loc{prev_i+1}'
                routes.append({
                    'from': prev_loc_name,
                    'to': loc_name,
                    'distance': radius / n_rings  # Short distance
                })
                
                # Option 2: Adjacent path (one location over) - LONGER but might be safer
                if ring > 1:
                    adj_i = (i + 1) % locations_per_ring
                    adj_loc_name = f'Ring{prev_ring}_Loc{adj_i+1}'
                    routes.append({
                        'from': adj_loc_name,
                        'to': loc_name,
                        'distance': radius / n_rings * 1.5  # Longer distance
                    })
            
            # Connect to adjacent locations in same ring (circular paths)
            # This creates choice: go around ring or go outward?
            next_i = (i + 1) % locations_per_ring
            next_loc_name = f'Ring{ring}_Loc{next_i+1}'
            routes.append({
                'from': loc_name,
                'to': next_loc_name,
                'distance': 2 * ring_radius * np.sin(angle_step / 2)  # Arc distance
            })
    
    # Add MULTIPLE safe zones at different angles (creates destination choice)
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
        
        # Connect outer ring locations to NEAREST safe zone (creates routing choice)
        for j in range(locations_per_ring):
            ring3_loc = f'Ring{n_rings}_Loc{j+1}'
            ring3_angle = j * angle_step
            # Calculate distance to this safe zone
            dist_to_safe = np.sqrt(
                (ring_radius * np.cos(ring3_angle) - safe_x)**2 + 
                (ring_radius * np.sin(ring3_angle) - safe_y)**2
            )
            # Only connect if this is one of the 2 closest safe zones
            # (creates choice between safe zones)
            if i < 2:  # Connect to first 2 safe zones from each location
                routes.append({
                    'from': ring3_loc,
                    'to': safe_name,
                    'distance': dist_to_safe
                })
    
    return locations, routes


def create_decision_rich_star_topology(n_spokes=6, spoke_length=200.0):
    """
    Star topology with multiple routes and decision points.
    
    Key improvements:
    - Multiple intermediate towns per spoke (creates route choices)
    - Some spokes have shortcuts (faster but more dangerous)
    - Some spokes have detours (safer but longer)
    - Cross-connections between spokes (creates routing complexity)
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
    
    angle_step = 2 * np.pi / n_spokes
    
    for i in range(n_spokes):
        angle = i * angle_step
        
        # Create MULTIPLE intermediate towns per spoke (creates choices)
        n_intermediate = 2
        
        for j in range(n_intermediate):
            # First intermediate town (closer, higher conflict)
            if j == 0:
                mid_x = spoke_length * 0.3 * np.cos(angle)
                mid_y = spoke_length * 0.3 * np.sin(angle)
                conflict = 0.6
            else:
                # Second intermediate town (further, lower conflict)
                mid_x = spoke_length * 0.6 * np.cos(angle)
                mid_y = spoke_length * 0.6 * np.sin(angle)
                conflict = 0.3
            
            mid_name = f'Route{i+1}_Town{j+1}'
            locations.append({
                'name': mid_name,
                'x': mid_x, 'y': mid_y,
                'type': 'town',
                'conflict': conflict,
                'movechance': 0.3,
                'capacity': -1
            })
            
            # Connect from previous location
            if j == 0:
                # From facility
                routes.append({
                    'from': 'Facility',
                    'to': mid_name,
                    'distance': spoke_length * 0.3
                })
            else:
                # From previous town
                prev_name = f'Route{i+1}_Town{j}'
                routes.append({
                    'from': prev_name,
                    'to': mid_name,
                    'distance': spoke_length * 0.3
                })
        
        # Safe zone at end
        end_x = spoke_length * np.cos(angle)
        end_y = spoke_length * np.sin(angle)
        end_name = f'SafeZone{i+1}'
        locations.append({
            'name': end_name,
            'x': end_x, 'y': end_y,
            'type': 'camp',
            'conflict': 0.0,
            'movechance': 0.001,
            'capacity': 10000
        })
        
        # Connect last town to safe zone
        last_town = f'Route{i+1}_Town{n_intermediate}'
        routes.append({
            'from': last_town,
            'to': end_name,
            'distance': spoke_length * 0.4
        })
        
        # ADD: Cross-connections between adjacent spokes (creates routing choices)
        # Agents can switch to a different route if it looks better
        if i < n_spokes - 1:
            next_angle = (i + 1) * angle_step
            next_town1 = f'Route{(i+1)%n_spokes+1}_Town1'
            routes.append({
                'from': mid_name,
                'to': next_town1,
                'distance': spoke_length * 0.4  # Cross-connection distance
            })
    
    return locations, routes


def create_decision_rich_linear_topology(n_locations=10, total_length=300.0):
    """
    Linear topology with branching paths and decision points.
    
    Key improvements:
    - Multiple parallel routes (some faster, some safer)
    - Branching points where agents choose
    - Some routes merge back (creates convergence)
    - Dead-end branches (tests S2 route planning)
    """
    locations = []
    routes = []
    
    # Start location
    locations.append({
        'name': 'NearFacility',
        'x': 0.0, 'y': 0.0,
        'type': 'conflict',
        'conflict': 0.9,
        'movechance': 1.0,
        'capacity': -1
    })
    
    step_length = total_length / (n_locations - 1)
    
    # Create main route with branching points
    for i in range(1, n_locations - 1):
        x = i * step_length
        conflict = max(0.1, 0.9 - (i * 0.1))
        
        # Main route location
        loc_name = f'Main{i}'
        locations.append({
            'name': loc_name,
            'x': x, 'y': 0.0,
            'type': 'town',
            'conflict': conflict,
            'movechance': 0.3,
            'capacity': -1
        })
        
        # Connect to previous location
        prev_name = 'NearFacility' if i == 1 else f'Main{i-1}'
        routes.append({
            'from': prev_name,
            'to': loc_name,
            'distance': step_length
        })
        
        # ADD: Branching routes at key decision points
        if i % 3 == 0:  # Every 3rd location has a branch
            # Branch route (alternative path)
            branch_name = f'Branch{i}'
            locations.append({
                'name': branch_name,
                'x': x, 'y': 30.0,  # Offset vertically
                'type': 'town',
                'conflict': conflict * 0.8,  # Slightly safer
                'movechance': 0.3,
                'capacity': -1
            })
            
            # Connect to branch (creates choice)
            routes.append({
                'from': prev_name,
                'to': branch_name,
                'distance': step_length * 1.2  # Longer but safer
            })
            
            # Branch connects to next main location (merges back)
            routes.append({
                'from': branch_name,
                'to': loc_name,
                'distance': step_length * 1.1
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
        'from': f'Main{n_locations-2}',
        'to': 'SafeZone',
        'distance': step_length
    })
    
    return locations, routes


def create_maze_like_topology():
    """
    Grid-like topology with multiple paths and decision complexity.
    
    Creates a more complex evacuation scenario where agents must navigate
    through a grid with multiple route choices at each intersection.
    """
    locations = []
    routes = []
    
    grid_size = 4  # 4x4 grid
    cell_size = 50.0
    
    # Create grid locations
    for i in range(grid_size):
        for j in range(grid_size):
            x = i * cell_size
            y = j * cell_size
            
            # Conflict decreases as we move away from origin
            conflict = max(0.1, 0.9 - ((i + j) * 0.1))
            
            loc_name = f'Grid_{i}_{j}'
            locations.append({
                'name': loc_name,
                'x': x, 'y': y,
                'type': 'town' if (i, j) != (0, 0) else 'conflict',
                'conflict': conflict,
                'movechance': 0.3 if (i, j) != (0, 0) else 1.0,
                'capacity': -1
            })
            
            # Connect to adjacent cells (creates grid structure)
            # Right neighbor
            if i < grid_size - 1:
                routes.append({
                    'from': loc_name,
                    'to': f'Grid_{i+1}_{j}',
                    'distance': cell_size
                })
            # Up neighbor
            if j < grid_size - 1:
                routes.append({
                    'from': loc_name,
                    'to': f'Grid_{i}_{j+1}',
                    'distance': cell_size
                })
            # Diagonal connections (creates shortcuts)
            if i < grid_size - 1 and j < grid_size - 1:
                routes.append({
                    'from': loc_name,
                    'to': f'Grid_{i+1}_{j+1}',
                    'distance': cell_size * np.sqrt(2)  # Diagonal distance
                })
    
    # Add safe zones at edges
    for i in [grid_size-1]:
        for j in [grid_size-1]:
            safe_name = f'SafeZone_{i}_{j}'
            locations.append({
                'name': safe_name,
                'x': i * cell_size, 'y': j * cell_size + cell_size,
                'type': 'camp',
                'conflict': 0.0,
                'movechance': 0.001,
                'capacity': 10000
            })
            routes.append({
                'from': f'Grid_{i}_{j}',
                'to': safe_name,
                'distance': cell_size
            })
    
    return locations, routes

