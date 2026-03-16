"""
Shared Utilities Module

Common functions for CSV I/O, validation, logging, and other utilities
used across the flee_dual_process framework.
"""

import csv
import os
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import pandas as pd


class CSVUtils:
    """
    Utilities for CSV file input/output operations in Flee format.
    """
    
    @staticmethod
    def write_locations_csv(locations: List[Dict[str, Any]], filepath: str) -> None:
        """
        Write locations data to CSV file in Flee format.
        
        Expected Flee locations.csv format:
        #name,region,country,lat,lon,location_type,conflict_date,pop/cap
        
        Args:
            locations: List of location dictionaries
            filepath: Output file path
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        fieldnames = ['name', 'region', 'country', 'lat', 'lon', 
                     'location_type', 'conflict_date', 'pop/cap']
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header with # prefix for Flee compatibility
            csvfile.write('#' + ','.join(fieldnames) + '\n')
            
            # Write data rows
            for location in locations:
                writer.writerow(location)
    
    @staticmethod
    def write_routes_csv(routes: List[Dict[str, Any]], filepath: str) -> None:
        """
        Write routes data to CSV file in Flee format.
        
        Expected Flee routes.csv format:
        #name1,name2,distance,forced_redirection
        
        Args:
            routes: List of route dictionaries
            filepath: Output file path
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        fieldnames = ['name1', 'name2', 'distance', 'forced_redirection']
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header with # prefix for Flee compatibility
            csvfile.write('#' + ','.join(fieldnames) + '\n')
            
            # Write data rows
            for route in routes:
                writer.writerow(route)
    
    @staticmethod
    def write_conflicts_csv(conflicts: Dict[int, Dict[str, float]], location_names: List[str], filepath: str) -> None:
        """
        Write conflicts data to CSV file in Flee matrix format.
        
        Expected Flee conflicts.csv format:
        #Day, Location1, Location2, ...
        0, intensity1, intensity2, ...
        1, intensity1, intensity2, ...
        
        Args:
            conflicts: Dictionary mapping days to location conflicts
            location_names: List of all location names for consistent ordering
            filepath: Output file path
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Get all days and sort them
        days = sorted(conflicts.keys()) if conflicts else []
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header: #Day, location1, location2, ...
            header = ['#Day'] + location_names
            writer.writerow(header)
            
            # Write data rows
            for day in days:
                row = [day]
                day_conflicts = conflicts.get(day, {})
                
                for location in location_names:
                    intensity = day_conflicts.get(location, 0.0)
                    row.append(intensity)
                
                writer.writerow(row)
    
    @staticmethod
    def read_locations_csv(filepath: str) -> List[Dict[str, Any]]:
        """
        Read locations data from CSV file.
        
        Args:
            filepath: Input file path
            
        Returns:
            List of location dictionaries
        """
        locations = []
        
        with open(filepath, 'r') as csvfile:
            # Read first line to check for header
            first_line = csvfile.readline().strip()
            
            if first_line.startswith('#'):
                # Remove # and use as fieldnames
                fieldnames = first_line[1:].split(',')
                reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            else:
                # No header, reset and use DictReader with default behavior
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
            
            for row in reader:
                locations.append(row)
        
        return locations
    
    @staticmethod
    def read_routes_csv(filepath: str) -> List[Dict[str, Any]]:
        """
        Read routes data from CSV file.
        
        Args:
            filepath: Input file path
            
        Returns:
            List of route dictionaries
        """
        routes = []
        
        with open(filepath, 'r') as csvfile:
            # Read first line to check for header
            first_line = csvfile.readline().strip()
            
            if first_line.startswith('#'):
                # Remove # and use as fieldnames
                fieldnames = first_line[1:].split(',')
                reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            else:
                # No header, reset and use DictReader with default behavior
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
            
            for row in reader:
                routes.append(row)
        
        return routes
    
    @staticmethod
    def read_conflicts_csv(filepath: str) -> Dict[int, Dict[str, float]]:
        """
        Read conflicts data from CSV file in Flee matrix format.
        
        Args:
            filepath: Input file path
            
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


