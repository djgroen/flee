"""
Topology Generator Module

Creates standardized network structures for testing different spatial 
configurations of refugee movement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any
import os
from .utils import CSVUtils, ValidationUtils


class TopologyGenerator(ABC):
    """
    Base class for generating different network topologies for Flee experiments.
    
    This abstract class defines the interface for creating various network
    structures (linear, star, tree, grid) that can be used to test how
    network topology affects cognitive decision-making in refugee movements.
    """
    
    def __init__(self, base_config: Dict[str, Any]):
        """
        Initialize the topology generator with base configuration.
        
        Args:
            base_config: Dictionary containing base configuration parameters
        """
        self.base_config = base_config
        self.csv_utils = CSVUtils()
        self.validation_utils = ValidationUtils()
    
    @abstractmethod
    def generate_linear(self, n_nodes: int, segment_distance: float, 
                       start_pop: int, pop_decay: float) -> Tuple[str, str]:
        """
        Generate a linear chain topology.
        
        Args:
            n_nodes: Number of nodes in the chain
            segment_distance: Distance between adjacent nodes
            start_pop: Initial population at origin
            pop_decay: Population decay factor along chain
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
        """
        pass
    
    @abstractmethod
    def generate_star(self, n_camps: int, hub_pop: int, 
                     camp_capacity: int, radius: float) -> Tuple[str, str]:
        """
        Generate a star (hub-and-spoke) topology.
        
        Args:
            n_camps: Number of camps around the hub
            hub_pop: Population at central hub
            camp_capacity: Capacity of each camp
            radius: Distance from hub to camps
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
        """
        pass
    
    @abstractmethod
    def generate_tree(self, branching_factor: int, depth: int, 
                     root_pop: int) -> Tuple[str, str]:
        """
        Generate a hierarchical tree topology.
        
        Args:
            branching_factor: Number of children per node
            depth: Depth of the tree
            root_pop: Population at root node
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
        """
        pass
    
    @abstractmethod
    def generate_grid(self, rows: int, cols: int, cell_distance: float, 
                     pop_distribution: str) -> Tuple[str, str]:
        """
        Generate a rectangular grid topology.
        
        Args:
            rows: Number of rows in grid
            cols: Number of columns in grid
            cell_distance: Distance between adjacent cells
            pop_distribution: Distribution pattern ('uniform', 'weighted')
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
        """
        pass
    
    def _write_locations_csv(self, locations: List[Dict[str, Any]], 
                           filepath: str) -> None:
        """
        Write locations data to CSV file in Flee format.
        
        Expected format:
        #name,region,country,lat,lon,location_type,conflict_date,pop/cap
        
        Args:
            locations: List of location dictionaries with keys:
                      - name: Location name
                      - region: Region name (optional, defaults to 'region')
                      - country: Country name (optional, defaults to 'country')
                      - lat: Latitude coordinate
                      - lon: Longitude coordinate
                      - location_type: Type ('town', 'camp', 'conflict_zone')
                      - conflict_date: Conflict start date (optional, defaults to '')
                      - pop/cap: Population or capacity value
            filepath: Output file path
        """
        # Validate locations before writing
        if not self._validate_locations_data(locations):
            raise ValueError("Invalid locations data provided")
        
        # Ensure all required fields are present with defaults
        processed_locations = []
        for loc in locations:
            processed_loc = {
                'name': loc['name'],
                'region': loc.get('region', 'region'),
                'country': loc.get('country', 'country'),
                'lat': loc['lat'],
                'lon': loc['lon'],
                'location_type': loc['location_type'],
                'conflict_date': loc.get('conflict_date', ''),
                'pop/cap': loc['pop/cap']
            }
            processed_locations.append(processed_loc)
        
        self.csv_utils.write_locations_csv(processed_locations, filepath)
    
    def _write_routes_csv(self, routes: List[Dict[str, Any]], 
                         filepath: str) -> None:
        """
        Write routes data to CSV file in Flee format.
        
        Expected format:
        #name1,name2,distance,forced_redirection
        
        Args:
            routes: List of route dictionaries with keys:
                   - name1: First location name
                   - name2: Second location name
                   - distance: Distance between locations
                   - forced_redirection: Redirection flag (optional, defaults to 0)
            filepath: Output file path
        """
        # Validate routes before writing
        if not self._validate_routes_data(routes):
            raise ValueError("Invalid routes data provided")
        
        # Ensure all required fields are present with defaults
        processed_routes = []
        for route in routes:
            processed_route = {
                'name1': route['name1'],
                'name2': route['name2'],
                'distance': route['distance'],
                'forced_redirection': route.get('forced_redirection', 0)
            }
            processed_routes.append(processed_route)
        
        self.csv_utils.write_routes_csv(processed_routes, filepath)
    
    def _validate_locations_data(self, locations: List[Dict[str, Any]]) -> bool:
        """
        Validate locations data before writing to CSV.
        
        Args:
            locations: List of location dictionaries
            
        Returns:
            True if data is valid, False otherwise
        """
        if not locations:
            return False
        
        required_fields = ['name', 'lat', 'lon', 'location_type', 'pop/cap']
        valid_location_types = ['town', 'camp', 'conflict_zone']
        
        location_names = set()
        
        for i, location in enumerate(locations):
            # Check required fields
            for field in required_fields:
                if field not in location:
                    print(f"Location {i}: Missing required field '{field}'")
                    return False
            
            # Check for duplicate names
            name = location['name']
            if name in location_names:
                print(f"Location {i}: Duplicate location name '{name}'")
                return False
            location_names.add(name)
            
            # Validate coordinates
            try:
                lat = float(location['lat'])
                lon = float(location['lon'])
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    print(f"Location '{name}': Invalid coordinates ({lat}, {lon})")
                    return False
            except (ValueError, TypeError):
                print(f"Location '{name}': Invalid coordinate format")
                return False
            
            # Validate location type
            if location['location_type'] not in valid_location_types:
                print(f"Location '{name}': Invalid location_type '{location['location_type']}'")
                return False
            
            # Validate population/capacity
            try:
                pop_cap = float(location['pop/cap'])
                if pop_cap < 0:
                    print(f"Location '{name}': Negative population/capacity")
                    return False
            except (ValueError, TypeError):
                print(f"Location '{name}': Invalid population/capacity format")
                return False
        
        return True
    
    def _validate_routes_data(self, routes: List[Dict[str, Any]]) -> bool:
        """
        Validate routes data before writing to CSV.
        
        Args:
            routes: List of route dictionaries
            
        Returns:
            True if data is valid, False otherwise
        """
        if not routes:
            return True  # Empty routes list is valid
        
        required_fields = ['name1', 'name2', 'distance']
        
        for i, route in enumerate(routes):
            # Check required fields
            for field in required_fields:
                if field not in route:
                    print(f"Route {i}: Missing required field '{field}'")
                    return False
            
            # Check for self-loops
            if route['name1'] == route['name2']:
                print(f"Route {i}: Self-loop detected ({route['name1']} -> {route['name2']})")
                return False
            
            # Validate distance
            try:
                distance = float(route['distance'])
                if distance <= 0:
                    print(f"Route {i}: Non-positive distance ({distance})")
                    return False
            except (ValueError, TypeError):
                print(f"Route {i}: Invalid distance format")
                return False
            
            # Validate forced_redirection if present
            if 'forced_redirection' in route:
                try:
                    redirection = int(route['forced_redirection'])
                    if redirection not in [0, 1]:
                        print(f"Route {i}: Invalid forced_redirection value ({redirection})")
                        return False
                except (ValueError, TypeError):
                    print(f"Route {i}: Invalid forced_redirection format")
                    return False
        
        return True
    
    def validate_topology(self, locations_file: str, routes_file: str) -> bool:
        """
        Validate generated topology for connectivity and consistency.
        
        Args:
            locations_file: Path to locations CSV file
            routes_file: Path to routes CSV file
            
        Returns:
            True if topology is valid, False otherwise
        """
        return self.validation_utils.validate_topology(locations_file, routes_file)
    
    def validate_topology_parameters(self, **kwargs) -> bool:
        """
        Validate topology generation parameters for consistency.
        
        Args:
            **kwargs: Topology-specific parameters
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Base validation - subclasses should override for specific validation
        for key, value in kwargs.items():
            if isinstance(value, (int, float)) and value < 0:
                print(f"Parameter '{key}': Negative value not allowed ({value})")
                return False
        
        return True


