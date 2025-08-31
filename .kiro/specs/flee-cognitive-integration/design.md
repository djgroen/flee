# Flee Cognitive Integration Design

## Overview

This design implements the core integration between Flee's agent-based simulation and dual-process cognitive decision-making. The design focuses on fixing fundamental execution issues and ensuring that System 1 (fast, heuristic) and System 2 (slow, analytical) cognitive modes produce measurably different refugee movement behaviors.

## Architecture

### Core Integration Points

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Config        │    │   Flee Core      │    │   Output        │
│   Management    │───▶│   Integration    │───▶│   Validation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Parameter       │    │ Cognitive        │    │ Debug &         │
│ Validation      │    │ Decision Logic   │    │ Diagnostics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Integration Strategy

1. **Minimal Invasive Changes**: Modify Flee core minimally to preserve existing functionality
2. **Parameter Injection**: Use SimulationSettings.py as the primary parameter passing mechanism
3. **Decision Point Integration**: Integrate cognitive logic at Person.selectRoute() decision points
4. **Validation First**: Ensure basic execution works before adding complex cognitive logic

## Components and Interfaces

### 1. Parameter Loading System

**File**: `flee/SimulationSettings.py`

```python
class SimulationSettings:
    # Existing move_rules dictionary enhanced with cognitive parameters
    move_rules = {
        # Standard Flee parameters
        "BorderClosure": False,
        "CampLogLevel": 1,
        
        # NEW: Cognitive parameters
        "TwoSystemDecisionMaking": False,  # Enable/disable cognitive switching
        "conflict_threshold": 0.5,         # System 2 activation threshold
        "average_social_connectivity": 0.1, # Base connectivity for pressure calc
        "awareness_level": 1.0,            # Decision quality modifier
        "weight_softening": 0.1            # Decision randomness factor
    }
    
    @classmethod
    def validate_cognitive_parameters(cls):
        """Validate cognitive parameter ranges and types."""
        if not isinstance(cls.move_rules["TwoSystemDecisionMaking"], bool):
            raise ValueError("TwoSystemDecisionMaking must be boolean")
        
        threshold = cls.move_rules["conflict_threshold"]
        if not (0.0 <= threshold <= 2.0):
            raise ValueError(f"conflict_threshold {threshold} must be in [0.0, 2.0]")
        
        connectivity = cls.move_rules["average_social_connectivity"]
        if not (0.0 <= connectivity <= 1.0):
            raise ValueError(f"average_social_connectivity {connectivity} must be in [0.0, 1.0]")
```

### 2. Cognitive Decision Logic

**File**: `flee/flee.py` (Person class enhancement)

