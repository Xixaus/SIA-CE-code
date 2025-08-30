"""
SIA API - Sequential Injection Analysis automation system.

This package provides control for syringe pumps, valve selectors,
and automated SI workflows for analytical chemistry applications.
"""

from .devices.syringe_controller import SyringeController
from .devices.valve_selector import ValveSelector
from .methods.prepared_methods import PreparedSIMethods
from .methods.config import SIConfig, DEFAULT_CONFIG
from .core.command_sender import CommandSender

__version__ = "0.1.0"
__author__ = "Richard Maršala"
__email__ = "your.email@example.com"

__all__ = [
    # Core
    'CommandSender',
    
    # Devices
    'SyringeController',
    'ValveSelector',
    
    # Methods
    'PreparedSIMethods',
    'SIConfig',
    'DEFAULT_CONFIG',
]

# Convenience function for quick setup
def create_si_system(syringe_port, valve_port, syringe_size=1000, num_valve_positions=8):
    """
    Quick setup function for SI system.
    
    Args:
        syringe_port: COM port for syringe pump
        valve_port: COM port for valve selector
        syringe_size: Syringe volume in µL (default: 1000)
        num_valve_positions: Number of valve positions (default: 8)
        
    Returns:
        Tuple of (SyringeController, ValveSelector)
    """
    syringe = SyringeController(
        port=syringe_port,
        syringe_size=syringe_size
    )
    valve = ValveSelector(
        port=valve_port,
        num_positions=num_valve_positions
    )
    return syringe, valve