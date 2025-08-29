"""
High-level SI (Sequential Injection) workflow methods with real-time feedback.

This module provides the PreparedSIMethods class, which implements complete
SI workflows for various analytical procedures. The class handles complex
sequences of valve switching, syringe operations, and sample handling with
comprehensive error checking and user feedback.

Key Features:
- Automated sample handling with autosampler integration
- Flexible volume handling with automatic cycle splitting
- Multiple flow modes (continuous, batch, multi-solvent)
- Sample homogenization methods (liquid mixing, air bubble mixing)
- Comprehensive cleaning and maintenance procedures
- Real-time status feedback and verbose logging
- Adaptive output for different environments (terminal vs non-interactive)
- Configurable parameters through SIConfig

Example:
    >>> from config import DEFAULT_CONFIG
    >>> from prepared_methods import PreparedSIMethods
    >>> 
    >>> # Initialize workflow system
    >>> workflow = PreparedSIMethods(
    ...     chemstation_controller,
    ...     syringe_device,
    ...     valve_device,
    ...     config=DEFAULT_CONFIG
    ... )
    >>> 
    >>> # Initialize system
    >>> workflow.system_initialization_and_cleaning()
    >>> 
    >>> # Prepare for continuous flow operations
    >>> workflow.prepare_continuous_flow(solvent_port=3)
    >>> 
    >>> # Fill samples
    >>> workflow.continuous_fill(vial=15, volume=500, solvent_port=3)
    >>> workflow.continuous_fill(vial=16, volume=750, solvent_port=3)
"""

import time
import sys
import os
from typing import Optional, Dict, Any, List, Tuple, Union
from ..devices.syringe_controller import SyringeController
from ..devices.valve_selector import ValveSelector
from .config import SIConfig, DEFAULT_CONFIG


