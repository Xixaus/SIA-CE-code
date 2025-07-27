"""
ChemStation API Controller - Main entry point for Agilent 7100 CE system control.

This module provides the unified interface for controlling the Agilent 7100 Capillary 
Electrophoresis System through ChemStation software. The API uses file-based communication
protocol to send commands and receive responses from ChemStation.

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
    """Main API controller for ChemStation.
    
    Serves as a unified gateway for all ChemStation functionality, organizing different 
    aspects of CE instrument control into logical modules. This class does not perform 
    business logic directly, but forwards calls to appropriate specialized modules.
    
    The API provides access to five main functional areas:
    - CE Module: Carousel vial handling, capillary operations, pressure control
    - Method Module: CE method management, parameter editing, method execution
    - Sequence Module: Sequence table editing, batch analysis management  
    - System Module: Instrument status monitoring, run control, diagnostics
    - Validation Module: Input validation, file existence checks, system state validation
    
    Communication Protocol:
        Uses file-based communication where commands are written to a command file
        and responses are read from a response file. ChemStation monitors the command
        file through a macro and executes commands via the Command Processor (CP).
    
    Attributes:
        ce (CEModule): Capillary Electrophoresis instrument control and vial management.
        method (MethodsModule): CE method loading, saving, parameter editing and execution.
        sequence (SequenceModule): Sequence table management and batch analysis control.
        system (SystemModule): System status monitoring and diagnostic functions.
        validation (ValidationModule): Input validation and system state checking.
    
    Example:
        Basic instrument control workflow:
        
        >>> # Initialize API connection
        >>> api = ChemstationAPI()
        
        >>> # Load vial to inlet position for analysis
        >>> api.ce.load_vial_to_position(15, "inlet")
        
        >>> # Load and execute a CE method
        >>> api.method.load("CE_Analysis_Method")
        >>> api.method.run("Sample_001")
        
        >>> # Monitor analysis progress
        >>> while api.system.method_on():
        ...     remaining = api.system.get_remaining_analysis_time()
        ...     print(f"Analysis remaining: {remaining:.1f} minutes")
        ...     time.sleep(30)
        
        >>> # Direct ChemStation command execution
        >>> current_voltage = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Voltage_actual"))')
        >>> print(f"Current HV: {current_voltage} kV")
    """
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        """Initialize ChemStation API controller.
        
        Sets up communication with ChemStation and initializes all functional modules.
        By default, tests the connection on startup to ensure ChemStation is responding.
        
        Args:
            config: Communication configuration settings. If None, uses default configuration
                   with standard file paths and communication parameters.
                   
        Raises:
            ConfigurationError: If communication setup fails or paths are invalid.
            ConnectionError: If ChemStation connection test fails (when test_on_init=True).
                           This typically indicates ChemStation is not running or the
                           communication macro is not loaded.
            
        Note:
            Before using the API, ensure ChemStation is running and execute this command
            in ChemStation's command line to start the communication macro:
            
            macro "path\\to\\ChemPyConnect.mac"; Python_Run
        """
        super().__init__(config)

        # Initialize all functional modules with shared communicator
        self.ce = CEModule(self)
        self.method = MethodsModule(self)
        self.sequence = SequenceModule(self)
        self.system = SystemModule(self)
        self.validation = ValidationModule(self)
            
    
    def send(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """Send command directly to ChemStation Command Processor.
        
        Executes raw ChemStation commands through the Command Processor (CP).
        This method provides direct access to ChemStation's scripting capabilities
        for advanced operations not covered by the specialized modules.
        
        For commands that should return a value, prefix the command with "response$ = "
        to capture the result. Commands without this prefix execute but return None.
        
        Args:
            command: ChemStation CP command string to execute. Can include:
                    - Variable assignments: SetTabHdrText, SetTabVal, SetObjHdrText
                    - Data retrieval: _METHPATH$, _DATAPATH$, ACQSTATUS$
                    - Module commands: WriteModule, SendModule$ 
                    - Macro calls: macro path; macro_name parameters
                    - System commands: LoadMethod, SaveMethod, RunMethod
            timeout: Maximum time to wait for command response in seconds.
                    Increase for long-running operations like method execution.
                    
        Returns:
            String response from ChemStation if command starts with "response$ = ...",
            otherwise None for commands that don't return values.
            
        Raises:
            CommandError: If ChemStation reports command execution failure.
            TimeoutError: If no response received within timeout period.
            ChemstationError: If ChemStation returns an error message.
            
        Examples:
            Get current method path:
            >>> path = api.send("response$ = _METHPATH$")
            >>> print(f"Method directory: {path}")
            
            Get current high voltage:
            >>> voltage = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Voltage_actual"))')
            >>> print(f"Current voltage: {voltage} kV")
            
            Load a specific method:
            >>> api.send('LoadMethod _METHPATH$, "MyMethod.M"')
            
            Execute a macro with parameters:
            >>> api.send('macro "c:\\macros\\mymacro.mac"; my_macro_name 15, "Sample001"')
            
            Send module command to CE instrument:
            >>> api.send('WriteModule "CE1", "FLSH 60.0,-2,-2"')  # 60s flush
        """
        return super().send(command, timeout)