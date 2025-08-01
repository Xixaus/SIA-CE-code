"""
Syringe pump controller for SIA (Sequential Injection Analysis) systems.

This module provides complete control of syringe pumps via serial communication,
supporting various syringe sizes, valve configurations, and automated workflows.

Based on concepts from CoCoSoft framework:
https://sites.google.com/view/cocovisolberglab/cocosoft
"""

import time
import re
from tqdm import tqdm
from typing import Optional
from ..core.command_sender import CommandSender


class SyringeController(CommandSender):
    """
    Complete syringe pump control for analytical automation.
    
    Provides precise volume control, flow rate management, and valve operation
    for Hamilton MVP series and compatible syringe pumps. Supports automatic
    volume tracking and safety validation.
    
    Attributes:
        syringe_size (int): Syringe volume capacity in microliters
        volume_counter (float): Current volume in syringe (µL)
        VALVE_TYPES_DICT (dict): Supported valve type configurations
    
    Examples:
        Basic syringe operations:
        
        >>> syringe = SyringeController(port="COM3", syringe_size=1000)
        >>> syringe.initialize()
        >>> syringe.set_speed_uL_min(1500)  # 1.5 mL/min
        >>> syringe.aspirate(500)           # Draw 500 µL
        >>> syringe.dispense(250)           # Dispense 250 µL
        
        Valve control:
        
        >>> syringe.valve_in()   # Switch to inlet
        >>> syringe.valve_out()  # Switch to outlet
        >>> syringe.valve_up()   # Switch to up position
        
        Volume tracking:
        
        >>> syringe.print_volume_in_syringe()
        The current volume in the syringe is: 250 µl
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
        Initialize syringe pump controller.
        
        Args:
            port: COM port for syringe pump (e.g., "COM3")
            syringe_size: Syringe volume in microliters (100-5000)
            address: Device address (default: "/1")
            prefix: Command prefix for specific protocols
            baudrate: Serial communication speed (default: 9600)
            print_info: Print syringe specifications on initialization
            
        Raises:
            ValueError: If syringe_size is outside supported range
            SerialException: If COM port cannot be opened
        """
        super().__init__(port=port, address=address, baudrate=baudrate, prefix=prefix)
        self.syringe_size = syringe_size
        self.volume_counter = 0
        self.speed = self.get_actual_set_speed()
        if print_info:
            self._print_syringe_info()

    def _print_syringe_info(self):
        """Print syringe specifications and operating limits."""
        print(f"Syringe size: {self.syringe_size} µL")
        print(f"Syringe resolution: {self.syringe_size / 3000:.2f} µL")
        print(f"Minimum flow rate: {0.05 * self.syringe_size:.1f} µL/min")
        print(f"Maximum flow rate: {60 * self.syringe_size:.1f} µL/min")

    def set_backlash(self, step):
        """Sets the backlash steps from 0 to 31 in standard mode and 0 to 248 in high resolution mode"""
        self.send_command(f"K{step}R")

    def emergency_stop(self):
        """Okamžité vypnutí"""

        self.send_command("TR")

    def get_actual_set_speed(self) -> float:
        """
        Get currently set flow rate from syringe pump.
        
        Returns:
            float: Current flow rate in µL/min
            
        Raises:
            ValueError: If response cannot be parsed
            
        Examples:
            >>> syringe.set_speed_uL_min(1500)
            >>> current_speed = syringe.get_actual_set_speed()
            >>> print(f"Current speed: {current_speed:.1f} µL/min")
            Current speed: 1500.0 µL/min
        """
        
        # Send query command for top speed (?2 doesn't need R suffix)
        response = self.send_command("?2", get_response=True)
        
        # Parse numeric value from response format '/0`VALUE\x03\r\n' using regex
        match = re.search(r'[/]?0?`(\d+)', response)
        
        if not match:
            raise ValueError(f"Could not parse speed from response: {response}")
        
        try:
            speed_steps = int(match.group(1))
        except ValueError:
            raise ValueError(f"Invalid numeric value in response: {response}")
        
        # Convert speed steps back to µL/min
        # Reverse of: speed_steps = int(speed * 100 / self.syringe_size)
        speed_uL_min = (speed_steps * self.syringe_size) / 100
        
        return speed_uL_min
    
    def print_actual_set_speed(self):
        """
        Print currently set flow rate in µL/min.
        
        Retrieves the actual speed from the syringe pump and prints it.
        
        Example:
            >>> syringe.print_actual_set_speed()
            Current speed: 1500.0 µL/min
        """
        speed = self.get_actual_set_speed()
        print(f"Current speed: {speed:.1f} µL/min")

    def wait_for_syringe(self, volume: float = 0, show_progress: bool = False):
        """
        Wait for syringe operation completion with optional progress bar.
        
        Args:
            volume: Volume being processed in µL (for time estimation)
            show_progress: Whether to show tqdm progress bar
        """
        if show_progress and volume > 0 and self.speed > 0:  # Přidat kontrolu speed
            try:
                # Calculate estimated time
                estimated_time = (volume / self.speed) * 60  # seconds
                
                # Kontrola že estimated_time je validní
                if estimated_time <= 0:
                    show_progress = False
                else:
                    with tqdm(total=estimated_time, desc="Processing", unit="s",
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n:.1f}s/{total:.1f}s [{elapsed}<{remaining}]",
                        mininterval=0.1,
                        maxinterval=0.1) as pbar:
                        start_time = time.time()
                        read = ''
                        
                        while '`' not in read:
                            self._write_command("QR")
                            time.sleep(0.2)
                            read = self._read_response(line=False)
                            
                            elapsed = time.time() - start_time
                            pbar.n = min(elapsed, estimated_time)
                            pbar.refresh()
                        
                        pbar.n = estimated_time
                        return 
                        
            except (ImportError, ZeroDivisionError, ValueError) as e:
                # Fallback na simple wait
                show_progress = False
        
        # Original simple wait (vždy se spustí pokud show_progress=False nebo jsou problémy)
        read = ''
        while '`' not in read:
            self._write_command("QR")
            time.sleep(0.2)
            read = self._read_response(line=False)

    def print_volume_in_syringe(self):
        """Print current volume tracked in syringe."""
        print(f"The current volume in the syringe is: {self.volume_counter} µl")

    def initialize(self) -> None:
        """
        Initialize syringe pump to home position.
        
        Performs complete initialization sequence, moving syringe to
        absolute zero position. Command varies based on syringe size:
        - ≥1000 µL: 'Z' command
        - >100 µL: 'Z1' command  
        - ≤100 µL: 'Z2' command
        
        Resets volume counter to zero after initialization.
        
        Note:
            Special handling for specific communication protocols that
            require temporary prefix removal during initialization.
        """
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
        self.speed = self.get_actual_set_speed()
        
    def dispense(self, volume: Optional[float] = None, wait: bool = True, show_progress:bool = False) -> None:
        """
        Dispense specified volume from syringe.
        
        Args:
            volume: Volume to dispense in µL. If None, dispenses entire syringe
            wait: Whether to wait for operation completion
            
        Raises:
            ValueError: If requested volume exceeds current syringe content
            
        Examples:
            >>> syringe.dispense(250)     # Dispense 250 µL
            >>> syringe.dispense()        # Dispense all content
            >>> syringe.dispense(100, wait=False)  # Non-blocking dispense
        """
        if volume is None:
            command = 'A0R'
            volume = self.volume_counter                     
            self.volume_counter = 0

        else: 
            if self.volume_counter - volume < 0:
                raise ValueError("The expelled volume in the syringe would be negative!")           
            steps = int(volume * 3000 / self.syringe_size)
            command = f"D{steps}R"
            self.volume_counter -= volume

        wait_func = lambda: self.wait_for_syringe(volume, show_progress) if wait else None
        self.send_command(command, wait_for_completion=wait_func)

    def aspirate(self, volume: Optional[float] = None, wait: bool = True, show_progress:bool = False) -> None:
        """
        Aspirate specified volume into syringe.
        
        Args:
            volume: Volume to aspirate in µL. If None, fills entire syringe
            wait: Whether to wait for operation completion
            
        Raises:
            ValueError: If requested volume exceeds syringe capacity
            
        Examples:
            >>> syringe.aspirate(500)     # Aspirate 500 µL
            >>> syringe.aspirate()        # Fill entire syringe
            >>> syringe.aspirate(200, wait=False)  # Non-blocking aspirate
        """
        if volume is None:
            command = "A3000R"       
            volume = self.syringe_size - self.volume_counter  
            self.volume_counter = self.syringe_size

        else:
            if self.volume_counter + volume > self.syringe_size:
                raise ValueError(f"The drawn volume in the syringe would be {self.volume_counter + volume} µl, which exceeds the syringe capacity of {self.syringe_size} µl!")

            steps = int(volume * 3000 / self.syringe_size)
            command = f"P{steps}R"
            self.volume_counter += volume
        
        wait_func = lambda: self.wait_for_syringe(volume, show_progress) if wait else None
        self.send_command(command, wait_for_completion=wait_func)

    def set_speed_uL_min(self, speed: float) -> None:
        """
        Set syringe flow rate in microliters per minute.
        
        Args:
            speed: Flow rate in µL/min
            
        Raises:
            ValueError: If speed is outside allowed range
            
        Note:
            Speed limits depend on syringe size:
            - Minimum: 0.05 × syringe_size µL/min
            - Maximum: 60 × syringe_size µL/min
            
        Examples:
            >>> syringe.set_speed_uL_min(1500)  # 1.5 mL/min for 1000µL syringe
            >>> syringe.set_speed_uL_min(500)   # 0.5 mL/min
        """
        min_speed = 0.05 * self.syringe_size
        max_speed = 60 * self.syringe_size
        if speed < min_speed:
            raise ValueError(f"Set flow rate too small! Minimum allowed rate is {min_speed:.1f} µL/min")
        elif speed > max_speed:
            raise ValueError(f"Set flow rate too large! Maximum allowed rate is {max_speed:.1f} µL/min")

        speed_steps = int(speed * 100 / self.syringe_size)
        self.speed = speed
        self.send_command(f'V{speed_steps}R')

    def configuration_valve_type(self, valve_type: str) -> None:
        """
        Configure valve type attached to syringe pump.
        
        Args:
            valve_type: Valve type from VALVE_TYPES_DICT keys
            
        Raises:
            ValueError: If valve_type is not supported
            
        Supported valve types:
            - 'No': No valve attached
            - '3-Port', '4-Port': Standard switching valves
            - '3-Port distribution (face seal)': Distribution valve with face seal
            - '6-Port distribution', '9-Port distribution', '12-Port distribution'
            - 'T': T-junction valve
            - 'Dual loop': Dual loop valve system
            
        Example:
            >>> syringe.configuration_valve_type('6-Port distribution')
        """
        try:
            num_type_valve = self.VALVE_TYPES_DICT[valve_type]
        except KeyError:
            raise ValueError(f"Invalid valve type. Valid options: {list(self.VALVE_TYPES_DICT.keys())}")
        
        self.send_command(command=f"U{num_type_valve}R")
    
    def valve_in(self) -> None:
        """
        Switch valve to IN position.
        
        For 3-port valves: connects syringe to input port.
        For multi-port valves: connects to designated input position.
        """
        self.send_command('IR')

    def valve_up(self) -> None:
        """
        Switch valve to UP position.
        
        For 3-port valves: connects syringe to upper port.
        For multi-port valves: connects to designated up position.
        """
        self.send_command('ER')

    def valve_out(self) -> None:
        """
        Switch valve to OUT position.
        
        For 3-port valves: connects syringe to output port.
        For multi-port valves: connects to designated output position.
        """
        self.send_command('OR')