class LinearTopologyGenerator(TopologyGenerator):
    """Concrete implementation for linear chain topologies."""
    
    def generate_linear(self, n_nodes: int, segment_distance: float, 
                       start_pop: int, pop_decay: float) -> Tuple[str, str]:
        """
        Generate a linear chain topology with parameterizable nodes, distances, and population decay.
        
        Creates a chain of locations connected sequentially, with population decreasing
        along the chain according to the decay factor.
        
        Args:
            n_nodes: Number of nodes in the chain (minimum 2)
            segment_distance: Distance between adjacent nodes (km)
            start_pop: Initial population at origin node
            pop_decay: Population decay factor (0.0-1.0, where 1.0 = no decay)
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if not self.validate_topology_parameters(
            n_nodes=n_nodes, 
            segment_distance=segment_distance, 
            start_pop=start_pop, 
            pop_decay=pop_decay
        ):
            raise ValueError("Invalid parameters for linear topology generation")
        
        if n_nodes < 2:
            raise ValueError("Linear topology requires at least 2 nodes")
        
        if not (0.0 <= pop_decay <= 1.0):
            raise ValueError("Population decay factor must be between 0.0 and 1.0")
        
        # Generate locations
        locations = []
        routes = []
        
        for i in range(n_nodes):
            # Calculate population for this node
            if i == 0:
                # Origin node (conflict zone)
                population = start_pop
                location_type = 'conflict_zone'
                name = 'Origin'
            elif i == n_nodes - 1:
                # Last node is typically a camp
                population = int(start_pop * (pop_decay ** i) * 5)  # Camps have higher capacity
                location_type = 'camp'
                name = f'Camp_{i}'
            else:
                # Intermediate nodes are towns
                population = int(start_pop * (pop_decay ** i))
                location_type = 'town'
                name = f'Town_{i}'
            
            # Position nodes along a line (for simplicity, along x-axis)
            lat = 0.0
            lon = i * segment_distance / 111.0  # Rough conversion to degrees
            
            location = {
                'name': name,
                'lat': lat,
                'lon': lon,
                'location_type': location_type,
                'pop/cap': population
            }
            locations.append(location)
            
            # Create route to next node
            if i < n_nodes - 1:
                route = {
                    'name1': name,
                    'name2': f'Town_{i+1}' if i+1 < n_nodes-1 else f'Camp_{i+1}',
                    'distance': segment_distance
                }
                routes.append(route)
        
        # Generate output file paths
        output_dir = self.base_config.get('output_dir', 'flee_dual_process/topologies/linear')
        os.makedirs(output_dir, exist_ok=True)
        
        locations_file = os.path.join(output_dir, 'locations.csv')
        routes_file = os.path.join(output_dir, 'routes.csv')
        
        # Write CSV files
        self._write_locations_csv(locations, locations_file)
        self._write_routes_csv(routes, routes_file)
        
        # Validate generated topology
        if not self.validate_topology(locations_file, routes_file):
            raise RuntimeError("Generated topology failed validation")
        
        return (locations_file, routes_file)
    
    def generate_star(self, n_camps: int, hub_pop: int, 
                     camp_capacity: int, radius: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for LinearTopologyGenerator")
    
    def generate_tree(self, branching_factor: int, depth: int, 
                     root_pop: int) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for LinearTopologyGenerator")
    
    def generate_grid(self, rows: int, cols: int, cell_distance: float, 
                     pop_distribution: str) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for LinearTopologyGenerator")


class StarTopologyGenerator(TopologyGenerator):
    """Concrete implementation for star (hub-and-spoke) topologies."""
    
    def generate_linear(self, n_nodes: int, segment_distance: float, 
                       start_pop: int, pop_decay: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for StarTopologyGenerator")
    
    def generate_star(self, n_camps: int, hub_pop: int, 
                     camp_capacity: int, radius: float) -> Tuple[str, str]:
        """
        Generate a star (hub-and-spoke) topology with central hub connected to multiple camps.
        
        Creates a central hub location (conflict zone) connected to multiple camps
        arranged in a circle around it at the specified radius.
        
        Args:
            n_camps: Number of camps around the hub (minimum 1)
            hub_pop: Population at central hub
            camp_capacity: Capacity of each camp
            radius: Distance from hub to camps (km)
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
            
        Raises:
            ValueError: If parameters are invalid
        """
        import math
        
        # Validate parameters
        if not self.validate_topology_parameters(
            n_camps=n_camps,
            hub_pop=hub_pop,
            camp_capacity=camp_capacity,
            radius=radius
        ):
            raise ValueError("Invalid parameters for star topology generation")
        
        if n_camps < 1:
            raise ValueError("Star topology requires at least 1 camp")
        
        # Generate locations
        locations = []
        routes = []
        
        # Create central hub (conflict zone)
        hub_location = {
            'name': 'Hub',
            'lat': 0.0,
            'lon': 0.0,
            'location_type': 'conflict_zone',
            'pop/cap': hub_pop
        }
        locations.append(hub_location)
        
        # Create camps around the hub in a circle
        for i in range(n_camps):
            # Calculate position on circle
            angle = 2 * math.pi * i / n_camps
            
            # Convert radius from km to approximate degrees
            # (rough conversion: 1 degree ≈ 111 km)
            radius_deg = radius / 111.0
            
            lat = radius_deg * math.sin(angle)
            lon = radius_deg * math.cos(angle)
            
            camp_location = {
                'name': f'Camp_{i+1}',
                'lat': lat,
                'lon': lon,
                'location_type': 'camp',
                'pop/cap': camp_capacity
            }
            locations.append(camp_location)
            
            # Create route from hub to camp
            route = {
                'name1': 'Hub',
                'name2': f'Camp_{i+1}',
                'distance': radius
            }
            routes.append(route)
        
        # Generate output file paths
        output_dir = self.base_config.get('output_dir', 'flee_dual_process/topologies/star')
        os.makedirs(output_dir, exist_ok=True)
        
        locations_file = os.path.join(output_dir, 'locations.csv')
        routes_file = os.path.join(output_dir, 'routes.csv')
        
        # Write CSV files
        self._write_locations_csv(locations, locations_file)
        self._write_routes_csv(routes, routes_file)
        
        # Validate generated topology
        if not self.validate_topology(locations_file, routes_file):
            raise RuntimeError("Generated topology failed validation")
        
        return (locations_file, routes_file)
    
    def generate_tree(self, branching_factor: int, depth: int, 
                     root_pop: int) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for StarTopologyGenerator")
    
    def generate_grid(self, rows: int, cols: int, cell_distance: float, 
                     pop_distribution: str) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for StarTopologyGenerator")


class TreeTopologyGenerator(TopologyGenerator):
    """Concrete implementation for hierarchical tree topologies."""
    
    def generate_linear(self, n_nodes: int, segment_distance: float, 
                       start_pop: int, pop_decay: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for TreeTopologyGenerator")
    
    def generate_star(self, n_camps: int, hub_pop: int, 
                     camp_capacity: int, radius: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for TreeTopologyGenerator")
    
    def generate_tree(self, branching_factor: int, depth: int, 
                     root_pop: int) -> Tuple[str, str]:
        """
        Generate a hierarchical tree topology with configurable branching factor and depth.
        
        Creates a tree structure with a root node (conflict zone) and hierarchical
        branching to intermediate towns and leaf camps. Population is distributed
        hierarchically from root to leaves.
        
        Args:
            branching_factor: Number of children per node (minimum 2)
            depth: Depth of the tree (minimum 1, root only)
            root_pop: Population at root node
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
            
        Raises:
            ValueError: If parameters are invalid
        """
        import math
        
        # Validate parameters
        if not self.validate_topology_parameters(
            branching_factor=branching_factor,
            depth=depth,
            root_pop=root_pop
        ):
            raise ValueError("Invalid parameters for tree topology generation")
        
        if branching_factor < 2:
            raise ValueError("Tree topology requires branching factor >= 2")
        
        if depth < 1:
            raise ValueError("Tree topology requires depth >= 1")
        
        # Generate tree structure
        locations = []
        routes = []
        
        # Create nodes level by level
        nodes_by_level = {}  # level -> list of node info
        
        # Level 0: Root node (conflict zone)
        root_node = {
            'name': 'Root',
            'level': 0,
            'parent': None,
            'children': [],
            'lat': 0.0,
            'lon': 0.0,
            'location_type': 'conflict_zone',
            'pop/cap': root_pop
        }
        nodes_by_level[0] = [root_node]
        
        # Generate subsequent levels
        for level in range(1, depth + 1):
            nodes_by_level[level] = []
            
            # For each node in previous level, create children
            for parent_node in nodes_by_level[level - 1]:
                for child_idx in range(branching_factor):
                    # Calculate position for child node
                    # Arrange children in a fan pattern around parent
                    if branching_factor == 1:
                        angle = 0
                    else:
                        angle = (2 * math.pi * child_idx / branching_factor) + (level * math.pi / 4)
                    
                    # Distance from parent increases with level
                    distance = 50.0 * level  # Base distance per level
                    
                    # Convert to approximate coordinates
                    distance_deg = distance / 111.0
                    child_lat = parent_node['lat'] + distance_deg * math.sin(angle)
                    child_lon = parent_node['lon'] + distance_deg * math.cos(angle)
                    
                    # Determine node type and population
                    if level == depth:
                        # Leaf nodes are camps with higher capacity
                        location_type = 'camp'
                        population = int(root_pop * 0.5 * (0.8 ** level) * 3)  # Camps have higher capacity
                        node_name = f'Camp_{level}_{len(nodes_by_level[level]) + 1}'
                    else:
                        # Intermediate nodes are towns
                        location_type = 'town'
                        population = int(root_pop * (0.8 ** level))
                        node_name = f'Town_{level}_{len(nodes_by_level[level]) + 1}'
                    
                    child_node = {
                        'name': node_name,
                        'level': level,
                        'parent': parent_node['name'],
                        'children': [],
                        'lat': child_lat,
                        'lon': child_lon,
                        'location_type': location_type,
                        'pop/cap': population
                    }
                    
                    nodes_by_level[level].append(child_node)
                    parent_node['children'].append(child_node['name'])
                    
                    # Create route from parent to child
                    route = {
                        'name1': parent_node['name'],
                        'name2': child_node['name'],
                        'distance': distance
                    }
                    routes.append(route)
        
        # Convert nodes to locations format
        for level_nodes in nodes_by_level.values():
            for node in level_nodes:
                location = {
                    'name': node['name'],
                    'lat': node['lat'],
                    'lon': node['lon'],
                    'location_type': node['location_type'],
                    'pop/cap': node['pop/cap']
                }
                locations.append(location)
        
        # Generate output file paths
        output_dir = self.base_config.get('output_dir', 'flee_dual_process/topologies/tree')
        os.makedirs(output_dir, exist_ok=True)
        
        locations_file = os.path.join(output_dir, 'locations.csv')
        routes_file = os.path.join(output_dir, 'routes.csv')
        
        # Write CSV files
        self._write_locations_csv(locations, locations_file)
        self._write_routes_csv(routes, routes_file)
        
        # Validate generated topology
        if not self.validate_topology(locations_file, routes_file):
            raise RuntimeError("Generated topology failed validation")
        
        return (locations_file, routes_file)
    
    def generate_grid(self, rows: int, cols: int, cell_distance: float, 
                     pop_distribution: str) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for TreeTopologyGenerator")


class GridTopologyGenerator(TopologyGenerator):
    """Concrete implementation for rectangular grid topologies."""
    
    def generate_linear(self, n_nodes: int, segment_distance: float, 
                       start_pop: int, pop_decay: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for GridTopologyGenerator")
    
    def generate_star(self, n_camps: int, hub_pop: int, 
                     camp_capacity: int, radius: float) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for GridTopologyGenerator")
    
    def generate_tree(self, branching_factor: int, depth: int, 
                     root_pop: int) -> Tuple[str, str]:
        raise NotImplementedError("Not applicable for GridTopologyGenerator")
    
    def generate_grid(self, rows: int, cols: int, cell_distance: float, 
                     pop_distribution: str) -> Tuple[str, str]:
        """
        Generate a rectangular grid topology with configurable dimensions and population distribution.
        
        Creates a rectangular grid of locations connected to their neighbors,
        with various population distribution patterns.
        
        Args:
            rows: Number of rows in grid (minimum 1)
            cols: Number of columns in grid (minimum 1)
            cell_distance: Distance between adjacent cells (km)
            pop_distribution: Distribution pattern ('uniform', 'weighted', 'center_heavy', 'edge_heavy')
            
        Returns:
            Tuple of (locations_file_path, routes_file_path)
            
        Raises:
            ValueError: If parameters are invalid
        """
        import random
        
        # Validate parameters
        if not self.validate_topology_parameters(
            rows=rows,
            cols=cols,
            cell_distance=cell_distance
        ):
            raise ValueError("Invalid parameters for grid topology generation")
        
        if rows < 1 or cols < 1:
            raise ValueError("Grid topology requires rows >= 1 and cols >= 1")
        
        valid_distributions = ['uniform', 'weighted', 'center_heavy', 'edge_heavy']
        if pop_distribution not in valid_distributions:
            raise ValueError(f"Invalid population distribution. Must be one of: {valid_distributions}")
        
        # Generate grid locations
        locations = []
        routes = []
        
        # Base population for calculations
        base_population = 1000
        
        # Calculate center coordinates for distribution patterns
        center_row = (rows - 1) / 2
        center_col = (cols - 1) / 2
        
        # Create locations
        for row in range(rows):
            for col in range(cols):
                # Generate location name
                location_name = f'Grid_{row}_{col}'
                
                # Calculate coordinates
                lat = row * cell_distance / 111.0  # Convert km to approximate degrees
                lon = col * cell_distance / 111.0
                
                # Determine location type and population based on position and distribution
                if row == 0 and col == 0:
                    # Origin is conflict zone
                    location_type = 'conflict_zone'
                    population = base_population * 2
                elif (row == rows - 1 or col == cols - 1 or row == 0 or col == 0) and rows > 2 and cols > 2:
                    # Edge locations are camps (if grid is large enough)
                    location_type = 'camp'
                    population = self._calculate_grid_population(
                        row, col, rows, cols, base_population, pop_distribution, center_row, center_col
                    ) * 3  # Camps have higher capacity
                else:
                    # Interior locations are towns
                    location_type = 'town'
                    population = self._calculate_grid_population(
                        row, col, rows, cols, base_population, pop_distribution, center_row, center_col
                    )
                
                location = {
                    'name': location_name,
                    'lat': lat,
                    'lon': lon,
                    'location_type': location_type,
                    'pop/cap': int(population)
                }
                locations.append(location)
                
                # Create routes to neighbors
                # Right neighbor
                if col < cols - 1:
                    neighbor_name = f'Grid_{row}_{col + 1}'
                    route = {
                        'name1': location_name,
                        'name2': neighbor_name,
                        'distance': cell_distance
                    }
                    routes.append(route)
                
                # Bottom neighbor
                if row < rows - 1:
                    neighbor_name = f'Grid_{row + 1}_{col}'
                    route = {
                        'name1': location_name,
                        'name2': neighbor_name,
                        'distance': cell_distance
                    }
                    routes.append(route)
        
        # Generate output file paths
        output_dir = self.base_config.get('output_dir', 'flee_dual_process/topologies/grid')
        os.makedirs(output_dir, exist_ok=True)
        
        locations_file = os.path.join(output_dir, 'locations.csv')
        routes_file = os.path.join(output_dir, 'routes.csv')
        
        # Write CSV files
        self._write_locations_csv(locations, locations_file)
        self._write_routes_csv(routes, routes_file)
        
        # Validate generated topology
        if not self.validate_topology(locations_file, routes_file):
            raise RuntimeError("Generated topology failed validation")
        
        return (locations_file, routes_file)
    
    def _calculate_grid_population(self, row: int, col: int, rows: int, cols: int, 
                                 base_pop: int, distribution: str, 
                                 center_row: float, center_col: float) -> float:
        """
        Calculate population for a grid cell based on distribution pattern.
        
        Args:
            row: Row index
            col: Column index
            rows: Total rows
            cols: Total columns
            base_pop: Base population value
            distribution: Distribution pattern
            center_row: Center row coordinate
            center_col: Center column coordinate
            
        Returns:
            Population value for the cell
        """
        import math
        
        if distribution == 'uniform':
            return base_pop
        
        elif distribution == 'weighted':
            # Random variation around base population
            import random
            random.seed(row * cols + col)  # Deterministic randomness
            return base_pop * (0.5 + random.random())
        
        elif distribution == 'center_heavy':
            # Higher population near center
            distance_from_center = math.sqrt((row - center_row)**2 + (col - center_col)**2)
            max_distance = math.sqrt(center_row**2 + center_col**2)
            
            if max_distance == 0:
                weight = 1.0
            else:
                weight = 1.0 - (distance_from_center / max_distance) * 0.7
            
            return base_pop * weight
        
        elif distribution == 'edge_heavy':
            # Higher population near edges
            distance_from_center = math.sqrt((row - center_row)**2 + (col - center_col)**2)
            max_distance = math.sqrt(center_row**2 + center_col**2)
            
            if max_distance == 0:
                weight = 1.0
            else:
                weight = 0.3 + (distance_from_center / max_distance) * 0.7
            
            return base_pop * weight
        
        else:
            return base_pop