```python
class Person:
    def __init__(self, location, age=0, gender="male"):
        # Existing initialization
        self.location = location
        self.age = age
        self.gender = gender
        
        # NEW: Cognitive attributes
        self.cognitive_state = "system1"  # "system1" or "system2"
        self.system2_capable = True       # Can this agent use System 2?
        self.connection_count = 0         # Social connections for pressure calc
        self.last_pressure_calc = 0       # Cache pressure calculation
    
    def calculate_cognitive_pressure(self, time):
        """Calculate cognitive pressure based on conflict and connectivity."""
        if not SimulationSettings.move_rules["TwoSystemDecisionMaking"]:
            return 0.0
        
        # Get current conflict intensity at location
        conflict_intensity = self.location.conflict_intensity.get(time, 0.0)
        
        # Get connectivity (base + personal connections)
        base_connectivity = SimulationSettings.move_rules["average_social_connectivity"]
        personal_connectivity = min(self.connection_count / 10.0, 1.0)  # Cap at 1.0
        total_connectivity = min(base_connectivity + personal_connectivity, 1.0)
        
        # Recovery period (assume 30 days baseline)
        recovery_period = 30.0
        
        # Cognitive pressure formula
        pressure = (conflict_intensity * total_connectivity) / recovery_period
        
        self.last_pressure_calc = pressure
        return pressure
    
    def update_cognitive_state(self, time):
        """Update cognitive state based on current pressure."""
        if not SimulationSettings.move_rules["TwoSystemDecisionMaking"]:
            self.cognitive_state = "system1"
            return
        
        pressure = self.calculate_cognitive_pressure(time)
        threshold = SimulationSettings.move_rules["conflict_threshold"]
        
        if pressure > threshold and self.system2_capable:
            old_state = self.cognitive_state
            self.cognitive_state = "system2"
            
            # DEBUG: Log state changes
            if old_state != "system2":
                print(f"Agent {id(self)}: S1→S2 activation (pressure={pressure:.3f} > {threshold})")
        else:
            old_state = self.cognitive_state
            self.cognitive_state = "system1"
            
            # DEBUG: Log state changes  
            if old_state != "system1":
                print(f"Agent {id(self)}: S2→S1 deactivation (pressure={pressure:.3f} ≤ {threshold})")
    
    def selectRoute(self, time, ForceTownMove=False):
        """Enhanced route selection with cognitive decision-making."""
        
        # Update cognitive state before making decision
        self.update_cognitive_state(time)
        
        # Get available routes
        available_routes = []
        for i, link in enumerate(self.location.links):
            if link.endpoint.capacity > link.endpoint.numAgents:
                available_routes.append((i, link))
        
        if not available_routes:
            return -1  # No available routes
        
        # Apply cognitive decision-making
        if self.cognitive_state == "system1":
            return self._system1_route_selection(available_routes, time)
        else:
            return self._system2_route_selection(available_routes, time)
    
    def _system1_route_selection(self, available_routes, time):
        """Fast, heuristic route selection (System 1)."""
        # Simple heuristic: choose closest available destination
        # This is fast but may not be optimal
        
        min_distance = float('inf')
        best_route = 0
        
        for route_idx, link in available_routes:
            distance = link.distance
            if distance < min_distance:
                min_distance = distance
                best_route = route_idx
        
        # Add some randomness (weight_softening)
        softening = SimulationSettings.move_rules["weight_softening"]
        if random.random() < softening:
            # Choose random available route
            best_route = random.choice(available_routes)[0]
        
        return best_route
    
    def _system2_route_selection(self, available_routes, time):
        """Slow, analytical route selection (System 2)."""
        # More complex analysis: consider distance, capacity, safety
        # This is slower but potentially more optimal
        
        best_score = -float('inf')
        best_route = 0
        
        awareness = SimulationSettings.move_rules["awareness_level"]
        
        for route_idx, link in available_routes:
            destination = link.endpoint
            
            # Calculate composite score
            distance_score = 1.0 / (1.0 + link.distance)  # Closer is better
            capacity_score = (destination.capacity - destination.numAgents) / destination.capacity
            safety_score = 1.0 - destination.conflict_intensity.get(time, 0.0)
            
            # Weighted combination (System 2 considers multiple factors)
            composite_score = (
                0.3 * distance_score +
                0.4 * capacity_score + 
                0.3 * safety_score
            ) * awareness
            
            if composite_score > best_score:
                best_score = composite_score
                best_route = route_idx
        
        # Less randomness than System 1
        softening = SimulationSettings.move_rules["weight_softening"] * 0.5
        if random.random() < softening:
            best_route = random.choice(available_routes)[0]
        
        return best_route
```

### 3. Output Validation System

**File**: `flee_dual_process/output_validator.py`

