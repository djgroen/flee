Scenario Generator API
=====================

.. currentmodule:: flee_dual_process.scenario_generator

The scenario generator module creates conflict patterns that trigger different cognitive responses in agents.

Classes
-------

.. autoclass:: ConflictScenarioGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Base class for generating different conflict scenarios for Flee experiments.
   
   This abstract class defines the interface for creating various conflict
   patterns (spike, gradual, cascading, oscillating) that can be used to test
   how different conflict dynamics trigger cognitive responses in refugee movements.

   **Example Usage:**
   
   .. code-block:: python
   
       from flee_dual_process.scenario_generator import SpikeConflictGenerator
       
       # Initialize generator with topology
       generator = SpikeConflictGenerator('topologies/locations.csv')
       
       # Generate spike conflict scenario
       conflicts_file = generator.generate_spike_conflict(
           origin='Origin',
           start_day=0,
           peak_intensity=0.9
       )

.. autoclass:: SpikeConflictGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for spike conflict scenarios.
   
   Creates conflicts that start at maximum intensity immediately and maintain
   that level, representing sudden onset conflicts like coups or terrorist
   attacks that trigger immediate System 1 responses.

   **Parameters:**
   
   - ``origin`` (str): Name of the origin location where conflict starts
   - ``start_day`` (int): Day when conflict begins (0-based)
   - ``peak_intensity`` (float): Maximum conflict intensity (0.0 to 1.0)
   - ``output_dir`` (str, optional): Directory to save conflicts.csv

   **Example:**
   
   .. code-block:: python
   
       generator = SpikeConflictGenerator('locations.csv')
       
       # Create sudden high-intensity conflict
       conflicts_file = generator.generate_spike_conflict(
           origin='Capital_City',
           start_day=5,
           peak_intensity=0.95,
           output_dir='scenarios/spike'
       )

.. autoclass:: GradualConflictGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for gradual conflict scenarios.
   
   Creates conflicts that start at low intensity and gradually increase to
   maximum intensity, representing escalating tensions that allow for System 2
   planning and deliberate decision-making.

   **Parameters:**
   
   - ``origin`` (str): Name of the origin location where conflict starts
   - ``start_day`` (int): Day when conflict begins (0-based)
   - ``end_day`` (int): Day when conflict reaches maximum intensity
   - ``max_intensity`` (float): Maximum conflict intensity (0.0 to 1.0)
   - ``output_dir`` (str, optional): Directory to save conflicts.csv

   **Example:**
   
   .. code-block:: python
   
       generator = GradualConflictGenerator('locations.csv')
       
       # Create gradually escalating conflict over 30 days
       conflicts_file = generator.generate_gradual_conflict(
           origin='Border_Town',
           start_day=0,
           end_day=30,
           max_intensity=0.8,
           output_dir='scenarios/gradual'
       )

.. autoclass:: CascadingConflictGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for cascading conflict scenarios.
   
   Creates conflicts that start at the origin and spread to connected locations
   based on network topology and spread rate. This tests how social connectivity
   and network effects influence cognitive responses.

   **Parameters:**
   
   - ``origin`` (str): Name of the origin location where conflict starts
   - ``start_day`` (int): Day when conflict begins (0-based)
   - ``spread_rate`` (float): Rate of conflict spread (locations per day)
   - ``max_intensity`` (float): Maximum conflict intensity (0.0 to 1.0)
   - ``routes_file`` (str, optional): Path to routes CSV file
   - ``output_dir`` (str, optional): Directory to save conflicts.csv

   **Example:**
   
   .. code-block:: python
   
       generator = CascadingConflictGenerator('locations.csv')
       
       # Create conflict that spreads through network
       conflicts_file = generator.generate_cascading_conflict(
           origin='Central_Hub',
           start_day=10,
           spread_rate=0.5,  # Spread to 1 new location every 2 days
           max_intensity=0.7,
           routes_file='routes.csv',
           output_dir='scenarios/cascading'
       )

.. autoclass:: OscillatingConflictGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Concrete implementation for oscillating conflict scenarios.
   
   Creates conflicts with cyclical intensity variations, representing conflicts
   that ebb and flow over time. This tests adaptation patterns and long-term
   cognitive responses to changing threat levels.

   **Parameters:**
   
   - ``origin`` (str): Name of the origin location where conflict starts
   - ``start_day`` (int): Day when conflict begins (0-based)
   - ``period`` (int): Period of oscillation in days
   - ``amplitude`` (float): Amplitude of oscillation (0.0 to 1.0)
   - ``output_dir`` (str, optional): Directory to save conflicts.csv

   **Example:**
   
   .. code-block:: python
   
       generator = OscillatingConflictGenerator('locations.csv')
       
       # Create conflict with 14-day cycles
       conflicts_file = generator.generate_oscillating_conflict(
           origin='Disputed_Region',
           start_day=0,
           period=14,
           amplitude=0.6,
           output_dir='scenarios/oscillating'
       )

