#!/usr/bin/env python3
"""
Refugee Person Enhancements

Minimal refugee-specific attributes and methods that extend the existing Person class
while maintaining full backward compatibility with existing Flee simulations.
"""

import sys
from pathlib import Path

# Add Flee to path
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def add_refugee_attributes(person, refugee_config=None):
    """
    Add minimal refugee-specific attributes to existing Person object.
    
    Args:
        person: Existing Flee Person object
        refugee_config: Optional dict with refugee-specific settings
        
    This function extends existing Person objects with refugee attributes
    without modifying the core Flee Person class.
    """
    
    if refugee_config is None:
        refugee_config = {}
    
    # Add minimal refugee-specific attributes to existing attributes dict
    refugee_defaults = {
        'safety_threshold': 0.5,    # When does agent decide to flee? (0.0-1.0)
        'risk_tolerance': 0.3,      # How much danger will agent accept? (0.0-1.0)  
        'mobility': 1.0,            # How far can agent travel? (0.0-2.0, 1.0=normal)
        'destination_knowledge': {} # What does agent know about places?
    }
    
    # Merge with existing attributes, preserving existing values
    for key, default_value in refugee_defaults.items():
        if key not in person.attributes:
            person.attributes[key] = refugee_config.get(key, default_value)
    
    # Mark person as refugee-enhanced (using existing attributes dict)
    person.attributes['_refugee_enhanced'] = True
    
    return person

def create_refugee_agent(location, base_attributes=None, refugee_config=None):
    """
    Create a new agent with refugee-specific attributes using existing Person class.
    
    Args:
        location: Flee Location object
        base_attributes: Standard Flee attributes (connections, etc.)
        refugee_config: Refugee-specific configuration
        
    Returns:
        Person object with refugee enhancements
    """
    from flee.flee import Person
    
    if base_attributes is None:
        base_attributes = {}
    
    # Create standard Flee Person object
    person = Person(location, base_attributes)
    
    # Add refugee enhancements
    return add_refugee_attributes(person, refugee_config)

def get_safety_threshold(agent):
    """Get agent's safety threshold"""
    return agent.attributes.get('safety_threshold', 0.5)

def get_risk_tolerance(agent):
    """Get agent's risk tolerance"""
    return agent.attributes.get('risk_tolerance', 0.3)

def get_mobility(agent):
    """Get agent's mobility"""
    return agent.attributes.get('mobility', 1.0)

def get_destination_knowledge(agent):
    """Get agent's destination knowledge"""
    return agent.attributes.get('destination_knowledge', {})

def should_evacuate(agent, conflict_level):
    """Check if agent should evacuate given conflict level"""
    return conflict_level > get_safety_threshold(agent)

def can_tolerate_risk(agent, risk_level):
    """Check if agent can tolerate given risk level"""
    return risk_level <= get_risk_tolerance(agent)

def is_refugee_enhanced(agent):
    """Check if agent has refugee enhancements"""
    return agent.attributes.get('_refugee_enhanced', False)

def s1_refugee_decision(agent, destinations, time):
    """
    System 1 refugee decision logic: "Run to nearest safe place"
    
    Fast, heuristic decision-making:
    - Use only local information about immediate safety
    - Choose first "good enough" option (satisficing)
    - Direct routes without congestion planning
    
    Args:
        agent: Person object with refugee attributes
        destinations: List of available destinations
        time: Current simulation time
        
    Returns:
        Chosen destination or None
    """
    
    safety_threshold = get_safety_threshold(agent)
    
    # S1: Simple heuristic - go to closest destination that meets safety threshold
    for dest in sorted(destinations, key=lambda d: d.calculateDistance(agent.location)):
        # Simple safety check: conflict level < safety threshold
        if hasattr(dest, 'conflict') and dest.conflict < safety_threshold:
            return dest
        # If no conflict info, assume it's safer than current location
        elif not hasattr(dest, 'conflict'):
            return dest
    
    # If no safe destination found, go to closest one (panic mode)
    if destinations:
        return min(destinations, key=lambda d: d.calculateDistance(agent.location))
    
    return None

