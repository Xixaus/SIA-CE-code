"""
SIA_API - Sequential Injection Analysis Control System.

This package provides comprehensive control for Sequential Injection Analysis
systems including syringe pumps, valve selectors, and prepared workflow methods.
"""

# Version information
__version__ = "1.0.0"
__author__ = "Richard Maršala"

# Import main components for convenient access
from .devices.syringe_controller import SyringeController
from .devices.valve_selector import ValveSelector
from .methods.prepared_methods import PreparedSIMethods
from .methods.config import SIConfig, DEFAULT_CONFIG
from .core.command_sender import CommandSender

__all__ = [
    'SyringeController',
    'ValveSelector', 
    'PreparedSIMethods',
    'SIConfig',
    'DEFAULT_CONFIG',
    'CommandSender',
    '__version__',
    '__author__',
]