"""
Simple command sender for serial communication - preserved from original.
"""

import time
import serial
from typing import Optional


class CommandSender:
    """
    Base class for sending commands over serial communication.
    
    Preserved from original implementation with minimal changes.
    """
    
    def __init__(self, port: str, prefix: str = "", address: str = "", baudrate: int = 9600):
        """
        Initializes the CommandSender with the given serial port parameters.
        
        Args:
            port (str): The COM port to be used.
            address (str): The address of the device.
            baudrate (int): Communication speed (default is 9600).
            prefix (str): A string prefix to prepend to all commands.
        """
        self.serial_device = serial.Serial(timeout=0.3)
        self.serial_device.port = port
        self.prefix = prefix
        self.address = address
        self.serial_device.baudrate = baudrate
    
    def _open_port(self) -> None:
        """Opens the serial port if it is not already open."""
        if not self.serial_device.is_open:
            try:
                self.serial_device.open()
            except serial.SerialException as e:
                print(f"Error opening COM port: {e}")
                raise

    def _close_port(self) -> None:
        """Closes the serial port if it is open."""
        if self.serial_device.is_open:
            self.serial_device.close()

    def _write_command(self, command: str) -> None:
        """
        Writes a command to the serial device.
        
        The command is prefixed with the address and terminated with a carriage return.
        
        Args:
            command (str): The command to send.
        """
        full_command = f"{self.prefix}{self.address}{command}\r"
        self.serial_device.flush()
        self.serial_device.write(full_command.encode('utf-8', 'ignore'))
        time.sleep(0.2)
    
    def _read_response(self, line: bool = True) -> str:
        """Read response from serial device."""
        if line:
            return self.serial_device.readline(self.serial_device.inWaiting()).decode('utf-8', 'ignore')
        else:
            return self.serial_device.read(self.serial_device.inWaiting()).decode('utf-8', 'ignore')

    def send_command(self, command: str, 
                     wait_for_completion: callable = None,
                     get_response: bool = False,
                     response_timeout: float = 3) -> Optional[str]:
        """
        Sends a sequence of commands over an open serial connection.
        
        Args:
            command (str): The main command to be sent.
            wait_for_completion (callable, optional): Function that will be called to wait until the operation completes.
            get_response (bool, optional): If True, the method waits for and returns a response.
            response_timeout (float, optional): Maximum time in seconds to wait for a response.
            
        Returns:
            str: The response from the device if get_response is True; otherwise, a None.
        """
        response = ""
        self._open_port()
        try:
            # Send main command
            self._write_command(command)
            
            # Wait for the operation to complete (via wait_for_completion function)
            if wait_for_completion:
                wait_for_completion()
            
            # Wait for and capture response if required.
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