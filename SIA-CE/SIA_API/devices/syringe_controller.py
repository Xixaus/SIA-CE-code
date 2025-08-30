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
from typing import Optional, Callable, Union
from ..core.command_sender import CommandSender


class SyringeController(CommandSender):
    """
    Complete syringe pump control for analytical automation.
    
    Provides precise volume control, flow rate management, and valve operation
    for Hamilton MVP series and compatible syringe pumps. Supports automatic
    volume tracking and safety validation.
    
    Constants:
        STANDARD_RESOLUTION: Standard mode resolution (3000 increments)
        MICROSTEP_RESOLUTION: Microstep mode resolution (24000 increments)
        MIN_SPEED_FACTOR: Minimum speed as fraction of syringe size (0.05)
        MAX_SPEED_FACTOR: Maximum speed as fraction of syringe size (60)
        SPEED_CONVERSION_FACTOR: Factor for speed conversion (100)
        SUPPORTED_SYRINGE_SIZES: Valid syringe sizes in µL
        QUERY_INTERVAL: Interval between status queries in seconds (0.2)
        
    Attributes:
        syringe_size (int): Syringe volume capacity in microliters
        volume_counter (float): Current volume in syringe (µL)
        speed (float): Current flow rate in µL/min
        max_increments (int): Maximum increments based on microstep mode
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
    
    # Resolution constants
    STANDARD_RESOLUTION = 3000
    MICROSTEP_RESOLUTION = 24000
    
    # Speed constants
    MIN_SPEED_FACTOR = 0.05  # Minimum speed = 0.05 × syringe_size µL/min
    MAX_SPEED_FACTOR = 60     # Maximum speed = 60 × syringe_size µL/min
    SPEED_CONVERSION_FACTOR = 100
    
    # Timing constants
    QUERY_INTERVAL = 0.2  # Seconds between status queries
    
    # Syringe size thresholds for initialization
    LARGE_SYRINGE_THRESHOLD = 1000  # µL
    SMALL_SYRINGE_THRESHOLD = 100   # µL
    
    # Supported syringe sizes in µL
    SUPPORTED_SYRINGE_SIZES = (50, 100, 250, 500, 1000, 2500, 5000)
    
    # Valve type configurations
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

    def __init__(
        self, 
        port: str, 
        syringe_size: int, 
        address: str = "/1", 
        prefix: str = "", 
        baudrate: int = 9600, 
        microstep_mode: bool = False, 
        print_info: bool = True
    ) -> None:
        """
        Initialize syringe pump controller.
        
        Args:
            port: COM port for syringe pump (e.g., "COM3", "/dev/ttyUSB0")
            syringe_size: Syringe volume in microliters (50, 100, 250, 500, 1000, 2500, 5000)
            address: Device address for multi-pump setups (default: "/1")
            prefix: Command prefix for specific protocols (default: "")
            baudrate: Serial communication speed in bps (default: 9600)
            microstep_mode: Enable high resolution mode (default: False)
            print_info: Print syringe specifications on initialization (default: True)
            
        Raises:
            ValueError: If syringe_size is not in SUPPORTED_SYRINGE_SIZES
            SerialException: If COM port cannot be opened
            
        Examples:
            >>> # Standard initialization
            >>> syringe = SyringeController(port="COM3", syringe_size=1000)
            
            >>> # High resolution mode with custom baudrate
            >>> syringe = SyringeController(
            ...     port="COM3", 
            ...     syringe_size=500,
            ...     microstep_mode=True,
            ...     baudrate=38400
            ... )
        """
        super().__init__(port=port, address=address, baudrate=baudrate, prefix=prefix)
        
        # Validate syringe size
        if syringe_size not in self.SUPPORTED_SYRINGE_SIZES:
            raise ValueError(
                f"Syringe size {syringe_size} µL not supported. "
                f"Valid sizes: {self.SUPPORTED_SYRINGE_SIZES}"
            )
        
        self._syringe_size = syringe_size
        self._max_increments = self.set_microstep_mode(microstep_mode=microstep_mode)
        self._volume_counter = self.get_actual_volume()
        self._speed = self.get_actual_set_speed()
        
        if print_info:
            self._print_syringe_info()

    @property
    def syringe_size(self) -> int:
        """Get syringe size in microliters."""
        return self._syringe_size
    
    @property
    def max_increments(self) -> int:
        """Get maximum increments based on current resolution mode."""
        return self._max_increments
    
    @property
    def volume_counter(self) -> float:
        """
        Get current volume in syringe.
        
        Returns:
            float: Current volume in microliters
        """
        return self._volume_counter
    
    @volume_counter.setter
    def volume_counter(self, value: float) -> None:
        """
        Set current volume with validation.
        
        Args:
            value: Volume in microliters
            
        Raises:
            ValueError: If volume is negative or exceeds syringe capacity
        """
        if value < 0:
            raise ValueError(f"Volume cannot be negative (got {value} µL)")
        if value > self._syringe_size:
            raise ValueError(
                f"Volume {value} µL exceeds syringe capacity {self._syringe_size} µL"
            )
        self._volume_counter = value
    
    @property
    def speed(self) -> float:
        """Get current flow rate in µL/min."""
        return self._speed
    
    @property
    def resolution(self) -> float:
        """
        Get syringe resolution in µL per increment.
        
        Returns:
            float: Volume resolution in microliters
        """
        return self._syringe_size / self._max_increments

    def _print_syringe_info(self) -> None:
        """Print syringe specifications and operating limits."""
        print(f"Syringe size: {self._syringe_size} µL")
        print(f"Syringe resolution: {self.resolution:.2f} µL")
        print(f"Minimum flow rate: {self.MIN_SPEED_FACTOR * self._syringe_size:.1f} µL/min")
        print(f"Maximum flow rate: {self.MAX_SPEED_FACTOR * self._syringe_size:.1f} µL/min")

    def set_backlash(self, steps: int) -> None:
        """
        Set backlash compensation steps.
        
        Compensates for mechanical play in the drive system by adding
        extra steps when changing direction.
        
        Args:
            steps: Backlash steps (0-31 standard mode, 0-248 microstep mode)
            
        Raises:
            ValueError: If steps exceed maximum for current mode
            
        Examples:
            >>> syringe.set_backlash(12)  # Standard compensation
            >>> syringe.set_backlash(0)   # Disable backlash compensation
        """
        max_backlash = 248 if self._max_increments == self.MICROSTEP_RESOLUTION else 31
        if not 0 <= steps <= max_backlash:
            raise ValueError(f"Backlash steps must be 0-{max_backlash} (got {steps})")
        
        self.send_command(f"K{steps}R")

    def emergency_stop(self) -> None:
        """
        Immediately stop all syringe operations.
        
        Examples:
            >>> syringe.emergency_stop()  # Stop immediately
        """
        self.send_command("TR")

        self.get_actual_volume()  # Update volume counter after stop

    def get_actual_volume(self) -> float:
        """
        Query and return actual syringe volume from pump.
        
        Communicates with pump to get current plunger position and
        converts to volume. Updates internal volume counter.
        
        Returns:
            float: Current volume in microliters
            
        Raises:
            ValueError: If response cannot be parsed
            
        Examples:
            >>> volume = syringe.get_actual_volume()
            >>> print(f"Actual volume: {volume:.1f} µL")
        """
        response = self.send_command("?", get_response=True)
        increments = self._parse_increment_response(response)
        
        volume = (increments / self._max_increments) * self._syringe_size
        self._volume_counter = volume
        
        return volume
    
    def _parse_increment_response(self, response: str) -> int:
        """
        Parse increment value from pump response.
        
        Args:
            response: Raw response string from pump
            
        Returns:
            int: Number of increments
            
        Raises:
            ValueError: If response format is invalid
        """
        match = re.search(r"`(\d+)\x03", response)
        if not match:
            raise ValueError(f"Could not parse increments from response: {response}")
        return int(match.group(1))

    def set_microstep_mode(self, microstep_mode: bool = False) -> int:
        """
        Configure pump resolution mode.
        
        Args:
            microstep_mode: True for high resolution (24000 steps),
                          False for standard (3000 steps)
                          
        Returns:
            int: Maximum increments for selected mode
            
        Examples:
            >>> # Enable high resolution mode
            >>> max_steps = syringe.set_microstep_mode(True)
            >>> print(f"Resolution: {syringe.resolution:.3f} µL/step")
        """
        if microstep_mode:
            self.send_command("N1R")
            self._max_increments = self.MICROSTEP_RESOLUTION
        else:
            self.send_command("N0R")
            self._max_increments = self.STANDARD_RESOLUTION
        
        return self._max_increments

    def get_actual_set_speed(self) -> float:
        """
        Get currently configured flow rate from pump.
        
        Queries pump for current speed setting and converts to µL/min.
        
        Returns:
            float: Current flow rate in µL/min
            
        Raises:
            ValueError: If response cannot be parsed
            
        Examples:
            >>> speed = syringe.get_actual_set_speed()
            >>> print(f"Current speed: {speed:.1f} µL/min")
        """
        response = self.send_command("?2", get_response=True)
        speed_steps = self._parse_speed_response(response)
        
        # Convert speed steps to µL/min
        speed_uL_min = (speed_steps * self._syringe_size) / self.SPEED_CONVERSION_FACTOR
        
        return speed_uL_min
    
    def _parse_speed_response(self, response: str) -> int:
        """
        Parse speed value from pump response.
        
        Args:
            response: Raw response string from pump
            
        Returns:
            int: Speed in pump units
            
        Raises:
            ValueError: If response format is invalid
        """
        match = re.search(r'[/]?0?`(\d+)', response)
        if not match:
            raise ValueError(f"Could not parse speed from response: {response}")
        
        try:
            return int(match.group(1))
        except ValueError:
            raise ValueError(f"Invalid numeric value in response: {response}")

    def wait_for_syringe(
        self, 
        volume: float = 0, 
        show_progress: bool = False
    ) -> None:
        """
        Wait for syringe operation to complete.
        
        Polls pump status until operation finishes. Optionally displays
        progress bar with time estimation based on volume and flow rate.
        
        Args:
            volume: Volume being processed in µL (for time estimation)
            show_progress: Whether to display progress bar (requires tqdm)
            
        Examples:
            >>> # Wait with progress bar
            >>> syringe.wait_for_syringe(volume=500, show_progress=True)
            
            >>> # Simple wait without progress
            >>> syringe.wait_for_syringe()
        """
        if show_progress and volume > 0:
            self._wait_with_progress(volume)
        else:
            self._wait_simple()
    
    def _wait_with_progress(self, volume: float) -> None:
        """
        Wait with progress bar display.
        
        Args:
            volume: Volume being processed for time estimation
        """
        try:
            # Calculate estimated time in seconds
            estimated_time = (volume / self._speed) * 60
            
            with tqdm(
                total=estimated_time, 
                desc="Processing", 
                unit="s",
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n:.1f}s/{total:.1f}s [{elapsed}<{remaining}]",
                mininterval=0.1,
                maxinterval=0.1
            ) as pbar:
                start_time = time.time()
                
                while not self._is_pump_ready():
                    elapsed = time.time() - start_time
                    pbar.n = min(elapsed, estimated_time)
                    pbar.refresh()
                
                pbar.n = estimated_time
                
        except ImportError:
            # Fall back to simple wait if tqdm not available
            self._wait_simple()
    
    def _wait_simple(self) -> None:
        """Simple wait without progress display."""
        while not self._is_pump_ready():
            pass
    
    def _is_pump_ready(self) -> bool:
        """
        Check if pump is ready for next command.
        
        Returns:
            bool: True if pump is ready, False if busy
        """
        self._write_command("QR")
        time.sleep(self.QUERY_INTERVAL)
        response = self._read_response(line=False)
        return '`' in response

    def print_volume_in_syringe(self) -> None:
        """
        Print current tracked volume in syringe.
        
        Examples:
            >>> syringe.print_volume_in_syringe()
            The current volume in the syringe is: 250.0 µl
        """
        print(f"The current volume in the syringe is: {self._volume_counter:.1f} µl")

    def initialize(self) -> None:
        """
        Initialize syringe pump to home position.
        
        Performs complete initialization sequence, moving plunger to
        absolute zero position. Command varies by syringe size:
        - ≥1000 µL: Standard force initialization
        - 100-1000 µL: Half force initialization
        - <100 µL: One-third force initialization
        
        Resets volume counter to zero and updates speed after completion.
        
        Note:
            Special handling for protocols requiring temporary prefix removal.
            
        Examples:
            >>> syringe.initialize()  # Home the syringe
            >>> print(syringe.volume_counter)  # Will show 0.0
        """
        # Select initialization command based on syringe size
        if self._syringe_size >= self.LARGE_SYRINGE_THRESHOLD:
            cmd = 'Z'
        elif self._syringe_size > self.SMALL_SYRINGE_THRESHOLD:
            cmd = 'Z1'
        else:
            cmd = 'Z2'
        
        # Special handling for specific protocol
        special_prefix = r'\x1b\x02\x04\x1b\x02A/'
        
        if self.prefix == special_prefix:
            original_prefix = self.prefix
            self.prefix = ''  
            self.send_command(f'{cmd}R', wait_for_completion=self.wait_for_syringe)
            self.prefix = original_prefix
        else:
            self.send_command(f'{cmd}R', wait_for_completion=self.wait_for_syringe)
        
        self._volume_counter = 0
        self._speed = self.get_actual_set_speed()
        
    def dispense(
        self, 
        volume: Optional[float] = None, 
        wait: bool = True, 
        show_progress: bool = False
    ) -> None:
        """
        Dispense specified volume from syringe.
        
        Args:
            volume: Volume to dispense in µL. If None, dispenses all content
            wait: Whether to wait for operation completion (default: True)
            show_progress: Display progress bar during operation (default: False)
            
        Raises:
            ValueError: If requested volume exceeds current syringe content
            
        Examples:
            >>> # Dispense specific volume
            >>> syringe.dispense(250)
            
            >>> # Dispense all content
            >>> syringe.dispense()
            
            >>> # Non-blocking dispense with progress
            >>> syringe.dispense(100, wait=False)
            
            >>> # Dispense with progress bar
            >>> syringe.dispense(500, show_progress=True)
        """
        if volume is None:
            command = 'A0R'
            volume = self._volume_counter                     
            self._volume_counter = 0
        else: 
            if self._volume_counter - volume < 0:
                raise ValueError(
                    f"Cannot dispense {volume} µL. "
                    f"Only {self._volume_counter:.1f} µL available in syringe."
                )
            
            steps = self._volume_to_increments(volume)
            command = f"D{steps}R"
            self._volume_counter -= volume

        wait_func = lambda: self.wait_for_syringe(volume, show_progress) if wait else None
        self.send_command(command, wait_for_completion=wait_func)

    def aspirate(
        self, 
        volume: Optional[float] = None, 
        wait: bool = True, 
        show_progress: bool = False
    ) -> None:
        """
        Aspirate specified volume into syringe.
        
        Args:
            volume: Volume to aspirate in µL. If None, fills entire syringe
            wait: Whether to wait for operation completion (default: True)
            show_progress: Display progress bar during operation (default: False)
            
        Raises:
            ValueError: If requested volume exceeds available syringe capacity
            
        Examples:
            >>> # Aspirate specific volume
            >>> syringe.aspirate(500)
            
            >>> # Fill entire syringe
            >>> syringe.aspirate()
            
            >>> # Non-blocking aspirate
            >>> syringe.aspirate(200, wait=False)
            
            >>> # Aspirate with progress bar
            >>> syringe.aspirate(1000, show_progress=True)
        """
        if volume is None:
            command = f"A{self._max_increments}R"       
            volume = self._syringe_size - self._volume_counter  
            self._volume_counter = self._syringe_size
        else:
            if self._volume_counter + volume > self._syringe_size:
                raise ValueError(
                    f"Cannot aspirate {volume} µL. "
                    f"Would exceed syringe capacity "
                    f"({self._volume_counter:.1f} + {volume} > {self._syringe_size} µL)"
                )

            steps = self._volume_to_increments(volume)
            command = f"P{steps}R"
            self._volume_counter += volume
        
        wait_func = lambda: self.wait_for_syringe(volume, show_progress) if wait else None
        self.send_command(command, wait_for_completion=wait_func)
    
    def _volume_to_increments(self, volume: float) -> int:
        """
        Convert volume to pump increments.
        
        Args:
            volume: Volume in microliters
            
        Returns:
            int: Number of pump increments
        """
        return int(volume * self._max_increments / self._syringe_size)

    def set_speed_uL_min(self, speed: float) -> None:
        """
        Set syringe flow rate in microliters per minute.
        
        Args:
            speed: Flow rate in µL/min
            
        Raises:
            ValueError: If speed is outside allowed range for syringe
            
        Note:
            Speed limits depend on syringe size:
            - Minimum: 0.05 × syringe_size µL/min
            - Maximum: 60 × syringe_size µL/min
            
        Examples:
            >>> # Set to 1.5 mL/min for 1000µL syringe
            >>> syringe.set_speed_uL_min(1500)
            
            >>> # Set slow speed for precise dispensing
            >>> syringe.set_speed_uL_min(100)
            
            >>> # Set maximum speed
            >>> max_speed = 60 * syringe.syringe_size
            >>> syringe.set_speed_uL_min(max_speed)
        """
        min_speed = self.MIN_SPEED_FACTOR * self._syringe_size
        max_speed = self.MAX_SPEED_FACTOR * self._syringe_size
        
        if speed < min_speed:
            raise ValueError(
                f"Flow rate {speed} µL/min too low. "
                f"Minimum: {min_speed:.1f} µL/min"
            )
        elif speed > max_speed:
            raise ValueError(
                f"Flow rate {speed} µL/min too high. "
                f"Maximum: {max_speed:.1f} µL/min"
            )

        speed_steps = int(speed * self.SPEED_CONVERSION_FACTOR / self._syringe_size)
        self._speed = speed
        self.send_command(f'V{speed_steps}R')

    def configuration_valve_type(self, valve_type: str) -> None:
        """
        Configure valve type attached to syringe pump.
        
        Sets pump firmware to match physical valve configuration.
        Must be called before valve movement commands.
        
        Args:
            valve_type: Valve type from VALVE_TYPES_DICT keys
            
        Raises:
            ValueError: If valve_type is not supported
            
        Supported valve types:
            - 'No': No valve attached
            - '3-Port': Standard 3-way valve
            - '4-Port': 4-way selection valve
            - '3-Port distribution (face seal)': Distribution valve with face seal
            - '3-Port distribution (plug)': Distribution valve with plug seal
            - '4-Port distribution': 4-port distribution valve
            - 'T': T-junction valve
            - '6-Port distribution': 6-port selection valve
            - '9-Port distribution': 9-port selection valve
            - '12-Port distribution': 12-port selection valve
            - 'Dual loop': Dual loop valve system
            
        Examples:
            >>> # Configure for 6-port distribution valve
            >>> syringe.configuration_valve_type('6-Port distribution')
            
            >>> # Configure for simple 3-port valve
            >>> syringe.configuration_valve_type('3-Port')
        """
        try:
            num_type_valve = self.VALVE_TYPES_DICT[valve_type]
        except KeyError:
            raise ValueError(
                f"Invalid valve type '{valve_type}'. "
                f"Valid options: {list(self.VALVE_TYPES_DICT.keys())}"
            )
        
        self.send_command(command=f"U{num_type_valve}R")
    
    def valve_in(self) -> None:
        """
        Switch valve to INPUT position.
        
        Connects syringe to input/inlet port for aspiration.
        Exact port depends on valve configuration:
        - 3-port: Connects to designated input port
        - Multi-port: Connects to port configured as input
        
        Examples:
            >>> syringe.valve_in()     # Switch to input
            >>> syringe.aspirate(500)  # Aspirate from input port
        """
        self.send_command('IR')

    def valve_up(self) -> None:
        """
        Switch valve to UP/EXTRA position.
        
        Connects syringe to auxiliary port (typically waste or air).
        Available on 4-port and special valve configurations.
        
        Examples:
            >>> syringe.valve_up()     # Switch to waste/air port
            >>> syringe.dispense()     # Empty to waste
        """
        self.send_command('ER')

    def valve_out(self) -> None:
        """
        Switch valve to OUTPUT position.
        
        Connects syringe to output/outlet port for dispensing.
        Exact port depends on valve configuration:
        - 3-port: Connects to designated output port
        - Multi-port: Connects to port configured as output
        
        Examples:
            >>> syringe.valve_out()    # Switch to output
            >>> syringe.dispense(100)  # Dispense to output port
        """
        self.send_command('OR')