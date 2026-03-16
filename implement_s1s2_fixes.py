#!/usr/bin/env python3
"""
Implementation of S1/S2 mathematical fixes
"""

import sys
import os
import math
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def implement_s1s2_fixes():
    """Implement the mathematical fixes for S1/S2 system"""
    
    print("🔧 Implementing S1/S2 Mathematical Fixes")
    print("=" * 60)
    
    # Phase 1: Fix Cognitive Pressure Calculation
    print("\n📋 Phase 1: Fixing Cognitive Pressure Calculation")
    print("-" * 50)
    
    # Read the current flee.py file
    flee_file = Path("flee/flee.py")
    if not flee_file.exists():
        print("❌ flee.py not found!")
        return
    
    with open(flee_file, 'r') as f:
        content = f.read()
    
    # Find and replace the calculate_cognitive_pressure method
    old_method = '''    @check_args_type
    def calculate_cognitive_pressure(self, time: int) -> float:
        """
        Calculate cognitive pressure based on conflict intensity, connectivity, and recovery period.
        
        Args:
            time: Current simulation time
            
        Returns:
            Cognitive pressure value (dimensionless parameter)
        """
        if self.location is None:
            return 0.0
            
        # Get conflict intensity (0.0 to 1.0)
        conflict_intensity = max(0.0, getattr(self.location, 'conflict', 0.0))
        
        # Get connectivity (0 to 10, normalized to 0.0 to 1.0)
        connectivity = min(1.0, self.attributes.get("connections", 0) / 10.0)
        
        # Calculate recovery period (days since last major conflict)
        recovery_period = 30.0  # Default recovery period
        if hasattr(self.location, 'time_of_conflict') and self.location.time_of_conflict >= 0:
            recovery_period = max(1.0, time - self.location.time_of_conflict)
        
        # Enhanced cognitive pressure formula with base pressure
        # Base pressure from connectivity and time (agents get more stressed over time)
        base_pressure = connectivity * 0.3 + (time / 20.0) * 0.2  # Time-based stress
        
        # Conflict-induced pressure
        conflict_pressure = (conflict_intensity * connectivity) / (recovery_period / 30.0)
        
        # Total cognitive pressure
        cognitive_pressure = base_pressure + conflict_pressure
        
        return cognitive_pressure'''
    
    new_method = '''    @check_args_type
    def calculate_cognitive_pressure(self, time: int) -> float:
        """
        Calculate cognitive pressure based on conflict intensity, connectivity, and recovery period.
        
        Uses bounded mathematical model with realistic dynamics.
        
        Args:
            time: Current simulation time
            
        Returns:
            Cognitive pressure value (dimensionless parameter, bounded [0.0, 1.0])
        """
        if self.location is None:
            return 0.0
            
        # Get conflict intensity (0.0 to 1.0)
        conflict_intensity = max(0.0, getattr(self.location, 'conflict', 0.0))
        
        # Get connectivity (0 to 10, normalized to 0.0 to 1.0)
        connectivity = min(1.0, self.attributes.get("connections", 0) / 10.0)
        
        # 1. Base Pressure (Internal Stress) - bounded to 0.4
        base_pressure = min(0.4, connectivity * 0.2 + self._calculate_time_stress(time))
        
        # 2. Conflict Pressure (External Stress) - bounded to 0.4
        conflict_pressure = min(0.4, conflict_intensity * connectivity * self._calculate_conflict_decay(time))
        
        # 3. Social Pressure (Network Effects) - bounded to 0.2
        social_pressure = min(0.2, self._calculate_social_pressure(time))
        
        # Total cognitive pressure (bounded [0.0, 1.0])
        cognitive_pressure = base_pressure + conflict_pressure + social_pressure
        
        return max(0.0, min(1.0, cognitive_pressure))
    
    def _calculate_time_stress(self, time: int) -> float:
        """
        Calculate time-based stress with realistic dynamics.
        
        Creates initial increase, peak, then decay.
        """
        # Time stress with decay: 0.1 * (1 - exp(-t/10)) * exp(-t/50)
        growth_factor = 1.0 - math.exp(-time / 10.0)
        decay_factor = math.exp(-time / 50.0)
        return 0.1 * growth_factor * decay_factor
    
    def _calculate_conflict_decay(self, time: int) -> float:
        """
        Calculate conflict decay factor based on time since conflict.
        """
        # Get conflict start time (default to 0 if not set)
        conflict_start_time = getattr(self.location, 'time_of_conflict', 0)
        recovery_time = 20.0  # 20 timesteps for recovery
        
        # Exponential decay after conflict starts
        time_since_conflict = max(0, time - conflict_start_time)
        return math.exp(-time_since_conflict / recovery_time)
    
    def _calculate_social_pressure(self, time: int) -> float:
        """
        Calculate social pressure from network effects.
        
        For now, simplified implementation. Can be enhanced later.
        """
        # Simplified: based on connectivity and time
        connectivity = min(1.0, self.attributes.get("connections", 0) / 10.0)
        
        # Social pressure increases with connectivity but is bounded
        return min(0.2, connectivity * 0.1)'''
    
    # Replace the method
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Updated calculate_cognitive_pressure method")
    else:
        print("❌ Could not find calculate_cognitive_pressure method to replace")
        return
    
    # Phase 2: Fix S2 Activation Probability
    print("\n📋 Phase 2: Fixing S2 Activation Probability")
    print("-" * 50)
    
    # Read the moving.py file
    moving_file = Path("flee/moving.py")
    if not moving_file.exists():
        print("❌ moving.py not found!")
        return
    
    with open(moving_file, 'r') as f:
        moving_content = f.read()
    
    # Find and replace the calculate_systematic_s2_activation function
    old_activation = '''def calculate_systematic_s2_activation(agent, pressure, base_threshold, time):
    """
    Calculate systematic S2 activation using continuous probability curves.
    
    This implements the evidence-based systematic optimization approach.
    """
    import math
    import random
    
    # Base sigmoid activation curve - pressure must exceed threshold for significant activation
    k = 8.0  # Steepness parameter (increased for sharper threshold)
    base_prob = 1.0 / (1.0 + math.exp(-k * (pressure - base_threshold)))
    
    # Individual difference modifiers (reduced to make pressure more important)
    education_level = agent.attributes.get('education_level', 0.5)
    education_boost = education_level * 0.1  # Reduced from 0.2
    
    stress_tolerance = agent.attributes.get('stress_tolerance', 0.5)
    stress_modifier = stress_tolerance * 0.05  # Reduced from 0.1
    
    # Social support modifier (reduced)
    connections = agent.attributes.get('connections', 5)
    social_support = min(connections * 0.02, 0.1)  # Reduced from 0.03, max 10% boost
    
    # Time-based modifiers (reduced)
    fatigue_penalty = min(time * 0.002, 0.1)  # Reduced from 0.005, max 10% penalty
    learning_boost = min(time * 0.001, 0.05)   # Reduced from 0.002, max 5% boost
    
    # Combine all modifiers
    final_prob = base_prob + education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
    
    # Ensure probability stays in valid range
    final_prob = max(0.0, min(1.0, final_prob))
    
    # Random activation based on probability
    return random.random() < final_prob'''
    
    new_activation = '''def calculate_systematic_s2_activation(agent, pressure, base_threshold, time):
    """
    Calculate systematic S2 activation using bounded mathematical model.
    
    Uses proper sigmoid function with bounded individual modifiers.
    """
    import math
    import random
    
    # Base sigmoid activation curve with proper steepness
    k = 6.0  # Steepness parameter (more realistic than 8.0)
    base_prob = 1.0 / (1.0 + math.exp(-k * (pressure - base_threshold)))
    
    # Individual difference modifiers (bounded and realistic)
    education_level = agent.attributes.get('education_level', 0.5)
    education_boost = education_level * 0.05  # Max 5% boost
    
    stress_tolerance = agent.attributes.get('stress_tolerance', 0.5)
    stress_modifier = stress_tolerance * 0.03  # Max 3% boost
    
    # Social support modifier (bounded)
    connections = agent.attributes.get('connections', 0)  # Start from 0, not 5
    social_support = min(connections * 0.01, 0.05)  # Max 5% boost
    
    # Time-based modifiers (bounded)
    fatigue_penalty = min(time * 0.001, 0.03)  # Max 3% penalty, bounded
    learning_boost = min(time * 0.002, 0.05)   # Max 5% boost, bounded
    
    # Combine all modifiers
    final_prob = base_prob + education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
    
    # Ensure probability stays in valid range
    final_prob = max(0.0, min(1.0, final_prob))
    
    # Random activation based on probability
    return random.random() < final_prob'''
    
    # Replace the function
    if old_activation in moving_content:
        moving_content = moving_content.replace(old_activation, new_activation)
        print("✅ Updated calculate_systematic_s2_activation function")
    else:
        print("❌ Could not find calculate_systematic_s2_activation function to replace")
        return
    
    # Phase 3: Fix S2 Capability
    print("\n📋 Phase 3: Fixing S2 Capability")
    print("-" * 50)
    
    # Find and replace the get_system2_capable method
    old_capability = '''    @check_args_type
    def get_system2_capable(self) -> bool:
        """
        Determine if agent is capable of System 2 thinking.
        
        Returns:
            True if agent can use System 2 thinking
        """
        # System 2 capability based on connections and experience
        min_connections = 2
        min_travel_experience = 5  # days since departure
        
        has_connections = self.attributes.get("connections", 0) >= min_connections
        has_experience = self.timesteps_since_departure >= min_travel_experience
        
        return has_connections or has_experience'''
    
    new_capability = '''    @check_args_type
    def get_system2_capable(self) -> bool:
        """
        Determine if agent is capable of System 2 thinking.
        
        More realistic requirements based on connections, experience, or education.
        
        Returns:
            True if agent can use System 2 thinking
        """
        # System 2 capability based on connections, experience, or education
        min_connections = 1  # Lowered from 2
        min_travel_experience = 3  # Lowered from 5
        min_education = 0.3  # Education-based capability
        
        has_connections = self.attributes.get("connections", 0) >= min_connections
        has_experience = self.timesteps_since_departure >= min_travel_experience
        has_education = self.attributes.get("education_level", 0.5) >= min_education
        
        return has_connections or has_experience or has_education'''
    
    # Replace the method
    if old_capability in content:
        content = content.replace(old_capability, new_capability)
        print("✅ Updated get_system2_capable method")
    else:
        print("❌ Could not find get_system2_capable method to replace")
        return
    
    # Write the updated files
    print("\n💾 Writing updated files...")
    
    with open(flee_file, 'w') as f:
        f.write(content)
    print("✅ Updated flee/flee.py")
    
    with open(moving_file, 'w') as f:
        f.write(moving_content)
    print("✅ Updated flee/moving.py")
    
    print("\n🎉 S1/S2 mathematical fixes implemented!")
    print("\n📋 Summary of changes:")
    print("  - Fixed cognitive pressure calculation with bounded components")
    print("  - Added time stress with realistic decay dynamics")
    print("  - Added conflict decay mechanism")
    print("  - Fixed S2 activation probability with bounded modifiers")
    print("  - Lowered S2 capability requirements")
    print("  - Added education-based S2 capability")
    
    print("\n🧪 Next step: Run tests to validate the fixes")

if __name__ == "__main__":
    implement_s1s2_fixes()