class ValidationUtils:
    """
    Utilities for validating experimental configurations and data files.
    """
    
    def __init__(self):
        self.logger = LoggingUtils().get_logger('ValidationUtils')
    
    def validate_topology(self, locations_file: str, routes_file: str) -> bool:
        """
        Validate topology for connectivity and consistency.
        
        Args:
            locations_file: Path to locations CSV file
            routes_file: Path to routes CSV file
            
        Returns:
            True if topology is valid, False otherwise
        """
        try:
            # Check if files exist
            if not os.path.exists(locations_file):
                self.logger.error(f"Locations file not found: {locations_file}")
                return False
            
            if not os.path.exists(routes_file):
                self.logger.error(f"Routes file not found: {routes_file}")
                return False
            
            # Load data
            locations = CSVUtils.read_locations_csv(locations_file)
            routes = CSVUtils.read_routes_csv(routes_file)
            
            # Validate locations
            if not self._validate_locations(locations):
                return False
            
            # Validate routes
            if not self._validate_routes(routes, locations):
                return False
            
            # Check connectivity
            if not self._check_connectivity(locations, routes):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Topology validation failed: {e}")
            return False
    
    def _validate_locations(self, locations: List[Dict[str, Any]]) -> bool:
        """Validate locations data."""
        required_fields = ['name', 'lat', 'lon', 'location_type', 'pop/cap']
        
        for i, location in enumerate(locations):
            # Check required fields
            for field in required_fields:
                if field not in location or not location[field]:
                    self.logger.error(f"Location {i}: Missing required field '{field}'")
                    return False
            
            # Validate coordinates
            try:
                lat = float(location['lat'])
                lon = float(location['lon'])
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    self.logger.error(f"Location {location['name']}: Invalid coordinates")
                    return False
            except ValueError:
                self.logger.error(f"Location {location['name']}: Invalid coordinate format")
                return False
            
            # Validate population/capacity
            try:
                pop_cap = float(location['pop/cap'])
                if pop_cap < 0:
                    self.logger.error(f"Location {location['name']}: Negative population/capacity")
                    return False
            except ValueError:
                self.logger.error(f"Location {location['name']}: Invalid population/capacity format")
                return False
        
        return True
    
    def _validate_routes(self, routes: List[Dict[str, Any]], 
                        locations: List[Dict[str, Any]]) -> bool:
        """Validate routes data."""
        location_names = {loc['name'] for loc in locations}
        
        for i, route in enumerate(routes):
            # Check required fields
            required_fields = ['name1', 'name2', 'distance']
            for field in required_fields:
                if field not in route or not route[field]:
                    self.logger.error(f"Route {i}: Missing required field '{field}'")
                    return False
            
            # Check if locations exist
            if route['name1'] not in location_names:
                self.logger.error(f"Route {i}: Unknown location '{route['name1']}'")
                return False
            
            if route['name2'] not in location_names:
                self.logger.error(f"Route {i}: Unknown location '{route['name2']}'")
                return False
            
            # Validate distance
            try:
                distance = float(route['distance'])
                if distance <= 0:
                    self.logger.error(f"Route {i}: Non-positive distance")
                    return False
            except ValueError:
                self.logger.error(f"Route {i}: Invalid distance format")
                return False
        
        return True
    
    def _check_connectivity(self, locations: List[Dict[str, Any]], 
                          routes: List[Dict[str, Any]]) -> bool:
        """Check if topology is connected."""
        if not locations:
            return True
        
        # Build adjacency list
        graph = {loc['name']: set() for loc in locations}
        for route in routes:
            graph[route['name1']].add(route['name2'])
            graph[route['name2']].add(route['name1'])
        
        # Check connectivity using DFS
        visited = set()
        start_node = next(iter(graph.keys()))
        
        def dfs(node):
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(start_node)
        
        if len(visited) != len(locations):
            self.logger.error("Topology is not connected")
            return False
        
        return True
    
    def validate_scenario(self, conflicts_file: str, topology_file: str) -> bool:
        """
        Validate conflict scenario for temporal consistency.
        
        Args:
            conflicts_file: Path to conflicts CSV file
            topology_file: Path to topology locations file
            
        Returns:
            True if scenario is valid, False otherwise
        """
        try:
            # Check if files exist
            if not os.path.exists(conflicts_file):
                self.logger.error(f"Conflicts file not found: {conflicts_file}")
                return False
            
            # Load data
            conflicts = CSVUtils.read_conflicts_csv(conflicts_file)
            locations = CSVUtils.read_locations_csv(topology_file)
            location_names = {loc['name'] for loc in locations}
            
            # Validate conflicts
            for day, location_conflicts in conflicts.items():
                if day < 0:
                    self.logger.error(f"Negative day in conflicts: {day}")
                    return False
                
                for location, intensity in location_conflicts.items():
                    if location not in location_names:
                        self.logger.error(f"Unknown location in conflicts: {location}")
                        return False
                    
                    if not (0 <= intensity <= 1):
                        self.logger.error(f"Invalid conflict intensity: {intensity}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Scenario validation failed: {e}")
            return False
    
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate experimental configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check for move_rules section
            if 'move_rules' not in config:
                self.logger.error("Missing required section: move_rules")
                return False
            
            move_rules = config['move_rules']
            
            # Check required parameters in move_rules
            required_params = ['TwoSystemDecisionMaking', 'awareness_level']
            for param in required_params:
                if param not in move_rules:
                    self.logger.error(f"Missing required parameter: move_rules.{param}")
                    return False
            
            # Validate parameter ranges
            if 'awareness_level' in move_rules:
                awareness = move_rules['awareness_level']
                if not isinstance(awareness, int) or not (1 <= awareness <= 3):
                    self.logger.error(f"Invalid move_rules.awareness_level: {awareness}")
                    return False
            
            if 'average_social_connectivity' in move_rules:
                connectivity = move_rules['average_social_connectivity']
                if not isinstance(connectivity, (int, float)) or connectivity < 0:
                    self.logger.error(f"Invalid move_rules.average_social_connectivity: {connectivity}")
                    return False
            
            if 'conflict_threshold' in move_rules:
                threshold = move_rules['conflict_threshold']
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                    self.logger.error(f"Invalid move_rules.conflict_threshold: {threshold}")
                    return False
            
            if 'weight_softening' in move_rules:
                weight = move_rules['weight_softening']
                if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
                    self.logger.error(f"Invalid move_rules.weight_softening: {weight}")
                    return False
            
            if 'recovery_period_max' in move_rules:
                period = move_rules['recovery_period_max']
                if not isinstance(period, int) or period < 1:
                    self.logger.error(f"Invalid move_rules.recovery_period_max: {period}")
                    return False
            
            if 'TwoSystemDecisionMaking' in move_rules:
                decision_making = move_rules['TwoSystemDecisionMaking']
                if not isinstance(decision_making, bool):
                    self.logger.error(f"Invalid move_rules.TwoSystemDecisionMaking: {decision_making}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False


class LoggingUtils:
    """
    Utilities for logging and progress tracking.
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize logging utilities.
        
        Args:
            log_level: Logging level (default: INFO)
        """
        self.log_level = log_level
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        logger = self.get_logger('flee_dual_process')
        logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log warning message."""
        logger = self.get_logger('flee_dual_process')
        logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log error message."""
        logger = self.get_logger('flee_dual_process')
        logger.error(message)
    
    def log_debug(self, message: str) -> None:
        """Log debug message."""
        logger = self.get_logger('flee_dual_process')
        logger.debug(message)
    
    def create_experiment_log(self, experiment_id: str, log_dir: str) -> str:
        """
        Create experiment-specific log file.
        
        Args:
            experiment_id: Experiment identifier
            log_dir: Directory for log files
            
        Returns:
            Path to created log file
        """
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"{experiment_id}_{timestamp}.log")
        
        # Create file handler for experiment
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to root logger
        logger = self.get_logger(experiment_id)
        logger.addHandler(file_handler)
        
        return log_file


class FileUtils:
    """
    Utilities for file and directory operations.
    """
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            path: Directory path
        """
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def copy_file(src: str, dst: str) -> None:
        """
        Copy file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
        """
        import shutil
        FileUtils.ensure_directory(os.path.dirname(dst))
        shutil.copy2(src, dst)
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """
        List files in directory matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (default: all files)
            
        Returns:
            List of matching file paths
        """
        import glob
        return glob.glob(os.path.join(directory, pattern))
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in bytes
        """
        return os.path.getsize(filepath)
    
    @staticmethod
    def get_file_timestamp(filepath: str) -> datetime:
        """
        Get file modification timestamp.
        
        Args:
            filepath: Path to file
            
        Returns:
            File modification datetime
        """
        timestamp = os.path.getmtime(filepath)
        return datetime.fromtimestamp(timestamp)