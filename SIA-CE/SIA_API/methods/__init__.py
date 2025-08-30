"""
SIA_API.methods - High-level workflow methods and configuration management.

This module provides complete automation workflows for SIA systems and
comprehensive configuration management.
"""

# High-level workflow methods
from .prepared_methods import PreparedSIMethods

# Configuration system
from .config import (
    SIConfig,
    DEFAULT_CONFIG,
    validate_config,
    create_config_from_dict,
    config_to_dict,
    create_high_throughput_config,
    create_precision_config, 
    create_cleaning_intensive_config
)

__all__ = [
    # Workflow methods
    'PreparedSIMethods',
    
    # Configuration management
    'SIConfig',
    'DEFAULT_CONFIG',
    'validate_config',
    'create_config_from_dict',
    'config_to_dict',
    'create_high_throughput_config',
    'create_precision_config',
    'create_cleaning_intensive_config',
]