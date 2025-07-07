"""
Syringe pump controller - preserved from original implementation.
"""

import time
from typing import Optional
from ..core.command_sender import CommandSender


class SyringeController(CommandSender):
    """
    Class for controlling syringe pump via serial communication.
    
    Preserved from original implementation with minimal changes.
    """
    
    VALVE_TYPES_DICT = {
        'No': '0',
        '3-Port': '1',
        '4-Port': '2',
        '3-Port distribution (face seal)': '3',
        '4-Port distribution': '10',
        'T': '5',
        '6-Port distribution': '7',
        '9-Port distribution': '8',
        'Dual loop': '9',
        '3-Port distribution (plug)': '11',
        '12-Port distribution': '12',
    }

    def __init__(self, port: str, syringe_size: int, address: str = "/1", prefix: str = "", 
                 baudrate: int = 9600, print_info: bool = True):
        """
        Initializes the SyringeController with syringe-specific parameters.
        
        Args:
            port (str): COM port for the syringe pump.
            syringe_size (int): Size of the syringe in microliters.
            address (str): Address of the syringe pump.
            prefix (str): Prefix for commands.
            baudrate (int): Baud rate for communication.
            print_info (bool): Print syringe info on init.
        """
        super().__init__(port=port, address=address, baudrate=baudrate, prefix=prefix)
        self.syringe_size = syringe_size
        self.volume_counter = 0
        if print_info:
            self._print_syringe_info()

    def _print_syringe_info(self):
        """Prints syringe information."""
        print(f"Syringe size: {self.syringe_size} µL")
        print(f"Syringe resolution: {self.syringe_size / 3000:.2f} µL")
        print(f"Minimum flow rate: {0.05 * self.syringe_size:.1f} µL/min")
        print(f"Maximum flow rate: {60 * self.syringe_size:.1f} µL/min")

    def wait_for_syringe(self):
        """
        Custom wait function for syringe completion.
        Sends a 'QR' command to the syringe and waits for completion.
        """
        read = ''
        while '`' not in read:
            self._write_command("QR")
            time.sleep(0.2)
            read = self._read_response(line=False)

    def print_volume_in_syringe(self):
        """Print current volume in syringe."""
        print(f"The current volume in the syringe is: {self.volume_counter} µl")

    def initialize(self) -> None:
        """Initializes the syringe pump."""
        cmd = 'Z' if self.syringe_size >= 1000 else 'Z1' if self.syringe_size > 100 else 'Z2'
        
        special_prefix = r'\x1b\x02\x04\x1b\x02A/'
        
        if self.prefix == special_prefix:
            original_prefix = self.prefix
            self.prefix = ''  
            self.send_command(f'{cmd}R', wait_for_completion=self.wait_for_syringe)
            self.prefix = original_prefix
        else:
            self.send_command(f'{cmd}R', wait_for_completion=self.wait_for_syringe)
        
        self.volume_counter = 0
        
    def dispense(self, volume: Optional[float] = None, wait: bool = True) -> None:
        """
        Dispenses specified volume in microliters.
        
        Args:
            volume (float, optional): Volume to dispense in µL. 
                                    If None, dispenses entire syringe volume.
        """
        if volume is None:
            command = 'A0R'                    
            self.volume_counter = 0
        else: 
            if self.volume_counter - volume < 0:
                raise ValueError("The expelled volume in the syringe would be negative!")           
            steps = int(volume * 3000 / self.syringe_size)
            command = f"D{steps}R"
            self.volume_counter -= volume

        self.send_command(command, wait_for_completion=self.wait_for_syringe if wait else None)

    def aspirate(self, volume: Optional[float] = None, wait: bool = True) -> None:
        """
        Aspirates specified volume in microliters.
        
        Args:
            volume (float, optional): Volume to aspirate in µL.
                                    If None, fills entire syringe.
        """
        if volume is None:
            command = "A3000R"       
            self.volume_counter = self.syringe_size
        else:
            if self.volume_counter + volume > self.syringe_size:
                raise ValueError(f"The drawn volume in the syringe would be {self.volume_counter + volume} µl, which exceeds the syringe capacity of {self.syringe_size} µl!")

            steps = int(volume * 3000 / self.syringe_size)
            command = f"P{steps}R"
            self.volume_counter += volume
            
        self.send_command(command, wait_for_completion=self.wait_for_syringe if wait else None)

    def set_speed_uL_min(self, speed: float) -> None:
        """
        Sets flow rate in microliters per minute.

        Args:
            speed (float): Speed in µL/min
        """
        min_speed = 0.05 * self.syringe_size
        max_speed = 60 * self.syringe_size
        if speed < min_speed:
            raise ValueError(f"Set flow rate too small! Minimum allowed rate is {min_speed:.1f} µL/min")
        elif speed > max_speed:
            raise ValueError(f"Set flow rate too large! Maximum allowed rate is {max_speed:.1f} µL/min")

        speed_steps = int(speed * 100 / self.syringe_size)
        self.send_command(f'V{speed_steps}R')

    def configuration_valve_type(self, valve_type: str) -> None:
        """
        Configures the valve type on the syringe pump.

        Args:
            valve_type (str): Valve type key; must be one of the keys in VALVE_TYPES_DICT.
        
        Raises:
            ValueError: If the provided valve type is invalid.
        """
        try:
            num_type_valve = self.VALVE_TYPES_DICT[valve_type]
        except KeyError:
            raise ValueError(f"Invalid valve type. Valid options: {list(self.VALVE_TYPES_DICT.keys())}")
        
        self.send_command(command=f"U{num_type_valve}R")
    
    def valve_in(self) -> None:
        """Switches valve to IN position."""
        self.send_command('IR')

    def valve_up(self) -> None:
        """Switches valve to UP position."""
        self.send_command('ER')

    def valve_out(self) -> None:
        """Switches valve to OUT position."""
        self.send_command('OR')

    # def valve(self, position: int) -> None:
    #     """
    #     Switches valve to specified position.
        
    #     Args:
    #         position (int): Valve position number
    #     """
    #     self.send_command(f'I{position}R')

    # def valve_bypass(self) -> None:
    #     """Switches the valve to the bypass position."""
    #     self.send_command('BR')