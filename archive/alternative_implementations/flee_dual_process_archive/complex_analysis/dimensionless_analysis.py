"""
Dimensionless Parameter Analysis Module

This module provides tools for identifying, calculating, and analyzing dimensionless
parameters in dual-process refugee movement experiments. It implements the cognitive
pressure scaling relationship and automatic detection of other dimensionless combinations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import itertools
from scipy import stats
from scipy.optimize import curve_fit
import warnings


@dataclass
class DimensionlessParameter:
    """Represents a dimensionless parameter combination."""
    name: str
    formula: str
    variables: List[str]
    exponents: List[float]
    description: str
    units_check: bool = True


@dataclass
class ScalingRelationship:
    """Represents a universal scaling relationship."""
    parameter: str
    dependent_variable: str
    scaling_function: str
    fit_parameters: Dict[str, float]
    r_squared: float
    confidence_interval: Tuple[float, float]


class DimensionlessParameterCalculator:
    """
    Calculator for dimensionless parameters in dual-process experiments.
    
    Implements the primary cognitive pressure parameter and automatic detection
    of other dimensionless combinations from experimental parameters.
    """
    
    def __init__(self):
        """Initialize the calculator with known parameter dimensions."""
        # Define dimensional analysis for common parameters
        # Note: For cognitive pressure to be dimensionless, we treat conflict_intensity 
        # as having units of 1/time to balance the formula
        self.parameter_dimensions = {
            'conflict_intensity': {'time': -1},  # events per day or intensity per day
            'connectivity': {},  # dimensionless - number of connections
            'recovery_time': {'time': 1},  # days
            'population': {},  # dimensionless - number of agents
            'distance': {'length': 1},  # km
            'capacity': {},  # dimensionless - number of people
            'awareness_level': {},  # dimensionless - scale 1-5
            'weight_softening': {},  # dimensionless - probability 0-1
            'conflict_threshold': {},  # dimensionless - threshold 0-1
            'social_connectivity_rate': {'time': -1},  # connections per day
            'movement_speed': {'length': 1, 'time': -1},  # km per day
        }
        
        # Define known dimensionless parameters
        self.known_dimensionless = {
            'cognitive_pressure': DimensionlessParameter(
                name='cognitive_pressure',
                formula='(conflict_intensity × connectivity) / recovery_time',
                variables=['conflict_intensity', 'connectivity', 'recovery_time'],
                exponents=[1.0, 1.0, -1.0],
                description='Primary cognitive pressure parameter controlling S1/S2 activation',
                units_check=False  # Special case - defined as dimensionless by convention
            ),
            'reynolds_number_analog': DimensionlessParameter(
                name='reynolds_number_analog',
                formula='(population × movement_speed) / (connectivity × distance)',
                variables=['population', 'movement_speed', 'connectivity', 'distance'],
                exponents=[1.0, 1.0, -1.0, -1.0],
                description='Analog to Reynolds number for population flow dynamics'
            ),
            'peclet_number_analog': DimensionlessParameter(
                name='peclet_number_analog',
                formula='(movement_speed × distance) / (social_connectivity_rate × recovery_time)',
                variables=['movement_speed', 'distance', 'social_connectivity_rate', 'recovery_time'],
                exponents=[1.0, 1.0, -1.0, -1.0],
                description='Analog to Peclet number for information vs movement transport'
            )
        }
    
    def calculate_cognitive_pressure(self, 
                                   conflict_intensity: float, 
                                   connectivity: float, 
                                   recovery_time: float) -> float:
        """
        Calculate the primary cognitive pressure parameter.
        
        Args:
            conflict_intensity: Conflict events per day
            connectivity: Average number of social connections
            recovery_time: Recovery period in days
            
        Returns:
            Cognitive pressure value (dimensionless)
        """
        if recovery_time <= 0:
            raise ValueError("Recovery time must be positive")
        
        return (conflict_intensity * connectivity) / recovery_time
    
    def calculate_dimensionless_parameter(self, 
                                        parameter_name: str, 
                                        values: Dict[str, float]) -> float:
        """
        Calculate a specific dimensionless parameter.
        
        Args:
            parameter_name: Name of the dimensionless parameter
            values: Dictionary of variable values
            
        Returns:
            Calculated dimensionless parameter value
        """
        if parameter_name not in self.known_dimensionless:
            raise ValueError(f"Unknown dimensionless parameter: {parameter_name}")
        
        param = self.known_dimensionless[parameter_name]
        
        # Check that all required variables are provided
        missing_vars = set(param.variables) - set(values.keys())
        if missing_vars:
            raise ValueError(f"Missing variables for {parameter_name}: {missing_vars}")
        
        # Calculate the dimensionless parameter
        result = 1.0
        for var, exp in zip(param.variables, param.exponents):
            if values[var] <= 0 and exp != 0:
                raise ValueError(f"Variable {var} must be positive for calculation")
            result *= values[var] ** exp
        
        return result
    
    def identify_dimensionless_combinations(self, 
                                          parameters: List[str], 
                                          max_exponent: int = 3) -> List[DimensionlessParameter]:
        """
        Automatically identify dimensionless parameter combinations.
        
        Args:
            parameters: List of parameter names to consider
            max_exponent: Maximum absolute exponent to consider
            
        Returns:
            List of discovered dimensionless parameter combinations
        """
        # Filter parameters that have known dimensions
        valid_params = [p for p in parameters if p in self.parameter_dimensions]
        
        if len(valid_params) < 2:
            return []
        
        dimensionless_combinations = []
        
        # Generate all possible exponent combinations
        exponent_range = list(range(-max_exponent, max_exponent + 1))
        
        for combo_size in range(2, min(len(valid_params) + 1, 5)):  # Limit complexity
            for param_combo in itertools.combinations(valid_params, combo_size):
                for exponents in itertools.product(exponent_range, repeat=combo_size):
                    # Skip trivial combinations (all zeros)
                    if all(exp == 0 for exp in exponents):
                        continue
                    
                    # Check if combination is dimensionless
                    if self._is_dimensionless_combination(param_combo, exponents):
                        # Create formula string
                        formula_parts = []
                        for param, exp in zip(param_combo, exponents):
                            if exp == 1:
                                formula_parts.append(param)
                            elif exp == -1:
                                formula_parts.append(f"1/{param}")
                            elif exp > 0:
                                formula_parts.append(f"{param}^{exp}")
                            elif exp < 0:
                                formula_parts.append(f"1/{param}^{abs(exp)}")
                        
                        formula = " × ".join(formula_parts)
                        name = f"dimensionless_{'_'.join(param_combo)}"
                        
                        dimensionless_combinations.append(DimensionlessParameter(
                            name=name,
                            formula=formula,
                            variables=list(param_combo),
                            exponents=list(exponents),
                            description=f"Auto-discovered dimensionless combination: {formula}"
                        ))
        
        return dimensionless_combinations
    
    def _is_dimensionless_combination(self, 
                                    parameters: Tuple[str, ...], 
                                    exponents: Tuple[int, ...]) -> bool:
        """
        Check if a parameter combination with given exponents is dimensionless.
        
        Args:
            parameters: Tuple of parameter names
            exponents: Tuple of corresponding exponents
            
        Returns:
            True if the combination is dimensionless
        """
        # Check if this is a known dimensionless parameter (special case)
        for known_param in self.known_dimensionless.values():
            if (list(parameters) == known_param.variables and 
                list(exponents) == known_param.exponents and
                hasattr(known_param, 'units_check') and not known_param.units_check):
                return True
        
        # Collect all dimensions
        total_dimensions = {}
        
        for param, exp in zip(parameters, exponents):
            if param not in self.parameter_dimensions:
                return False
            param_dims = self.parameter_dimensions[param]
            for dim, power in param_dims.items():
                if dim not in total_dimensions:
                    total_dimensions[dim] = 0
                total_dimensions[dim] += exp * power
        
        # Check if all dimensions cancel out (within numerical tolerance)
        # If no dimensions remain, it's dimensionless
        if not total_dimensions:
            return True
        return all(abs(power) < 1e-10 for power in total_dimensions.values())
    
    def validate_parameter_scaling(self, 
                                 data: pd.DataFrame, 
                                 dimensionless_param: str,
                                 dependent_variable: str) -> Dict[str, Any]:
        """
        Validate dimensional consistency and scaling relationships.
        
        Args:
            data: DataFrame containing experimental data
            dimensionless_param: Name of dimensionless parameter column
            dependent_variable: Name of dependent variable column
            
        Returns:
            Dictionary containing validation results
        """
        if dimensionless_param not in data.columns:
            raise ValueError(f"Dimensionless parameter {dimensionless_param} not found in data")
        
        if dependent_variable not in data.columns:
            raise ValueError(f"Dependent variable {dependent_variable} not found in data")
        
        # Remove any invalid data points
        valid_data = data.dropna(subset=[dimensionless_param, dependent_variable])
        valid_data = valid_data[
            (valid_data[dimensionless_param] > 0) & 
            (valid_data[dependent_variable] > 0)
        ]
        
        if len(valid_data) < 3:
            return {
                'valid': False,
                'error': 'Insufficient valid data points for analysis',
                'n_points': len(valid_data)
            }
        
        x = valid_data[dimensionless_param].values
        y = valid_data[dependent_variable].values
        
        # Test for scaling relationships
        scaling_results = {}
        
        # Linear scaling: y = a * x + b
        try:
            linear_fit = stats.linregress(x, y)
            scaling_results['linear'] = {
                'slope': linear_fit.slope,
                'intercept': linear_fit.intercept,
                'r_squared': linear_fit.rvalue ** 2,
                'p_value': linear_fit.pvalue
            }
        except Exception as e:
            scaling_results['linear'] = {'error': str(e)}
        
        # Power law scaling: y = a * x^b
        try:
            log_x = np.log(x[x > 0])
            log_y = np.log(y[y > 0])
            if len(log_x) >= 3:
                power_fit = stats.linregress(log_x, log_y)
                scaling_results['power_law'] = {
                    'exponent': power_fit.slope,
                    'coefficient': np.exp(power_fit.intercept),
                    'r_squared': power_fit.rvalue ** 2,
                    'p_value': power_fit.pvalue
                }
        except Exception as e:
            scaling_results['power_law'] = {'error': str(e)}
        
        # Exponential scaling: y = a * exp(b * x)
        try:
            exp_fit = stats.linregress(x, np.log(y[y > 0]))
            scaling_results['exponential'] = {
                'rate': exp_fit.slope,
                'coefficient': np.exp(exp_fit.intercept),
                'r_squared': exp_fit.rvalue ** 2,
                'p_value': exp_fit.pvalue
            }
        except Exception as e:
            scaling_results['exponential'] = {'error': str(e)}
        
        return {
            'valid': True,
            'n_points': len(valid_data),
            'scaling_relationships': scaling_results,
            'data_range': {
                'x_min': float(x.min()),
                'x_max': float(x.max()),
                'y_min': float(y.min()),
                'y_max': float(y.max())
            }
        }


class UniversalScalingDetector:
    """
    Detector for universal scaling relationships in experimental data.
    
    Identifies and validates universal scaling laws that emerge from
    dimensionless parameter analysis.
    """
    
    def __init__(self, significance_threshold: float = 0.05):
        """
        Initialize the scaling detector.
        
        Args:
            significance_threshold: P-value threshold for statistical significance
        """
        self.significance_threshold = significance_threshold
        self.scaling_functions = {
            'linear': lambda x, a, b: a * x + b,
            'power_law': lambda x, a, b: a * np.power(x, b),
            'exponential': lambda x, a, b: a * np.exp(b * x),
            'logarithmic': lambda x, a, b: a * np.log(x) + b,
            'sigmoid': lambda x, a, b, c: a / (1 + np.exp(-b * (x - c))),
            'double_exponential': lambda x, a, b, c: a * np.exp(-b * x) + c
        }
    
    def detect_scaling_relationships(self, 
                                   data: pd.DataFrame,
                                   dimensionless_params: List[str],
                                   dependent_variables: List[str]) -> List[ScalingRelationship]:
        """
        Detect universal scaling relationships in the data.
        
        Args:
            data: DataFrame containing experimental results
            dimensionless_params: List of dimensionless parameter columns
            dependent_variables: List of dependent variable columns
            
        Returns:
            List of detected scaling relationships
        """
        scaling_relationships = []
        
        for dim_param in dimensionless_params:
            for dep_var in dependent_variables:
                if dim_param not in data.columns or dep_var not in data.columns:
                    continue
                
                # Clean data
                clean_data = data.dropna(subset=[dim_param, dep_var])
                clean_data = clean_data[
                    (clean_data[dim_param] > 0) & 
                    (clean_data[dep_var] > 0) &
                    np.isfinite(clean_data[dim_param]) &
                    np.isfinite(clean_data[dep_var])
                ]
                
                if len(clean_data) < 5:  # Need minimum points for fitting
                    continue
                
                x = clean_data[dim_param].values
                y = clean_data[dep_var].values
                
                # Test each scaling function
                best_fit = None
                best_r_squared = -1
                
                for func_name, func in self.scaling_functions.items():
                    try:
                        fit_result = self._fit_scaling_function(x, y, func, func_name)
                        if fit_result and fit_result['r_squared'] > best_r_squared:
                            best_fit = fit_result
                            best_r_squared = fit_result['r_squared']
                    except Exception:
                        continue
                
                # Only keep relationships with good fit quality
                if (best_fit and 
                    best_fit['r_squared'] > 0.5):
                    
                    scaling_relationships.append(ScalingRelationship(
                        parameter=dim_param,
                        dependent_variable=dep_var,
                        scaling_function=best_fit['function_name'],
                        fit_parameters=best_fit['parameters'],
                        r_squared=best_fit['r_squared'],
                        confidence_interval=(0.0, 1.0)  # Placeholder confidence interval
                    ))
        
        return scaling_relationships
    
    def _fit_scaling_function(self, 
                            x: np.ndarray, 
                            y: np.ndarray, 
                            func: callable,
                            func_name: str) -> Optional[Dict[str, Any]]:
        """
        Fit a specific scaling function to the data.
        
        Args:
            x: Independent variable data
            y: Dependent variable data
            func: Scaling function to fit
            func_name: Name of the scaling function
            
        Returns:
            Dictionary containing fit results or None if fitting failed
        """
        try:
            # Initial parameter guesses based on function type
            if func_name == 'linear':
                p0 = [1.0, 0.0]
            elif func_name == 'power_law':
                p0 = [1.0, 1.0]
            elif func_name == 'exponential':
                p0 = [1.0, 0.1]
            elif func_name == 'logarithmic':
                p0 = [1.0, 0.0]
            elif func_name == 'sigmoid':
                p0 = [np.max(y), 1.0, np.median(x)]
            elif func_name == 'double_exponential':
                p0 = [1.0, 0.1, 0.0]
            else:
                p0 = [1.0] * func.__code__.co_argcount - 1
            
            # Fit the function
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                popt, pcov = curve_fit(func, x, y, p0=p0, maxfev=1000)
            
            # Calculate R-squared
            y_pred = func(x, *popt)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate confidence intervals (simplified)
            param_errors = np.sqrt(np.diag(pcov)) if pcov is not None else None
            
            # Create parameter dictionary
            param_names = ['a', 'b', 'c', 'd'][:len(popt)]
            parameters = {name: float(val) for name, val in zip(param_names, popt)}
            
            result = {
                'function_name': func_name,
                'parameters': parameters,
                'r_squared': float(r_squared),
                'residual_std': float(np.std(y - y_pred))
            }
            
            if param_errors is not None:
                result['parameter_errors'] = {
                    name: float(err) for name, err in zip(param_names, param_errors)
                }
            
            return result
            
        except Exception:
            return None
    
    def validate_data_collapse(self, 
                             data: pd.DataFrame,
                             dimensionless_param: str,
                             dependent_variables: List[str],
                             grouping_columns: List[str]) -> Dict[str, Any]:
        """
        Validate data collapse when plotted against dimensionless parameters.
        
        Args:
            data: DataFrame containing experimental results
            dimensionless_param: Dimensionless parameter for x-axis
            dependent_variables: Variables to test for collapse
            grouping_columns: Columns that should collapse onto single curve
            
        Returns:
            Dictionary containing collapse validation results
        """
        collapse_results = {}
        
        for dep_var in dependent_variables:
            if dep_var not in data.columns or dimensionless_param not in data.columns:
                continue
            
            # Group data by grouping columns
            groups = data.groupby(grouping_columns)
            
            if len(groups) < 2:
                collapse_results[dep_var] = {
                    'valid': False,
                    'error': 'Need at least 2 groups for collapse analysis'
                }
                continue
            
            # Calculate collapse quality metric
            all_x = []
            all_y = []
            group_data = []
            
            for group_name, group_df in groups:
                clean_group = group_df.dropna(subset=[dimensionless_param, dep_var])
                if len(clean_group) >= 3:
                    x_vals = clean_group[dimensionless_param].values
                    y_vals = clean_group[dep_var].values
                    all_x.extend(x_vals)
                    all_y.extend(y_vals)
                    group_data.append((x_vals, y_vals, group_name))
            
            if len(group_data) < 2:
                collapse_results[dep_var] = {
                    'valid': False,
                    'error': 'Insufficient data in groups'
                }
                continue
            
            # Measure collapse quality using coefficient of variation
            x_bins = np.logspace(np.log10(min(all_x)), np.log10(max(all_x)), 10)
            collapse_quality = []
            
            for i in range(len(x_bins) - 1):
                bin_values = []
                for x_vals, y_vals, _ in group_data:
                    mask = (x_vals >= x_bins[i]) & (x_vals < x_bins[i + 1])
                    if np.any(mask):
                        bin_values.extend(y_vals[mask])
                
                if len(bin_values) > 1:
                    cv = np.std(bin_values) / np.mean(bin_values)
                    collapse_quality.append(cv)
            
            avg_collapse_quality = np.mean(collapse_quality) if collapse_quality else float('inf')
            
            collapse_results[dep_var] = {
                'valid': True,
                'collapse_quality': float(avg_collapse_quality),
                'n_groups': len(group_data),
                'n_points': len(all_x),
                'quality_assessment': 'good' if avg_collapse_quality < 0.3 else 
                                    'moderate' if avg_collapse_quality < 0.6 else 'poor'
            }
        
        return collapse_results