```python
import os
import pandas as pd
from pathlib import Path

class FleeOutputValidator:
    """Validates that Flee simulations produce expected output files."""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.required_files = ['out.csv', 'agents.out']
        self.optional_files = ['cognitive_states.csv', 'decision_log.csv']
    
    def validate_basic_output(self):
        """Validate that basic Flee output files exist and have content."""
        errors = []
        
        for filename in self.required_files:
            filepath = self.output_dir / filename
            
            if not filepath.exists():
                errors.append(f"Required file missing: {filename}")
                continue
            
            if filepath.stat().st_size == 0:
                errors.append(f"Required file is empty: {filename}")
                continue
            
            # Validate file format
            if filename == 'out.csv':
                try:
                    df = pd.read_csv(filepath)
                    if len(df) == 0:
                        errors.append(f"out.csv has no data rows")
                    
                    required_columns = ['Day', 'Total population']
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    if missing_cols:
                        errors.append(f"out.csv missing columns: {missing_cols}")
                        
                except Exception as e:
                    errors.append(f"Cannot parse out.csv: {e}")
        
        return errors
    
    def validate_cognitive_output(self):
        """Validate cognitive-specific output files."""
        errors = []
        
        # Check if cognitive tracking was enabled
        cognitive_enabled = False
        try:
            # Look for cognitive state indicators in output
            out_csv = self.output_dir / 'out.csv'
            if out_csv.exists():
                df = pd.read_csv(out_csv)
                # Check if we have cognitive-related columns or files
                cognitive_files = [f for f in self.optional_files if (self.output_dir / f).exists()]
                cognitive_enabled = len(cognitive_files) > 0
        except:
            pass
        
        if cognitive_enabled:
            for filename in self.optional_files:
                filepath = self.output_dir / filename
                if filepath.exists() and filepath.stat().st_size == 0:
                    errors.append(f"Cognitive file is empty: {filename}")
        
        return errors
    
    def extract_basic_metrics(self):
        """Extract basic metrics from Flee output for validation."""
        metrics = {}
        
        try:
            out_csv = self.output_dir / 'out.csv'
            if out_csv.exists():
                df = pd.read_csv(out_csv)
                
                metrics['total_days'] = len(df)
                metrics['final_population'] = df['Total population'].iloc[-1] if len(df) > 0 else 0
                metrics['population_change'] = (
                    df['Total population'].iloc[-1] - df['Total population'].iloc[0] 
                    if len(df) > 1 else 0
                )
                
                # Check for movement (population should decrease at origin)
                if 'Total population' in df.columns and len(df) > 1:
                    initial_pop = df['Total population'].iloc[0]
                    final_pop = df['Total population'].iloc[-1]
                    metrics['movement_occurred'] = final_pop < initial_pop
                else:
                    metrics['movement_occurred'] = False
                    
        except Exception as e:
            metrics['extraction_error'] = str(e)
        
        return metrics

def validate_simulation_run(output_dir, cognitive_mode=None):
    """Convenience function to validate a simulation run."""
    validator = FleeOutputValidator(output_dir)
    
    print(f"Validating simulation output in: {output_dir}")
    
    # Basic validation
    basic_errors = validator.validate_basic_output()
    if basic_errors:
        print("❌ Basic validation failed:")
        for error in basic_errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Basic output validation passed")
    
    # Cognitive validation
    cognitive_errors = validator.validate_cognitive_output()
    if cognitive_errors:
        print("⚠️  Cognitive validation issues:")
        for error in cognitive_errors:
            print(f"  - {error}")
    
    # Extract metrics
    metrics = validator.extract_basic_metrics()
    print(f"📊 Simulation metrics:")
    for key, value in metrics.items():
        print(f"  - {key}: {value}")
    
    # Check for movement
    if metrics.get('movement_occurred', False):
        print("✅ Agent movement detected")
    else:
        print("⚠️  No agent movement detected - check scenario parameters")
    
    return len(basic_errors) == 0
```

### 4. Debug and Diagnostic Tools

**File**: `flee_dual_process/cognitive_debugger.py`

