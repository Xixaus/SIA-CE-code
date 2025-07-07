"""
Protocol implementation for communication with Agilent ChemStation software.

This module provides low-level communication primitives for interacting with 
ChemStation software through a file-based command protocol. The protocol works
by writing commands to a command file and reading responses from a reply file.

The communication is based on ChemStation's macro system, where a custom macro
running in ChemStation continuously monitors the command file for new commands,
executes them, and writes results to the reply file. Each command is assigned
a unique number (command_number) to track command processing and match responses.

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
    """Handles file-based communication with ChemStation software.
    
    This class implements the low-level protocol for sending commands to and
    receiving responses from ChemStation through a file-based interface.
    
    The communication protocol uses a command file for outgoing commands and
    a response file for incoming responses. Each command is assigned a unique
    number to track processing and match responses.
    
    Attributes:
        config: Communication configuration settings.
        command_number: Current command number counter.
        comm_dir: Path to communication directory.
        command_file: Path to command file.
        response_file: Path to response file.
        macros_path: Path to macro files.
    """

    def __init__(self, config: Optional[CommunicationConfig] = None):
        """Initialize the communication handler.
        
        Args:
            config: Communication configuration. If None, uses default configuration.
            
        Raises:
            ConfigurationError: If communication directory cannot be created.
            ConnectionError: If connection test fails (when test_on_init is True).
        """
        self.config = config or CommunicationConfig()
        self.command_number = 0
        
        # Convert to Path objects
        self.comm_dir = self.config.get_comm_dir_path()
        self.command_file = self.config.get_command_file_path()
        self.response_file = self.config.get_response_file_path()
        
        # Macro paths are now available through self.config
        self.macros_path = str(self.config.get_macros_path())
        
        # Set up communication environment
        try:
            self.comm_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigurationError(f"Failed to create communication directory: {e}")

        self._initialize_files()
        time.sleep(0.5)
        
        # Test connection if enabled
        if self.config.test_on_init:
            if self.config.verbose:
                print("Testing ChemStation connection...")
            
            if not self._test_connection():
                raise ConnectionError(
                    "Failed to establish communication with ChemStation. "
                    "Please ensure:\n"
                    "1. ChemStation is running\n"
                    f"2. The communication macro is loaded and running (command: macro {self.config.get_chempy_connect_path()}; Python_Run)\n"
                    "3. The communication files path is correct"
                )
            
            if self.config.verbose:
                print("✓ ChemStation connection test passed")

    def _initialize_files(self) -> None:
        """Ensure command and reply files exist and are ready for use.
        
        Creates empty command and response files if they don't exist and
        resets the command counter to initial state.
        
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
        """Write a command to the command file with retry logic.
        
        Args:
            command: Command string to write.
            command_number: Command number for tracking.
            
        Raises:
            FileOperationError: If command cannot be written after retries.
        """
        command_line = f"{command_number} {command}"
        
        for attempt in range(self.config.max_retries):
            try:
                with open(self.command_file, 'w', encoding='utf-16') as f:
                    f.write(command_line)
                    f.flush()
                    os.fsync(f.fileno())
                return
            except IOError as e:
                if attempt == self.config.max_retries - 1:
                    raise FileOperationError(f"Failed to write command after {self.config.max_retries} attempts: {e}")
                time.sleep(self.config.retry_delay)

    def _read_response(self, expected_command_number: int, timeout: float) -> Optional[str]:
        """Read response from the reply file with timeout.
        
        Args:
            expected_command_number: Expected command number in response.
            timeout: Maximum time to wait for response in seconds.
            
        Returns:
            Response string from ChemStation, or None if response is "None".
            
        Raises:
            TimeoutError: If response not received within timeout.
            ChemstationError: If ChemStation returns an error.
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
                
                # Parse response: "command_number response_text"
                parts = content.split(' ', 1)
                if len(parts) < 2:
                    time.sleep(self.config.retry_delay)
                    continue
                
                try:
                    response_command_number = int(parts[0])
                except ValueError:
                    time.sleep(self.config.retry_delay)
                    continue
                
                if response_command_number == expected_command_number:
                    response = parts[1]
                    
                    # Check for error response
                    if response.startswith(" ERROR:"):
                        raise ChemstationError(f"ChemStation command failed: {response}")
                    
                    if response == "None":
                        return None
                    else:
                        return response
                
                time.sleep(self.config.retry_delay)
                
            except IOError as e:
                if time.time() - start_time >= timeout - 0.1:  # Close to timeout
                    raise FileOperationError(f"Failed to read response: {e}")
                time.sleep(self.config.retry_delay)
        
        raise TimeoutError(f"No response received within {timeout} seconds for command {expected_command_number}")

    def _get_next_command_number(self) -> int:
        """Generate next command number with wraparound.
        
        Returns:
            int: Next command number (1 to max_command_number).
        """
        self.command_number = (self.command_number + 1)

        return self.command_number

    def _reset_command_counter(self) -> None:
        """Reset command counter to initial state.
        
        Sends a special command to ChemStation to reset the command tracking
        and resets the local command counter.
        """
        if self.config.verbose:
            print("Reseting counter")
        self._write_command(command="last_command_number = 0", command_number=self.config.max_command_number+1)
        self.command_number = 0
        time.sleep(0.5)

    def send(self, command: str, timeout: float = 10) -> Optional[str]:
        """Send a command to ChemStation and wait for response.
        
        Args:
            command: ChemStation command string to execute.
            timeout: Response timeout in seconds.
            
        Returns:
            Response string from ChemStation, or None if no response expected.
            
        Raises:
            CommandError: If command execution fails.
            TimeoutError: If response timeout occurs.
            FileOperationError: If file operations fail.
            
        Example:
            >>> comm = ChemstationCommunicator()
            >>> response = comm.send('response$ = "Hello"')
            >>> print(response)  # "Hello"
        """
        if self.command_number >= self.config.max_command_number:
            self._reset_command_counter()

        command_number = self._get_next_command_number()
        
        if self.config.verbose:
            print(f"Sending command {command_number}: {command}")
        
        self._write_command(command, command_number)
        
        response_text = self._read_response(command_number, timeout)
        if self.config.verbose:
            print(f"Received response {command_number}: {response_text}")

        if self.command_number >= self.config.max_command_number:
            self._reset_command_counter()
        return response_text
        

    def _test_connection(self, timeout: float = 3.0) -> bool:
        """Test communication with ChemStation.
        
        Args:
            timeout: Test timeout in seconds.
            
        Returns:
            True if communication is working, False otherwise.
        """
        try:
            response = self.send('response$ = "CONNECTION_TEST"', timeout=timeout)
            return response is not None and "CONNECTION_TEST" in response
        except Exception:
            return False