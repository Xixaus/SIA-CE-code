"""
Configuration management for SI (Sequential Injection) system.

This module provides centralized configuration for all adjustable parameters
used in SI workflows. The SIConfig dataclass contains all system parameters
organized into logical groups for easy maintenance and customization.

Example:
    >>> from config import SIConfig, DEFAULT_CONFIG
    >>> 
    >>> # Use default configuration
    >>> config = DEFAULT_CONFIG
    >>> 
    >>> # Create custom configuration
    >>> custom_config = SIAConfig(
    ...     speed_normal=1800,
    ...     verbose=False,
    ...     homogenization_liquid_cycles=3
    ... )
    >>> 
    >>> # Modify existing configuration
    >>> config.speed_fast = 4000
    >>> config.default_bubble_volume = 20
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SIConfig:
    """
    Complete configuration for SI (Sequential Injection) system.
    
    This dataclass contains all adjustable parameters organized into logical
    groups. All parameters have sensible defaults that work for most
    applications, but can be customized as needed.
    
    The configuration covers:
    - Port assignments for different reagents and functions
    - Standard vial positions for system components
    - Volume parameters for various operations
    - Speed settings for different types of flows
    - Timing parameters for system operations
    - Homogenization settings
    - Display and logging preferences
    
    Attributes are grouped logically and documented individually below.
    """
    
    # ==========================================================================
    # PORT ASSIGNMENTS
    # ==========================================================================
    # These define which valve ports are connected to which reagents/functions
    
    waste_port: int = 1
    """Port connected to waste line (typically port 1)"""
    
    air_port: int = 2
    """Port for air aspiration (typically port 2)"""
    
    di_port: int = 3
    """Port connected to deionized water reservoir (typically port 3)"""
    
    transfer_port: int = 4
    """Port connected to transfer line leading to sample needle (typically port 4)"""
    
    meoh_port: int = 5
    """Port connected to methanol reservoir for cleaning (typically port 5)"""
    
    naoh_port: int = 6
    """Port connected to sodium hydroxide solution for cleaning (typically port 6)"""
    
    buffer_port: int = 7
    """Port connected to buffer solution reservoir (typically port 7)"""
    
    sample_port: int = 8
    """Port connected to sample input line (typically port 8)"""
    
    # ==========================================================================
    # STANDARD VIAL POSITIONS
    # ==========================================================================
    # Fixed positions in the autosampler carousel for system functions
    
    wash_vial: int = 48
    """Carousel position for needle wash vial (contains wash solution)"""
    
    dry_vial: int = 49
    """Carousel position for dry/empty vial (for air aspiration if needed)"""
    
    waste_vial: int = 50
    """Carousel position for waste collection vial"""
    
    cleaning_solution_vial: int = 47
    """Carousel position for cleaning solution vial (e.g., NaOH solution)"""
    
    # ==========================================================================
    # VOLUME PARAMETERS (in microliters)
    # ==========================================================================
    # Default volumes for various operations - can be overridden in method calls
    
    # Bubble and separation volumes
    default_bubble_volume: int = 15
    """Default volume for separating air bubbles between different solutions (µL)"""
    
    # System volumes
    default_transfer_line_volume: int = 600
    """Volume of the transfer line from valve to sample needle (µL)"""
    
    default_holding_coil_volume: int = 1000
    """Volume of the holding coil in the flow injection system (µL)"""
    
    # Cleaning and maintenance volumes
    default_needle_flush: int = 50
    """Default volume for flushing the sample needle to prevent contamination (µL)"""
    
    default_cleaning_solution_volume: int = 350
    """Default volume of cleaning solution (e.g., NaOH) for system cleaning (µL)"""
    
    default_air_flush: int = 30
    """Default volume of air for flushing operations (µL)"""
    
    # Homogenization volumes
    default_homogenization_volume: int = 320
    """Default volume to aspirate/dispense during sample homogenization (µL)"""
    
    # ==========================================================================
    # FLOW RATE PARAMETERS (in microliters per minute)
    # ==========================================================================
    # Speed settings for different types of operations
    
    # Basic flow rates
    speed_air: int = 5000
    """High speed for air aspiration and fast transfers (µL/min)"""
    
    speed_fast: int = 3500
    """Fast flow rate for routine liquid transfers (µL/min)"""
    
    speed_normal: int = 2000
    """Normal flow rate for standard operations (µL/min)"""
    
    speed_slow: int = 1500
    """Slow flow rate for precise operations or viscous liquids (µL/min)"""
    
    # Specialized flow rates
    speed_cleaning: int = 2500
    """Flow rate for cleaning operations (µL/min)"""
    
    speed_homogenization_aspirate: int = 2000
    """Flow rate for aspirating during sample homogenization (µL/min)"""
    
    speed_homogenization_dispense: int = 2000
    """Flow rate for dispensing during sample homogenization (µL/min)"""
    
    # ==========================================================================
    # HOMOGENIZATION SETTINGS
    # ==========================================================================
    # Default parameters for sample homogenization operations
    
    homogenization_liquid_cycles: int = 2
    """Number of aspiration/dispense cycles for liquid-based homogenization"""
    
    homogenization_air_cycles: int = 3
    """Number of aspiration/dispense cycles for air bubble-based homogenization"""
    
    homogenization_clean_after: bool = False
    """Whether to automatically clean the transfer line after homogenization"""
    
    # ==========================================================================
    # TIMING PARAMETERS (in seconds)
    # ==========================================================================
    # Wait times for various operations to ensure proper system response
    
    # Vial handling timing
    wait_vial_load: float = 2.0
    """Wait time after loading a vial to replenishment position (seconds)"""
    
    wait_vial_unload: float = 1.0
    """Wait time after unloading a vial from replenishment position (seconds)"""
    
    # Flow operation timing
    wait_after_aspirate: float = 1.0
    """Wait time after liquid aspiration for system stabilization (seconds)"""
    
    wait_after_dispense: float = 0.5
    """Wait time after liquid dispensing for system stabilization (seconds)"""
    
    # Specialized operation timing
    wait_homogenization_settle: float = 5.0
    """Wait time for sample settling during homogenization operations (seconds)"""
    
    wait_cleaning_reaction: float = 3.0
    """Wait time for cleaning solution to react before flushing (seconds)"""
    
    # ==========================================================================
    # DISPLAY AND LOGGING SETTINGS
    # ==========================================================================
    # Parameters controlling system output and user feedback
    
    verbose: bool = True
    """Global verbose setting - controls whether status messages are displayed"""


# =============================================================================
# DEFAULT CONFIGURATION INSTANCE
# =============================================================================

DEFAULT_CONFIG = SIConfig()
"""
Default configuration instance with standard parameters.