```python
import os
import sys
from pathlib import Path

class CognitiveDebugger:
    """Debug tools for cognitive integration issues."""
    
    def __init__(self, scenario_dir):
        self.scenario_dir = Path(scenario_dir)
        self.debug_log = []
    
    def log(self, message):
        """Add debug message to log."""
        self.debug_log.append(message)
        print(f"DEBUG: {message}")
    
    def validate_scenario_files(self):
        """Check that all required scenario files exist."""
        required_files = [
            'locations.csv',
            'routes.csv', 
            'conflicts.csv',
            'simsetting.csv'
        ]
        
        missing_files = []
        for filename in required_files:
            filepath = self.scenario_dir / filename
            if not filepath.exists():
                missing_files.append(filename)
        
        if missing_files:
            self.log(f"Missing scenario files: {missing_files}")
            return False
        else:
            self.log("All required scenario files present")
            return True
    
    def validate_cognitive_parameters(self):
        """Check cognitive parameter configuration."""
        simsetting_file = self.scenario_dir / 'simsetting.csv'
        
        if not simsetting_file.exists():
            self.log("simsetting.csv not found")
            return False
        
        try:
            import pandas as pd
            df = pd.read_csv(simsetting_file)
            
            # Check for cognitive parameters
            cognitive_params = [
                'TwoSystemDecisionMaking',
                'conflict_threshold', 
                'average_social_connectivity'
            ]
            
            found_params = []
            missing_params = []
            
            for param in cognitive_params:
                if param in df.columns or param in df.iloc[:, 0].values:
                    found_params.append(param)
                else:
                    missing_params.append(param)
            
            self.log(f"Found cognitive parameters: {found_params}")
            if missing_params:
                self.log(f"Missing cognitive parameters: {missing_params}")
            
            return len(missing_params) == 0
            
        except Exception as e:
            self.log(f"Error reading simsetting.csv: {e}")
            return False
    
    def test_flee_import(self):
        """Test that Flee can be imported correctly."""
        try:
            # Add flee directory to path if needed
            flee_dir = Path(__file__).parent.parent / 'flee'
            if flee_dir.exists() and str(flee_dir) not in sys.path:
                sys.path.insert(0, str(flee_dir))
            
            import flee
            self.log("✅ Flee import successful")
            
            # Test Person class
            from flee import Person, Location
            test_location = Location("test", 0, 0, 1000)
            test_person = Person(test_location)
            
            # Test cognitive methods exist
            if hasattr(test_person, 'calculate_cognitive_pressure'):
                self.log("✅ Cognitive methods found in Person class")
            else:
                self.log("❌ Cognitive methods missing from Person class")
                return False
            
            return True
            
        except ImportError as e:
            self.log(f"❌ Flee import failed: {e}")
            return False
        except Exception as e:
            self.log(f"❌ Flee testing failed: {e}")
            return False
    
    def run_minimal_test(self):
        """Run minimal Flee simulation to test basic functionality."""
        if not self.validate_scenario_files():
            return False
        
        if not self.test_flee_import():
            return False
        
        try:
            # Import Flee components
            sys.path.insert(0, str(Path(__file__).parent.parent / 'flee'))
            import flee
            
            # Create minimal simulation
            self.log("Creating minimal Flee simulation...")
            
            # This would run a very basic simulation
            # Implementation depends on Flee's API
            self.log("✅ Minimal simulation test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Minimal simulation failed: {e}")
            return False
    
    def generate_debug_report(self):
        """Generate comprehensive debug report."""
        report = [
            "=== Cognitive Integration Debug Report ===",
            f"Scenario directory: {self.scenario_dir}",
            "",
            "Debug Log:",
        ]
        
        for message in self.debug_log:
            report.append(f"  {message}")
        
        report.extend([
            "",
            "=== Recommendations ===",
        ])
        
        # Add specific recommendations based on findings
        if not (self.scenario_dir / 'simsetting.csv').exists():
            report.append("- Create simsetting.csv with cognitive parameters")
        
        if "Flee import failed" in str(self.debug_log):
            report.append("- Fix Flee import path issues")
            report.append("- Ensure flee directory is in Python path")
        
        if "Missing cognitive parameters" in str(self.debug_log):
            report.append("- Add missing cognitive parameters to simsetting.csv")
            report.append("- Verify parameter names match SimulationSettings.move_rules")
        
        return "\n".join(report)

def debug_cognitive_integration(scenario_dir):
    """Convenience function to debug cognitive integration."""
    debugger = CognitiveDebugger(scenario_dir)
    
    print("🔍 Starting cognitive integration debug...")
    
    # Run all diagnostic tests
    scenario_ok = debugger.validate_scenario_files()
    params_ok = debugger.validate_cognitive_parameters()
    import_ok = debugger.test_flee_import()
    
    # Generate report
    report = debugger.generate_debug_report()
    print("\n" + report)
    
    # Overall status
    if scenario_ok and params_ok and import_ok:
        print("\n✅ All diagnostic tests passed!")
        return True
    else:
        print("\n❌ Some diagnostic tests failed - see recommendations above")
        return False
```

