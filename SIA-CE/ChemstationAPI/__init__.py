"""
ChemStation API - Unified interface for Agilent 7100 CE system control.

This package provides comprehensive control of Agilent ChemStation software
and CE instruments through file-based communication protocol.
"""

from .ChemstationAPI import ChemstationAPI
from .core.communication_config import CommunicationConfig
from .exceptions import (
    ChemstationError,
    CommunicationError,
    CommandError,
    FileOperationError,
    SequenceError,
    MethodError,
    VialError,
    ConfigurationError,
    ValidationError,
    TimeoutError
)

__version__ = "0.1.0"
__author__ = "Richard Maršala"
__email__ = "your.email@example.com"

__all__ = [
    # Main API
    'ChemstationAPI',
    'CommunicationConfig',
    
    # Exceptions
    'ChemstationError',
    'CommunicationError',
    'CommandError',
    'FileOperationError',
    'SequenceError',
    'MethodError',
    'VialError',
    'ConfigurationError',
    'ValidationError',
    'TimeoutError',
]

# Convenience function for quick setup
def create_api(port=None, config=None):
    """
    Quick setup function for ChemStation API.
    
    Args:
        port: COM port for communication
        config: Optional CommunicationConfig instance
        
    Returns:
        Initialized ChemstationAPI instance
    """
    if config is None:
        config = CommunicationConfig()
    return ChemstationAPI(config)