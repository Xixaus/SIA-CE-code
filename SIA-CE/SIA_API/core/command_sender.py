"""
Serial communication base class for analytical instruments.

Provides reliable serial communication with automatic port management,
error handling, and configurable timeouts for laboratory automation.
"""

import time
import serial
from typing import Optional


class CommandSender:
    """
    Base class for serial communication with analytical instruments.
    
    Handles COM port management, command formatting, and response processing
    for syringe pumps, valve selectors, and other RS-232/USB devices.
    
    Attributes:
        serial_device (serial.Serial): PySerial device instance
        prefix (str): Command prefix string
        address (str): Device address identifier
    
    Examples:
        Basic usage:
        
        >>> sender = CommandSender(port="COM3", address="/1", baudrate=9600)
        >>> response = sender.send_command("Z", get_response=True)
        
        With custom timeout and completion function:
        
        >>> def wait_for_ready():
        ...     time.sleep(2)
        >>> sender.send_command("INIT", wait_for_completion=wait_for_ready)
    """
    
    def __init__(self, port: str, prefix: str = "", address: str = "", baudrate: int = 9600):
        """
        Initialize serial communication interface.
        
        Args:
            port: COM port identifier (e.g., "COM3", "/dev/ttyUSB0")
            prefix: Command prefix string for protocol formatting
            address: Device address identifier
            baudrate: Serial communication speed (default: 9600)
            
        Raises:
            SerialException: If port configuration is invalid
            
        Note:
            Port is not opened during initialization. Connection is established
            automatically when sending commands.
        """
        self.serial_device = serial.Serial(timeout=0.3)
        self.serial_device.port = port
        self.prefix = prefix
        self.address = address
        self.serial_device.baudrate = baudrate
    
    def _open_port(self) -> None:
        """
        Open serial port for communication.
        
        Raises:
            SerialException: If port cannot be opened (already in use, 
                           invalid port name, hardware not connected)
        """
        if not self.serial_device.is_open:
            try:
                self.serial_device.open()
            except serial.SerialException as e:
                print(f"Error opening COM port: {e}")
                raise

    def _close_port(self) -> None:
        """Close serial port if currently open."""
        if self.serial_device.is_open:
            self.serial_device.close()

    def _write_command(self, command: str) -> None:
        """
        Write formatted command to serial device.
        
        Command is formatted as: {prefix}{address}{command}\r
        
        Args:
            command: Raw command string to send
            
        Note:
            Includes buffer flush and 200ms delay for device processing.
        """
        full_command = f"{self.prefix}{self.address}{command}\r"
        self.serial_device.flush()
        self.serial_device.write(full_command.encode('utf-8', 'ignore'))
        time.sleep(0.2)
    
    def _read_response(self, line: bool = True) -> str:
        """
        Read response from serial device.
        
        Args:
            line: If True, read until newline. If False, read all available data.
            
        Returns:
            Decoded response string
        """
        if line:
            return self.serial_device.readline(self.serial_device.inWaiting()).decode('utf-8', 'ignore')
        else:
            return self.serial_device.read(self.serial_device.inWaiting()).decode('utf-8', 'ignore')

    def send_command(self, command: str, 
                     wait_for_completion: callable = None,
                     get_response: bool = False,
                     response_timeout: float = 3) -> Optional[str]:
        """
        Send command with optional response handling and completion waiting.
        
        Provides complete command execution cycle with automatic port management,
        optional completion waiting, and response capture.
        
        Args:
            command: Command string to send to device
            wait_for_completion: Optional function to call while waiting for operation
            get_response: Whether to wait for and return device response
            response_timeout: Maximum time to wait for response (seconds)
            
        Returns:
            Device response string if get_response=True, otherwise None
            
        Raises:
            SerialException: If communication fails
            TimeoutError: If response timeout exceeded (when get_response=True)
        """
        response = ""
        self._open_port()
        try:
            # Send main command
            self._write_command(command)
            
            # Wait for operation completion if function provided
            if wait_for_completion:
                wait_for_completion()
            
            # Capture response if requested
            if get_response:
                start_time = time.time()
                while time.time() - start_time < response_timeout:
                    if self.serial_device.inWaiting() > 0:
                        response = self._read_response()
                        break
                    time.sleep(0.2)
                
                return response
            else:
                return None
                
        finally:
            self._close_port()