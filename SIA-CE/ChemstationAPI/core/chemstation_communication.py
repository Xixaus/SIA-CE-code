"""
ChemStation Communication Protocol - File-based command/response interface.

This module implements the low-level communication protocol for interacting with 
Agilent ChemStation software through a file-based command/response system. The protocol
enables Python applications to send commands to ChemStation's Command Processor (CP)
and receive responses for automated instrument control.

Communication Architecture:
    Python Application ←→ Command/Response Files ←→ ChemStation Macro ←→ Command Processor

Protocol Operation:
    1. Python writes commands to command file with unique numbers
    2. ChemStation macro monitors file and executes commands via CP
    3. Responses written to response file with matching command numbers
    4. Python reads responses and matches them to original commands

File Format:
    Command File: "<command_number> <command_string>"
    Response File: "<command_number> <response_string>"

The communication is reliable, supports concurrent operations, and provides
timeout handling and error recovery mechanisms.

Original concept by:
    Alexander Hammer, Hessam Mehr
    https://github.com/croningp/analyticallabware/blob/master/AnalyticalLabware/devices/Agilent/hplc.py

.. moduleauthor:: Richard Maršala
"""

import os
import time
from typing import Optional

from .communication_config import CommunicationConfig
from ..exceptions import *


class ChemstationCommunicator:
    """Low-level file-based communication handler for ChemStation software.
    
    This class implements the communication protocol that enables Python applications
    to control ChemStation through file-based command/response exchange. The protocol
    uses numbered commands to ensure reliable command tracking and response matching.
    
    Communication Features:
        - Unique command numbering with wraparound for long sessions
        - Response matching and timeout handling
        - Retry logic for file operations and communication failures
        - Connection testing and validation
        - Error detection and reporting from ChemStation
    
    File Protocol Details:
        - Commands written to command file with incrementing numbers
        - ChemStation macro continuously monitors command file
        - Commands executed via ChemStation Command Processor (CP)
        - Responses written to response file with matching command numbers
        - Command numbers wrap around at configurable maximum
    
    Error Handling:
        - File operation retries with configurable delays
        - Timeout detection for unresponsive ChemStation
        - ChemStation error parsing and exception raising
        - Communication validation and recovery
    
    Attributes:
        config: Communication configuration settings and paths.
        command_number: Current command number counter for tracking.
        comm_dir: Path to communication directory containing files.
        command_file: Path to command file for outgoing commands.
        response_file: Path to response file for incoming responses.
        macros_path: Path to macro files for ChemStation integration.
    """

    def __init__(self, config: Optional[CommunicationConfig] = None):
        """Initialize ChemStation communication interface.
        
        Sets up file-based communication system, creates necessary directories
        and files, and optionally tests connection to ChemStation.
        
        Args:
            config: Communication configuration object. If None, uses default
                   configuration with standard paths and timeout settings.
                   
        Raises:
            ConfigurationError: If communication directory cannot be created
                               or configuration parameters are invalid.
            ConnectionError: If connection test fails (when test_on_init=True).
                           This typically indicates ChemStation is not running
                           or the communication macro is not loaded.
                           
        Note:
            Before using the communicator, ensure ChemStation is running and
            execute this command in ChemStation's command line:
            
            macro "path\\to\\ChemPyConnect.mac"; Python_Run
            
            This starts the monitoring macro that enables communication.
        """
        self.config = config or CommunicationConfig()
        self.command_number = 0
        
        # Initialize file paths from configuration
        self.comm_dir = self.config.get_comm_dir_path()
        self.command_file = self.config.get_command_file_path()
        self.response_file = self.config.get_response_file_path()
        self.macros_path = str(self.config.get_macros_path())
        
        # Set up communication environment
        try:
            self.comm_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigurationError(f"Failed to create communication directory: {e}")

        self._initialize_files()
        time.sleep(0.5)
        
        # Test connection if enabled in configuration
        if self.config.test_on_init:
            if self.config.verbose:
                print("Testing ChemStation connection...")
            
            if not self._test_connection():
                raise ConnectionError(
                    "Failed to establish communication with ChemStation.\n"
                    "Please ensure:\n"
                    "1. ChemStation is running\n"
                    f"2. Communication macro is loaded: macro \"{self.config.get_chempy_connect_path()}\"; Python_Run\n"
                    "3. Communication files path is accessible"
                )
            
            if self.config.verbose:
                print("✓ ChemStation connection established")

    def _initialize_files(self) -> None:
        """Initialize command and response files for communication.
        
        Creates empty command and response files if they don't exist and
        resets the command counter to ensure clean communication startup.
        
        Raises:
            FileOperationError: If files cannot be created or initialized.
        """
        try:
            self.command_file.touch()
            self.response_file.touch()
            self._reset_command_counter()
        except IOError as e:
            raise FileOperationError(f"Failed to initialize communication files: {e}")

    def _write_command(self, command: str, command_number: int) -> None:
        """Write command to command file with retry logic.
        
        Writes a numbered command to the command file using UTF-16 encoding
        for ChemStation compatibility. Includes retry logic for handling
        temporary file access issues.
        
        Args:
            command: ChemStation command string to write.
            command_number: Unique command number for tracking.
            
        Raises:
            FileOperationError: If command cannot be written after all retries.
        """
        command_line = f"{command_number} {command}"
        
        for attempt in range(self.config.max_retries):
            try:
                with open(self.command_file, 'w', encoding='utf-16') as f:
                    f.write(command_line)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                return
            except IOError as e:
                if attempt == self.config.max_retries - 1:
                    raise FileOperationError(f"Failed to write command after {self.config.max_retries} attempts: {e}")
                time.sleep(self.config.retry_delay)

    def _read_response(self, expected_command_number: int, timeout: float) -> Optional[str]:
        """Read response from response file with timeout and error handling.
        
        Continuously monitors the response file for a response with the expected
        command number. Handles file parsing, error detection, and timeout management.
        
        Args:
            expected_command_number: Command number to match in response.
            timeout: Maximum time to wait for response in seconds.
            
        Returns:
            Response string from ChemStation, or None if response is "None".
            
        Raises:
            TimeoutError: If response not received within timeout period.
            ChemstationError: If ChemStation returns an error message.
            FileOperationError: If response file cannot be read.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                with open(self.response_file, 'r', encoding='utf-16') as f:
                    content = f.read().strip()
                    
                if not content:
                    time.sleep(self.config.retry_delay)
                    continue
                
                # Parse response format: "command_number response_text"
                parts = content.split(' ', 1)
                if len(parts) < 2:
                    time.sleep(self.config.retry_delay)
                    continue
                
                try:
                    response_command_number = int(parts[0])
                except ValueError:
                    time.sleep(self.config.retry_delay)
                    continue
                
                # Check if this response matches our command
                if response_command_number == expected_command_number:
                    response = parts[1]
                    
                    # Check for ChemStation error response
                    if response.startswith(" ERROR:"):
                        raise ChemstationError(f"ChemStation command failed: {response}")
                    
                    # Return None for "None" responses, otherwise return content
                    return None if response == "None" else response
                
                time.sleep(self.config.retry_delay)
                
            except IOError as e:
                if time.time() - start_time >= timeout - 0.1:  # Near timeout
                    raise FileOperationError(f"Failed to read response: {e}")
                time.sleep(self.config.retry_delay)
        
        raise TimeoutError(f"No response received within {timeout} seconds for command {expected_command_number}")

    def _get_next_command_number(self) -> int:
        """Generate next command number with wraparound handling.
        
        Increments the command counter and handles wraparound when the
        maximum command number is reached to prevent overflow.
        
        Returns:
            Next command number for use in command tracking.
        """
        self.command_number = (self.command_number + 1)
        return self.command_number

    def _reset_command_counter(self) -> None:
        """Reset command counter and synchronize with ChemStation.
        
        Sends a special command to reset ChemStation's command tracking
        and resets the local command counter. This ensures command
        synchronization after initialization or communication errors.
        """
        if self.config.verbose:
            print("Resetting command counter for synchronization")
            
        # Send reset command using special high number
        self._write_command(command="last_command_number = 0", 
                          command_number=self.config.max_command_number + 1)
        self.command_number = 0
        time.sleep(0.5)  # Allow ChemStation to process reset

    def send(self, command: str, timeout: float = 5) -> Optional[str]:
        """Send command to ChemStation and wait for response.
        
        Executes a command in ChemStation's Command Processor and returns
        the response. This is the main interface method for all ChemStation
        communication operations.
        
        Command Types:
            - Variable assignments: SetTabHdrText, SetTabVal, SetObjHdrText
            - Data retrieval: Use "response$ = ..." to capture return values
            - Module commands: WriteModule, SendModule$ for instrument control
            - System commands: LoadMethod, SaveMethod, RunMethod
            - Macro execution: macro path; macro_name parameters
        
        Args:
            command: ChemStation command string to execute. Examples:
                    'response$ = _METHPATH$' - Get method directory path
                    'LoadMethod _METHPATH$, "MyMethod.M"' - Load method
                    'WriteModule "CE1", "FLSH 60,-2,-2"' - Flush capillary
                    'macro "path\\macro.mac"; macro_name param1, param2'
            timeout: Maximum time to wait for response in seconds.
                    Increase for long-running operations like method execution.
                    
        Returns:
            Response string from ChemStation if command starts with "response$ = ",
            otherwise None for commands that don't return values.
            
        Raises:
            CommandError: If command execution fails in ChemStation.
            TimeoutError: If response timeout occurs.
            FileOperationError: If file communication fails.
            ChemstationError: If ChemStation returns an error message.
            
        Examples:
            Get system information:
            >>> path = comm.send("response$ = _METHPATH$")
            >>> print(f"Method directory: {path}")
            
            Execute instrument command:
            >>> comm.send('WriteModule "CE1", "FLSH 60,-2,-2"')  # 60s flush
            
            Load and run method:
            >>> comm.send('LoadMethod _METHPATH$, "CE_Analysis.M"')
            >>> comm.send('RunMethod _DATAPATH$,, "Sample001"')
            
            Execute macro with parameters:
            >>> response = comm.send('macro "c:\\macros\\test.mac"; test_macro 15, "Sample"')
            
        Note:
            - Commands without "response$ = " return None but still execute
            - Command numbers automatically wrap around at maximum
            - Connection is automatically reset if counter overflow occurs
            - Verbose mode shows command/response details for debugging
        """
        # Handle command counter wraparound
        if self.command_number >= self.config.max_command_number:
            self._reset_command_counter()

        command_number = self._get_next_command_number()
        
        if self.config.verbose:
            print(f"Sending command {command_number}: {command}")
        
        # Write command and wait for response
        self._write_command(command, command_number)
        response_text = self._read_response(command_number, timeout)
        
        if self.config.verbose:
            print(f"Received response {command_number}: {response_text}")

        # Reset counter if approaching limit
        if self.command_number >= self.config.max_command_number:
            self._reset_command_counter()
            
        return response_text
        

    def _test_connection(self, timeout: float = 3.0) -> bool:
        """Test communication link with ChemStation.
        
        Sends a test command to verify that ChemStation is responding
        and the communication protocol is working correctly.
        
        Args:
            timeout: Test timeout in seconds.
            
        Returns:
            True if communication is working, False if test fails.
        """
        try:
            response = self.send('response$ = "CONNECTION_TEST"', timeout=timeout)
            return response is not None and "CONNECTION_TEST" in response
        except Exception:
            return False