This instance can be used directly for most applications, or serves as a 
starting point for creating custom configurations.

Example:
    >>> from config import DEFAULT_CONFIG
    >>> 
    >>> # Use directly
    >>> my_workflow = PreparedSIMethods(controller, syringe, valve, DEFAULT_CONFIG)
    >>> 
    >>> # Or modify as needed
    >>> DEFAULT_CONFIG.speed_normal = 1800
    >>> DEFAULT_CONFIG.verbose = False
"""


# =============================================================================
# CONFIGURATION VALIDATION AND UTILITIES
# =============================================================================

def validate_config(config: SIConfig) -> list[str]:
    """
    Validate a SIConfig instance and return any issues found.
    
    Args:
        config: The SIConfig instance to validate
        
    Returns:
        List of validation error messages (empty if no issues)
        
    Example:
        >>> config = SIConfig(speed_normal=-100)  # Invalid negative speed
        >>> errors = validate_config(config)
        >>> if errors:
        ...     print("Configuration issues:", errors)
    """
    errors = []
    
    # Validate port numbers (should be 1-8 for typical valve systems)
    ports = [
        config.waste_port, config.air_port, config.di_port, config.transfer_port,
        config.meoh_port, config.naoh_port, config.buffer_port, config.sample_port
    ]
    
    for i, port in enumerate(ports):
        if not (1 <= port <= 8):
            port_names = ['waste', 'air', 'di', 'transfer', 'meoh', 'naoh', 'buffer', 'sample']
            errors.append(f"{port_names[i]}_port ({port}) should be between 1 and 8")
    
    # Check for duplicate ports
    if len(set(ports)) != len(ports):
        errors.append("Duplicate port assignments detected")
    
    # Validate vial positions (should be 1-50 for typical autosamplers)
    vials = [config.wash_vial, config.dry_vial, config.waste_vial, config.cleaning_solution_vial]
    for i, vial in enumerate(vials):
        if not (1 <= vial <= 50):
            vial_names = ['wash', 'dry', 'waste', 'cleaning_solution']
            errors.append(f"{vial_names[i]}_vial ({vial}) should be between 1 and 50")
    
    # Validate volumes (should be positive)
    volumes = [
        config.default_bubble_volume, config.default_transfer_line_volume,
        config.default_holding_coil_volume, config.default_needle_flush,
        config.default_cleaning_solution_volume, config.default_air_flush,
        config.default_homogenization_volume
    ]
    
    volume_names = [
        'default_bubble_volume', 'default_transfer_line_volume',
        'default_holding_coil_volume', 'default_needle_flush',
        'default_cleaning_solution_volume', 'default_air_flush',
        'default_homogenization_volume'
    ]
    
    for volume, name in zip(volumes, volume_names):
        if volume <= 0:
            errors.append(f"{name} ({volume}) should be positive")
    
    # Validate speeds (should be positive)
    speeds = [
        config.speed_air, config.speed_fast, config.speed_normal, config.speed_slow,
        config.speed_cleaning, config.speed_homogenization_aspirate,
        config.speed_homogenization_dispense
    ]
    
    speed_names = [
        'speed_air', 'speed_fast', 'speed_normal', 'speed_slow',
        'speed_cleaning', 'speed_homogenization_aspirate',
        'speed_homogenization_dispense'
    ]
    
    for speed, name in zip(speeds, speed_names):
        if speed <= 0:
            errors.append(f"{name} ({speed}) should be positive")
    
    # Validate cycle counts (should be positive integers)
    if config.homogenization_liquid_cycles <= 0:
        errors.append(f"homogenization_liquid_cycles ({config.homogenization_liquid_cycles}) should be positive")
    
    if config.homogenization_air_cycles <= 0:
        errors.append(f"homogenization_air_cycles ({config.homogenization_air_cycles}) should be positive")
    
    # Validate timing parameters (should be non-negative)
    timings = [
        config.wait_vial_load, config.wait_vial_unload, config.wait_after_aspirate,
        config.wait_after_dispense, config.wait_homogenization_settle, config.wait_cleaning_reaction
    ]
    
    timing_names = [
        'wait_vial_load', 'wait_vial_unload', 'wait_after_aspirate',
        'wait_after_dispense', 'wait_homogenization_settle', 'wait_cleaning_reaction'
    ]
    
    for timing, name in zip(timings, timing_names):
        if timing < 0:
            errors.append(f"{name} ({timing}) should be non-negative")
    
    return errors


def create_config_from_dict(config_dict: dict) -> SIConfig:
    """
    Create a SIConfig instance from a dictionary.
    
    Useful for loading configuration from JSON files or other sources.
    Unknown keys in the dictionary are ignored.
    
    Args:
        config_dict: Dictionary with configuration parameters
        
    Returns:
        New SIConfig instance with specified parameters
        
    Example:
        >>> config_data = {
        ...     'speed_normal': 1800,
        ...     'verbose': False,
        ...     'default_bubble_volume': 20
        ... }
        >>> config = create_config_from_dict(config_data)
    """
    # Get default config as starting point
    defaults = DEFAULT_CONFIG.__dict__.copy()
    
    # Update with provided values
    for key, value in config_dict.items():
        if key in defaults:
            defaults[key] = value
    
    return SIConfig(**defaults)


def config_to_dict(config: SIConfig) -> dict:
    """
    Convert a SIConfig instance to a dictionary.
    
    Useful for saving configuration to JSON files or other formats.
    
    Args:
        config: The SIConfig instance to convert
        
    Returns:
        Dictionary representation of the configuration
        
    Example:
        >>> config = SIConfig(speed_normal=1800)
        >>> config_dict = config_to_dict(config)
        >>> import json
        >>> json.dump(config_dict, open('config.json', 'w'), indent=2)
    """
    return config.__dict__.copy()


# =============================================================================
# CONFIGURATION PRESETS
# =============================================================================

def create_high_throughput_config() -> SIConfig:
    """
    Create a configuration optimized for high-throughput operations.
    
    This preset uses faster flow rates and shorter wait times to maximize
    sample processing speed, at the cost of some precision.
    
    Returns:
        SIConfig instance optimized for speed
    """
    return SIConfig(
        speed_fast=4000,
        speed_normal=2500,
        speed_slow=2000,
        wait_after_aspirate=0.5,
        wait_after_dispense=0.2,
        wait_vial_load=1.0,
        wait_vial_unload=0.5,
        homogenization_liquid_cycles=1,
        homogenization_air_cycles=2,
        verbose=True
    )


def create_precision_config() -> SIConfig:
    """
    Create a configuration optimized for high-precision operations.
    
    This preset uses slower flow rates and longer wait times to maximize
    precision and reproducibility, at the cost of throughput.
    
    Returns:
        SIConfig instance optimized for precision
    """
    return SIConfig(
        speed_fast=2500,
        speed_normal=1500,
        speed_slow=1000,
        wait_after_aspirate=2.0,
        wait_after_dispense=1.0,
        wait_vial_load=3.0,
        wait_vial_unload=2.0,
        homogenization_liquid_cycles=3,
        homogenization_air_cycles=4,
        wait_homogenization_settle=8.0,
        verbose=True
    )


def create_cleaning_intensive_config() -> SIConfig:
    """
    Create a configuration with enhanced cleaning procedures.
    
    This preset includes more thorough cleaning steps and larger cleaning
    volumes, suitable for applications requiring minimal cross-contamination.
    
    Returns:
        SIConfig instance with enhanced cleaning
    """
    return SIConfig(
        default_cleaning_solution_volume=500,
        default_needle_flush=100,
        wait_cleaning_reaction=5.0,
        homogenization_clean_after=True,
        speed_cleaning=2000,  # Slower for thorough cleaning
        verbose=True
    )