class PreparedSIMethods:
    """
    High-level SI (Sequential Injection) workflows with real-time status feedback.
    
    This class provides complete automation workflows for SI systems, handling
    complex sequences of operations including sample preparation, reagent mixing,
    cleaning procedures, and sample homogenization. All methods include
    comprehensive error checking and optional verbose feedback.
    
    The class integrates three main components:
    1. ChemStation controller for autosampler operations
    2. SyringeController for precise fluid handling
    3. ValveSelector for reagent/port switching
    
    All operations can be customized through the SIConfig instance, allowing
    fine-tuning of volumes, speeds, timing, and other parameters.
    
    Attributes:
        chemstation: ChemStation API controller instance
        config: SIConfig instance with system parameters
        syringe: SyringeController instance for fluid operations
        valve: ValveSelector instance for port switching
        syringe_size: Maximum volume capacity of the syringe (µL)
        _interactive_terminal: Boolean indicating if running in interactive terminal
    """
    
    def __init__(self, 
                 chemstation_controller, 
                 syringe_device: SyringeController, 
                 valve_device: ValveSelector, 
                 config: Optional[SIConfig] = None):
        """
        Initialize SI workflow system with hardware controllers and configuration.
        
        Args:
            chemstation_controller: ChemStation API controller instance for autosampler
            syringe_device: Initialized SyringeController instance
            valve_device: Initialized ValveSelector instance  
            config: SIConfig instance (uses DEFAULT_CONFIG if None)
            
        Raises:
            ValidationError: If required vials are not present in the system
            
        Example:
            >>> workflow = PreparedSIMethods(
            ...     chemstation_controller=my_controller,
            ...     syringe_device=my_syringe,
            ...     valve_device=my_valve,
            ...     config=custom_config
            ... )
        """
        self.chemstation = chemstation_controller
        self.config = config or DEFAULT_CONFIG
        self.syringe = syringe_device
        self.valve = valve_device
        self.syringe_size = syringe_device.syringe_size

        # Detect if we're running in an interactive terminal
        self._interactive_terminal = self._is_interactive_terminal()

        # Validate that required system vials are present
        self._validate_system_setup()

    def _is_interactive_terminal(self) -> bool:
        """
        Detect if we're running in an interactive terminal.
        
        Returns:
            True if running in interactive terminal, False for output shells/redirects
        """
        return (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and 
            os.getenv('TERM') is not None and
            # Additional check for Jupyter notebooks
            'ipykernel' not in sys.modules
        )

    def _print_status(self, message: str, verbose: Optional[bool] = None) -> None:
        """
        Print status message with adaptive output based on terminal type.
        
        Args:
            message: Status message to display
            verbose: Show status messages (uses config.verbose if None)
        """
        verbose = self._get_verbose(verbose)
        if not verbose:
            return
        
        if self._interactive_terminal:
            # Interactive terminal - overwrite current line
            print(f"\r{message}".ljust(80), end='', flush=True)
        else:
            # Non-interactive output - new lines with prefix
            print(f"[SI] {message}")

    def _complete_status_line(self, verbose: Optional[bool] = None) -> None:
        """
        Complete the current status line (add newline in interactive mode).
        
        Args:
            verbose: Whether to complete line (uses config.verbose if None)
        """
        verbose = self._get_verbose(verbose)
        if verbose and self._interactive_terminal:
            print()  # Add newline to complete the overwritten line

    def _validate_system_setup(self) -> None:
        """
        Validate that required vials are present in the autosampler.
        
        Raises:
            ValidationError: If wash_vial or waste_vial are not found
        """
        try:
            self.chemstation.validation.validate_vial_in_system(self.config.wash_vial)
            self.chemstation.validation.validate_vial_in_system(self.config.waste_vial)
        except Exception as e:
            raise ValueError(f"System validation failed: {e}")

    # ==========================================================================
    # BASIC SYSTEM OPERATIONS
    # ==========================================================================

    def load_to_replenishment(self, vial_number: int, verbose: Optional[bool] = None) -> None:
        """
        Load specified vial to replenishment position in CE carousel.
        
        The replenishment position is where the sample needle can access
        the vial contents for aspiration or dispensing operations.
        
        Args:
            vial_number: Vial position number (1-50 for typical autosamplers)
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            ValueError: If vial_number is outside valid range
            SystemError: If autosampler operation fails
            
        Example:
            >>> workflow.load_to_replenishment(vial_number=25)
            Loading vial 25 to replenishment position...
        """
        verbose = self._get_verbose(verbose)
        
        if not (1 <= vial_number <= 50):
            raise ValueError(f"Vial number {vial_number} outside valid range (1-50)")
        
        if verbose:
            self._print_status(f"Loading vial {vial_number} to replenishment position...")
        
        try:
            self.chemstation.ce.load_vial_to_position(vial_number, "replenishment")
        except Exception as e:
            raise SystemError(f"Failed to load vial {vial_number}: {e}")
        
        if verbose:
            time.sleep(0.1)  # Brief pause for visual feedback

    def unload_from_replenishment(self, verbose: Optional[bool] = None) -> None:
        """
        Unload vial from replenishment position back to carousel.
        
        Returns the currently loaded vial back to its original position
        in the autosampler carousel.
        
        Args:
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            SystemError: If autosampler operation fails
            
        Example:
            >>> workflow.unload_from_replenishment()
            Unloading vial from replenishment position...
        """
        verbose = self._get_verbose(verbose)
        
        if verbose:
            self._print_status("Unloading vial from replenishment position...")
        
        try:
            self.chemstation.ce.unload_vial_from_position()
        except Exception as e:
            raise SystemError(f"Failed to unload vial: {e}")
        
        if verbose:
            time.sleep(0.1)

    def _flush_syringe_loop(self, verbose: Optional[bool] = None) -> None:
        """
        Flush and prime the syringe holding loop.
        
        This internal method performs a complete flush of the syringe loop
        to remove any residual liquids and prime the system with fresh
        solution. Used during system initialization.
        
        Args:
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            This is an internal method typically called by other procedures.
            The sequence includes multiple aspiration/dispensing cycles with
            valve switching to ensure complete flushing.
        """
        verbose = self._get_verbose(verbose)
        
        if verbose:
            self._print_status("Flushing syringe loop...")
        
        # Complete flushing sequence
        self.valve.position(self.config.waste_port)
        self.syringe.valve_in()
        self.syringe.aspirate(150)
        self.syringe.valve_up()
        self.syringe.aspirate(75)
        self.syringe.valve_out()
        self.syringe.dispense()
        self.syringe.valve_in()
        self.syringe.aspirate()
        self.syringe.valve_out()
        self.syringe.dispense()

    def _create_separating_bubble(self, port: int, bubble_volume: int, 
                                  verbose: Optional[bool] = None) -> None:
        """
        Create separating bubble at end of holding coil.
        
        Separating bubbles prevent mixing between different solutions
        in the holding coil and transfer lines. This is crucial for
        maintaining sample integrity in sequential operations.
        
        Args:
            port: Port number to aspirate from (typically air_port)
            bubble_volume: Volume of bubble in microliters
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            The bubble is created by aspirating from the specified port
            (usually air) and positioning it at the end of the holding coil
            using valve switching and syringe operations.
        """
        verbose = self._get_verbose(verbose)
        
        port_name = "air" if port == self.config.air_port else f"port {port}"
        if verbose:
            self._print_status(f"Creating {bubble_volume} µL {port_name} bubble in holding coil...")
        
        self.syringe.valve_out()
        self.valve.position(port)
        self.syringe.aspirate(bubble_volume)
        self.syringe.valve_up()
        self.syringe.dispense()
        self.syringe.valve_out()

    def clean_needle(self, volume_flush: float, wash_vial: Optional[int] = None, 
                     verbose: Optional[bool] = None) -> None:
        """
        Clean the dispensing needle to prevent cross-contamination.
        
        This procedure uses a wash vial containing cleaning solution to
        flush the needle exterior and interior, preventing sample carryover
        between different vials or operations.
        
        Args:
            volume_flush: Total volume for needle cleaning (µL)
            wash_vial: Vial number containing wash solution (uses config default if None)
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            The cleaning is split into two parts: half dispensed into the wash vial
            (for exterior cleaning) and half dispensed to waste (for interior cleaning).
            
        Example:
            >>> workflow.clean_needle(volume_flush=100, wash_vial=48)
            Cleaning needle with 100 µL in vial 48...
        """
        verbose = self._get_verbose(verbose)
        wash_vial = wash_vial or self.config.wash_vial
        
        if verbose:
            self._print_status(f"Cleaning needle with {volume_flush} µL in vial {wash_vial}...")
        
        # Load wash vial and clean with half volume
        self.load_to_replenishment(wash_vial, verbose=False)
        time.sleep(self.config.wait_vial_load)
        self.syringe.dispense(volume_flush/2)

        # Unload and dispense remaining to waste
        self.unload_from_replenishment(verbose=False)
        time.sleep(self.config.wait_vial_unload)
        self.syringe.dispense(volume_flush/2)

    # ==========================================================================
    # SYSTEM INITIALIZATION AND SETUP
    # ==========================================================================

    def system_initialization_and_cleaning(self, 
                                          waste_vial: Optional[int] = None, 
                                          bubble: int = 20,
                                          verbose: Optional[bool] = None) -> None:
        """
        Perform complete system initialization and cleaning procedure.
        
        This comprehensive procedure prepares the SI system for operation by:
        1. Initializing the syringe pump
        2. Flushing all lines with appropriate solvents
        3. Creating separating bubbles
        4. Priming transfer lines
        
        This should be run at the beginning of each analytical session.
        
        Args:
            waste_vial: Waste vial number (uses config default if None)
            bubble: Separating bubble volume in µL
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            SystemError: If any initialization step fails
            
        Example:
            >>> workflow.system_initialization_and_cleaning()
            [SI] Loading vial 50 to replenishment position...
            [SI] Initializing syringe pump...
            [SI] Flushing syringe loop...
            [SI] Creating 20 µL air bubble in holding coil...
            [SI] Flushing system with methanol (250 µL)...
            [SI] Flushing with DI water...
            [SI] Flushing transfer line...
            [SI] System initialization completed successfully!
        """
        verbose = self._get_verbose(verbose)
        waste_vial = waste_vial or self.config.waste_vial
        
        if verbose:
            print(f"\r{'='*80}")
            print(f"\rSYSTEM INITIALIZATION AND CLEANING")
            print(f"\r{'='*80}")
        
        # Load waste vial and set initial conditions
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.valve.position(self.config.waste_port)

        # Initialize syringe pump
        if verbose:
            self._print_status("Initializing syringe pump...")
        
        try:
            self.syringe.initialize()
            self.syringe.set_speed_uL_min(self.config.speed_fast)
        except Exception as e:
            raise SystemError(f"Syringe initialization failed: {e}")

        # Flush and prime holding loop
        self._flush_syringe_loop(verbose=verbose)
        time.sleep(1)

        # Create separating bubble
        self._create_separating_bubble(self.config.air_port, bubble, verbose=verbose)

        # Flush system with methanol for cleaning
        if verbose:
            self._print_status("Flushing system with methanol (250 µL)...")
        time.sleep(1)
        
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(20)
        self.valve.position(self.config.meoh_port)
        self.syringe.aspirate(250)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate()
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Flush with DI water to remove methanol residue
        if verbose:
            self._print_status("Flushing with DI water...")
        time.sleep(1)
        
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(50)
        self.valve.position(self.config.di_port)
        self.syringe.aspirate()
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Flush transfer line to ensure connectivity
        if verbose:
            self._print_status("Flushing transfer line...")
            
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(500)
        self.valve.position(self.config.di_port)
        self.syringe.aspirate(100)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            self._print_status("System initialization completed successfully!")
            self._complete_status_line(verbose)

    # ==========================================================================
    # FLOW PREPARATION METHODS
    # ==========================================================================

    def prepare_continuous_flow(self, 
                               solvent_port: int, 
                               waste_vial: Optional[int] = None,
                               bubble_volume: int = 10,
                               solvent_holding_coil_volume: int = 10,
                               transfer_coil_flush: int = 500,
                               holding_coil_flush: Optional[int] = None,
                               speed: Optional[int] = None,
                               verbose: Optional[bool] = None) -> None:
        """
        Prepare system for continuous flow filling operations.
        
        Continuous flow mode maintains a continuous column of solvent from
        the reservoir through the holding coil to the transfer line. This
        mode is ideal for multiple fills with the same solvent, providing
        consistent flow rates and minimal air bubbles.
        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number (uses config default if None)
            bubble_volume: Air bubble volume in µL for separation
            solvent_holding_coil_volume: Solvent volume at end of holding coil
            transfer_coil_flush: Volume for transfer coil flushing  
            holding_coil_flush: Volume for holding coil flushing (uses config default if None)
            speed: Flow rate in µL/min (uses config.speed_slow if None)
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            After this preparation, use continuous_fill() for sample dispensing.
            The system maintains solvent continuity between fills, making it
            efficient for processing multiple samples with the same solvent.
            
        Example:
            >>> workflow.prepare_continuous_flow(
            ...     solvent_port=3,  # DI water
            ...     transfer_coil_flush=600
            ... )
            [SI] Loading vial 50 to replenishment position...
            [SI] Flushing holding coil with 500 µL solvent...
            [SI] Creating 10 µL air bubble in holding coil...
            [SI] System ready for continuous flow operations
        """
        verbose = self._get_verbose(verbose)
        waste_vial = waste_vial or self.config.waste_vial
        holding_coil_flush = holding_coil_flush or self.config.default_holding_coil_volume
        speed = speed or self.config.speed_slow
        
        if verbose:
            print(f"\r{'='*80}")
            print(f"\rPREPARING CONTINUOUS FLOW (Solvent Port: {solvent_port})")
            print(f"\r{'='*80}")
        
        # Load waste vial and set speed
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Flush holding coil with solvent
        if verbose:
            self._print_status(f"Flushing holding coil with {transfer_coil_flush} µL solvent...")
        
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(transfer_coil_flush)
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Create separating bubbles for system organization
        self._create_separating_bubble(self.config.air_port, bubble_volume, verbose=verbose)
        self._create_separating_bubble(solvent_port, solvent_holding_coil_volume, verbose=verbose)

        # Fill transfer line with solvent to establish continuity
        if verbose:
            self._print_status(f"Filling transfer line with {holding_coil_flush} µL solvent...")
            
        self.valve.position(solvent_port)
        self.syringe.aspirate(holding_coil_flush)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            self._print_status("System ready for continuous flow operations")
            self._complete_status_line(verbose)

    def prepare_batch_flow(self, 
                          solvent_port: int, 
                          waste_vial: Optional[int] = None,
                          bubble_volume: int = 10,
                          transfer_coil_volume: Optional[int] = None,
                          coil_flush: int = 150,
                          speed: Optional[int] = None,
                          verbose: Optional[bool] = None) -> None:
        """
        Prepare system for batch flow (discontinuous) filling operations.
        
        Batch flow mode uses air-driven dispensing where the transfer line is
        filled with air rather than solvent. This mode is suitable for single
        fills or when changing solvents between operations, as it provides
        complete separation between different solutions.
        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number (uses config default if None)
            bubble_volume: Air bubble volume in µL
            transfer_coil_volume: Transfer line volume in µL (uses config default if None)
            coil_flush: Volume for coil flushing in µL
            speed: Flow rate in µL/min (uses config.speed_slow if None)
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            After this preparation, use batch_fill() methods for sample dispensing.
            Each fill operation is independent, with air separation preventing
            cross-contamination between different solvents or samples.
            
        Example:
            >>> workflow.prepare_batch_flow(
            ...     solvent_port=3,  # DI water port
            ...     transfer_coil_volume=600
            ... )
            PREPARING BATCH FLOW (Solvent Port: 3)
            [SI] Loading vial 50 to replenishment position...
            [SI] Flushing transfer loop with 150 µL...
            [SI] Creating 10 µL air bubble in holding coil...
            [SI] Filling transfer line with 600 µL air...
            [SI] System ready for batch flow operations
        """
        verbose = self._get_verbose(verbose)
        waste_vial = waste_vial or self.config.waste_vial
        transfer_coil_volume = transfer_coil_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_slow
        
        if verbose:
            print(f"\r{'='*80}")
            print(f"\rPREPARING BATCH FLOW (Solvent Port: {solvent_port})")
            print(f"\r{'='*80}")
        
        # Load waste vial and set speed
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Flush transfer loop to remove previous contents
        if verbose:
            self._print_status(f"Flushing transfer loop with {coil_flush} µL...")
        
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Create separating bubble
        self._create_separating_bubble(self.config.air_port, bubble_volume, verbose=verbose)

        # Fill transfer line with air for batch operations
        if verbose:
            self._print_status(f"Filling transfer line with {transfer_coil_volume} µL air...")
        
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_coil_volume)
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            self._print_status("System ready for batch flow operations")
            self._complete_status_line(verbose)

    # ==========================================================================
    # SAMPLE FILLING METHODS
    # ==========================================================================

    def continuous_fill(self, 
                       vial: int, 
                       volume: int, 
                       solvent_port: int,
                       flush_needle: Optional[int] = None,
                       wash_vial: Optional[int] = None,
                       speed: Optional[int] = None,
                       verbose: Optional[bool] = None) -> None:
        """
        Execute continuous flow filling operation.
        
        Performs sample filling using continuous solvent flow from the reservoir
        through the holding coil to the target vial. This method is efficient
        for multiple fills with the same solvent and provides consistent flow
        characteristics.
        
        Args:
            vial: Target vial number (1-50)
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent reservoir
            flush_needle: Optional needle flush volume in µL (for cleaning)
            wash_vial: Vial for needle washing (uses config default if None)
            speed: Flow rate in µL/min (uses config.speed_normal if None)
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            The system must first be prepared using prepare_continuous_flow().
            Large volumes are automatically split into multiple syringe cycles.
            
        Raises:
            ValueError: If volume is negative or vial number is invalid
            
        Example:
            >>> workflow.continuous_fill(
            ...     vial=15, 
            ...     volume=750, 
            ...     solvent_port=3,
            ...     flush_needle=50
            ... )
            [SI] Continuous fill: Vial 15, Volume 750 µL, Port 3
            [SI] Loading vial 15 to replenishment position...
            [SI] Cycle 1/2: Aspirating 500 µL from port 3...
            [SI] Cycle 1/2: Dispensing 500 µL to vial 15...
            [SI] Cycle 2/2: Aspirating 300 µL from port 3...
            [SI] Cycle 2/2: Dispensing 250 µL, keeping 50 µL for flush...
            [SI] Cleaning needle with 50 µL in vial 48...
            [SI] Continuous fill of vial 15 completed (750 µL)
        """
        verbose = self._get_verbose(verbose)
        wash_vial = wash_vial or self.config.wash_vial
        speed = speed or self.config.speed_normal

        # Validate input parameters
        if volume <= 0:
            raise ValueError(f"Volume must be positive, got {volume}")
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial number {vial} outside valid range (1-50)")

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size)
        
        if verbose:
            self._print_status(f"Continuous fill: Vial {vial}, Volume {volume} µL, Port {solvent_port}")
        
        # Load target vial and set flow rate
        self.load_to_replenishment(vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Execute filling cycles
        for i, cycle_vol in enumerate(cycle_volumes):
            if verbose:
                self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Aspirating {cycle_vol} µL from port {solvent_port}...")
            
            if i != len(cycle_volumes) - 1:
                # Regular cycles - full volume transfer
                self.valve.position(solvent_port)
                self.syringe.aspirate(cycle_vol)
                
                if verbose:
                    self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Dispensing {cycle_vol} µL to vial {vial}...")
                
                self.valve.position(self.config.transfer_port)
                self.syringe.dispense(cycle_vol)
            else:
                # Last cycle with optional needle flush
                if flush_needle is not None:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    
                    if verbose:
                        self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Dispensing {cycle_vol - flush_needle} µL, keeping {flush_needle} µL for flush...")
                    
                    self.valve.position(self.config.transfer_port)
                    self.syringe.dispense(cycle_vol - flush_needle)
                    
                    self.clean_needle(flush_needle, wash_vial, verbose=verbose)
                else:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    
                    if verbose:
                        self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Dispensing final {cycle_vol} µL...")
                    
                    self.valve.position(self.config.transfer_port)
                    self.syringe.dispense(cycle_vol)

        self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            self._print_status(f"Continuous fill of vial {vial} completed ({volume} µL)")
            self._complete_status_line(verbose)

    def batch_fill(self, 
                  vial: int, 
                  volume: int, 
                  solvent_port: int,
                  transfer_line_volume: Optional[int] = None,
                  bubble_volume: int = 10,
                  flush_needle: Optional[int] = None,
                  speed: Optional[int] = None,
                  unload: bool = True,
                  wait: Optional[int] = None,
                  verbose: Optional[bool] = None) -> None:
        """
        Execute batch flow (discontinuous) filling operation.
        
        Performs sample filling using batch (discontinuous) flow where solvent
        is first loaded into the holding coil with an air bubble, then pushed
        to the target vial using air pressure. This provides complete isolation
        between different solutions.
        
        Args:
            vial: Target vial number (1-50)
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent reservoir
            transfer_line_volume: Volume of transfer line (uses config default if None)
            bubble_volume: Air bubble volume for separation
            flush_needle: Optional needle flush volume in µL
            speed: Flow rate in µL/min (uses config.speed_normal if None)
            unload: Whether to unload vial after filling
            wait: Optional wait time after dispensing (seconds)
            verbose: Show status messages (uses config.verbose if None)
            
        Note:
            The system must first be prepared using prepare_batch_flow().
            Large volumes are automatically split into multiple cycles.
            
        Example:
            >>> workflow.batch_fill(
            ...     vial=20,
            ...     volume=400,
            ...     solvent_port=5,  # Methanol
            ...     bubble_volume=15,
            ...     wait=2
            ... )
            [SI] Batch fill: Vial 20, Volume 400 µL, Port 5
            [SI] Loading vial 20 to replenishment position...
            [SI] Aspirating 15 µL air bubble...
            [SI] Cycle 1/1: Aspirating 400 µL from port 5...
            [SI] Cycle 1/1: Transferring to line...
            [SI] Dispensing air bubble...
            [SI] Pushing with 600 µL air at high speed...
            [SI] Dispensing to vial 20...
            [SI] Waiting 2 seconds...
            [SI] Batch fill of vial 20 completed (400 µL)
        """
        verbose = self._get_verbose(verbose)
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_normal

        # Validate input parameters
        if volume <= 0:
            raise ValueError(f"Volume must be positive, got {volume}")
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial number {vial} outside valid range (1-50)")

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size - bubble_volume)
        
        if verbose:
            self._print_status(f"Batch fill: Vial {vial}, Volume {volume} µL, Port {solvent_port}")
        
        # Load target vial and set flow rate
        self.load_to_replenishment(vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Aspirate air bubble for separation
        if verbose:
            self._print_status(f"Aspirating {bubble_volume} µL air bubble...")
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(bubble_volume)

        # Fill cycles with solvent
        for i, cycle_vol in enumerate(cycle_volumes):
            if verbose:
                self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Aspirating {cycle_vol} µL from port {solvent_port}...")
            
            self.valve.position(solvent_port)
            self.syringe.aspirate(cycle_vol)
            
            if verbose:
                self._print_status(f"Cycle {i+1}/{len(cycle_volumes)}: Transferring to line...")
            
            self.valve.position(self.config.transfer_port)
            self.syringe.dispense(cycle_vol)

        # Dispense air bubble separator
        if verbose:
            self._print_status("Dispensing air bubble...")
        self.syringe.dispense()
        
        # Push with high-speed air
        if verbose:
            self._print_status(f"Pushing with {transfer_line_volume} µL air at high speed...")
        
        self.syringe.set_speed_uL_min(self.config.speed_air)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_line_volume)
        self.valve.position(self.config.transfer_port)
        self.syringe.set_speed_uL_min(speed)

        # Final dispensing with optional needle cleaning
        if flush_needle is None:
            if verbose:
                self._print_status(f"Dispensing to vial {vial}...")
            self.syringe.dispense()
            if wait:
                if verbose:
                    self._print_status(f"Waiting {wait} seconds...")
                time.sleep(wait)
        else:
            if verbose:
                self._print_status(f"Dispensing {transfer_line_volume - flush_needle} µL, keeping {flush_needle} µL for flush...")
            self.syringe.dispense(transfer_line_volume - flush_needle)
            if wait:
                time.sleep(wait)
            self.clean_needle(flush_needle, verbose=verbose)

        if unload:
            self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            self._print_status(f"Batch fill of vial {vial} completed ({volume} µL)")
            self._complete_status_line(verbose)

    def batch_fill_multiple_solvents(self,
                                    vial: int,
                                    solvent_ports: List[int],
                                    volumes: List[int],
                                    air_push_volume: int = 15,
                                    transfer_line_volume: Optional[int] = None,
                                    speed: Optional[int] = None,
                                    solvent_speeds: Optional[List[int]] = None,
                                    air_speed: Optional[int] = None,
                                    flush_needle: Optional[int] = None,
                                    wash_vial: Optional[int] = None,
                                    unload: bool = True,
                                    wait: Optional[int] = None,
                                    verbose: Optional[bool] = None) -> None:
        """
        Execute batch filling with multiple solvents from different ports.
        
        This advanced method allows sequential dispensing of different solvents
        into a single vial, with air bubble separation between each solvent.
        Useful for creating solvent mixtures or adding reagents in sequence.
        
        Args:
            vial: Target vial number (1-50)
            solvent_ports: List of port numbers for different solvents
            volumes: List of volumes corresponding to each port (µL)
            air_push_volume: Air bubble volume between solvents (µL)
            transfer_line_volume: Volume for final air push (uses config default if None)
            speed: Default flow rate for liquid handling (µL/min)
            solvent_speeds: Optional list of speeds for each solvent (µL/min)
            air_speed: Flow rate for air aspiration (uses config.speed_air if None)
            flush_needle: Optional needle flush volume (µL)
            wash_vial: Vial for needle washing (uses config default if None)
            unload: Whether to unload vial after filling
            wait: Optional wait time after dispensing (seconds)
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            ValueError: If port and volume lists don't match, or volumes are invalid
            
        Example:
            >>> workflow.batch_fill_multiple_solvents(
            ...     vial=25,
            ...     solvent_ports=[3, 5, 6],  # DI water, methanol, buffer
            ...     volumes=[300, 150, 50],   # Different volumes for each
            ...     solvent_speeds=[2000, 1500, 1000]  # Custom speeds
            ... )
            [SI] Multi-solvent batch fill: Vial 25, Total volume 500 µL from 3 ports
            [SI] Loading vial 25 to replenishment position...
            [SI] Solvent 1/3: Aspirating 15 µL air bubble...
            [SI] Solvent 1/3: Aspirating 300 µL from port 3 at 2000 µL/min...
            [SI] Solvent 2/3: Aspirating 150 µL from port 5 at 1500 µL/min...
            [SI] Solvent 3/3: Aspirating 50 µL from port 6 at 1000 µL/min...
            [SI] Final air push: 600 µL at 5000 µL/min...
            [SI] Multi-solvent batch fill completed: 500 µL total in vial 25
        """
        verbose = self._get_verbose(verbose)
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_normal
        air_speed = air_speed or self.config.speed_air
        wash_vial = wash_vial or self.config.wash_vial
        
        # Validate input parameters
        if len(solvent_ports) != len(volumes):
            raise ValueError("Number of solvent ports and volumes must match")
        
        if not solvent_ports or not volumes:
            raise ValueError("At least one solvent port and volume must be specified")
        
        if any(v <= 0 for v in volumes):
            raise ValueError("All volumes must be positive")
        
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial number {vial} outside valid range (1-50)")
        
        # Set up solvent speeds
        if solvent_speeds is not None:
            if len(solvent_speeds) != len(solvent_ports):
                raise ValueError("Number of solvent speeds must match number of solvent ports")
        else:
            solvent_speeds = [speed] * len(solvent_ports)
        
        # Validate individual volumes don't exceed syringe capacity
        max_single_volume = max(volumes) + air_push_volume
        if max_single_volume > self.syringe_size:
            raise ValueError(f"Largest single volume ({max_single_volume} µL) exceeds syringe capacity")
        
        if verbose:
            total_volume = sum(volumes)
            self._print_status(f"Multi-solvent batch fill: Vial {vial}, Total volume {total_volume} µL from {len(solvent_ports)} ports")
        
        # Load target vial
        self.load_to_replenishment(vial, verbose=verbose)
        
        # Sequential processing of solvents
        for idx, (port, volume, solvent_speed) in enumerate(zip(solvent_ports, volumes, solvent_speeds)):
            if verbose:
                self._print_status(f"Solvent {idx+1}/{len(solvent_ports)}: Aspirating {air_push_volume} µL air bubble...")
            
            # Set speed for air aspiration
            self.syringe.set_speed_uL_min(air_speed)
            
            # Aspirate air bubble separator
            self.valve.position(self.config.air_port)
            self.syringe.aspirate(air_push_volume)
            
            if verbose:
                self._print_status(f"Solvent {idx+1}/{len(solvent_ports)}: Aspirating {volume} µL from port {port} at {solvent_speed} µL/min...")
            
            # Set speed for this specific solvent
            self.syringe.set_speed_uL_min(solvent_speed)
            
            # Aspirate solvent from specified port
            self.valve.position(port)
            self.syringe.aspirate(volume)
            
            if verbose:
                self._print_status(f"Solvent {idx+1}/{len(solvent_ports)}: Transferring to line...")
            
            # Transfer to transfer line immediately
            self.valve.position(self.config.transfer_port)
            self.syringe.dispense()
        
        # Final air push to dispense mixture
        if verbose:
            self._print_status(f"Final air push: {transfer_line_volume} µL at {air_speed} µL/min...")
        
        self.syringe.set_speed_uL_min(air_speed)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_line_volume)
        
        # Change speed back to normal for dispensing
        self.syringe.set_speed_uL_min(speed)
        self.valve.position(self.config.transfer_port)
        
        # Final dispensing with optional needle cleaning
        if flush_needle is None:
            if verbose:
                self._print_status(f"Dispensing mixture to vial {vial}...")
            self.syringe.dispense()
            if wait:
                time.sleep(wait)
        else:
            if verbose:
                self._print_status(f"Dispensing mixture, keeping {flush_needle} µL for flush...")
            self.syringe.dispense(transfer_line_volume - flush_needle)
            if wait:
                time.sleep(wait)
            self.clean_needle(flush_needle, wash_vial, verbose=verbose)
        
        # Unload vial if requested
        if unload:
            self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            total_volume = sum(volumes)
            self._print_status(f"Multi-solvent batch fill completed: {total_volume} µL total in vial {vial}")
            self._complete_status_line(verbose)

    # ==========================================================================
    # SAMPLE HOMOGENIZATION METHODS
    # ==========================================================================

    def prepare_for_liquid_homogenization(self, 
                                        waste_vial: Optional[int] = None,
                                        transfer_line_volume: Optional[int] = None,
                                        meoh_flush_volume: Optional[int] = 20,
                                        air_bubble: Optional[int] = None,
                                        verbose: Optional[bool] = None) -> None:
        """
        Prepare system for liquid-based homogenization operations.
        
        This procedure flushes the transfer line and creates a protective air
        bubble in the holding coil. Used before liquid homogenization to ensure
        a clean system and prevent contamination of the holding coil.
        
        Args:
            waste_vial: Waste vial number (uses config default if None)
            transfer_line_volume: Volume to flush from transfer line (µL)
            meoh_flush_volume: Optional methanol flush volume (µL), None to skip
            air_bubble: Air bubble volume in holding coil (µL)
            verbose: Show status messages (uses config.verbose if None)
        
        Example:
            >>> workflow.prepare_for_liquid_homogenization(verbose=True)
            [SI] Preparing for liquid homogenization...
            [SI] Loading vial 50 to replenishment position...
            [SI] Flushing transfer line (600 µL)...
            [SI] Adding methanol flush (20 µL)...
            [SI] Creating air bubble (30 µL) in holding coil...
            [SI] System ready for liquid homogenization
        """
        verbose = self._get_verbose(verbose)
        
        # Use config defaults
        waste_vial = waste_vial or self.config.waste_vial
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        air_bubble = air_bubble or self.config.default_air_flush
        
        if verbose:
            self._print_status("Preparing for liquid homogenization...")
        
        self.load_to_replenishment(waste_vial)
        self.valve.position(self.config.transfer_port)
        
        self.syringe.valve_in()
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        if verbose:
            self._print_status(f"Flushing transfer line ({transfer_line_volume} µL)...")
        
        self.syringe.aspirate(transfer_line_volume)
        self.syringe.valve_out()
        
        # Optional methanol flush for better cleaning
        if meoh_flush_volume is not None:
            if verbose:
                self._print_status(f"Adding methanol flush ({meoh_flush_volume} µL)...")
            self.valve.position(self.config.meoh_port)
            self.syringe.aspirate(meoh_flush_volume)
            self.valve.position(self.config.transfer_port)
        
        self.syringe.dispense()
        self.unload_from_replenishment()
        
        # Create protective air bubble in holding coil
        if verbose:
            self._print_status(f"Creating air bubble ({air_bubble} µL) in holding coil...")
        
        self.syringe.aspirate(air_bubble)
        self.syringe.valve_in()
        self.syringe.dispense()
        self.syringe.valve_out()
        
        if verbose:
            self._print_status("System ready for liquid homogenization")
            self._complete_status_line(verbose)

    def homogenize_by_liquid_mixing(self,
                                    vial: int,
                                    volume_aspirate: Optional[int] = None,
                                    num_cycles: Optional[int] = None,
                                    aspirate_speed: Optional[int] = None,
                                    dispense_speed: Optional[int] = None,
                                    wait_after_aspirate: Optional[float] = None,
                                    wait_after_dispense: Optional[float] = None,
                                    air_flush: Optional[int] = 10,
                                    clean_after: Optional[bool] = None,
                                    cleaning_solution_volume: Optional[int] = None,
                                    verbose: Optional[bool] = None) -> None:
        """
        Homogenize sample by liquid aspiration and dispensing.
        
        This gentle homogenization method mixes samples by repeatedly aspirating
        and dispensing liquid. It's suitable for sensitive samples that might be
        damaged by vigorous air bubble mixing, and provides precise control over
        mixing intensity.
        
        Args:
            vial: Target vial number (1-50)
            volume_aspirate: Volume to aspirate per cycle (µL)
            num_cycles: Number of mixing cycles
            aspirate_speed: Speed for aspiration (µL/min)
            dispense_speed: Speed for dispensing (µL/min)
            wait_after_aspirate: Wait time after aspiration (seconds)
            wait_after_dispense: Wait time after dispensing (seconds)
            air_flush: Air volume to flush at end (µL), None to skip
            clean_after: Whether to clean transfer line after
            cleaning_solution_volume: Volume for cleaning (µL)
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            ValueError: If aspirate volume exceeds syringe capacity
        
        Example:
            >>> workflow.homogenize_by_liquid_mixing(
            ...     vial=15,
            ...     volume_aspirate=400,
            ...     num_cycles=3,
            ...     aspirate_speed=1500,
            ...     dispense_speed=2000,
            ...     verbose=True
            ... )
            [SI] Loading vial 15 for liquid homogenization...
            [SI] Cycle 1/3: Aspirating 400 µL at 1500 µL/min...
            [SI] Cycle 1/3: Dispensing at 2000 µL/min...
            [SI] Cycle 2/3: Aspirating 400 µL at 1500 µL/min...
            [SI] Cycle 2/3: Dispensing at 2000 µL/min...
            [SI] Cycle 3/3: Aspirating 400 µL at 1500 µL/min...
            [SI] Cycle 3/3: Dispensing at 2000 µL/min...
            [SI] Flushing needle with 10 µL air...
            [SI] Liquid homogenization of vial 15 completed
        """
        # Use config defaults
        verbose = self._get_verbose(verbose)
        volume_aspirate = volume_aspirate or self.config.default_homogenization_volume
        num_cycles = num_cycles or self.config.homogenization_liquid_cycles
        aspirate_speed = aspirate_speed or self.config.speed_homogenization_aspirate
        dispense_speed = dispense_speed or self.config.speed_homogenization_dispense
        wait_after_aspirate = wait_after_aspirate or self.config.wait_after_aspirate
        wait_after_dispense = wait_after_dispense or self.config.wait_after_dispense
        clean_after = clean_after if clean_after is not None else self.config.homogenization_clean_after
        cleaning_solution_volume = cleaning_solution_volume or self.config.default_cleaning_solution_volume
        
        # Validate parameters
        if volume_aspirate > self.syringe_size:
            raise ValueError(f"Aspirate volume ({volume_aspirate} µL) exceeds syringe capacity ({self.syringe_size} µL)")
        
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial number {vial} outside valid range (1-50)")
        
        if verbose:
            self._print_status(f"Loading vial {vial} for liquid homogenization...")
        
        self.load_to_replenishment(vial)
        
        self.syringe.valve_out()
        self.valve.position(self.config.transfer_port)
        
        # Execute mixing cycles
        for cycle in range(num_cycles):
            if verbose:
                self._print_status(f"Cycle {cycle+1}/{num_cycles}: Aspirating {volume_aspirate} µL at {aspirate_speed} µL/min...")
            
            self.syringe.set_speed_uL_min(aspirate_speed)
            self.syringe.aspirate(volume_aspirate)
            
            if wait_after_aspirate > 0:
                time.sleep(wait_after_aspirate)
            
            if verbose:
                self._print_status(f"Cycle {cycle+1}/{num_cycles}: Dispensing at {dispense_speed} µL/min...")
            
            self.syringe.set_speed_uL_min(dispense_speed)
            self.syringe.dispense()
            
            if wait_after_dispense > 0:
                time.sleep(wait_after_dispense)
        
        # Air flush to clear needle
        if air_flush is not None and air_flush > 0:
            if verbose:
                self._print_status(f"Flushing needle with {air_flush} µL air...")
            
            self.syringe.valve_in()
            self.syringe.aspirate(air_flush)
            self.syringe.valve_out()
            self.syringe.dispense()
        
        self.unload_from_replenishment()
        
        # Optional cleaning after homogenization
        if clean_after:
            if verbose:
                self._print_status("Cleaning transfer line after homogenization...")
            self.clean_transfer_line_after_homogenization(
                cleaning_solution_volume=cleaning_solution_volume,
                verbose=verbose
            )
        
        if verbose:
            self._print_status(f"Liquid homogenization of vial {vial} completed")
            self._complete_status_line(verbose)

    def homogenize_by_air_mixing(self,
                                vial: int,
                                volume_aspirate: Optional[int] = None,
                                num_cycles: Optional[int] = None,
                                aspirate_speed: Optional[int] = None,
                                dispense_speed: Optional[int] = None,
                                air_bubble_volume: Optional[int] = None,
                                wait_between_cycles: float = 3.0,
                                wait_after: float = 0,
                                verbose: Optional[bool] = None) -> None:
        """
        Homogenize sample using air bubble mixing.
        
        This vigorous homogenization method creates air bubbles in the liquid
        for aggressive mixing. The air bubbles create turbulence and shearing
        forces that are effective for viscous samples or when thorough mixing
        is required.
        
        Args:
            vial: Target vial number (1-50)
            volume_aspirate: Liquid volume to aspirate per cycle (µL)
            num_cycles: Number of mixing cycles
            aspirate_speed: Speed for liquid aspiration (µL/min)
            dispense_speed: Speed for dispensing (µL/min)
            air_bubble_volume: Air volume per cycle (µL)
            wait_between_cycles: Wait time between cycles for bubble mixing (seconds)
            wait_after: Final wait time after homogenization (seconds)
            verbose: Show status messages (uses config.verbose if None)
            
        Raises:
            ValueError: If total volume exceeds syringe capacity
        
        Example:
            >>> workflow.homogenize_by_air_mixing(
            ...     vial=22,
            ...     volume_aspirate=300,
            ...     air_bubble_volume=50,
            ...     num_cycles=2,
            ...     wait_between_cycles=8.0,
            ...     verbose=True
            ... )
            [SI] Loading vial 22 for air bubble homogenization...
            [SI] Cycle 1/2: Aspirating 50 µL air...
            [SI] Cycle 1/2: Aspirating 300 µL liquid at 1500 µL/min...
            [SI] Cycle 1/2: Waiting 8.0 seconds for bubble mixing...
            [SI] Cycle 1/2: Dispensing mixture at 1500 µL/min...
            [SI] Cycle 2/2: Aspirating 50 µL air...
            [SI] Cycle 2/2: Aspirating 300 µL liquid at 1500 µL/min...
            [SI] Cycle 2/2: Waiting 8.0 seconds for bubble mixing...
            [SI] Cycle 2/2: Dispensing mixture at 1500 µL/min...
            [SI] Air bubble homogenization of vial 22 completed
        """
        # Use config defaults
        verbose = self._get_verbose(verbose)
        volume_aspirate = volume_aspirate or self.config.default_homogenization_volume
        num_cycles = num_cycles or self.config.homogenization_air_cycles
        aspirate_speed = aspirate_speed or self.config.speed_slow
        dispense_speed = dispense_speed or self.config.speed_slow
        air_bubble_volume = air_bubble_volume or 50
        
        # Validate parameters
        if volume_aspirate + air_bubble_volume > self.syringe_size:
            raise ValueError(f"Total volume ({volume_aspirate + air_bubble_volume} µL) exceeds syringe capacity")
        
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial number {vial} outside valid range (1-50)")
        
        if verbose:
            self._print_status(f"Loading vial {vial} for air bubble homogenization...")
        
        self.load_to_replenishment(vial)
        
        self.syringe.valve_out()
        self.valve.position(self.config.transfer_port)
        
        # Execute mixing cycles with air bubbles
        for cycle in range(num_cycles):
            if verbose:
                self._print_status(f"Cycle {cycle+1}/{num_cycles}: Aspirating {air_bubble_volume} µL air...")
            
            # Aspirate air bubble first
            self.valve.position(self.config.air_port)
            self.syringe.set_speed_uL_min(self.config.speed_air)
            self.syringe.aspirate(air_bubble_volume)
            
            if verbose:
                self._print_status(f"Cycle {cycle+1}/{num_cycles}: Aspirating {volume_aspirate} µL liquid at {aspirate_speed} µL/min...")
            
            # Aspirate liquid sample
            self.valve.position(self.config.transfer_port)
            self.syringe.set_speed_uL_min(aspirate_speed)
            self.syringe.aspirate(volume_aspirate)
            
            # Wait for bubble mixing action
            if wait_between_cycles > 0:
                if verbose:
                    self._print_status(f"Cycle {cycle+1}/{num_cycles}: Waiting {wait_between_cycles} seconds for bubble mixing...")
                time.sleep(wait_between_cycles)
            
            if verbose:
                self._print_status(f"Cycle {cycle+1}/{num_cycles}: Dispensing mixture at {dispense_speed} µL/min...")
            
            # Dispense air-liquid mixture
            self.syringe.set_speed_uL_min(dispense_speed)
            self.syringe.dispense()
        
        # Final wait period if specified
        if wait_after > 0:
            if verbose:
                self._print_status(f"Waiting {wait_after} seconds after homogenization...")
            time.sleep(wait_after)
        
        self.unload_from_replenishment()
        
        if verbose:
            self._print_status(f"Air bubble homogenization of vial {vial} completed")
            self._complete_status_line(verbose)

    # ==========================================================================
    # CLEANING AND MAINTENANCE METHODS  
    # ==========================================================================

    def clean_transfer_line_after_homogenization(self,
                                                waste_vial: Optional[int] = None,
                                                flush_volume: Optional[int] = 70,
                                                air_bubble: Optional[int] = 50,
                                                cleaning_solution_volume: Optional[int] = None,
                                                cleaning_solution_vial: Optional[int] = None,
                                                verbose: Optional[bool] = None) -> None:
        """
        Clean transfer line after homogenization operations.
        
        This comprehensive cleaning procedure removes sample residues from
        the transfer line using optional chemical cleaning followed by
        thorough rinsing and air bubble creation for system protection.
        
        Args:
            waste_vial: Waste vial number (uses config default if None)
            flush_volume: Volume to flush from syringe (µL)
            air_bubble: Air bubble volume for holding coil protection (µL)
            cleaning_solution_volume: Volume of cleaning solution (µL), None to skip
            cleaning_solution_vial: Vial with cleaning solution (uses config default if None)
            verbose: Show status messages (uses config.verbose if None)
        
        Example:
            >>> workflow.clean_transfer_line_after_homogenization(
            ...     cleaning_solution_volume=350,
            ...     verbose=True
            ... )
            [SI] Aspirating air bubble before cleaning...
            [SI] Loading cleaning solution vial 47...
            [SI] Cleaning with 350 µL solution...
            [SI] Waiting 3.0 seconds for cleaning reaction...
            [SI] Flushing 70 µL to waste...
            [SI] Creating 50 µL air bubble in holding coil...
            [SI] Transfer line cleaning completed
        """
        # Use config defaults
        verbose = self._get_verbose(verbose)
        waste_vial = waste_vial or self.config.waste_vial
        cleaning_solution_volume = cleaning_solution_volume or self.config.default_cleaning_solution_volume
        cleaning_solution_vial = cleaning_solution_vial or self.config.cleaning_solution_vial
        
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        # Chemical cleaning if requested
        if cleaning_solution_volume is not None and cleaning_solution_volume > 0:
            if verbose:
                self._print_status("Aspirating air bubble before cleaning...")
            
            self.syringe.aspirate(20)
            
            if verbose:
                self._print_status(f"Loading cleaning solution vial {cleaning_solution_vial}...")
            
            self.load_to_replenishment(cleaning_solution_vial)
            
            if verbose:
                self._print_status(f"Cleaning with {cleaning_solution_volume} µL solution...")
            
            self.syringe.aspirate(cleaning_solution_volume)
            
            if verbose:
                self._print_status(f"Waiting {self.config.wait_cleaning_reaction} seconds for cleaning reaction...")
            
            time.sleep(self.config.wait_cleaning_reaction)
            self.syringe.dispense()
            
            self.unload_from_replenishment()
        
        # Flush residues to waste
        if verbose:
            self._print_status(f"Flushing {flush_volume} µL to waste...")
        
        self.syringe.valve_in()
        self.syringe.aspirate(flush_volume)
        self.syringe.valve_out()
        
        self.load_to_replenishment(waste_vial)
        self.syringe.dispense()
        self.unload_from_replenishment()
        
        # Create protective air bubble in holding coil
        if verbose:
            self._print_status(f"Creating {air_bubble} µL air bubble in holding coil...")
        
        self.syringe.aspirate(air_bubble)
        self.syringe.valve_in()
        self.syringe.dispense()
        self.syringe.valve_out()
        
        if verbose:
            self._print_status("Transfer line cleaning completed")
            self._complete_status_line(verbose)

    def flush_transfer_line_to_waste(self,
                                    transfer_line_volume: Optional[int] = None,
                                    air_push: int = 30,
                                    verbose: Optional[bool] = None) -> None:
        """
        Quick flush of transfer line contents to waste.
        
        Simple utility method to empty the transfer line without chemical
        cleaning. Useful for quick changeovers between incompatible solvents
        or when removing samples before system shutdown.
        
        Args:
            transfer_line_volume: Volume to flush (µL, uses config default if None)
            air_push: Initial air volume for pushing (µL)
            verbose: Show status messages (uses config.verbose if None)
        
        Example:
            >>> workflow.flush_transfer_line_to_waste(verbose=True)
            [SI] Flushing transfer line to waste (600 µL)...
            [SI] Transfer line flushed to waste
        """
        verbose = self._get_verbose(verbose)
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        
        # Ensure no vial is loaded
        self.unload_from_replenishment()
        
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        if verbose:
            self._print_status(f"Flushing transfer line to waste ({transfer_line_volume} µL)...")
        
        # Create small air bubble for pushing
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(air_push)
        
        # Move bubble to holding coil
        self.syringe.valve_in()
        self.syringe.dispense(air_push // 2)
        self.syringe.valve_out()
        
        # Aspirate from transfer line
        self.valve.position(self.config.transfer_port)
        self.syringe.aspirate(transfer_line_volume)
        
        # Dispense to waste port
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()
        
        if verbose:
            self._print_status("Transfer line flushed to waste")
            self._complete_status_line(verbose)

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def _split_volume_to_cycles(self, total_volume: int, max_volume: int) -> List[int]:
        """
        Split large volume into multiple syringe cycles.
        
        When a requested volume exceeds the syringe capacity, this method
        splits it into multiple cycles of maximum volume, with a final
        cycle for any remainder.
        
        Args:
            total_volume: Total volume to be dispensed (µL)
            max_volume: Maximum volume per cycle (typically syringe capacity)
            
        Returns:
            List of volumes for each cycle
            
        Example:
            >>> workflow._split_volume_to_cycles(1250, 500)
            [500, 500, 250]
        """
        if total_volume <= max_volume:
            return [total_volume]
        
        full_cycles = total_volume // max_volume
        remainder = total_volume % max_volume
        
        cycles = [max_volume] * full_cycles
        if remainder > 0:
            cycles.append(remainder)
        
        return cycles

    def _get_verbose(self, verbose: Optional[bool]) -> bool:
        """
        Get the effective verbose setting.
        
        Args:
            verbose: Explicit verbose setting, or None to use config default
            
        Returns:
            Boolean verbose setting to use
        """
        return self.config.verbose if verbose is None else verbose

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and configuration.
        
        Returns:
            Dictionary containing system configuration and status information
            
        Example:
            >>> status = workflow.get_system_status()
            >>> print(f"Syringe size: {status['syringe_size']} µL")
            >>> print(f"Current speed setting: {status['config']['speed_normal']} µL/min")
            >>> print(f"Interactive terminal: {status['interactive_terminal']}")
        """
        return {
            'syringe_size': self.syringe_size,
            'interactive_terminal': self._interactive_terminal,
            'config': self.config.__dict__.copy(),
            'port_assignments': {
                'waste': self.config.waste_port,
                'air': self.config.air_port,
                'di': self.config.di_port,
                'transfer': self.config.transfer_port,
                'meoh': self.config.meoh_port,
                'naoh': self.config.naoh_port,
                'buffer': self.config.buffer_port,
                'sample': self.config.sample_port
            },
            'vial_assignments': {
                'wash': self.config.wash_vial,
                'dry': self.config.dry_vial,
                'waste': self.config.waste_vial,
                'cleaning_solution': self.config.cleaning_solution_vial
            }
        }

    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Example:
            >>> workflow.update_config(
            ...     speed_normal=1800,
            ...     verbose=False,
            ...     homogenization_liquid_cycles=3
            ... )
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")