"""
Scenario Generator Module

Generates conflict patterns that trigger different cognitive responses in agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import os
import csv
import math
from .utils import CSVUtils, ValidationUtils, LoggingUtils


class ConflictScenarioGenerator(ABC):
    """
    Base class for generating different conflict scenarios for Flee experiments.
    
    This abstract class defines the interface for creating various conflict
    patterns (spike, gradual, cascading, oscillating) that can be used to test
    how different conflict dynamics trigger cognitive responses in refugee movements.
    """
    
    def __init__(self, topology_file: str):
        """
        Initialize the scenario generator with topology information.
        
        Args:
            topology_file: Path to the topology locations file
        """
        self.topology_file = topology_file
        self.csv_utils = CSVUtils()
        self.validation_utils = ValidationUtils()
        self.logger = LoggingUtils().get_logger('ConflictScenarioGenerator')
        self.locations = []
        self.location_names = []
        self._load_topology()
    
    def _load_topology(self) -> None:
        """Load topology information from the locations file."""
        try:
            if not os.path.exists(self.topology_file):
                raise FileNotFoundError(f"Topology file not found: {self.topology_file}")
            
            self.locations = self.csv_utils.read_locations_csv(self.topology_file)
            self.location_names = [loc['name'] for loc in self.locations]
            
            self.logger.info(f"Loaded topology with {len(self.locations)} locations")
            
        except Exception as e:
            self.logger.error(f"Failed to load topology: {e}")
            raise
    
    @abstractmethod
    def generate_spike_conflict(self, origin: str, start_day: int, 
                               peak_intensity: float) -> str:
        """
        Generate a spike conflict scenario with sudden high-intensity conflict.
        
        Args:
            origin: Name of the origin location
            start_day: Day when conflict begins
            peak_intensity: Maximum conflict intensity
            
        Returns:
            Path to generated conflicts.csv file
        """
        pass
    
    @abstractmethod
    def generate_gradual_conflict(self, origin: str, start_day: int, 
                                 end_day: int, max_intensity: float) -> str:
        """
        Generate a gradual conflict scenario with linear escalation.
        
        Args:
            origin: Name of the origin location
            start_day: Day when conflict begins
            end_day: Day when conflict reaches maximum
            max_intensity: Maximum conflict intensity
            
        Returns:
            Path to generated conflicts.csv file
        """
        pass
    
    @abstractmethod
    def generate_cascading_conflict(self, origin: str, start_day: int, 
                                   spread_rate: float, max_intensity: float) -> str:
        """
        Generate a cascading conflict scenario that spreads through network.
        
        Args:
            origin: Name of the origin location
            start_day: Day when conflict begins
            spread_rate: Rate of conflict spread per day
            max_intensity: Maximum conflict intensity
            
        Returns:
            Path to generated conflicts.csv file
        """
        pass
    
    @abstractmethod
    def generate_oscillating_conflict(self, origin: str, start_day: int, 
                                     period: int, amplitude: float) -> str:
        """
        Generate an oscillating conflict scenario with cyclical variations.
        
        Args:
            origin: Name of the origin location
            start_day: Day when conflict begins
            period: Period of oscillation in days
            amplitude: Amplitude of oscillation
            
        Returns:
            Path to generated conflicts.csv file
        """
        pass
    
    def _write_conflicts_csv(self, conflicts: Dict[int, Dict[str, float]], filepath: str) -> None:
        """
        Write conflicts data to CSV file in Flee matrix format.
        
        The Flee conflicts.csv format is a matrix with:
        - First row: header with #Day followed by location names
        - Subsequent rows: day number followed by conflict intensities for each location
        
        Args:
            conflicts: Dictionary mapping days to location conflicts
            filepath: Output file path
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Get all days and sort them
            days = sorted(conflicts.keys())
            
            # Ensure all locations are represented in conflicts data
            all_locations = set(self.location_names)
            for day_conflicts in conflicts.values():
                all_locations.update(day_conflicts.keys())
            
            # Sort locations for consistent output
            sorted_locations = sorted(all_locations)
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header: #Day, location1, location2, ...
                header = ['#Day'] + sorted_locations
                writer.writerow(header)
                
                # Write data rows
                for day in days:
                    row = [day]
                    day_conflicts = conflicts.get(day, {})
                    
                    for location in sorted_locations:
                        intensity = day_conflicts.get(location, 0.0)
                        row.append(intensity)
                    
                    writer.writerow(row)
            
            self.logger.info(f"Written conflicts CSV with {len(days)} days and {len(sorted_locations)} locations to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to write conflicts CSV: {e}")
            raise
    
    def validate_scenario(self, conflicts_file: str, sim_period: Tuple[int, int] = None) -> bool:
        """
        Validate generated scenario for temporal consistency.
        
        Args:
            conflicts_file: Path to conflicts CSV file
            sim_period: Optional tuple of (start_day, end_day) for simulation period
            
        Returns:
            True if scenario is valid, False otherwise
        """
        try:
            if not os.path.exists(conflicts_file):
                self.logger.error(f"Conflicts file not found: {conflicts_file}")
                return False
            
            # Read conflicts using matrix format
            conflicts = self._read_conflicts_matrix(conflicts_file)
            
            # Validate temporal consistency
            if not self._validate_temporal_consistency(conflicts, sim_period):
                return False
            
            # Validate location consistency
            if not self._validate_location_consistency(conflicts):
                return False
            
            # Validate intensity ranges
            if not self._validate_intensity_ranges(conflicts):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Scenario validation failed: {e}")
            return False
    
    def _read_conflicts_matrix(self, filepath: str) -> Dict[int, Dict[str, float]]:
        """
        Read conflicts from Flee matrix format CSV file.
        
        Args:
            filepath: Path to conflicts CSV file
            
        Returns:
            Dictionary mapping days to location conflicts
        """
        conflicts = {}
        
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            
            # Read header to get location names
            header = next(reader)
            # Remove '#Day' from header and get location names
            location_names = [name.strip() for name in header[1:]]
            
            # Read data rows
            for row in reader:
                if not row or not row[0].strip():
                    continue
                
                day = int(row[0])
                day_conflicts = {}
                
                for i, intensity_str in enumerate(row[1:]):
                    if i < len(location_names):
                        location = location_names[i]
                        intensity = float(intensity_str.strip())
                        if intensity > 0:  # Only store non-zero conflicts
                            day_conflicts[location] = intensity
                
                if day_conflicts:  # Only store days with conflicts
                    conflicts[day] = day_conflicts
        
        return conflicts
    
    def _validate_temporal_consistency(self, conflicts: Dict[int, Dict[str, float]], 
                                     sim_period: Tuple[int, int] = None) -> bool:
        """
        Validate temporal consistency of conflicts.
        
        Args:
            conflicts: Dictionary of conflict data
            sim_period: Optional simulation period (start_day, end_day)
            
        Returns:
            True if temporally consistent, False otherwise
        """
        if not conflicts:
            self.logger.warning("No conflicts found in scenario")
            return True
        
        days = list(conflicts.keys())
        
        # Check for negative days
        if any(day < 0 for day in days):
            self.logger.error("Found negative days in conflicts")
            return False
        
        # Check simulation period consistency if provided
        if sim_period:
            start_day, end_day = sim_period
            
            if any(day < start_day or day > end_day for day in days):
                self.logger.error(f"Conflicts outside simulation period [{start_day}, {end_day}]")
                return False
        
        # Check for reasonable day progression (no huge gaps)
        sorted_days = sorted(days)
        max_gap = 30  # Maximum allowed gap between conflict days
        
        for i in range(1, len(sorted_days)):
            gap = sorted_days[i] - sorted_days[i-1]
            if gap > max_gap:
                self.logger.warning(f"Large gap ({gap} days) between conflicts at days {sorted_days[i-1]} and {sorted_days[i]}")
        
        return True
    
    def _validate_location_consistency(self, conflicts: Dict[int, Dict[str, float]]) -> bool:
        """
        Validate that all conflict locations exist in topology.
        
        Args:
            conflicts: Dictionary of conflict data
            
        Returns:
            True if locations are consistent, False otherwise
        """
        topology_locations = set(self.location_names)
        
        for day, day_conflicts in conflicts.items():
            for location in day_conflicts.keys():
                if location not in topology_locations:
                    self.logger.error(f"Unknown location '{location}' in conflicts at day {day}")
                    return False
        
        return True
    
    def _validate_intensity_ranges(self, conflicts: Dict[int, Dict[str, float]]) -> bool:
        """
        Validate that conflict intensities are within valid ranges.
        
        Args:
            conflicts: Dictionary of conflict data
            
        Returns:
            True if intensities are valid, False otherwise
        """
        for day, day_conflicts in conflicts.items():
            for location, intensity in day_conflicts.items():
                if not isinstance(intensity, (int, float)):
                    self.logger.error(f"Non-numeric intensity at day {day}, location {location}: {intensity}")
                    return False
                
                if not (0 <= intensity <= 1):
                    self.logger.error(f"Invalid intensity range at day {day}, location {location}: {intensity}")
                    return False
        
        return True