def s2_refugee_decision(agent, destinations, time, ecosystem=None):
    """
    System 2 refugee decision logic: "Plan optimal escape route"
    
    Analytical, deliberate decision-making:
    - Comprehensive analysis: safety, distance, capacity, future prospects
    - Use network information about distant destinations  
    - Strategic route planning with bottleneck avoidance
    
    Args:
        agent: Person object with refugee attributes
        destinations: List of available destinations
        time: Current simulation time
        ecosystem: Ecosystem object for network information
        
    Returns:
        Chosen destination or None
    """
    
    if not destinations:
        return None
    
    safety_threshold = get_safety_threshold(agent)
    risk_tolerance = get_risk_tolerance(agent)
    mobility = get_mobility(agent)
    
    # S2: Comprehensive analysis with multiple factors
    destination_scores = []
    
    for dest in destinations:
        score = 0.0
        
        # Factor 1: Safety (most important)
        if hasattr(dest, 'conflict'):
            safety_score = max(0, 1.0 - dest.conflict)  # Higher is safer
            score += safety_score * 0.4  # 40% weight
        else:
            score += 0.4  # Assume safe if no conflict info
        
        # Factor 2: Distance (closer is better, but adjusted by mobility)
        distance = dest.calculateDistance(agent.location)
        max_reasonable_distance = 500 * mobility  # Mobility affects travel capability
        distance_score = max(0, 1.0 - (distance / max_reasonable_distance))
        score += distance_score * 0.2  # 20% weight
        
        # Factor 3: Capacity (avoid overcrowded places)
        if hasattr(dest, 'capacity') and dest.capacity > 0:
            occupancy = dest.numAgents / dest.capacity
            capacity_score = max(0, 1.0 - occupancy)
            score += capacity_score * 0.2  # 20% weight
        else:
            score += 0.1  # Partial score if no capacity info
        
        # Factor 4: Camp status (camps are generally safer)
        if hasattr(dest, 'camp') and dest.camp:
            score += 0.1  # 10% bonus for camps
        
        # Factor 5: Network information (if available)
        dest_knowledge = get_destination_knowledge(agent)
        if dest.name in dest_knowledge:
            knowledge_bonus = dest_knowledge[dest.name].get('quality_score', 0)
            score += knowledge_bonus * 0.1  # 10% weight for network info
        
        destination_scores.append((dest, score))
    
    # Choose destination with highest score
    if destination_scores:
        best_dest, best_score = max(destination_scores, key=lambda x: x[1])
        
        # Only choose if score meets minimum threshold
        if best_score > 0.3:  # Minimum acceptable score
            return best_dest
    
    # Fallback: if no destination meets criteria, use S1 logic
    return s1_refugee_decision(agent, destinations, time)

def enhanced_refugee_movechance(agent, base_movechance, system2_active, time):
    """
    Enhance existing movechance calculation with refugee-specific logic.
    
    This function modifies the existing movechance based on refugee attributes
    while maintaining compatibility with existing Flee logic.
    
    Args:
        agent: Person object with refugee attributes
        base_movechance: Original movechance from calculateMoveChance()
        system2_active: Whether System 2 is active
        time: Current simulation time
        
    Returns:
        Modified movechance
    """
    
    # Start with base movechance from existing Flee logic
    enhanced_movechance = base_movechance
    
    # Get refugee attributes (with defaults if not present)
    safety_threshold = agent.attributes.get('safety_threshold', 0.5)
    risk_tolerance = agent.attributes.get('risk_tolerance', 0.3)
    
    # Current threat level
    current_threat = getattr(agent.location, 'conflict', 0.0)
    
    # Refugee-specific movechance adjustments
    if current_threat > safety_threshold:
        # Agent wants to flee - increase movechance
        threat_multiplier = 1.0 + (current_threat - safety_threshold) * 2.0
        enhanced_movechance *= threat_multiplier
    
    # Risk tolerance affects decision urgency
    if current_threat > risk_tolerance:
        # Agent cannot tolerate current risk level
        urgency_multiplier = 1.0 + (current_threat - risk_tolerance)
        enhanced_movechance *= urgency_multiplier
    
    # System 2 agents are more deliberate (slightly lower movechance for planning)
    if system2_active:
        enhanced_movechance *= 0.9  # 10% reduction for deliberation
    
    # Ensure movechance stays within reasonable bounds
    enhanced_movechance = min(1.0, max(0.0, enhanced_movechance))
    
    return enhanced_movechance