Methods
-------

.. automethod:: ConflictScenarioGenerator.generate_spike_conflict
.. automethod:: ConflictScenarioGenerator.generate_gradual_conflict
.. automethod:: ConflictScenarioGenerator.generate_cascading_conflict
.. automethod:: ConflictScenarioGenerator.generate_oscillating_conflict
.. automethod:: ConflictScenarioGenerator.validate_scenario

Output Format
-------------

All scenario generators produce a ``conflicts.csv`` file in Flee matrix format:

**conflicts.csv**
   Matrix format with columns:
   
   - ``#Day``: Day number (0-based)
   - ``Location1``, ``Location2``, ...: Conflict intensity (0.0-1.0) for each location
   
   Example:
   
   .. code-block:: csv
   
       #Day,Origin,Town_1,Town_2,Camp_1
       0,0.9,0.0,0.0,0.0
       1,0.9,0.0,0.0,0.0
       2,0.9,0.2,0.0,0.0
       3,0.9,0.4,0.1,0.0

Validation
----------

All generated scenarios are automatically validated for:

- **Temporal Consistency**: No negative days, reasonable day progression
- **Location Consistency**: All conflict locations exist in topology
- **Intensity Ranges**: Conflict intensities between 0.0 and 1.0
- **Scenario Logic**: Patterns match expected scenario type behavior

Scenario Types in Detail
------------------------

**Spike Conflicts**
   - Immediate onset at maximum intensity
   - Maintains peak level for duration
   - Tests System 1 rapid response mechanisms
   - Typical duration: 30 days
   - Use cases: Coups, terrorist attacks, sudden violence

**Gradual Conflicts**
   - Linear escalation from minimum to maximum intensity
   - Allows time for System 2 planning and preparation
   - Peak intensity maintained after escalation
   - Use cases: Political tensions, resource conflicts, border disputes

**Cascading Conflicts**
   - Spreads through network based on connectivity
   - Intensity decays with distance from origin
   - Tests social connectivity effects on decision-making
   - Spread rate controls propagation speed
   - Use cases: Regional instability, ethnic conflicts, resource wars

**Oscillating Conflicts**
   - Cyclical intensity variations over time
   - Tests adaptation to changing threat levels
   - Configurable period and amplitude
   - Use cases: Seasonal conflicts, cyclical violence, unstable ceasefires

Error Handling
--------------

Comprehensive error handling for common issues:

.. code-block:: python

    try:
        conflicts_file = generator.generate_spike_conflict(
            origin='NonexistentLocation',  # Invalid location
            start_day=0,
            peak_intensity=1.5  # Invalid intensity > 1.0
        )
    except FileNotFoundError as e:
        print(f"Location not found: {e}")
    except ValueError as e:
        print(f"Parameter validation failed: {e}")
    except RuntimeError as e:
        print(f"Scenario generation failed: {e}")

Common validation errors include:

- Origin location not found in topology
- Invalid parameter ranges (negative days, intensity > 1.0)
- Inconsistent temporal parameters (end_day <= start_day)
- Missing or invalid routes file for cascading scenarios
- File system errors during output generation

Advanced Usage
--------------

**Custom Conflict Patterns**

You can create custom conflict patterns by extending the base class:

.. code-block:: python

    class CustomConflictGenerator(ConflictScenarioGenerator):
        def generate_custom_pattern(self, origin, start_day, **params):
            conflicts = {}
            # Implement custom logic here
            output_file = 'custom_conflicts.csv'
            self._write_conflicts_csv(conflicts, output_file)
            return output_file

**Scenario Validation**

Validate scenarios against simulation periods:

.. code-block:: python

    # Validate scenario fits within simulation period
    is_valid = generator.validate_scenario(
        conflicts_file='conflicts.csv',
        sim_period=(0, 100)  # 100-day simulation
    )

**Network-Based Scenarios**

For cascading scenarios, the network topology affects spread patterns:

.. code-block:: python

    # Dense networks spread faster
    # Sparse networks create isolated conflict zones
    # Hub-and-spoke networks concentrate conflicts at hubs

Best Practices
--------------

1. **Scenario Selection**: Choose scenarios that match research questions
2. **Parameter Tuning**: Test different intensities and timings
3. **Validation**: Always validate scenarios before experiments
4. **Documentation**: Record scenario parameters for reproducibility
5. **Realism**: Base parameters on real-world conflict patterns
6. **Testing**: Verify scenarios produce expected agent behaviors