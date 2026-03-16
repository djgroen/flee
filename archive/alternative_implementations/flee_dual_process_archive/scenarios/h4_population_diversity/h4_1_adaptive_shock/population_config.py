"""
Population Configuration for H4.1 Adaptive Shock Response

Defines different population compositions for testing diversity advantages.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class PopulationType(Enum):
    """Types of population compositions"""
    PURE_S1 = "pure_s1"
    PURE_S2 = "pure_s2"
    BALANCED = "balanced"
    REALISTIC = "realistic"


@dataclass
class CognitiveProfile:
    """Cognitive profile for an agent type"""
    decision_speed: float
    heuristic_weight: float
    deliberation_depth: float
    social_connectivity: float
    shock_sensitivity: float
    learning_rate: float


@dataclass
class PopulationComposition:
    """Population composition specification"""
    name: str
    description: str
    system1_ratio: float
    system2_ratio: float
    s1_profile: CognitiveProfile
    s2_profile: CognitiveProfile
    expected_characteristics: List[str]


class PopulationConfig:
    """Manages population configurations for adaptive shock scenarios"""
    
    def __init__(self):
        self.compositions = self._initialize_compositions()
    
    def _initialize_compositions(self) -> Dict[str, PopulationComposition]:
        """Initialize predefined population compositions"""
        
        # System 1 cognitive profile (fast, heuristic)
        s1_profile = CognitiveProfile(
            decision_speed=0.9,
            heuristic_weight=0.8,
            deliberation_depth=0.2,
            social_connectivity=1.0,
            shock_sensitivity=0.8,
            learning_rate=0.05
        )
        
        # System 2 cognitive profile (slow, deliberative)
        s2_profile = CognitiveProfile(
            decision_speed=0.3,
            heuristic_weight=0.3,
            deliberation_depth=0.8,
            social_connectivity=6.0,
            shock_sensitivity=0.5,
            learning_rate=0.15
        )
        
        return {
            PopulationType.PURE_S1.value: PopulationComposition(
                name="Pure System 1",
                description="100% System 1 agents (fast, reactive)",
                system1_ratio=1.0,
                system2_ratio=0.0,
                s1_profile=s1_profile,
                s2_profile=s1_profile,  # All agents use S1 profile
                expected_characteristics=[
                    "Fast initial evacuation response",
                    "Poor adaptation to unexpected changes",
                    "Limited information sharing",
                    "Suboptimal route choices under pressure",
                    "High movement clustering"
                ]
            ),
            
            PopulationType.PURE_S2.value: PopulationComposition(
                name="Pure System 2",
                description="100% System 2 agents (slow, deliberative)",
                system1_ratio=0.0,
                system2_ratio=1.0,
                s1_profile=s2_profile,  # All agents use S2 profile
                s2_profile=s2_profile,
                expected_characteristics=[
                    "Slow initial evacuation response",
                    "Good adaptation once information is processed",
                    "Effective information sharing within networks",
                    "Better route optimization",
                    "Coordinated collective movement"
                ]
            ),
            
            PopulationType.BALANCED.value: PopulationComposition(
                name="Balanced Population",
                description="50% S1, 50% S2 agents",
                system1_ratio=0.5,
                system2_ratio=0.5,
                s1_profile=s1_profile,
                s2_profile=s2_profile,
                expected_characteristics=[
                    "Moderate initial response speed",
                    "Good adaptation through S1-S2 interaction",
                    "Information cascades from S1 scouts to S2 followers",
                    "Balanced speed-optimality trade-offs",
                    "Emergent collective intelligence"
                ]
            ),
            
            PopulationType.REALISTIC.value: PopulationComposition(
                name="Realistic Population",
                description="70% S1, 30% S2 agents (research-based)",
                system1_ratio=0.7,
                system2_ratio=0.3,
                s1_profile=s1_profile,
                s2_profile=s2_profile,
                expected_characteristics=[
                    "Fast initial response with deliberative oversight",
                    "S1 majority provides rapid scouting",
                    "S2 minority provides strategic guidance",
                    "Information flow from S1 discoveries to S2 analysis",
                    "Realistic cognitive diversity effects"
                ]
            )
        }
    
    def get_composition(self, composition_type: str) -> PopulationComposition:
        """
        Get population composition by type
        
        Args:
            composition_type: Type of composition (pure_s1, pure_s2, balanced, realistic)
            
        Returns:
            PopulationComposition object
            
        Raises:
            ValueError: If composition type is not recognized
        """
        if composition_type not in self.compositions:
            available = list(self.compositions.keys())
            raise ValueError(f"Unknown composition type: {composition_type}. Available: {available}")
        
        return self.compositions[composition_type]
    
    def get_all_compositions(self) -> Dict[str, PopulationComposition]:
        """Get all available population compositions"""
        return self.compositions.copy()
    
    def generate_agent_config(self, composition_type: str, total_agents: int = 10000) -> Dict[str, Any]:
        """
        Generate agent configuration for FLEE simulation
        
        Args:
            composition_type: Type of population composition
            total_agents: Total number of agents to generate
            
        Returns:
            Configuration dictionary for FLEE simulation
        """
        composition = self.get_composition(composition_type)
        
        s1_count = int(total_agents * composition.system1_ratio)
        s2_count = total_agents - s1_count
        
        config = {
            'population': {
                'total_agents': total_agents,
                'system1_count': s1_count,
                'system2_count': s2_count,
                'composition_type': composition_type,
                'description': composition.description
            },
            'cognitive_profiles': {
                'system1': {
                    'decision_speed': composition.s1_profile.decision_speed,
                    'heuristic_weight': composition.s1_profile.heuristic_weight,
                    'deliberation_depth': composition.s1_profile.deliberation_depth,
                    'social_connectivity': composition.s1_profile.social_connectivity,
                    'shock_sensitivity': composition.s1_profile.shock_sensitivity,
                    'learning_rate': composition.s1_profile.learning_rate
                },
                'system2': {
                    'decision_speed': composition.s2_profile.decision_speed,
                    'heuristic_weight': composition.s2_profile.heuristic_weight,
                    'deliberation_depth': composition.s2_profile.deliberation_depth,
                    'social_connectivity': composition.s2_profile.social_connectivity,
                    'shock_sensitivity': composition.s2_profile.shock_sensitivity,
                    'learning_rate': composition.s2_profile.learning_rate
                }
            },
            'expected_characteristics': composition.expected_characteristics
        }
        
        return config
    
    def compare_compositions(self) -> Dict[str, Any]:
        """
        Generate comparison matrix of all population compositions
        
        Returns:
            Comparison data for analysis and visualization
        """
        comparison = {
            'compositions': {},
            'metrics': {
                'response_speed': {},
                'adaptation_capability': {},
                'information_sharing': {},
                'collective_intelligence': {}
            }
        }
        
        for comp_type, composition in self.compositions.items():
            comparison['compositions'][comp_type] = {
                'name': composition.name,
                'description': composition.description,
                's1_ratio': composition.system1_ratio,
                's2_ratio': composition.system2_ratio,
                'characteristics': composition.expected_characteristics
            }
            
            # Predicted performance metrics (0-1 scale)
            if comp_type == PopulationType.PURE_S1.value:
                comparison['metrics']['response_speed'][comp_type] = 0.9
                comparison['metrics']['adaptation_capability'][comp_type] = 0.3
                comparison['metrics']['information_sharing'][comp_type] = 0.4
                comparison['metrics']['collective_intelligence'][comp_type] = 0.4
            elif comp_type == PopulationType.PURE_S2.value:
                comparison['metrics']['response_speed'][comp_type] = 0.4
                comparison['metrics']['adaptation_capability'][comp_type] = 0.8
                comparison['metrics']['information_sharing'][comp_type] = 0.8
                comparison['metrics']['collective_intelligence'][comp_type] = 0.7
            elif comp_type == PopulationType.BALANCED.value:
                comparison['metrics']['response_speed'][comp_type] = 0.7
                comparison['metrics']['adaptation_capability'][comp_type] = 0.9
                comparison['metrics']['information_sharing'][comp_type] = 0.8
                comparison['metrics']['collective_intelligence'][comp_type] = 0.9
            elif comp_type == PopulationType.REALISTIC.value:
                comparison['metrics']['response_speed'][comp_type] = 0.8
                comparison['metrics']['adaptation_capability'][comp_type] = 0.8
                comparison['metrics']['information_sharing'][comp_type] = 0.7
                comparison['metrics']['collective_intelligence'][comp_type] = 0.8
        
        return comparison


def create_population_sweep_configs(base_output_dir: str) -> List[Dict[str, Any]]:
    """
    Create configuration sweep across all population compositions
    
    Args:
        base_output_dir: Base directory for output files
        
    Returns:
        List of configuration dictionaries for parameter sweep
    """
    config_manager = PopulationConfig()
    sweep_configs = []
    
    for comp_type in [PopulationType.PURE_S1.value, PopulationType.PURE_S2.value, 
                      PopulationType.BALANCED.value, PopulationType.REALISTIC.value]:
        
        config = config_manager.generate_agent_config(comp_type)
        
        sweep_config = {
            'scenario_name': f'h4_1_adaptive_shock_{comp_type}',
            'output_dir': f'{base_output_dir}/h4_1_{comp_type}',
            'population_composition': comp_type,
            'agent_config': config,
            'replications': 10,  # Multiple runs for statistical significance
            'parameters': {
                'shock_intensity': 0.8,
                'adaptation_window': 10,
                'total_simulation_days': 45
            }
        }
        
        sweep_configs.append(sweep_config)
    
    return sweep_configs