class SpikeConflictGenerator(ConflictScenarioGenerator):
    """Concrete implementation for spike conflict scenarios."""
    
    def generate_spike_conflict(self, origin: str, start_day: int, 
                               peak_intensity: float, output_dir: str = None) -> str:
        """
        Generate a spike conflict scenario with sudden high-intensity conflict at origin.
        
        This creates a conflict that starts at maximum intensity immediately and
        maintains that level, representing sudden onset conflicts like coups or
        terrorist attacks that trigger immediate System 1 responses.
        
        Args:
            origin: Name of the origin location where conflict starts
            start_day: Day when conflict begins (0-based)
            peak_intensity: Maximum conflict intensity (0.0 to 1.0)
            output_dir: Directory to save conflicts.csv (default: current directory)
            
        Returns:
            Path to generated conflicts.csv file
            
        Raises:
            ValueError: If parameters are invalid
            FileNotFoundError: If origin location doesn't exist in topology
        """
        # Validate parameters
        if origin not in self.location_names:
            raise FileNotFoundError(f"Origin location '{origin}' not found in topology")
        
        if not isinstance(start_day, int) or start_day < 0:
            raise ValueError(f"start_day must be a non-negative integer, got {start_day}")
        
        if not isinstance(peak_intensity, (int, float)) or not (0 <= peak_intensity <= 1):
            raise ValueError(f"peak_intensity must be between 0 and 1, got {peak_intensity}")
        
        # Set default output directory
        if output_dir is None:
            output_dir = "."
        
        # Generate spike conflict pattern
        conflicts = {}
        
        # Spike conflicts start immediately at peak intensity and maintain it
        # This represents sudden onset conflicts that trigger immediate System 1 responses
        spike_duration = 30  # Default duration for spike conflicts
        
        for day in range(start_day, start_day + spike_duration):
            conflicts[day] = {origin: peak_intensity}
        
        # Write conflicts to CSV file
        output_file = os.path.join(output_dir, 'conflicts.csv')
        self._write_conflicts_csv(conflicts, output_file)
        
        # Validate the generated scenario
        if not self.validate_scenario(output_file):
            raise RuntimeError("Generated spike conflict scenario failed validation")
        
        self.logger.info(f"Generated spike conflict scenario: origin={origin}, "
                        f"start_day={start_day}, peak_intensity={peak_intensity}, "
                        f"duration={spike_duration} days")
        
        return output_file
    
    def generate_gradual_conflict(self, origin: str, start_day: int, 
                                 end_day: int, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for SpikeConflictGenerator")
    
    def generate_cascading_conflict(self, origin: str, start_day: int, 
                                   spread_rate: float, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for SpikeConflictGenerator")
    
    def generate_oscillating_conflict(self, origin: str, start_day: int, 
                                     period: int, amplitude: float) -> str:
        raise NotImplementedError("Not applicable for SpikeConflictGenerator")


class GradualConflictGenerator(ConflictScenarioGenerator):
    """Concrete implementation for gradual conflict scenarios."""
    
    def generate_spike_conflict(self, origin: str, start_day: int, 
                               peak_intensity: float) -> str:
        raise NotImplementedError("Not applicable for GradualConflictGenerator")
    
    def generate_gradual_conflict(self, origin: str, start_day: int, 
                                 end_day: int, max_intensity: float, output_dir: str = None) -> str:
        """
        Generate a gradual conflict scenario with linear escalation over time.
        
        This creates a conflict that starts at low intensity and gradually increases
        to maximum intensity, representing escalating tensions that allow for
        System 2 planning and deliberate decision-making.
        
        Args:
            origin: Name of the origin location where conflict starts
            start_day: Day when conflict begins (0-based)
            end_day: Day when conflict reaches maximum intensity
            max_intensity: Maximum conflict intensity (0.0 to 1.0)
            output_dir: Directory to save conflicts.csv (default: current directory)
            
        Returns:
            Path to generated conflicts.csv file
            
        Raises:
            ValueError: If parameters are invalid
            FileNotFoundError: If origin location doesn't exist in topology
        """
        # Validate parameters
        if origin not in self.location_names:
            raise FileNotFoundError(f"Origin location '{origin}' not found in topology")
        
        if not isinstance(start_day, int) or start_day < 0:
            raise ValueError(f"start_day must be a non-negative integer, got {start_day}")
        
        if not isinstance(end_day, int) or end_day <= start_day:
            raise ValueError(f"end_day must be greater than start_day, got start_day={start_day}, end_day={end_day}")
        
        if not isinstance(max_intensity, (int, float)) or not (0 <= max_intensity <= 1):
            raise ValueError(f"max_intensity must be between 0 and 1, got {max_intensity}")
        
        # Set default output directory
        if output_dir is None:
            output_dir = "."
        
        # Generate gradual conflict pattern
        conflicts = {}
        
        # Calculate escalation parameters
        escalation_period = end_day - start_day
        min_intensity = 0.1  # Start with minimal conflict
        
        # Linear escalation from min_intensity to max_intensity
        for day in range(start_day, end_day + 1):
            # Calculate progress through escalation (0.0 to 1.0)
            progress = (day - start_day) / escalation_period
            
            # Linear interpolation between min and max intensity
            intensity = min_intensity + (max_intensity - min_intensity) * progress
            
            conflicts[day] = {origin: intensity}
        
        # Maintain peak intensity for a period after reaching maximum
        peak_duration = min(30, escalation_period // 2)  # Peak duration based on escalation period
        
        for day in range(end_day + 1, end_day + 1 + peak_duration):
            conflicts[day] = {origin: max_intensity}
        
        # Write conflicts to CSV file
        output_file = os.path.join(output_dir, 'conflicts.csv')
        self._write_conflicts_csv(conflicts, output_file)
        
        # Validate the generated scenario
        if not self.validate_scenario(output_file):
            raise RuntimeError("Generated gradual conflict scenario failed validation")
        
        self.logger.info(f"Generated gradual conflict scenario: origin={origin}, "
                        f"start_day={start_day}, end_day={end_day}, max_intensity={max_intensity}, "
                        f"escalation_period={escalation_period} days, peak_duration={peak_duration} days")
        
        return output_file
    
    def generate_cascading_conflict(self, origin: str, start_day: int, 
                                   spread_rate: float, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for GradualConflictGenerator")
    
    def generate_oscillating_conflict(self, origin: str, start_day: int, 
                                     period: int, amplitude: float) -> str:
        raise NotImplementedError("Not applicable for GradualConflictGenerator")


class CascadingConflictGenerator(ConflictScenarioGenerator):
    """Concrete implementation for cascading conflict scenarios."""
    
    def generate_spike_conflict(self, origin: str, start_day: int, 
                               peak_intensity: float) -> str:
        raise NotImplementedError("Not applicable for CascadingConflictGenerator")
    
    def generate_gradual_conflict(self, origin: str, start_day: int, 
                                 end_day: int, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for CascadingConflictGenerator")
    
    def generate_cascading_conflict(self, origin: str, start_day: int, 
                                   spread_rate: float, max_intensity: float, 
                                   routes_file: str = None, output_dir: str = None) -> str:
        """
        Generate a cascading conflict scenario that spreads through the network.
        
        This creates a conflict that starts at the origin and spreads to connected
        locations based on network topology and spread rate. This tests how
        social connectivity and network effects influence cognitive responses.
        
        Args:
            origin: Name of the origin location where conflict starts
            start_day: Day when conflict begins (0-based)
            spread_rate: Rate of conflict spread (locations per day)
            max_intensity: Maximum conflict intensity (0.0 to 1.0)
            routes_file: Path to routes CSV file (optional, inferred from topology_file)
            output_dir: Directory to save conflicts.csv (default: current directory)
            
        Returns:
            Path to generated conflicts.csv file
            
        Raises:
            ValueError: If parameters are invalid
            FileNotFoundError: If origin location or routes file doesn't exist
        """
        # Validate parameters
        if origin not in self.location_names:
            raise FileNotFoundError(f"Origin location '{origin}' not found in topology")
        
        if not isinstance(start_day, int) or start_day < 0:
            raise ValueError(f"start_day must be a non-negative integer, got {start_day}")
        
        if not isinstance(spread_rate, (int, float)) or spread_rate <= 0:
            raise ValueError(f"spread_rate must be positive, got {spread_rate}")
        
        if not isinstance(max_intensity, (int, float)) or not (0 <= max_intensity <= 1):
            raise ValueError(f"max_intensity must be between 0 and 1, got {max_intensity}")
        
        # Set default routes file path
        if routes_file is None:
            routes_file = self.topology_file.replace('locations.csv', 'routes.csv')
        
        # Set default output directory
        if output_dir is None:
            output_dir = "."
        
        # Load network topology
        network = self._build_network_graph(routes_file)
        
        # Generate cascading conflict pattern
        conflicts = {}
        
        # Track which locations have been affected and when
        affected_locations = {origin: start_day}
        conflict_queue = [(start_day, origin, max_intensity)]
        
        # Simulate conflict spread
        while conflict_queue:
            day, location, intensity = conflict_queue.pop(0)
            
            # Add conflict for this day and location
            if day not in conflicts:
                conflicts[day] = {}
            conflicts[day][location] = intensity
            
            # Find neighbors to spread to
            if location in network:
                neighbors = network[location]
                
                # Calculate spread timing based on spread_rate
                spread_delay = max(1, int(1.0 / spread_rate))  # Days between spreads
                next_spread_day = day + spread_delay
                
                for neighbor, distance in neighbors:
                    # Only spread to unaffected locations
                    if neighbor not in affected_locations:
                        # Calculate intensity decay based on distance
                        distance_decay = min(0.9, 1.0 - (distance / 1000.0))  # Decay over distance
                        neighbor_intensity = intensity * distance_decay
                        
                        # Only spread if intensity is still significant
                        if neighbor_intensity >= 0.1:
                            affected_locations[neighbor] = next_spread_day
                            conflict_queue.append((next_spread_day, neighbor, neighbor_intensity))
        
        # Extend conflicts for persistence (conflicts don't immediately disappear)
        extended_conflicts = {}
        persistence_duration = 20  # Days conflicts persist after initial spread
        
        for day, day_conflicts in conflicts.items():
            for location, intensity in day_conflicts.items():
                # Add conflicts for persistence period
                for persist_day in range(day, day + persistence_duration):
                    if persist_day not in extended_conflicts:
                        extended_conflicts[persist_day] = {}
                    
                    # Gradually decay intensity over time
                    decay_factor = max(0.1, 1.0 - (persist_day - day) / persistence_duration)
                    decayed_intensity = intensity * decay_factor
                    
                    # Keep the highest intensity if multiple conflicts affect same location
                    if location not in extended_conflicts[persist_day]:
                        extended_conflicts[persist_day][location] = decayed_intensity
                    else:
                        extended_conflicts[persist_day][location] = max(
                            extended_conflicts[persist_day][location], 
                            decayed_intensity
                        )
        
        # Write conflicts to CSV file
        output_file = os.path.join(output_dir, 'conflicts.csv')
        self._write_conflicts_csv(extended_conflicts, output_file)
        
        # Validate the generated scenario
        if not self.validate_scenario(output_file):
            raise RuntimeError("Generated cascading conflict scenario failed validation")
        
        affected_count = len(affected_locations)
        total_days = max(extended_conflicts.keys()) - start_day + 1 if extended_conflicts else 0
        
        self.logger.info(f"Generated cascading conflict scenario: origin={origin}, "
                        f"start_day={start_day}, spread_rate={spread_rate}, max_intensity={max_intensity}, "
                        f"affected_locations={affected_count}, total_duration={total_days} days")
        
        return output_file
    
    def _build_network_graph(self, routes_file: str) -> Dict[str, List[Tuple[str, float]]]:
        """
        Build network graph from routes file.
        
        Args:
            routes_file: Path to routes CSV file
            
        Returns:
            Dictionary mapping locations to list of (neighbor, distance) tuples
        """
        network = {}
        
        try:
            if not os.path.exists(routes_file):
                self.logger.warning(f"Routes file not found: {routes_file}, using complete graph")
                # Create complete graph with default distances
                for i, loc1 in enumerate(self.location_names):
                    network[loc1] = []
                    for j, loc2 in enumerate(self.location_names):
                        if i != j:
                            network[loc1].append((loc2, 100.0))  # Default distance
                return network
            
            routes = self.csv_utils.read_routes_csv(routes_file)
            
            # Initialize network
            for location in self.location_names:
                network[location] = []
            
            # Add routes (bidirectional)
            for route in routes:
                name1 = route['name1']
                name2 = route['name2']
                distance = float(route['distance'])
                
                if name1 in network:
                    network[name1].append((name2, distance))
                if name2 in network:
                    network[name2].append((name1, distance))
            
            self.logger.info(f"Built network graph with {len(routes)} routes")
            
        except Exception as e:
            self.logger.error(f"Failed to build network graph: {e}")
            # Fallback to complete graph
            network = {}
            for i, loc1 in enumerate(self.location_names):
                network[loc1] = []
                for j, loc2 in enumerate(self.location_names):
                    if i != j:
                        network[loc1].append((loc2, 100.0))
        
        return network
    
    def generate_oscillating_conflict(self, origin: str, start_day: int, 
                                     period: int, amplitude: float) -> str:
        raise NotImplementedError("Not applicable for CascadingConflictGenerator")


class OscillatingConflictGenerator(ConflictScenarioGenerator):
    """Concrete implementation for oscillating conflict scenarios."""
    
    def generate_spike_conflict(self, origin: str, start_day: int, 
                               peak_intensity: float) -> str:
        raise NotImplementedError("Not applicable for OscillatingConflictGenerator")
    
    def generate_gradual_conflict(self, origin: str, start_day: int, 
                                 end_day: int, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for OscillatingConflictGenerator")
    
    def generate_cascading_conflict(self, origin: str, start_day: int, 
                                   spread_rate: float, max_intensity: float) -> str:
        raise NotImplementedError("Not applicable for OscillatingConflictGenerator")
    
    def generate_oscillating_conflict(self, origin: str, start_day: int, 
                                     period: int, amplitude: float, 
                                     baseline: float = 0.2, duration: int = 100,
                                     phase: float = 0.0, output_dir: str = None) -> str:
        """
        Generate an oscillating conflict scenario with cyclical intensity variations.
        
        This creates a conflict that oscillates between baseline and peak intensity
        in a sinusoidal pattern, representing cyclical conflicts like seasonal
        violence or recurring political tensions that test adaptive responses.
        
        Args:
            origin: Name of the origin location where conflict oscillates
            start_day: Day when conflict begins (0-based)
            period: Period of oscillation in days
            amplitude: Amplitude of oscillation (peak intensity above baseline)
            baseline: Baseline conflict intensity (0.0 to 1.0)
            duration: Total duration of oscillating conflict in days
            phase: Phase shift in radians (0.0 = start at baseline)
            output_dir: Directory to save conflicts.csv (default: current directory)
            
        Returns:
            Path to generated conflicts.csv file
            
        Raises:
            ValueError: If parameters are invalid
            FileNotFoundError: If origin location doesn't exist in topology
        """
        # Validate parameters
        if origin not in self.location_names:
            raise FileNotFoundError(f"Origin location '{origin}' not found in topology")
        
        if not isinstance(start_day, int) or start_day < 0:
            raise ValueError(f"start_day must be a non-negative integer, got {start_day}")
        
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"period must be a positive integer, got {period}")
        
        if not isinstance(amplitude, (int, float)) or amplitude <= 0:
            raise ValueError(f"amplitude must be positive, got {amplitude}")
        
        if not isinstance(baseline, (int, float)) or not (0 <= baseline <= 1):
            raise ValueError(f"baseline must be between 0 and 1, got {baseline}")
        
        if baseline + amplitude > 1.0:
            raise ValueError(f"baseline + amplitude must not exceed 1.0, got {baseline + amplitude}")
        
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError(f"duration must be a positive integer, got {duration}")
        
        # Set default output directory
        if output_dir is None:
            output_dir = "."
        
        # Generate oscillating conflict pattern
        conflicts = {}
        
        # Generate sinusoidal oscillation
        for day in range(start_day, start_day + duration):
            # Calculate oscillation progress
            day_in_cycle = day - start_day
            
            # Sinusoidal function: baseline + amplitude * sin(2π * day / period + phase)
            angle = 2 * math.pi * day_in_cycle / period + phase
            intensity = baseline + amplitude * math.sin(angle)
            
            # Ensure intensity stays within valid bounds
            intensity = max(0.0, min(1.0, intensity))
            
            # Only add conflicts if intensity is above minimum threshold
            if intensity >= 0.05:  # Minimum threshold to avoid noise
                conflicts[day] = {origin: intensity}
        
        # Write conflicts to CSV file
        output_file = os.path.join(output_dir, 'conflicts.csv')
        self._write_conflicts_csv(conflicts, output_file)
        
        # Validate the generated scenario
        if not self.validate_scenario(output_file):
            raise RuntimeError("Generated oscillating conflict scenario failed validation")
        
        # Calculate statistics for logging
        intensities = [conflicts[day][origin] for day in conflicts.keys()]
        min_intensity = min(intensities) if intensities else 0
        max_intensity = max(intensities) if intensities else 0
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0
        
        self.logger.info(f"Generated oscillating conflict scenario: origin={origin}, "
                        f"start_day={start_day}, period={period}, amplitude={amplitude}, "
                        f"baseline={baseline}, duration={duration}, "
                        f"intensity_range=[{min_intensity:.3f}, {max_intensity:.3f}], "
                        f"avg_intensity={avg_intensity:.3f}")
        
        return output_file