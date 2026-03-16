Topology Generator API
=====================

.. currentmodule:: flee_dual_process.topology_generator

The topology generator module creates standardized network structures for testing different spatial configurations of refugee movement.

Classes
-------

.. autoclass:: TopologyGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Base class for generating different network topologies for Flee experiments.
   
   This abstract class defines the interface for creating various network
   structures (linear, star, tree, grid) that can be used to test how
   network topology affects cognitive decision-making in refugee movements.

   **Example Usage:**
   
   .. code-block:: python
   
       from flee_dual_process.topology_generator import LinearTopologyGenerator
       
       # Initialize generator
       generator = LinearTopologyGenerator({'output_dir': 'topologies/linear'})
       
       # Generate linear topology
       locations_file, routes_file = generator.generate_linear(
           n_nodes=5,
           segment_distance=50.0,
           start_pop=10000,
           pop_decay=0.8
       )

.. autoclass:: LinearTopologyGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for linear chain topologies.
   
   Creates a chain of locations connected sequentially, with population decreasing
   along the chain according to the decay factor. This topology is useful for
   testing movement along corridors or escape routes.

   **Parameters:**
   
   - ``n_nodes`` (int): Number of nodes in the chain (minimum 2)
   - ``segment_distance`` (float): Distance between adjacent nodes in km
   - ``start_pop`` (int): Initial population at origin node
   - ``pop_decay`` (float): Population decay factor (0.0-1.0, where 1.0 = no decay)

   **Example:**
   
   .. code-block:: python
   
       generator = LinearTopologyGenerator({'output_dir': 'output'})
       
       # Create 6-node chain with 40km segments
       locations, routes = generator.generate_linear(
           n_nodes=6,
           segment_distance=40.0,
           start_pop=15000,
           pop_decay=0.7
       )

.. autoclass:: StarTopologyGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for star (hub-and-spoke) topologies.
   
   Creates a central hub location (conflict zone) connected to multiple camps
   arranged in a circle around it at the specified radius. This topology tests
   centralized vs distributed movement patterns.

   **Parameters:**
   
   - ``n_camps`` (int): Number of camps around the hub (minimum 1)
   - ``hub_pop`` (int): Population at central hub
   - ``camp_capacity`` (int): Capacity of each camp
   - ``radius`` (float): Distance from hub to camps in km

   **Example:**
   
   .. code-block:: python
   
       generator = StarTopologyGenerator({'output_dir': 'output'})
       
       # Create hub with 4 camps at 60km radius
       locations, routes = generator.generate_star(
           n_camps=4,
           hub_pop=20000,
           camp_capacity=5000,
           radius=60.0
       )

.. autoclass:: TreeTopologyGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for hierarchical tree topologies.
   
   Creates a tree structure with a root node (conflict zone) and hierarchical
   branching to intermediate towns and leaf camps. Population is distributed
   hierarchically from root to leaves.

   **Parameters:**
   
   - ``branching_factor`` (int): Number of children per node (minimum 2)
   - ``depth`` (int): Depth of the tree (minimum 1, root only)
   - ``root_pop`` (int): Population at root node

   **Example:**
   
   .. code-block:: python
   
       generator = TreeTopologyGenerator({'output_dir': 'output'})
       
       # Create binary tree with depth 3
       locations, routes = generator.generate_tree(
           branching_factor=2,
           depth=3,
           root_pop=25000
       )

.. autoclass:: GridTopologyGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for rectangular grid topologies.
   
   Creates a rectangular grid of locations connected to their neighbors,
   with various population distribution patterns. Useful for testing
   movement in urban or structured environments.

   **Parameters:**
   
   - ``rows`` (int): Number of rows in grid (minimum 1)
   - ``cols`` (int): Number of columns in grid (minimum 1)
   - ``cell_distance`` (float): Distance between adjacent cells in km
   - ``pop_distribution`` (str): Distribution pattern ('uniform', 'weighted', 'center_heavy', 'edge_heavy')

   **Example:**
   
   .. code-block:: python
   
       generator = GridTopologyGenerator({'output_dir': 'output'})
       
       # Create 3x4 grid with center-heavy population
       locations, routes = generator.generate_grid(
           rows=3,
           cols=4,
           cell_distance=25.0,
           pop_distribution='center_heavy'
       )

Methods
-------

.. automethod:: TopologyGenerator.generate_linear
.. automethod:: TopologyGenerator.generate_star
.. automethod:: TopologyGenerator.generate_tree
.. automethod:: TopologyGenerator.generate_grid
.. automethod:: TopologyGenerator.validate_topology
.. automethod:: TopologyGenerator.validate_topology_parameters

Output Format
-------------

All topology generators produce two CSV files in standard Flee format:

**locations.csv**
   Contains location information with columns:
   
   - ``name``: Location identifier
   - ``region``: Region name (default: 'region')
   - ``country``: Country name (default: 'country')
   - ``lat``: Latitude coordinate
   - ``lon``: Longitude coordinate
   - ``location_type``: Type ('town', 'camp', 'conflict_zone')
   - ``conflict_date``: Conflict start date (optional)
   - ``pop/cap``: Population or capacity value

**routes.csv**
   Contains route information with columns:
   
   - ``name1``: First location name
   - ``name2``: Second location name
   - ``distance``: Distance between locations in km
   - ``forced_redirection``: Redirection flag (0 or 1)

Validation
----------

All generated topologies are automatically validated for:

- **Connectivity**: No isolated nodes (except for star topology hub)
- **Consistency**: All route endpoints exist in locations
- **Parameters**: Valid ranges for all input parameters
- **Format**: Proper CSV format compatible with Flee

Error Handling
--------------

The topology generators provide comprehensive error handling:

.. code-block:: python

    try:
        locations, routes = generator.generate_linear(
            n_nodes=1,  # Invalid: minimum 2 nodes required
            segment_distance=50.0,
            start_pop=10000,
            pop_decay=0.8
        )
    except ValueError as e:
        print(f"Parameter validation failed: {e}")
    except RuntimeError as e:
        print(f"Topology generation failed: {e}")

Common validation errors include:

- Invalid parameter ranges (negative values, out of bounds)
- Insufficient nodes for topology type
- Invalid population distribution patterns
- File system errors during output generation

Best Practices
--------------

1. **Parameter Selection**: Choose parameters that create realistic movement scenarios
2. **Validation**: Always validate generated topologies before use
3. **Output Management**: Use descriptive output directories for different experiments
4. **Performance**: Large topologies (>100 nodes) may impact simulation performance
5. **Reproducibility**: Save topology parameters for experiment reproducibility