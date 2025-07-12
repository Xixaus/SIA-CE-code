"""
Configuration management for SIA system port assignments.

Provides centralized configuration for valve position mappings to different
solvents, reagents, and system lines in SIA analytical workflows.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PortConfig:
    """
    Configuration for SIA system valve port assignments.
    
    Defines standard port mappings for common SIA system components.
    Allows customization while maintaining consistent interface across workflows.
    
    Attributes:
        waste_port: Port connected to waste line (default: 1)
        air_port: Port connected to air/gas line (default: 2)
        di_port: Port connected to deionized water (default: 3)
        transfer_port: Port connected to CE transfer line (default: 4)
        meoh_port: Port connected to methanol/organic solvent (default: 5)
    
    Examples:
        Using default configuration:
        
        >>> config = PortConfig()
        >>> print(config.waste_port)  # 1
        >>> print(config.meoh_port)   # 5
        
        Custom configuration:
        
        >>> custom = PortConfig(waste_port=8, meoh_port=6)
        >>> print(custom.waste_port)  # 8
        >>> print(custom.meoh_port)   # 6
    """
    waste_port: int = 1          # Port for waste line
    air_port: int = 2            # Port for air/gas line  
    di_port: int = 3             # Port for deionized water
    transfer_port: int = 4       # Port for CE transfer line
    meoh_port: int = 5           # Port for methanol/organic solvent


# Default configuration instance
DEFAULT_PORTS = PortConfig()


def create_custom_config(**kwargs) -> PortConfig:
    """
    Create custom port configuration with specified overrides.
    
    Args:
        **kwargs: Port assignments to override (waste_port, air_port, di_port, 
                 transfer_port, meoh_port)
    
    Returns:
        PortConfig instance with custom settings
    
    Raises:
        TypeError: If invalid port parameter is provided
    
    Examples:
        Override specific ports:
        
        >>> config = create_custom_config(waste_port=8, meoh_port=6)
        >>> config.waste_port  # 8
        >>> config.air_port    # 2 (default)
        
        Complete custom configuration:
        
        >>> config = create_custom_config(
        ...     waste_port=8,
        ...     air_port=1, 
        ...     di_port=2,
        ...     transfer_port=3,
        ...     meoh_port=4
        ... )
    """
    return PortConfig(**kwargs)


def validate_config(config: PortConfig) -> bool:
    """
    Validate port configuration for conflicts and valid ranges.
    
    Args:
        config: PortConfig instance to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration has duplicate ports or invalid ranges
        
    Examples:
        >>> config = PortConfig()
        >>> validate_config(config)  # True
        
        >>> bad_config = PortConfig(waste_port=1, air_port=1)  # Duplicate ports
        >>> validate_config(bad_config)  # Raises ValueError
    """
    ports = [config.waste_port, config.air_port, config.di_port, 
             config.transfer_port, config.meoh_port]
    
    # Check for duplicate ports
    if len(ports) != len(set(ports)):
        raise ValueError("Port assignments cannot be duplicated")
    
    # Check valid port range (typical valve selectors: 1-12 positions)
    if not all(1 <= port <= 12 for port in ports):
        raise ValueError("Port numbers must be in range 1-12")
    
    return True