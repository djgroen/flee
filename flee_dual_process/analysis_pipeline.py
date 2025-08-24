"""
Analysis Pipeline System for Dual Process Experiments

This module provides comprehensive analysis capabilities for dual-process experiments,
including movement metrics, cognitive state analysis, and comparative statistics.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass
from scipy import stats
from scipy.stats import mannwhitneyu, kruskal, chi2_contingency
import warnings

try:
    from .utils import LoggingUtils, ValidationUtils, FileUtils, CSVUtils
except ImportError:
    from utils import LoggingUtils, ValidationUtils, FileUtils, CSVUtils


@dataclass
class ExperimentResults:
    """Data class for storing experiment analysis results."""
    experiment_id: str
    metrics: Dict[str, Any]
    cognitive_states: Optional[pd.DataFrame] = None
    decision_log: Optional[pd.DataFrame] = None
    movement_data: Optional[pd.DataFrame] = None
    summary_statistics: Optional[Dict[str, Any]] = None


class AnalysisPipeline:
    """
    Base analysis pipeline class with modular metric calculation methods.
    
    This class processes experimental outputs and generates comprehensive
    insights about dual-process decision-making in refugee movement simulations.
    """
    
    def __init__(self, results_directory: str, output_directory: str = None):
        """
        Initialize analysis pipeline.
        
        Args:
            results_directory: Directory containing experiment results
            output_directory: Directory for analysis outputs (default: results_directory/analysis)
        """
        self.results_directory = Path(results_directory)
        self.output_directory = Path(output_directory) if output_directory else self.results_directory / "analysis"
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        self.csv_utils = CSVUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('AnalysisPipeline')
        
        # Ensure output directory exists
        self.file_utils.ensure_directory(str(self.output_directory))
        
        # Cache for loaded data
        self._data_cache = {}
        
        self.logger.info(f"AnalysisPipeline initialized with results_directory: {self.results_directory}")
        self.logger.info(f"Analysis outputs will be saved to: {self.output_directory}")
    
    def load_experiment_data(self, experiment_dir: str) -> ExperimentResults:
        """
        Load and preprocess experiment output data.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            ExperimentResults object with loaded data
            
        Raises:
            FileNotFoundError: If required output files are missing
            ValueError: If data format is invalid
        """
        experiment_path = Path(experiment_dir)
        experiment_id = experiment_path.name
        
        self.logger.info(f"Loading experiment data for: {experiment_id}")
        
        # Check if data is cached
        if experiment_id in self._data_cache:
            self.logger.debug(f"Using cached data for experiment: {experiment_id}")
            return self._data_cache[experiment_id]
        
        try:
            # Initialize results object
            results = ExperimentResults(
                experiment_id=experiment_id,
                metrics={}
            )
            
            # Load basic movement data (out.csv files)
            movement_data = self._load_movement_data(experiment_path)
            results.movement_data = movement_data
            
            # Load cognitive states data if available
            cognitive_states = self._load_cognitive_states_data(experiment_path)
            results.cognitive_states = cognitive_states
            
            # Load decision log data if available
            decision_log = self._load_decision_log_data(experiment_path)
            results.decision_log = decision_log
            
            # Load experiment metadata
            metadata = self._load_experiment_metadata(experiment_path)
            results.metrics['metadata'] = metadata
            
            # Validate loaded data
            self._validate_experiment_data(results)
            
            # Cache results
            self._data_cache[experiment_id] = results
            
            self.logger.info(f"Successfully loaded experiment data for: {experiment_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to load experiment data for {experiment_id}: {e}")
            raise
    
    def _load_movement_data(self, experiment_path: Path) -> pd.DataFrame:
        """
        Load movement data from Flee output files.
        
        Args:
            experiment_path: Path to experiment directory
            
        Returns:
            DataFrame with movement data
        """
        output_dir = experiment_path / "output"
        
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        # Look for out.csv files (standard Flee output)
        out_files = list(output_dir.glob("out.csv*"))
        
        if not out_files:
            self.logger.warning(f"No out.csv files found in {output_dir}")
            return pd.DataFrame()
        
        # Load and combine all out.csv files
        movement_data_frames = []
        
        for out_file in out_files:
            try:
                # Determine if file has header
                with open(out_file, 'r') as f:
                    first_line = f.readline().strip()
                
                if first_line.startswith('#'):
                    # Has header with #, extract column names and read data
                    column_names = first_line[1:].strip().split(',')
                    df = pd.read_csv(out_file, skiprows=1, names=column_names)
                else:
                    # No header, use standard Flee column names
                    df = pd.read_csv(out_file, names=['day', 'location', 'refugees', 'total_refugees'])
                
                # Add source file information
                df['source_file'] = out_file.name
                movement_data_frames.append(df)
                
            except Exception as e:
                self.logger.warning(f"Failed to load {out_file}: {e}")
                continue
        
        if movement_data_frames:
            movement_data = pd.concat(movement_data_frames, ignore_index=True)
            self.logger.debug(f"Loaded movement data: {len(movement_data)} rows")
            return movement_data
        else:
            return pd.DataFrame()
    
    def _load_cognitive_states_data(self, experiment_path: Path) -> Optional[pd.DataFrame]:
        """
        Load cognitive states data from experiment outputs.
        
        Args:
            experiment_path: Path to experiment directory
            
        Returns:
            DataFrame with cognitive states data or None if not available
        """
        output_dir = experiment_path / "output"
        
        # Look for cognitive_states.out files
        cognitive_files = list(output_dir.glob("cognitive_states.out*"))
        
        if not cognitive_files:
            self.logger.debug(f"No cognitive states files found in {output_dir}")
            return None
        
        # Load and combine all cognitive states files
        cognitive_data_frames = []
        
        for cognitive_file in cognitive_files:
            try:
                # Check for header format
                with open(cognitive_file, 'r') as f:
                    first_line = f.readline().strip()
                
                if first_line.startswith('#'):
                    # Has header with #, extract column names and read data
                    column_names = first_line[1:].strip().split(',')
                    df = pd.read_csv(cognitive_file, skiprows=1, names=column_names)
                else:
                    # No header, read with pandas default
                    df = pd.read_csv(cognitive_file)
                
                # Add source file information
                df['source_file'] = cognitive_file.name
                cognitive_data_frames.append(df)
                
            except Exception as e:
                self.logger.warning(f"Failed to load {cognitive_file}: {e}")
                continue
        
        if cognitive_data_frames:
            cognitive_data = pd.concat(cognitive_data_frames, ignore_index=True)
            self.logger.debug(f"Loaded cognitive states data: {len(cognitive_data)} rows")
            return cognitive_data
        else:
            return None
    
    def _load_decision_log_data(self, experiment_path: Path) -> Optional[pd.DataFrame]:
        """
        Load decision log data from experiment outputs.
        
        Args:
            experiment_path: Path to experiment directory
            
        Returns:
            DataFrame with decision log data or None if not available
        """
        output_dir = experiment_path / "output"
        
        # Look for decision_log.out files
        decision_files = list(output_dir.glob("decision_log.out*"))
        
        if not decision_files:
            self.logger.debug(f"No decision log files found in {output_dir}")
            return None
        
        # Load and combine all decision log files
        decision_data_frames = []
        
        for decision_file in decision_files:
            try:
                # Check for header format
                with open(decision_file, 'r') as f:
                    first_line = f.readline().strip()
                
                if first_line.startswith('#'):
                    # Has header with #, extract column names and read data
                    column_names = first_line[1:].strip().split(',')
                    df = pd.read_csv(decision_file, skiprows=1, names=column_names)
                else:
                    # No header, read with pandas default
                    df = pd.read_csv(decision_file)
                
                # Add source file information
                df['source_file'] = decision_file.name
                decision_data_frames.append(df)
                
            except Exception as e:
                self.logger.warning(f"Failed to load {decision_file}: {e}")
                continue
        
        if decision_data_frames:
            decision_data = pd.concat(decision_data_frames, ignore_index=True)
            self.logger.debug(f"Loaded decision log data: {len(decision_data)} rows")
            return decision_data
        else:
            return None
    
    def _load_experiment_metadata(self, experiment_path: Path) -> Dict[str, Any]:
        """
        Load experiment metadata from metadata files.
        
        Args:
            experiment_path: Path to experiment directory
            
        Returns:
            Dictionary with experiment metadata
        """
        metadata_dir = experiment_path / "metadata"
        metadata_file = metadata_dir / "experiment_metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                self.logger.debug(f"Loaded experiment metadata from {metadata_file}")
                return metadata
            except Exception as e:
                self.logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
        
        # Return basic metadata if file not found
        return {
            'experiment_id': experiment_path.name,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'inferred'
        }
    
    def _validate_experiment_data(self, results: ExperimentResults) -> None:
        """
        Validate loaded experiment data for completeness and format.
        
        Args:
            results: ExperimentResults object to validate
            
        Raises:
            ValueError: If data validation fails
        """
        experiment_id = results.experiment_id
        
        # Check if we have at least movement data
        if results.movement_data is None or results.movement_data.empty:
            raise ValueError(f"No movement data found for experiment {experiment_id}")
        
        # Validate movement data columns
        required_movement_cols = ['day', 'location']
        movement_cols = results.movement_data.columns.tolist()
        
        missing_cols = [col for col in required_movement_cols if col not in movement_cols]
        if missing_cols:
            self.logger.warning(f"Missing movement data columns for {experiment_id}: {missing_cols}")
        
        # Validate cognitive states data if present
        if results.cognitive_states is not None:
            required_cognitive_cols = ['day', 'agent_id', 'cognitive_state']
            cognitive_cols = results.cognitive_states.columns.tolist()
            
            missing_cols = [col for col in required_cognitive_cols if col not in cognitive_cols]
            if missing_cols:
                self.logger.warning(f"Missing cognitive states columns for {experiment_id}: {missing_cols}")
        
        # Validate decision log data if present
        if results.decision_log is not None:
            required_decision_cols = ['day', 'agent_id', 'decision_type']
            decision_cols = results.decision_log.columns.tolist()
            
            missing_cols = [col for col in required_decision_cols if col not in decision_cols]
            if missing_cols:
                self.logger.warning(f"Missing decision log columns for {experiment_id}: {missing_cols}")
        
        self.logger.debug(f"Data validation completed for experiment {experiment_id}")
    
    def process_experiment(self, experiment_dir: str) -> ExperimentResults:
        """
        Process a single experiment and calculate all metrics.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            ExperimentResults with calculated metrics
        """
        self.logger.info(f"Processing experiment: {experiment_dir}")
        
        # Load experiment data
        results = self.load_experiment_data(experiment_dir)
        
        # Calculate movement metrics
        movement_metrics = self.calculate_movement_metrics(experiment_dir)
        results.metrics.update(movement_metrics)
        
        # Calculate cognitive state analysis if data available
        if results.cognitive_states is not None:
            cognitive_metrics = self.analyze_cognitive_transitions(experiment_dir)
            results.metrics.update(cognitive_metrics)
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_statistics(results)
        results.summary_statistics = summary_stats
        
        # Save processed results
        self._save_experiment_results(results)
        
        self.logger.info(f"Completed processing experiment: {results.experiment_id}")
        return results
    
    def _calculate_summary_statistics(self, results: ExperimentResults) -> Dict[str, Any]:
        """
        Calculate summary statistics for experiment results.
        
        Args:
            results: ExperimentResults object
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'experiment_id': results.experiment_id,
            'data_availability': {
                'movement_data': results.movement_data is not None and not results.movement_data.empty,
                'cognitive_states': results.cognitive_states is not None and not results.cognitive_states.empty,
                'decision_log': results.decision_log is not None and not results.decision_log.empty
            }
        }
        
        # Movement data summary
        if results.movement_data is not None and not results.movement_data.empty:
            movement_data = results.movement_data
            summary['movement_summary'] = {
                'total_days': movement_data['day'].max() if 'day' in movement_data.columns else 0,
                'total_locations': movement_data['location'].nunique() if 'location' in movement_data.columns else 0,
                'total_records': len(movement_data)
            }
        
        # Cognitive states summary
        if results.cognitive_states is not None and not results.cognitive_states.empty:
            cognitive_data = results.cognitive_states
            summary['cognitive_summary'] = {
                'total_agents': cognitive_data['agent_id'].nunique() if 'agent_id' in cognitive_data.columns else 0,
                'total_observations': len(cognitive_data),
                'cognitive_states': cognitive_data['cognitive_state'].value_counts().to_dict() if 'cognitive_state' in cognitive_data.columns else {}
            }
        
        # Decision log summary
        if results.decision_log is not None and not results.decision_log.empty:
            decision_data = results.decision_log
            summary['decision_summary'] = {
                'total_decisions': len(decision_data),
                'decision_types': decision_data['decision_type'].value_counts().to_dict() if 'decision_type' in decision_data.columns else {}
            }
        
        return summary
    
    def _save_experiment_results(self, results: ExperimentResults) -> None:
        """
        Save processed experiment results to output directory.
        
        Args:
            results: ExperimentResults object to save
        """
        experiment_output_dir = self.output_directory / results.experiment_id
        self.file_utils.ensure_directory(str(experiment_output_dir))
        
        # Save metrics as JSON
        metrics_file = experiment_output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(results.metrics, f, indent=2, default=str)
        
        # Save summary statistics as JSON
        if results.summary_statistics:
            summary_file = experiment_output_dir / "summary_statistics.json"
            with open(summary_file, 'w') as f:
                json.dump(results.summary_statistics, f, indent=2, default=str)
        
        # Save processed data as CSV files
        if results.movement_data is not None and not results.movement_data.empty:
            movement_file = experiment_output_dir / "processed_movement_data.csv"
            results.movement_data.to_csv(movement_file, index=False)
        
        if results.cognitive_states is not None and not results.cognitive_states.empty:
            cognitive_file = experiment_output_dir / "processed_cognitive_states.csv"
            results.cognitive_states.to_csv(cognitive_file, index=False)
        
        if results.decision_log is not None and not results.decision_log.empty:
            decision_file = experiment_output_dir / "processed_decision_log.csv"
            results.decision_log.to_csv(decision_file, index=False)
        
        self.logger.debug(f"Saved experiment results to {experiment_output_dir}")
    
    def get_experiment_list(self) -> List[str]:
        """
        Get list of available experiment directories.
        
        Returns:
            List of experiment directory paths
        """
        experiment_dirs = []
        
        if not self.results_directory.exists():
            self.logger.warning(f"Results directory does not exist: {self.results_directory}")
            return experiment_dirs
        
        # Look for directories that contain output subdirectories
        for item in self.results_directory.iterdir():
            if item.is_dir() and (item / "output").exists():
                experiment_dirs.append(str(item))
        
        self.logger.debug(f"Found {len(experiment_dirs)} experiment directories")
        return sorted(experiment_dirs)
    
    def calculate_movement_metrics(self, experiment_dir: str) -> Dict[str, Any]:
        """
        Calculate movement metrics for timing, distance, and destination analysis.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            Dictionary with movement metrics including statistical measures
        """
        self.logger.info(f"Calculating movement metrics for: {experiment_dir}")
        
        # Load experiment data
        results = self.load_experiment_data(experiment_dir)
        movement_data = results.movement_data
        
        if movement_data is None or movement_data.empty:
            self.logger.warning(f"No movement data available for {experiment_dir}")
            return {'movement_metrics': {}}
        
        metrics = {}
        
        try:
            # Calculate timing metrics
            timing_metrics = self._calculate_timing_metrics(movement_data)
            metrics['timing'] = timing_metrics
            
            # Calculate destination metrics
            destination_metrics = self._calculate_destination_metrics(movement_data)
            metrics['destinations'] = destination_metrics
            
            # Calculate distance metrics (if location coordinates available)
            distance_metrics = self._calculate_distance_metrics(movement_data, experiment_dir)
            metrics['distances'] = distance_metrics
            
            # Calculate flow metrics
            flow_metrics = self._calculate_flow_metrics(movement_data)
            metrics['flows'] = flow_metrics
            
            # Calculate temporal patterns
            temporal_metrics = self._calculate_temporal_patterns(movement_data)
            metrics['temporal_patterns'] = temporal_metrics
            
            self.logger.info(f"Completed movement metrics calculation for: {experiment_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to calculate movement metrics for {experiment_dir}: {e}")
            metrics['error'] = str(e)
        
        return {'movement_metrics': metrics}
    
    def _calculate_timing_metrics(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate timing-related movement metrics.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary with timing metrics
        """
        timing_metrics = {}
        
        if 'day' not in movement_data.columns:
            return timing_metrics
        
        # Basic timing statistics
        days = movement_data['day'].dropna()
        if not days.empty:
            timing_metrics['simulation_duration'] = {
                'min_day': int(days.min()),
                'max_day': int(days.max()),
                'total_days': int(days.max() - days.min() + 1)
            }
            
            # First movement day (when refugees start moving)
            if 'refugees' in movement_data.columns:
                refugee_data = movement_data[movement_data['refugees'] > 0]
                if not refugee_data.empty:
                    first_movement_day = refugee_data['day'].min()
                    timing_metrics['first_movement_day'] = int(first_movement_day)
            
            # Peak movement periods
            daily_totals = movement_data.groupby('day')['refugees'].sum() if 'refugees' in movement_data.columns else pd.Series()
            if not daily_totals.empty:
                peak_day = daily_totals.idxmax()
                peak_refugees = daily_totals.max()
                timing_metrics['peak_movement'] = {
                    'day': int(peak_day),
                    'refugees': int(peak_refugees)
                }
                
                # Calculate movement distribution over time
                timing_metrics['movement_distribution'] = {
                    'mean_daily_movement': float(daily_totals.mean()),
                    'std_daily_movement': float(daily_totals.std()),
                    'median_daily_movement': float(daily_totals.median())
                }
        
        return timing_metrics
    
    def _calculate_destination_metrics(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate destination-related metrics.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary with destination metrics
        """
        destination_metrics = {}
        
        if 'location' not in movement_data.columns:
            return destination_metrics
        
        # Get final day data for destination analysis
        if 'day' in movement_data.columns:
            final_day = movement_data['day'].max()
            final_data = movement_data[movement_data['day'] == final_day]
        else:
            final_data = movement_data
        
        if not final_data.empty and 'refugees' in final_data.columns:
            # Destination distribution
            destination_counts = final_data.groupby('location')['refugees'].sum().sort_values(ascending=False)
            total_refugees = destination_counts.sum()
            
            if total_refugees > 0:
                destination_proportions = destination_counts / total_refugees
                
                destination_metrics['distribution'] = {
                    'total_locations': len(destination_counts),
                    'total_refugees': int(total_refugees),
                    'top_destinations': destination_counts.head(5).to_dict(),
                    'destination_proportions': destination_proportions.to_dict()
                }
                
                # Calculate concentration metrics
                destination_metrics['concentration'] = self._calculate_concentration_metrics(destination_proportions)
                
                # Calculate entropy (measure of distribution spread)
                entropy = -np.sum(destination_proportions * np.log2(destination_proportions + 1e-10))
                max_entropy = np.log2(len(destination_proportions))
                normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                
                destination_metrics['entropy'] = {
                    'entropy': float(entropy),
                    'max_entropy': float(max_entropy),
                    'normalized_entropy': float(normalized_entropy)
                }
        
        return destination_metrics
    
    def _calculate_concentration_metrics(self, proportions: pd.Series) -> Dict[str, float]:
        """
        Calculate concentration metrics for destination distribution.
        
        Args:
            proportions: Series with destination proportions
            
        Returns:
            Dictionary with concentration metrics
        """
        if proportions.empty:
            return {}
        
        # Gini coefficient
        sorted_props = np.sort(proportions.values)
        n = len(sorted_props)
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_props)) / (n * np.sum(sorted_props)) - (n + 1) / n
        
        # Herfindahl-Hirschman Index
        hhi = np.sum(proportions ** 2)
        
        # Top-k concentration ratios
        sorted_desc = proportions.sort_values(ascending=False)
        cr1 = sorted_desc.iloc[0] if len(sorted_desc) >= 1 else 0
        cr3 = sorted_desc.head(3).sum() if len(sorted_desc) >= 3 else sorted_desc.sum()
        cr5 = sorted_desc.head(5).sum() if len(sorted_desc) >= 5 else sorted_desc.sum()
        
        return {
            'gini_coefficient': float(gini),
            'herfindahl_hirschman_index': float(hhi),
            'concentration_ratio_1': float(cr1),
            'concentration_ratio_3': float(cr3),
            'concentration_ratio_5': float(cr5)
        }
    
    def _calculate_distance_metrics(self, movement_data: pd.DataFrame, experiment_dir: str) -> Dict[str, Any]:
        """
        Calculate distance-related metrics if location coordinates are available.
        
        Args:
            movement_data: DataFrame with movement data
            experiment_dir: Path to experiment directory
            
        Returns:
            Dictionary with distance metrics
        """
        distance_metrics = {}
        
        try:
            # Try to load location coordinates from input files
            experiment_path = Path(experiment_dir)
            input_dir = experiment_path / "input"
            locations_file = input_dir / "locations.csv"
            
            if not locations_file.exists():
                self.logger.debug(f"No locations.csv found for distance calculation: {locations_file}")
                return distance_metrics
            
            # Load location coordinates
            locations = self.csv_utils.read_locations_csv(str(locations_file))
            location_coords = {}
            
            for loc in locations:
                if 'name' in loc and 'lat' in loc and 'lon' in loc:
                    try:
                        location_coords[loc['name']] = (float(loc['lat']), float(loc['lon']))
                    except (ValueError, TypeError):
                        continue
            
            if not location_coords:
                self.logger.debug("No valid location coordinates found for distance calculation")
                return distance_metrics
            
            # Calculate distances for movement flows
            if 'location' in movement_data.columns and 'day' in movement_data.columns:
                # Get movement flows between consecutive days
                flows = self._extract_movement_flows(movement_data)
                
                if flows:
                    distances = []
                    for flow in flows:
                        origin = flow.get('origin')
                        destination = flow.get('destination')
                        
                        if origin in location_coords and destination in location_coords:
                            dist = self._calculate_haversine_distance(
                                location_coords[origin], location_coords[destination]
                            )
                            distances.append(dist)
                    
                    if distances:
                        distance_metrics['movement_distances'] = {
                            'mean_distance': float(np.mean(distances)),
                            'median_distance': float(np.median(distances)),
                            'std_distance': float(np.std(distances)),
                            'min_distance': float(np.min(distances)),
                            'max_distance': float(np.max(distances)),
                            'total_flows': len(distances)
                        }
        
        except Exception as e:
            self.logger.debug(f"Could not calculate distance metrics: {e}")
        
        return distance_metrics
    
    def _extract_movement_flows(self, movement_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract movement flows from movement data.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            List of movement flow dictionaries
        """
        flows = []
        
        # This is a simplified approach - in practice, would need more sophisticated
        # flow detection based on agent tracking or location population changes
        
        # Group by location and look for population changes
        location_groups = movement_data.groupby('location')
        
        for location, group in location_groups:
            if 'day' in group.columns and 'refugees' in group.columns:
                group_sorted = group.sort_values('day')
                
                # Look for significant population increases (indicating arrivals)
                for i in range(1, len(group_sorted)):
                    prev_refugees = group_sorted.iloc[i-1]['refugees']
                    curr_refugees = group_sorted.iloc[i]['refugees']
                    
                    if curr_refugees > prev_refugees + 10:  # Threshold for significant movement
                        flows.append({
                            'destination': location,
                            'day': group_sorted.iloc[i]['day'],
                            'refugees': curr_refugees - prev_refugees,
                            'origin': 'unknown'  # Would need more data to determine origin
                        })
        
        return flows
    
    def _calculate_haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate haversine distance between two coordinates.
        
        Args:
            coord1: (latitude, longitude) of first point
            coord2: (latitude, longitude) of second point
            
        Returns:
            Distance in kilometers
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        
        return r * c
    
    def _calculate_flow_metrics(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate flow-related metrics.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary with flow metrics
        """
        flow_metrics = {}
        
        if 'location' not in movement_data.columns or 'day' not in movement_data.columns:
            return flow_metrics
        
        # Calculate location popularity over time
        location_popularity = movement_data.groupby(['day', 'location'])['refugees'].sum().unstack(fill_value=0)
        
        if not location_popularity.empty:
            # Calculate flow stability (how consistent are the flows)
            location_std = location_popularity.std(axis=0)
            location_mean = location_popularity.mean(axis=0)
            
            # Coefficient of variation for each location
            cv = location_std / (location_mean + 1e-10)
            
            flow_metrics['stability'] = {
                'mean_coefficient_of_variation': float(cv.mean()),
                'std_coefficient_of_variation': float(cv.std()),
                'most_stable_location': cv.idxmin(),
                'least_stable_location': cv.idxmax()
            }
            
            # Calculate flow trends
            flow_trends = {}
            for location in location_popularity.columns:
                location_data = location_popularity[location]
                if len(location_data) > 1:
                    # Simple linear trend
                    days = np.arange(len(location_data))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(days, location_data)
                    flow_trends[location] = {
                        'slope': float(slope),
                        'r_squared': float(r_value**2),
                        'p_value': float(p_value)
                    }
            
            flow_metrics['trends'] = flow_trends
        
        return flow_metrics
    
    def _calculate_temporal_patterns(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate temporal patterns in movement data.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary with temporal pattern metrics
        """
        temporal_metrics = {}
        
        if 'day' not in movement_data.columns or 'refugees' not in movement_data.columns:
            return temporal_metrics
        
        # Daily movement totals
        daily_totals = movement_data.groupby('day')['refugees'].sum()
        
        if not daily_totals.empty:
            # Movement phases (early, middle, late)
            total_days = len(daily_totals)
            early_phase = daily_totals.iloc[:total_days//3]
            middle_phase = daily_totals.iloc[total_days//3:2*total_days//3]
            late_phase = daily_totals.iloc[2*total_days//3:]
            
            temporal_metrics['phases'] = {
                'early_phase_mean': float(early_phase.mean()) if not early_phase.empty else 0,
                'middle_phase_mean': float(middle_phase.mean()) if not middle_phase.empty else 0,
                'late_phase_mean': float(late_phase.mean()) if not late_phase.empty else 0,
                'early_phase_total': int(early_phase.sum()) if not early_phase.empty else 0,
                'middle_phase_total': int(middle_phase.sum()) if not middle_phase.empty else 0,
                'late_phase_total': int(late_phase.sum()) if not late_phase.empty else 0
            }
            
            # Movement acceleration/deceleration
            if len(daily_totals) > 2:
                # Calculate second derivative (acceleration)
                first_diff = daily_totals.diff()
                second_diff = first_diff.diff()
                
                temporal_metrics['acceleration'] = {
                    'mean_acceleration': float(second_diff.mean()),
                    'std_acceleration': float(second_diff.std()),
                    'max_acceleration': float(second_diff.max()),
                    'min_acceleration': float(second_diff.min())
                }
            
            # Identify movement waves/peaks
            peaks = self._identify_movement_peaks(daily_totals)
            temporal_metrics['peaks'] = peaks
        
        return temporal_metrics
    
    def _identify_movement_peaks(self, daily_totals: pd.Series) -> Dict[str, Any]:
        """
        Identify peaks in movement data.
        
        Args:
            daily_totals: Series with daily movement totals
            
        Returns:
            Dictionary with peak information
        """
        if len(daily_totals) < 3:
            return {}
        
        # Simple peak detection: local maxima
        peaks = []
        values = daily_totals.values
        
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append({
                    'day': daily_totals.index[i],
                    'value': values[i]
                })
        
        if peaks:
            peak_values = [p['value'] for p in peaks]
            return {
                'num_peaks': len(peaks),
                'peak_days': [p['day'] for p in peaks],
                'peak_values': peak_values,
                'mean_peak_value': float(np.mean(peak_values)),
                'max_peak_value': float(np.max(peak_values)),
                'peak_spacing': float(np.mean(np.diff([p['day'] for p in peaks]))) if len(peaks) > 1 else 0
            }
        else:
            return {'num_peaks': 0}
    
    def analyze_cognitive_transitions(self, experiment_dir: str) -> Dict[str, Any]:
        """
        Analyze cognitive state transitions and S1/S2 patterns.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            Dictionary with cognitive analysis metrics
        """
        self.logger.info(f"Analyzing cognitive transitions for: {experiment_dir}")
        
        # Load experiment data
        results = self.load_experiment_data(experiment_dir)
        cognitive_data = results.cognitive_states
        
        if cognitive_data is None or cognitive_data.empty:
            self.logger.warning(f"No cognitive states data available for {experiment_dir}")
            return {'cognitive_analysis': {}}
        
        metrics = {}
        
        try:
            # Calculate state distribution metrics
            state_metrics = self._calculate_state_distribution(cognitive_data)
            metrics['state_distribution'] = state_metrics
            
            # Calculate transition metrics
            transition_metrics = self._calculate_transition_patterns(cognitive_data)
            metrics['transitions'] = transition_metrics
            
            # Calculate duration metrics
            duration_metrics = self._calculate_state_durations(cognitive_data)
            metrics['durations'] = duration_metrics
            
            # Calculate activation triggers
            trigger_metrics = self._calculate_activation_triggers(cognitive_data)
            metrics['triggers'] = trigger_metrics
            
            # Calculate social connectivity impact
            social_metrics = self._calculate_social_connectivity_impact(cognitive_data)
            metrics['social_connectivity'] = social_metrics
            
            # Calculate temporal patterns
            temporal_cognitive_metrics = self._calculate_cognitive_temporal_patterns(cognitive_data)
            metrics['temporal_patterns'] = temporal_cognitive_metrics
            
            self.logger.info(f"Completed cognitive analysis for: {experiment_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to analyze cognitive transitions for {experiment_dir}: {e}")
            metrics['error'] = str(e)
        
        return {'cognitive_analysis': metrics}
    
    def _calculate_state_distribution(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate distribution of cognitive states.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with state distribution metrics
        """
        state_metrics = {}
        
        if 'cognitive_state' not in cognitive_data.columns:
            return state_metrics
        
        # Overall state distribution
        state_counts = cognitive_data['cognitive_state'].value_counts()
        total_observations = len(cognitive_data)
        
        state_proportions = state_counts / total_observations
        
        state_metrics['overall'] = {
            'state_counts': state_counts.to_dict(),
            'state_proportions': state_proportions.to_dict(),
            'total_observations': total_observations,
            'unique_states': len(state_counts)
        }
        
        # State distribution by agent
        if 'agent_id' in cognitive_data.columns:
            agent_state_dist = cognitive_data.groupby('agent_id')['cognitive_state'].value_counts(normalize=True).unstack(fill_value=0)
            
            if not agent_state_dist.empty:
                state_metrics['by_agent'] = {
                    'mean_s1_proportion': float(agent_state_dist.get('S1', pd.Series()).mean()) if 'S1' in agent_state_dist.columns else 0,
                    'mean_s2_proportion': float(agent_state_dist.get('S2', pd.Series()).mean()) if 'S2' in agent_state_dist.columns else 0,
                    'std_s1_proportion': float(agent_state_dist.get('S1', pd.Series()).std()) if 'S1' in agent_state_dist.columns else 0,
                    'std_s2_proportion': float(agent_state_dist.get('S2', pd.Series()).std()) if 'S2' in agent_state_dist.columns else 0,
                    'num_agents': len(agent_state_dist)
                }
        
        # State distribution over time
        if 'day' in cognitive_data.columns:
            daily_state_dist = cognitive_data.groupby('day')['cognitive_state'].value_counts(normalize=True).unstack(fill_value=0)
            
            if not daily_state_dist.empty:
                state_metrics['temporal'] = {
                    'daily_distributions': daily_state_dist.to_dict(),
                    'mean_daily_s1': float(daily_state_dist.get('S1', pd.Series()).mean()) if 'S1' in daily_state_dist.columns else 0,
                    'mean_daily_s2': float(daily_state_dist.get('S2', pd.Series()).mean()) if 'S2' in daily_state_dist.columns else 0
                }
        
        return state_metrics
    
    def _calculate_transition_patterns(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate cognitive state transition patterns.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with transition metrics
        """
        transition_metrics = {}
        
        required_cols = ['agent_id', 'day', 'cognitive_state']
        if not all(col in cognitive_data.columns for col in required_cols):
            return transition_metrics
        
        # Calculate transitions for each agent
        agent_transitions = []
        transition_counts = {}
        
        for agent_id in cognitive_data['agent_id'].unique():
            agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
            
            if len(agent_data) < 2:
                continue
            
            # Find state transitions
            prev_state = None
            transitions = []
            
            for _, row in agent_data.iterrows():
                current_state = row['cognitive_state']
                
                if prev_state is not None and current_state != prev_state:
                    transition = f"{prev_state}->{current_state}"
                    transitions.append({
                        'agent_id': agent_id,
                        'day': row['day'],
                        'from_state': prev_state,
                        'to_state': current_state,
                        'transition': transition
                    })
                    
                    # Count transitions
                    transition_counts[transition] = transition_counts.get(transition, 0) + 1
                
                prev_state = current_state
            
            agent_transitions.extend(transitions)
        
        if agent_transitions:
            transition_df = pd.DataFrame(agent_transitions)
            
            # Overall transition statistics
            total_transitions = len(agent_transitions)
            unique_transitions = len(transition_counts)
            
            transition_metrics['overall'] = {
                'total_transitions': total_transitions,
                'unique_transition_types': unique_transitions,
                'transition_counts': transition_counts,
                'transition_rates': {k: v/total_transitions for k, v in transition_counts.items()}
            }
            
            # Transition timing
            if 'day' in transition_df.columns:
                transition_days = transition_df['day']
                transition_metrics['timing'] = {
                    'mean_transition_day': float(transition_days.mean()),
                    'std_transition_day': float(transition_days.std()),
                    'earliest_transition': int(transition_days.min()),
                    'latest_transition': int(transition_days.max())
                }
            
            # Agent-level transition statistics
            agent_transition_counts = transition_df.groupby('agent_id').size()
            transition_metrics['by_agent'] = {
                'mean_transitions_per_agent': float(agent_transition_counts.mean()),
                'std_transitions_per_agent': float(agent_transition_counts.std()),
                'max_transitions_per_agent': int(agent_transition_counts.max()),
                'agents_with_transitions': len(agent_transition_counts),
                'total_agents': cognitive_data['agent_id'].nunique()
            }
        
        return transition_metrics
    
    def _calculate_state_durations(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate duration statistics for cognitive states.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with duration metrics
        """
        duration_metrics = {}
        
        required_cols = ['agent_id', 'day', 'cognitive_state']
        if not all(col in cognitive_data.columns for col in required_cols):
            return duration_metrics
        
        # Calculate state durations for each agent
        all_durations = {'S1': [], 'S2': []}
        
        for agent_id in cognitive_data['agent_id'].unique():
            agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
            
            if len(agent_data) < 2:
                continue
            
            # Track state durations
            current_state = None
            state_start_day = None
            
            for _, row in agent_data.iterrows():
                state = row['cognitive_state']
                day = row['day']
                
                if current_state != state:
                    # State changed, record duration of previous state
                    if current_state is not None and state_start_day is not None:
                        duration = day - state_start_day
                        if current_state in all_durations:
                            all_durations[current_state].append(duration)
                    
                    # Start tracking new state
                    current_state = state
                    state_start_day = day
            
            # Handle final state duration (use last day as end)
            if current_state is not None and state_start_day is not None:
                final_day = agent_data['day'].max()
                duration = final_day - state_start_day + 1
                if current_state in all_durations:
                    all_durations[current_state].append(duration)
        
        # Calculate statistics for each state
        for state, durations in all_durations.items():
            if durations:
                duration_metrics[f'{state}_durations'] = {
                    'mean': float(np.mean(durations)),
                    'median': float(np.median(durations)),
                    'std': float(np.std(durations)),
                    'min': int(np.min(durations)),
                    'max': int(np.max(durations)),
                    'count': len(durations),
                    'total_duration': int(np.sum(durations))
                }
        
        return duration_metrics
    
    def _calculate_activation_triggers(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate metrics for System 2 activation triggers.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with trigger metrics
        """
        trigger_metrics = {}
        
        # Check for conflict level data
        if 'conflict_level' in cognitive_data.columns and 'cognitive_state' in cognitive_data.columns:
            # Analyze conflict levels at state transitions
            s2_activations = cognitive_data[cognitive_data['cognitive_state'] == 'S2']
            
            if not s2_activations.empty:
                conflict_at_s2 = s2_activations['conflict_level']
                
                trigger_metrics['conflict_triggers'] = {
                    'mean_conflict_at_s2': float(conflict_at_s2.mean()),
                    'std_conflict_at_s2': float(conflict_at_s2.std()),
                    'min_conflict_at_s2': float(conflict_at_s2.min()),
                    'max_conflict_at_s2': float(conflict_at_s2.max()),
                    's2_observations': len(s2_activations)
                }
                
                # Compare with S1 conflict levels
                s1_activations = cognitive_data[cognitive_data['cognitive_state'] == 'S1']
                if not s1_activations.empty:
                    conflict_at_s1 = s1_activations['conflict_level']
                    
                    trigger_metrics['conflict_comparison'] = {
                        'mean_conflict_s1': float(conflict_at_s1.mean()),
                        'mean_conflict_s2': float(conflict_at_s2.mean()),
                        'conflict_difference': float(conflict_at_s2.mean() - conflict_at_s1.mean())
                    }
                    
                    # Statistical test for difference
                    if len(conflict_at_s1) > 1 and len(conflict_at_s2) > 1:
                        try:
                            statistic, p_value = mannwhitneyu(conflict_at_s2, conflict_at_s1, alternative='greater')
                            trigger_metrics['conflict_comparison']['mann_whitney_u'] = {
                                'statistic': float(statistic),
                                'p_value': float(p_value),
                                'significant': p_value < 0.05
                            }
                        except Exception as e:
                            self.logger.debug(f"Could not perform Mann-Whitney U test: {e}")
        
        # Check for system2_activations data
        if 'system2_activations' in cognitive_data.columns:
            s2_activations_count = cognitive_data['system2_activations']
            
            trigger_metrics['activation_frequency'] = {
                'mean_activations': float(s2_activations_count.mean()),
                'std_activations': float(s2_activations_count.std()),
                'max_activations': int(s2_activations_count.max()),
                'agents_with_activations': int((s2_activations_count > 0).sum()),
                'total_agents': len(s2_activations_count.unique()) if 'agent_id' in cognitive_data.columns else len(s2_activations_count)
            }
        
        return trigger_metrics
    
    def _calculate_social_connectivity_impact(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate impact of social connectivity on cognitive transitions.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with social connectivity metrics
        """
        social_metrics = {}
        
        if 'connections' not in cognitive_data.columns or 'cognitive_state' not in cognitive_data.columns:
            return social_metrics
        
        # Analyze connections by cognitive state
        state_connections = cognitive_data.groupby('cognitive_state')['connections'].agg(['mean', 'std', 'count'])
        
        social_metrics['connections_by_state'] = state_connections.to_dict()
        
        # Compare connections between S1 and S2
        s1_connections = cognitive_data[cognitive_data['cognitive_state'] == 'S1']['connections']
        s2_connections = cognitive_data[cognitive_data['cognitive_state'] == 'S2']['connections']
        
        if not s1_connections.empty and not s2_connections.empty:
            social_metrics['state_comparison'] = {
                'mean_connections_s1': float(s1_connections.mean()),
                'mean_connections_s2': float(s2_connections.mean()),
                'connection_difference': float(s2_connections.mean() - s1_connections.mean())
            }
            
            # Statistical test
            if len(s1_connections) > 1 and len(s2_connections) > 1:
                try:
                    statistic, p_value = mannwhitneyu(s2_connections, s1_connections, alternative='two-sided')
                    social_metrics['state_comparison']['mann_whitney_u'] = {
                        'statistic': float(statistic),
                        'p_value': float(p_value),
                        'significant': p_value < 0.05
                    }
                except Exception as e:
                    self.logger.debug(f"Could not perform Mann-Whitney U test for connections: {e}")
        
        # Analyze connection changes over time
        if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
            # Calculate connection changes for each agent
            connection_changes = []
            
            for agent_id in cognitive_data['agent_id'].unique():
                agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                
                if len(agent_data) > 1:
                    agent_data['connection_change'] = agent_data['connections'].diff()
                    connection_changes.extend(agent_data['connection_change'].dropna().tolist())
            
            if connection_changes:
                social_metrics['connection_dynamics'] = {
                    'mean_connection_change': float(np.mean(connection_changes)),
                    'std_connection_change': float(np.std(connection_changes)),
                    'positive_changes': int(sum(1 for x in connection_changes if x > 0)),
                    'negative_changes': int(sum(1 for x in connection_changes if x < 0)),
                    'total_changes': len(connection_changes)
                }
        
        return social_metrics
    
    def _calculate_cognitive_temporal_patterns(self, cognitive_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate temporal patterns in cognitive state evolution.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            Dictionary with temporal cognitive metrics
        """
        temporal_metrics = {}
        
        if 'day' not in cognitive_data.columns or 'cognitive_state' not in cognitive_data.columns:
            return temporal_metrics
        
        # Daily cognitive state proportions
        daily_states = cognitive_data.groupby('day')['cognitive_state'].value_counts(normalize=True).unstack(fill_value=0)
        
        if not daily_states.empty:
            # S2 activation trends over time
            if 'S2' in daily_states.columns:
                s2_proportions = daily_states['S2']
                
                # Linear trend analysis
                days = np.arange(len(s2_proportions))
                if len(days) > 1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(days, s2_proportions)
                    
                    temporal_metrics['s2_trend'] = {
                        'slope': float(slope),
                        'intercept': float(intercept),
                        'r_squared': float(r_value**2),
                        'p_value': float(p_value),
                        'trend_direction': 'increasing' if slope > 0 else 'decreasing'
                    }
                
                # Peak S2 activation periods
                s2_peaks = self._identify_cognitive_peaks(s2_proportions)
                temporal_metrics['s2_peaks'] = s2_peaks
            
            # Overall cognitive dynamics
            temporal_metrics['daily_patterns'] = {
                'mean_daily_s1': float(daily_states.get('S1', pd.Series()).mean()) if 'S1' in daily_states.columns else 0,
                'mean_daily_s2': float(daily_states.get('S2', pd.Series()).mean()) if 'S2' in daily_states.columns else 0,
                'std_daily_s1': float(daily_states.get('S1', pd.Series()).std()) if 'S1' in daily_states.columns else 0,
                'std_daily_s2': float(daily_states.get('S2', pd.Series()).std()) if 'S2' in daily_states.columns else 0
            }
        
        return temporal_metrics
    
    def _identify_cognitive_peaks(self, proportions: pd.Series) -> Dict[str, Any]:
        """
        Identify peaks in cognitive state proportions.
        
        Args:
            proportions: Series with daily cognitive state proportions
            
        Returns:
            Dictionary with peak information
        """
        if len(proportions) < 3:
            return {}
        
        # Simple peak detection
        peaks = []
        values = proportions.values
        
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1] and values[i] > 0.1:  # Minimum threshold
                peaks.append({
                    'day': proportions.index[i],
                    'proportion': values[i]
                })
        
        if peaks:
            peak_proportions = [p['proportion'] for p in peaks]
            return {
                'num_peaks': len(peaks),
                'peak_days': [p['day'] for p in peaks],
                'peak_proportions': peak_proportions,
                'mean_peak_proportion': float(np.mean(peak_proportions)),
                'max_peak_proportion': float(np.max(peak_proportions))
            }
        else:
            return {'num_peaks': 0}
    
    def compare_cognitive_modes(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Compare cognitive modes across multiple experiments with statistical significance testing.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary with comparative analysis results
        """
        self.logger.info(f"Comparing cognitive modes across {len(experiment_dirs)} experiments")
        
        if len(experiment_dirs) < 2:
            self.logger.warning("Need at least 2 experiments for comparison")
            return {'comparison_error': 'Insufficient experiments for comparison'}
        
        comparison_results = {}
        
        try:
            # Load all experiment data
            experiments_data = {}
            for exp_dir in experiment_dirs:
                try:
                    results = self.load_experiment_data(exp_dir)
                    experiments_data[results.experiment_id] = results
                except Exception as e:
                    self.logger.warning(f"Failed to load experiment {exp_dir}: {e}")
                    continue
            
            if len(experiments_data) < 2:
                return {'comparison_error': 'Could not load sufficient experiment data'}
            
            # Extract cognitive modes from metadata
            cognitive_modes = self._extract_cognitive_modes(experiments_data)
            comparison_results['cognitive_modes'] = cognitive_modes
            
            # Compare movement metrics
            movement_comparison = self._compare_movement_metrics(experiments_data)
            comparison_results['movement_comparison'] = movement_comparison
            
            # Compare cognitive metrics if available
            cognitive_comparison = self._compare_cognitive_metrics(experiments_data)
            comparison_results['cognitive_comparison'] = cognitive_comparison
            
            # Perform statistical tests
            statistical_tests = self._perform_statistical_tests(experiments_data)
            comparison_results['statistical_tests'] = statistical_tests
            
            # Calculate effect sizes
            effect_sizes = self._calculate_effect_sizes(experiments_data)
            comparison_results['effect_sizes'] = effect_sizes
            
            # Multiple comparison corrections
            corrected_results = self._apply_multiple_comparison_corrections(comparison_results)
            comparison_results['corrected_results'] = corrected_results
            
            self.logger.info("Completed cognitive mode comparison")
            
        except Exception as e:
            self.logger.error(f"Failed to compare cognitive modes: {e}")
            comparison_results['error'] = str(e)
        
        return comparison_results
    
    def _extract_cognitive_modes(self, experiments_data: Dict[str, ExperimentResults]) -> Dict[str, str]:
        """
        Extract cognitive modes from experiment metadata.
        
        Args:
            experiments_data: Dictionary of experiment results
            
        Returns:
            Dictionary mapping experiment IDs to cognitive modes
        """
        cognitive_modes = {}
        
        for exp_id, results in experiments_data.items():
            metadata = results.metrics.get('metadata', {})
            
            # Try to extract cognitive mode from configuration
            config = metadata.get('configuration', {})
            cognitive_mode = config.get('cognitive_mode', 'unknown')
            
            # If not found, try to infer from simulation parameters
            if cognitive_mode == 'unknown':
                sim_params = config.get('simulation_params', {})
                move_rules = sim_params.get('move_rules', {})
                
                if move_rules.get('two_system_decision_making', False):
                    connectivity = move_rules.get('average_social_connectivity', 0)
                    if connectivity == 0:
                        cognitive_mode = 's2_disconnected'
                    elif connectivity >= 8:
                        cognitive_mode = 's2_full'
                    else:
                        cognitive_mode = 'dual_process'
                else:
                    cognitive_mode = 's1_only'
            
            cognitive_modes[exp_id] = cognitive_mode
        
        return cognitive_modes
    
    def _compare_movement_metrics(self, experiments_data: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Compare movement metrics across experiments.
        
        Args:
            experiments_data: Dictionary of experiment results
            
        Returns:
            Dictionary with movement metric comparisons
        """
        movement_comparison = {}
        
        # Extract movement metrics for comparison
        metrics_by_experiment = {}
        
        for exp_id, results in experiments_data.items():
            movement_metrics = results.metrics.get('movement_metrics', {})
            metrics_by_experiment[exp_id] = movement_metrics
        
        # Compare key movement metrics
        key_metrics = [
            'timing.first_movement_day',
            'timing.peak_movement.day',
            'destinations.concentration.gini_coefficient',
            'destinations.entropy.normalized_entropy',
            'distances.movement_distances.mean_distance'
        ]
        
        for metric_path in key_metrics:
            metric_values = {}
            
            for exp_id, metrics in metrics_by_experiment.items():
                value = self._get_nested_metric(metrics, metric_path)
                if value is not None:
                    metric_values[exp_id] = value
            
            if len(metric_values) >= 2:
                comparison = self._compare_metric_values(metric_values, metric_path)
                movement_comparison[metric_path.replace('.', '_')] = comparison
        
        return movement_comparison
    
    def _compare_cognitive_metrics(self, experiments_data: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Compare cognitive metrics across experiments.
        
        Args:
            experiments_data: Dictionary of experiment results
            
        Returns:
            Dictionary with cognitive metric comparisons
        """
        cognitive_comparison = {}
        
        # Extract cognitive metrics for comparison
        metrics_by_experiment = {}
        
        for exp_id, results in experiments_data.items():
            cognitive_metrics = results.metrics.get('cognitive_analysis', {})
            metrics_by_experiment[exp_id] = cognitive_metrics
        
        # Compare key cognitive metrics
        key_metrics = [
            'state_distribution.overall.state_proportions.S2',
            'transitions.overall.total_transitions',
            'durations.S2_durations.mean',
            'triggers.conflict_triggers.mean_conflict_at_s2',
            'social_connectivity.state_comparison.mean_connections_s2'
        ]
        
        for metric_path in key_metrics:
            metric_values = {}
            
            for exp_id, metrics in metrics_by_experiment.items():
                value = self._get_nested_metric(metrics, metric_path)
                if value is not None:
                    metric_values[exp_id] = value
            
            if len(metric_values) >= 2:
                comparison = self._compare_metric_values(metric_values, metric_path)
                cognitive_comparison[metric_path.replace('.', '_')] = comparison
        
        return cognitive_comparison
    
    def _get_nested_metric(self, metrics: Dict[str, Any], path: str) -> Any:
        """
        Get nested metric value using dot notation path.
        
        Args:
            metrics: Dictionary with nested metrics
            path: Dot-separated path to metric
            
        Returns:
            Metric value or None if not found
        """
        try:
            value = metrics
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def _compare_metric_values(self, metric_values: Dict[str, float], metric_name: str) -> Dict[str, Any]:
        """
        Compare metric values across experiments.
        
        Args:
            metric_values: Dictionary mapping experiment IDs to metric values
            metric_name: Name of the metric being compared
            
        Returns:
            Dictionary with comparison statistics
        """
        values = list(metric_values.values())
        exp_ids = list(metric_values.keys())
        
        comparison = {
            'metric_name': metric_name,
            'experiment_values': metric_values,
            'descriptive_stats': {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'range': float(np.max(values) - np.min(values))
            }
        }
        
        # Add pairwise comparisons if more than 2 experiments
        if len(values) > 2:
            pairwise_comparisons = []
            
            for i in range(len(exp_ids)):
                for j in range(i + 1, len(exp_ids)):
                    exp1, exp2 = exp_ids[i], exp_ids[j]
                    val1, val2 = metric_values[exp1], metric_values[exp2]
                    
                    pairwise_comparisons.append({
                        'experiment_1': exp1,
                        'experiment_2': exp2,
                        'value_1': val1,
                        'value_2': val2,
                        'difference': val2 - val1,
                        'percent_difference': ((val2 - val1) / val1 * 100) if val1 != 0 else float('inf')
                    })
            
            comparison['pairwise_comparisons'] = pairwise_comparisons
        
        return comparison
    
    def _perform_statistical_tests(self, experiments_data: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Perform statistical significance tests across experiments.
        
        Args:
            experiments_data: Dictionary of experiment results
            
        Returns:
            Dictionary with statistical test results
        """
        statistical_tests = {}
        
        # Group experiments by cognitive mode
        mode_groups = {}
        cognitive_modes = self._extract_cognitive_modes(experiments_data)
        
        for exp_id, mode in cognitive_modes.items():
            if mode not in mode_groups:
                mode_groups[mode] = []
            mode_groups[mode].append(exp_id)
        
        # Perform tests if we have multiple groups
        if len(mode_groups) >= 2:
            # Test movement timing differences
            timing_test = self._test_movement_timing_differences(experiments_data, mode_groups)
            statistical_tests['movement_timing'] = timing_test
            
            # Test destination distribution differences
            destination_test = self._test_destination_differences(experiments_data, mode_groups)
            statistical_tests['destination_distribution'] = destination_test
            
            # Test cognitive state differences (if data available)
            cognitive_test = self._test_cognitive_differences(experiments_data, mode_groups)
            statistical_tests['cognitive_states'] = cognitive_test
        
        return statistical_tests
    
    def _test_movement_timing_differences(self, experiments_data: Dict[str, ExperimentResults], 
                                        mode_groups: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Test for differences in movement timing across cognitive modes.
        
        Args:
            experiments_data: Dictionary of experiment results
            mode_groups: Dictionary mapping cognitive modes to experiment IDs
            
        Returns:
            Dictionary with timing test results
        """
        timing_test = {}
        
        # Extract first movement days by mode
        first_movement_days = {}
        
        for mode, exp_ids in mode_groups.items():
            days = []
            for exp_id in exp_ids:
                results = experiments_data[exp_id]
                first_day = self._get_nested_metric(
                    results.metrics, 'movement_metrics.timing.first_movement_day'
                )
                if first_day is not None:
                    days.append(first_day)
            
            if days:
                first_movement_days[mode] = days
        
        if len(first_movement_days) >= 2:
            # Perform Kruskal-Wallis test (non-parametric ANOVA)
            groups = list(first_movement_days.values())
            
            try:
                statistic, p_value = kruskal(*groups)
                timing_test['kruskal_wallis'] = {
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'significant': p_value < 0.05,
                    'groups': {mode: {'mean': float(np.mean(days)), 'count': len(days)} 
                              for mode, days in first_movement_days.items()}
                }
            except Exception as e:
                timing_test['error'] = str(e)
        
        return timing_test
    
    def _test_destination_differences(self, experiments_data: Dict[str, ExperimentResults], 
                                    mode_groups: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Test for differences in destination distribution across cognitive modes.
        
        Args:
            experiments_data: Dictionary of experiment results
            mode_groups: Dictionary mapping cognitive modes to experiment IDs
            
        Returns:
            Dictionary with destination test results
        """
        destination_test = {}
        
        # Extract Gini coefficients by mode
        gini_coefficients = {}
        
        for mode, exp_ids in mode_groups.items():
            ginis = []
            for exp_id in exp_ids:
                results = experiments_data[exp_id]
                gini = self._get_nested_metric(
                    results.metrics, 'movement_metrics.destinations.concentration.gini_coefficient'
                )
                if gini is not None:
                    ginis.append(gini)
            
            if ginis:
                gini_coefficients[mode] = ginis
        
        if len(gini_coefficients) >= 2:
            # Perform Kruskal-Wallis test
            groups = list(gini_coefficients.values())
            
            try:
                statistic, p_value = kruskal(*groups)
                destination_test['gini_kruskal_wallis'] = {
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'significant': p_value < 0.05,
                    'groups': {mode: {'mean': float(np.mean(ginis)), 'count': len(ginis)} 
                              for mode, ginis in gini_coefficients.items()}
                }
            except Exception as e:
                destination_test['error'] = str(e)
        
        return destination_test
    
    def _test_cognitive_differences(self, experiments_data: Dict[str, ExperimentResults], 
                                  mode_groups: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Test for differences in cognitive states across modes.
        
        Args:
            experiments_data: Dictionary of experiment results
            mode_groups: Dictionary mapping cognitive modes to experiment IDs
            
        Returns:
            Dictionary with cognitive test results
        """
        cognitive_test = {}
        
        # Extract S2 proportions by mode
        s2_proportions = {}
        
        for mode, exp_ids in mode_groups.items():
            proportions = []
            for exp_id in exp_ids:
                results = experiments_data[exp_id]
                s2_prop = self._get_nested_metric(
                    results.metrics, 'cognitive_analysis.state_distribution.overall.state_proportions.S2'
                )
                if s2_prop is not None:
                    proportions.append(s2_prop)
            
            if proportions:
                s2_proportions[mode] = proportions
        
        if len(s2_proportions) >= 2:
            # Perform Kruskal-Wallis test
            groups = list(s2_proportions.values())
            
            try:
                statistic, p_value = kruskal(*groups)
                cognitive_test['s2_proportion_kruskal_wallis'] = {
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'significant': p_value < 0.05,
                    'groups': {mode: {'mean': float(np.mean(props)), 'count': len(props)} 
                              for mode, props in s2_proportions.items()}
                }
            except Exception as e:
                cognitive_test['error'] = str(e)
        
        return cognitive_test
    
    def _calculate_effect_sizes(self, experiments_data: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Calculate effect sizes for comparisons between cognitive modes.
        
        Args:
            experiments_data: Dictionary of experiment results
            
        Returns:
            Dictionary with effect size calculations
        """
        effect_sizes = {}
        
        # Group experiments by cognitive mode
        cognitive_modes = self._extract_cognitive_modes(experiments_data)
        mode_groups = {}
        
        for exp_id, mode in cognitive_modes.items():
            if mode not in mode_groups:
                mode_groups[mode] = []
            mode_groups[mode].append(exp_id)
        
        # Calculate Cohen's d for pairwise comparisons
        modes = list(mode_groups.keys())
        
        for i in range(len(modes)):
            for j in range(i + 1, len(modes)):
                mode1, mode2 = modes[i], modes[j]
                
                # Calculate effect sizes for key metrics
                pairwise_effects = self._calculate_pairwise_effect_sizes(
                    experiments_data, mode_groups[mode1], mode_groups[mode2], mode1, mode2
                )
                
                comparison_key = f"{mode1}_vs_{mode2}"
                effect_sizes[comparison_key] = pairwise_effects
        
        return effect_sizes
    
    def _calculate_pairwise_effect_sizes(self, experiments_data: Dict[str, ExperimentResults],
                                       group1_ids: List[str], group2_ids: List[str],
                                       mode1: str, mode2: str) -> Dict[str, Any]:
        """
        Calculate effect sizes for pairwise comparison between two cognitive modes.
        
        Args:
            experiments_data: Dictionary of experiment results
            group1_ids: Experiment IDs for first group
            group2_ids: Experiment IDs for second group
            mode1: Name of first cognitive mode
            mode2: Name of second cognitive mode
            
        Returns:
            Dictionary with pairwise effect sizes
        """
        pairwise_effects = {
            'mode1': mode1,
            'mode2': mode2,
            'group1_size': len(group1_ids),
            'group2_size': len(group2_ids)
        }
        
        # Key metrics to compare
        metrics_to_compare = [
            ('movement_metrics.timing.first_movement_day', 'first_movement_day'),
            ('movement_metrics.destinations.concentration.gini_coefficient', 'gini_coefficient'),
            ('cognitive_analysis.state_distribution.overall.state_proportions.S2', 's2_proportion')
        ]
        
        for metric_path, metric_name in metrics_to_compare:
            # Extract values for both groups
            group1_values = []
            group2_values = []
            
            for exp_id in group1_ids:
                value = self._get_nested_metric(experiments_data[exp_id].metrics, metric_path)
                if value is not None:
                    group1_values.append(value)
            
            for exp_id in group2_ids:
                value = self._get_nested_metric(experiments_data[exp_id].metrics, metric_path)
                if value is not None:
                    group2_values.append(value)
            
            if len(group1_values) > 0 and len(group2_values) > 0:
                # Calculate Cohen's d
                cohens_d = self._calculate_cohens_d(group1_values, group2_values)
                
                pairwise_effects[metric_name] = {
                    'cohens_d': cohens_d,
                    'effect_size_interpretation': self._interpret_effect_size(cohens_d),
                    'group1_mean': float(np.mean(group1_values)),
                    'group2_mean': float(np.mean(group2_values)),
                    'group1_std': float(np.std(group1_values)),
                    'group2_std': float(np.std(group2_values))
                }
        
        return pairwise_effects
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """
        Calculate Cohen's d effect size.
        
        Args:
            group1: Values for first group
            group2: Values for second group
            
        Returns:
            Cohen's d effect size
        """
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        # Cohen's d
        cohens_d = (mean1 - mean2) / pooled_std
        
        return float(cohens_d)
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """
        Interpret Cohen's d effect size.
        
        Args:
            cohens_d: Cohen's d value
            
        Returns:
            Interpretation string
        """
        abs_d = abs(cohens_d)
        
        if abs_d < 0.2:
            return 'negligible'
        elif abs_d < 0.5:
            return 'small'
        elif abs_d < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def _apply_multiple_comparison_corrections(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply multiple comparison corrections (Bonferroni, FDR).
        
        Args:
            comparison_results: Dictionary with comparison results
            
        Returns:
            Dictionary with corrected p-values
        """
        corrected_results = {}
        
        # Collect all p-values from statistical tests
        p_values = []
        test_names = []
        
        statistical_tests = comparison_results.get('statistical_tests', {})
        
        for test_category, tests in statistical_tests.items():
            for test_name, test_result in tests.items():
                if isinstance(test_result, dict) and 'p_value' in test_result:
                    p_values.append(test_result['p_value'])
                    test_names.append(f"{test_category}.{test_name}")
        
        if p_values:
            # Bonferroni correction
            bonferroni_alpha = 0.05 / len(p_values)
            bonferroni_significant = [p < bonferroni_alpha for p in p_values]
            
            # Benjamini-Hochberg FDR correction
            fdr_significant = self._benjamini_hochberg_correction(p_values, 0.05)
            
            corrected_results = {
                'original_p_values': dict(zip(test_names, p_values)),
                'bonferroni': {
                    'corrected_alpha': bonferroni_alpha,
                    'significant_tests': dict(zip(test_names, bonferroni_significant)),
                    'num_significant': sum(bonferroni_significant)
                },
                'fdr_bh': {
                    'significant_tests': dict(zip(test_names, fdr_significant)),
                    'num_significant': sum(fdr_significant)
                }
            }
        
        return corrected_results
    
    def _benjamini_hochberg_correction(self, p_values: List[float], alpha: float = 0.05) -> List[bool]:
        """
        Apply Benjamini-Hochberg FDR correction.
        
        Args:
            p_values: List of p-values
            alpha: Significance level
            
        Returns:
            List of boolean values indicating significance after correction
        """
        n = len(p_values)
        
        # Sort p-values with original indices
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]
        
        # Apply BH procedure
        significant = np.zeros(n, dtype=bool)
        
        for i in range(n - 1, -1, -1):
            if sorted_p_values[i] <= (i + 1) / n * alpha:
                significant[sorted_indices[:i + 1]] = True
                break
        
        return significant.tolist()
    
    def clear_cache(self) -> None:
        """Clear the data cache to free memory."""
        self._data_cache.clear()
        self.logger.debug("Cleared data cache")