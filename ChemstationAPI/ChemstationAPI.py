"""
ChemStation Main Controller - API Orchestrator.

This module provides the main entry point for the ChemStation API, initializing
all modules and providing a unified interface for accessing their functionality.

.. moduleauthor:: Richard Maršala
"""

from typing import Optional

from .core.chemstation_communication import ChemstationCommunicator, CommunicationConfig
from .controllers.ce_module import CEModule
from .controllers.sequence_module import SequenceModule
from .controllers.methods_module import MethodsModule
from .controllers.system_module import SystemModule
from .controllers.validation import ValidationModule
from .exceptions import *


class ChemstationAPI(ChemstationCommunicator):
    """Main controller - initializes modules and provides access to them.
    
    Serves as a unified interface (gateway) for all ChemStation modules.
    Does not perform business logic, only forwards calls to appropriate modules.
    
    This class provides a single entry point for all ChemStation functionality,
    organizing different aspects of instrument control into logical modules:
    - CE: Capillary Electrophoresis instrument control
    - Sequence: Sequence management and execution
    - Method: Method loading, saving, and execution
    - System: System monitoring and status management
    
    Attributes:
        ce: CEModule instance for vial handling and CE operations.
        method: MethodsModule instance for method management.
        sequence: SequenceModule instance for sequence management.
        system: SystemModule instance for system monitoring.
    
    Example:
        >>> api = ChemstationAPI()
        >>> api.ce.load_vial_to_position(15, VialPosition.INLET)
        >>> api.sequence.load_sequence("MySequence")
        >>> api.method.load("TestMethod")
        >>> status = api.system.status()
        >>> result = api.send("response$ = _METHPATH$")
    """
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        """Initialize ChemStation main controller.
        
        Args:
            config: Configuration for communication or None for default.
            
        Raises:
            ConfigurationError: If initialization failed.
            ConnectionError: If connection to ChemStation failed.
        """
        super().__init__(config)

        # Initialize all modules
        self.ce = CEModule(self)
        self.method = MethodsModule(self)
        self.sequence = SequenceModule(self)
        self.system = SystemModule(self)
        self.validation = ValidationModule(self)
            
    
    def send(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """Send command directly to ChemStation Command Processor.
        
        For getting a response in string format, add `response$ = ` at the
        beginning of the command.
        
        Args:
            command: CP command to execute.
            timeout: Timeout for response in seconds.
            
        Returns:
            Response from CP if command starts with "response$ = ...", otherwise None.
            
        Raises:
            CommandError: If command failed.
            TimeoutError: If response doesn't arrive within timeout.
            
        Example:
            >>> api = ChemstationAPI()
            >>> path = api.send("response$ = _METHPATH$")
            >>> print(f"Method path: {path}")
        """
        return super().send(command, timeout)