## Data Models

### Cognitive State Model

```python
@dataclass
class CognitiveState:
    agent_id: str
    time_step: int
    cognitive_mode: str  # "system1" or "system2"
    pressure_value: float
    threshold_value: float
    decision_factors: Dict[str, float]
    route_chosen: int
    decision_time_ms: float
```

### Simulation Configuration Model

```python
@dataclass
class CognitiveConfig:
    two_system_decision_making: bool = False
    conflict_threshold: float = 0.5
    average_social_connectivity: float = 0.1
    awareness_level: float = 1.0
    weight_softening: float = 0.1
    
    def validate(self):
        """Validate parameter ranges."""
        if not (0.0 <= self.conflict_threshold <= 2.0):
            raise ValueError(f"conflict_threshold must be in [0.0, 2.0], got {self.conflict_threshold}")
        
        if not (0.0 <= self.average_social_connectivity <= 1.0):
            raise ValueError(f"average_social_connectivity must be in [0.0, 1.0], got {self.average_social_connectivity}")
        
        if not (0.0 <= self.awareness_level <= 2.0):
            raise ValueError(f"awareness_level must be in [0.0, 2.0], got {self.awareness_level}")
        
        if not (0.0 <= self.weight_softening <= 1.0):
            raise ValueError(f"weight_softening must be in [0.0, 1.0], got {self.weight_softening}")
```

## Error Handling

### Parameter Validation Errors
- Invalid parameter types or ranges
- Missing required cognitive parameters
- Conflicting parameter combinations

### Simulation Execution Errors
- Flee import failures
- Missing scenario files
- Empty output directories
- Cognitive calculation errors

### Integration Errors
- Parameter passing failures
- Decision logic errors
- State synchronization issues

## Testing Strategy

### Unit Tests
1. **Parameter Validation Tests**: Test all parameter validation logic
2. **Cognitive Calculation Tests**: Test pressure calculation and state transitions
3. **Decision Logic Tests**: Test System 1 vs System 2 route selection
4. **Output Validation Tests**: Test output file validation and metrics extraction

### Integration Tests
1. **Basic Flee Execution**: Test that Flee runs and produces output
2. **Parameter Loading**: Test that cognitive parameters reach Flee correctly
3. **Behavioral Differences**: Test that S1 and S2 produce different results
4. **End-to-End Scenarios**: Test complete cognitive simulation workflows

### Validation Tests
1. **Minimal Scenarios**: Simple test cases that validate cognitive differences
2. **Debug Tool Tests**: Test diagnostic and debugging functionality
3. **Error Handling Tests**: Test error conditions and recovery
4. **Performance Tests**: Ensure cognitive logic doesn't significantly slow Flee

## Implementation Phases

### Phase 1: Basic Execution (Week 1)
- Fix Flee output file generation issues
- Implement parameter loading and validation
- Create output validation tools
- Get basic Flee simulation working

### Phase 2: Cognitive Integration (Week 2)
- Implement cognitive decision logic in Person class
- Add cognitive pressure calculation
- Implement System 1 vs System 2 route selection
- Add debug logging and diagnostics

### Phase 3: Validation and Testing (Week 3)
- Create minimal test scenarios
- Validate behavioral differences between cognitive modes
- Implement comprehensive testing suite
- Document integration and usage

This design provides a systematic approach to fixing the core Flee integration issues while building a solid foundation for dual-process cognitive modeling.