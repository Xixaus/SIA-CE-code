"""
Configuration management for SIA system.
Simple centralized configuration for all adjustable parameters.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SIAConfig:
    """
    Complete configuration for SIA system.
    All adjustable parameters in one place.
    """
    # Port assignments
    waste_port: int = 1
    air_port: int = 2
    di_port: int = 3
    transfer_port: int = 4
    meoh_port: int = 5
    naoh_port: int = 6
    buffer_port: int = 7
    sample_port: int = 8
    
    # Standard vial positions
    wash_vial: int = 48
    dry_vial: int = 49
    waste_vial: int = 50
    cleaning_solution_vial: int = 47
    
    # Volumes (µL)
    default_bubble_volume: int = 15
    default_transfer_line_volume: int = 600
    default_holding_coil_volume: int = 1000
    default_needle_flush: int = 50
    default_cleaning_solution_volume: int = 350
    default_air_flush: int = 30
    default_homogenization_volume: int = 320
    
    # Speeds (µL/min)
    speed_air: int = 5000
    speed_fast: int = 3500
    speed_normal: int = 2000
    speed_slow: int = 1500
    speed_cleaning: int = 2500
    speed_homogenization_aspirate: int = 2000
    speed_homogenization_dispense: int = 2000
    
    # Homogenization defaults
    homogenization_liquid_cycles: int = 2
    homogenization_air_cycles: int = 3
    homogenization_clean_after: bool = True
    
    # Timing (seconds)
    wait_vial_load: float = 2.0
    wait_vial_unload: float = 1.0
    wait_after_aspirate: float = 1.0
    wait_after_dispense: float = 0.5
    wait_homogenization_settle: float = 5.0
    wait_cleaning_reaction: float = 3.0
    
    # Display settings
    verbose: bool = True  # Global verbose setting


# Default configuration instance
DEFAULT_CONFIG = SIAConfig()