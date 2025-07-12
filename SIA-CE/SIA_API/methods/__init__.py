"""
SIA - Serial Instrument Automation
Simple modular library for controlling syringe pumps and valve selectors
with basic port configuration.
"""
from ..devices.syringe_controller import SyringeController
from ..devices.valve_selector import ValveSelector
from .prepared_methods import PreparedSIAMethods  # Opravený import
from .config import create_custom_config, DEFAULT_PORTS, PortConfig  # Opravený import

__all__ = [
    # Device controllers
    'SyringeController',
    'ValveSelector',
    'Prepared_methods',  # Nový název třídy
   
    # Configuration
    'create_custom_config',
    'DEFAULT_PORTS', 
    'PortConfig'
]