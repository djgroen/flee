# S1/S2 Integration Instructions

## Overview

This patch integrates the refactored S1/S2 dual-process decision-making system into FLEE with exact mathematical specifications.

## Files Modified

1. **`flee/flee.py`** - Updated Person class methods
2. **`flee/moving.py`** - Updated move chance calculation
3. **`flee/SimulationSettings.py`** - Added S1/S2 configuration options

## New Configuration Options

Add these options to your YAML configuration file:

```yaml
# S1/S2 System Configuration
connectivity_mode: "baseline"  # "baseline" or "diminishing"
soft_capability: false         # true for soft gate, false for hard gate
pmove_s2_mode: "scaled"        # "scaled" or "constant"
pmove_s2_constant: 0.9         # Fixed value for constant mode [0.8, 0.95]
eta: 0.5                       # Scaling factor for scaled mode [0.2, 0.8]
steepness: 6.0                 # Sigmoid steepness
soft_gate_steepness: 8.0       # Steepness for soft capability gate [6, 12]
```

## Mathematical Specifications

### Pressure Components
- **P(t) = min(1, B(t) + C(t) + S(t))**
- **B(t) = min(0.4, 0.2*fc + 0.1*(1-exp(-t/10))*exp(-t/50))**
- **C(t) = min(0.4, I(t)*fc*exp(-max(0,t-tc)/20))**
- **S(t) = min(0.2, 0.1*fc)**
- **fc = min(1, c/10)** (baseline) or **fc = c/(1+c)** (diminishing)

### S2 Activation
- **base = 1/(1+exp(-6*(P(t)-theta_i)))**
- **modifiers = 0.05*e + 0.03*tau + min(0.01*c,0.05) - min(0.001*t,0.03) + min(0.002*t,0.05)**
- **pS2 = gate * clip(base + modifiers, 0, 1)**

### Capability Gates
- **Hard**: 1[c≥1] OR 1[Δt≥3] OR 1[e≥0.3]
- **Soft**: 1 - (1-sig(c-0.5))(1-sig(Δt-3))(1-sig(e-0.3))

### Move Probabilities
- **pmove = (1 - pS2)*pmove_S1 + pS2*pmove_S2**
- **p(move|S2) = clip(mu_loc*(1 + eta*P(t)), 0, 1)** (scaled mode)

## Integration Steps

1. **Copy the refactored module**:
   ```bash
   cp s1s2_refactored.py flee/
   ```

2. **Apply the patch**:
   ```bash
   patch -p0 < s1s2_integration.patch
   ```

3. **Update your YAML configuration** with the new S1/S2 options

4. **Run tests** to verify integration:
   ```bash
   python -m pytest test_s1s2_refactored.py -v
   ```

## Validation

The refactored system has been validated with comprehensive unit tests covering:
- ✅ All formulas match exact specifications
- ✅ All probabilities/pressures clipped to [0,1]
- ✅ Capability gate toggle works (hard/soft)
- ✅ Connectivity mode toggle works (baseline/diminishing)
- ✅ p(move|S2) not hard-coded to 1.0
- ✅ Unit tests pass (< 200ms)
- ✅ No new dependencies beyond stdlib/numpy/pytest

## Benefits

1. **Mathematically Sound**: Exact implementation of specified formulas
2. **Configurable**: All parameters exposed via YAML configuration
3. **Bounded**: All intermediate outputs clipped to documented bounds
4. **Tested**: Comprehensive unit test coverage
5. **Clean**: Pure functions with no hidden state or side effects
6. **Fast**: Optimized implementation with minimal overhead

## Backward Compatibility

The system maintains backward compatibility:
- Existing YAML files work without modification (uses defaults)
- Original S1 logic preserved when S1/S2 disabled
- No breaking changes to existing APIs