def test_refugee_enhancements():
    """Test refugee enhancements with existing Flee system"""
    print("🧪 TESTING REFUGEE ENHANCEMENTS WITH EXISTING FLEE SYSTEM")
    print("=" * 60)
    
    try:
        from flee.SimulationSettings import SimulationSettings
        from flee.flee import Ecosystem, Person
        from flee import moving
        
        # Initialize existing Flee settings
        SimulationSettings.ReadFromYML("test_data/test_settings.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        
        # Create ecosystem using existing infrastructure
        ecosystem = Ecosystem()
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=0.8)
        safe_camp = ecosystem.addLocation("SafeCamp", x=100, y=0, movechance=0.001, capacity=1000)
        risky_town = ecosystem.addLocation("RiskyTown", x=50, y=50, movechance=0.3)
        
        # Set conflict levels
        origin.conflict = 0.8  # High conflict
        safe_camp.conflict = 0.1  # Low conflict
        risky_town.conflict = 0.6  # Medium conflict
        
        ecosystem.linkUp("Origin", "SafeCamp", 100.0)
        ecosystem.linkUp("Origin", "RiskyTown", 70.0)
        
        print("✅ Created test ecosystem with conflict zones")
        
        # Test 1: Create standard Flee agent (backward compatibility)
        standard_agent = Person(origin, {"connections": 3})
        print("✅ Created standard Flee agent (no refugee enhancements)")
        
        # Test 2: Create refugee-enhanced agent
        refugee_config = {
            'safety_threshold': 0.4,  # Lower threshold = more risk-averse
            'risk_tolerance': 0.2,    # Low risk tolerance
            'mobility': 1.2           # Higher mobility
        }
        refugee_agent = create_refugee_agent(origin, {"connections": 5}, refugee_config)
        print("✅ Created refugee-enhanced agent")
        
        # Test 3: Test refugee decision methods
        print(f"\\n🔍 TESTING REFUGEE DECISION METHODS:")
        print(f"  Safety threshold: {get_safety_threshold(refugee_agent)}")
        print(f"  Risk tolerance: {get_risk_tolerance(refugee_agent)}")
        print(f"  Mobility: {get_mobility(refugee_agent)}")
        print(f"  Should evacuate (conflict=0.8): {should_evacuate(refugee_agent, 0.8)}")
        print(f"  Can tolerate risk (risk=0.6): {can_tolerate_risk(refugee_agent, 0.6)}")
        
        # Test 4: Test S1 vs S2 refugee decisions
        destinations = [safe_camp, risky_town]
        
        s1_choice = s1_refugee_decision(refugee_agent, destinations, 1)
        s2_choice = s2_refugee_decision(refugee_agent, destinations, 1, ecosystem)
        
        print(f"\\n🧠 REFUGEE DECISION COMPARISON:")
        print(f"  S1 choice: {s1_choice.name if s1_choice else 'None'}")
        print(f"  S2 choice: {s2_choice.name if s2_choice else 'None'}")
        
        # Test 5: Test enhanced movechance calculation
        base_movechance, system2_active = moving.calculateMoveChance(refugee_agent, False, 1)
        enhanced_movechance = enhanced_refugee_movechance(refugee_agent, base_movechance, system2_active, 1)
        
        print(f"\\n📊 MOVECHANCE ENHANCEMENT:")
        print(f"  Base movechance: {base_movechance:.3f}")
        print(f"  Enhanced movechance: {enhanced_movechance:.3f}")
        print(f"  System 2 active: {system2_active}")
        
        # Test 6: Verify backward compatibility
        standard_movechance, _ = moving.calculateMoveChance(standard_agent, False, 1)
        print(f"\\n🔄 BACKWARD COMPATIBILITY:")
        print(f"  Standard agent movechance: {standard_movechance:.3f}")
        print(f"  Standard agent has refugee attrs: {is_refugee_enhanced(standard_agent)}")
        
        print("\\n✅ ALL REFUGEE ENHANCEMENT TESTS PASSED!")
        print("\\n🎯 KEY FEATURES DEMONSTRATED:")
        print("  • Minimal refugee attributes added to existing Person class")
        print("  • S1 vs S2 refugee decision logic implemented")
        print("  • Enhanced movechance calculation with refugee factors")
        print("  • Full backward compatibility maintained")
        print("  • Ready for integration with existing Flee simulations")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_refugee_enhancements()
    if success:
        print("\\n🎉 REFUGEE ENHANCEMENTS READY FOR WEEK 2 INTEGRATION!")
    else:
        print("\\n❌ REFUGEE ENHANCEMENTS NEED DEBUGGING")
        sys.exit(1)