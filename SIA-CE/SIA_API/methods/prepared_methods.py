"""
Updated PreparedSIAMethods class with verbose support.
Shows how to modify existing methods to include status output.
"""

import time
from typing import Optional, Dict, Any, List, Tuple
from ..devices.syringe_controller import SyringeController
from ..devices.valve_selector import ValveSelector
from .config import SIAConfig, DEFAULT_CONFIG


class PreparedSIAMethods:
    """
    High-level SIA workflows with real-time status feedback.
    """
    
    def __init__(self, 
                 chemstation_controller, 
                 syringe_device: SyringeController, 
                 valve_device: ValveSelector, 
                 config: Optional[SIAConfig] = None):
        """
        Initialize SIA workflow system with configuration.
        
        Args:
            chemstation_controller: ChemStation API controller instance
            syringe_device: Initialized SyringeController instance
            valve_device: Initialized ValveSelector instance
            config: SIAConfig instance (uses DEFAULT_CONFIG if None)
        """
        self.chemstation = chemstation_controller
        self.config = config or DEFAULT_CONFIG
        self.syringe = syringe_device
        self.valve = valve_device
        self.syringe_size = syringe_device.syringe_size

        # Validate required vials are present
        self.chemstation.validation.validate_vial_in_system(self.config.wash_vial)
        self.chemstation.validation.validate_vial_in_system(self.config.waste_vial)

    def load_to_replenishment(self, vial_number: int, verbose: Optional[bool] = None) -> None:
        """
        Load vial to replenishment position in CE carousel.
        
        Args:
            vial_number: Vial position number (1-50)
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        
        if verbose:
            print(f"\rLoading vial {vial_number} to replenishment position...                                                      ", end='', flush=True)
        
        self.chemstation.ce.load_vial_to_position(vial_number, "replenishment")
        
        if verbose:
            time.sleep(0.1)  # Brief pause for visual feedback

    def unload_from_replenishment(self, verbose: Optional[bool] = None) -> None:
        """
        Unload vial from replenishment position back to carousel.
        
        Args:
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        
        if verbose:
            print(f"\rUnloading vial from replenishment position...                                                                ", end='', flush=True)
        
        self.chemstation.ce.unload_vial_from_position()
        
        if verbose:
            time.sleep(0.1)

    def _flush_syringe_loop(self, verbose: Optional[bool] = None) -> None:
        """
        Flush and prime syringe holding loop.
        
        Args:
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        
        if verbose:
            print(f"\rFlushing syringe loop...                                                                                      ", end='', flush=True)
        
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

    def _create_separating_bubble(self, port: int, bubble_volume: int, verbose: Optional[bool] = None) -> None:
        """
        Create separating bubble at end of holding coil.
        
        Args:
            port: Port number to aspirate from
            bubble_volume: Volume of bubble in microliters
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        
        port_name = "air" if port == self.config.air_port else f"port {port}"
        if verbose:
            print(f"\rCreating {bubble_volume} µL {port_name} bubble in holding coil...                                           ", end='', flush=True)
        
        self.syringe.valve_out()
        self.valve.position(port)
        self.syringe.aspirate(bubble_volume)
        self.syringe.valve_up()
        self.syringe.dispense()
        self.syringe.valve_out()

    def clean_needle(self, volume_flush: float, wash_vial: Optional[int] = None, verbose: Optional[bool] = None):
        """
        Clean dispensing needle to prevent cross-contamination.
        
        Args:
            volume_flush: Volume for needle cleaning (µL)
            wash_vial: Vial number for needle washing
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        wash_vial = wash_vial or self.config.wash_vial
        
        if verbose:
            print(f"\rCleaning needle with {volume_flush} µL in vial {wash_vial}...                                               ", end='', flush=True)
        
        self.load_to_replenishment(wash_vial, verbose=False)
        time.sleep(2)
        self.syringe.dispense(volume_flush/2)

        self.unload_from_replenishment(verbose=False)
        time.sleep(1)
        self.syringe.dispense(volume_flush/2)

    def system_initialization_and_cleaning(self, 
                                          waste_vial: Optional[int] = None, 
                                          bubble: int = 20,
                                          verbose: Optional[bool] = None):
        """
        Complete system initialization and cleaning procedure.
        
        Args:
            waste_vial: Waste vial number
            bubble: Separating bubble volume in µL
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        waste_vial = waste_vial or self.config.waste_vial
        
        # Load vial and set waste position
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.valve.position(self.config.waste_port)

        # Initialize and set speed
        if verbose:
            print(f"\rInitializing syringe pump...                                                                                  ", end='', flush=True)
        self.syringe.initialize()
        self.syringe.set_speed_uL_min(self.config.speed_fast)

        # Flush and prime loop
        self._flush_syringe_loop(verbose=verbose)
        time.sleep(1)

        # Create separating bubble
        self._create_separating_bubble(self.config.air_port, bubble, verbose=verbose)

        # Flush with methanol
        if verbose:
            print(f"\rFlushing system with methanol (250 µL)...                                                                    ", end='', flush=True)
        time.sleep(1)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(20)
        self.valve.position(self.config.meoh_port)
        self.syringe.aspirate(250)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate()
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Flush and prime DI loop
        if verbose:
            print(f"\rFlushing with DI water...                                                                                     ", end='', flush=True)
        time.sleep(1)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(50)
        self.valve.position(self.config.di_port)
        self.syringe.aspirate()
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Flush transfer line
        if verbose:
            print(f"\rFlushing transfer line...                                                                                     ", end='', flush=True)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(500)
        self.valve.position(self.config.di_port)
        self.syringe.aspirate(100)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            print(f"\rSystem initialization completed successfully!                                                                ", end='', flush=True)

    def prepare_continuous_flow(self, 
                               solvent_port: int, 
                               waste_vial: Optional[int] = None,
                               bubble_volume: int = 10,
                               solvent_holding_coil_volume: int = 10,
                               transfer_coil_flush: int = 500,
                               holding_coil_flush: Optional[int] = None,
                               speed: Optional[int] = None,
                               verbose: Optional[bool] = None):
        """
        Prepare system for continuous flow filling operations.
        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number
            bubble_volume: Air bubble volume in µL
            solvent_holding_coil_volume: Solvent volume at end of holding coil
            transfer_coil_flush: Volume for transfer coil flushing
            holding_coil_flush: Volume for holding coil flushing
            speed: Flow rate in µL/min
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        waste_vial = waste_vial or self.config.waste_vial
        holding_coil_flush = holding_coil_flush or self.config.default_holding_coil_volume
        speed = speed or self.config.speed_slow
        
        
        # Load vial and set speed
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Flush holding coil
        if verbose:
            print(f"\rFlushing holding coil with {transfer_coil_flush} µL solvent...                                               ", end='', flush=True)
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(transfer_coil_flush)
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Create separating bubbles
        self._create_separating_bubble(self.config.air_port, bubble_volume, verbose=verbose)
        self._create_separating_bubble(solvent_port, solvent_holding_coil_volume, verbose=verbose)

        # Fill transfer line with solvent
        if verbose:
            print(f"\rFilling transfer line with {holding_coil_flush} µL solvent...                                               ", end='', flush=True)
        self.valve.position(solvent_port)
        self.syringe.aspirate(holding_coil_flush)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            print(f"\rSystem ready for continuous flow operations                                                                  ", end='', flush=True)

    def continuous_fill(self, 
                       vial: int, 
                       volume: int, 
                       solvent_port: int,
                       flush_needle: Optional[int] = None,
                       wash_vial: Optional[int] = None,
                       speed: Optional[int] = None,
                       verbose: Optional[bool] = None):
        """
        Execute continuous flow filling operation.
        
        Args:
            vial: Target vial number
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent
            flush_needle: Optional needle flush volume
            wash_vial: Vial for needle washing
            speed: Flow rate in µL/min
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        wash_vial = wash_vial or self.config.wash_vial
        speed = speed or self.config.speed_normal

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size)
        
        if verbose:
            print(f"\rContinuous fill: Vial {vial}, Volume {volume} µL, Port {solvent_port}                                       ", end='', flush=True)
        
        # Load vial and set speed
        self.load_to_replenishment(vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        for i, cycle_vol in enumerate(cycle_volumes):
            if verbose:
                print(f"\rCycle {i+1}/{len(cycle_volumes)}: Aspirating {cycle_vol} µL from port {solvent_port}...                    ", end='', flush=True)
            
            if i != len(cycle_volumes) - 1:
                # Regular cycles
                self.valve.position(solvent_port)
                self.syringe.aspirate(cycle_vol)
                
                if verbose:
                    print(f"\rCycle {i+1}/{len(cycle_volumes)}: Dispensing {cycle_vol} µL to vial {vial}...                              ", end='', flush=True)
                
                self.valve.position(self.config.transfer_port)
                self.syringe.dispense(cycle_vol)
            else:
                # Last cycle with optional needle flush
                if flush_needle is not None:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    
                    if verbose:
                        print(f"\rCycle {i+1}/{len(cycle_volumes)}: Dispensing {cycle_vol - flush_needle} µL, keeping {flush_needle} µL for flush...", end='', flush=True)
                    
                    self.valve.position(self.config.transfer_port)
                    self.syringe.dispense(cycle_vol - flush_needle)
                    
                    self.clean_needle(flush_needle, wash_vial, verbose=verbose)
                else:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    
                    if verbose:
                        print(f"\rCycle {i+1}/{len(cycle_volumes)}: Dispensing final {cycle_vol} µL...                                       ", end='', flush=True)
                    
                    self.valve.position(self.config.transfer_port)
                    self.syringe.dispense(cycle_vol)

        self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            print(f"\rContinuous fill of vial {vial} completed ({volume} µL)                                                       ", end='', flush=True)

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
                  verbose: Optional[bool] = None):
        """
        Execute batch flow (discontinuous) filling operation.
        
        Args:
            vial: Target vial number
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent
            transfer_line_volume: Volume of transfer line
            bubble_volume: Air bubble volume
            flush_needle: Optional needle flush volume
            speed: Flow rate in µL/min
            unload: Whether to unload vial after filling
            wait: Optional wait time after dispensing
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_normal

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size - bubble_volume)
        
        if verbose:
            print(f"\rBatch fill: Vial {vial}, Volume {volume} µL, Port {solvent_port}                                            ", end='', flush=True)
        
        # Load vial and set speed
        self.load_to_replenishment(vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Aspirate air bubble first
        if verbose:
            print(f"\rAspirating {bubble_volume} µL air bubble...                                                                  ", end='', flush=True)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(bubble_volume)

        # Fill cycles with solvent
        for i, cycle_vol in enumerate(cycle_volumes):
            if verbose:
                print(f"\rCycle {i+1}/{len(cycle_volumes)}: Aspirating {cycle_vol} µL from port {solvent_port}...                    ", end='', flush=True)
            
            self.valve.position(solvent_port)
            self.syringe.aspirate(cycle_vol)
            
            if verbose:
                print(f"\rCycle {i+1}/{len(cycle_volumes)}: Transferring to line...                                                  ", end='', flush=True)
            
            self.valve.position(self.config.transfer_port)
            self.syringe.dispense(cycle_vol)

        if verbose:
            print(f"\rDispensingair bubble...                                                                                      ", end='', flush=True)
        self.syringe.dispense()  # Dispense air bubble
        
        # Push with air at high speed
        if verbose:
            print(f"\rPushing with {transfer_line_volume} µL air at high speed...                                                  ", end='', flush=True)
        
        self.syringe.set_speed_uL_min(self.config.speed_air)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_line_volume)
        self.valve.position(self.config.transfer_port)
        self.syringe.set_speed_uL_min(speed)

        if flush_needle is None:
            if verbose:
                print(f"\rDispensing to vial {vial}...                                                                                 ", end='', flush=True)
            self.syringe.dispense()
            if wait:
                if verbose:
                    print(f"\rWaiting {wait} seconds...                                                                                    ", end='', flush=True)
                time.sleep(wait)
        else:
            if verbose:
                print(f"\rDispensing {transfer_line_volume - flush_needle} µL, keeping {flush_needle} µL for flush...                 ", end='', flush=True)
            self.syringe.dispense(transfer_line_volume - flush_needle)
            if wait:
                time.sleep(wait)
            self.clean_needle(flush_needle, verbose=verbose)

        if unload:
            self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            print(f"\rBatch fill of vial {vial} completed ({volume} µL)                                                            ", end='', flush=True)

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
                                    verbose: Optional[bool] = None):
        """
        Execute batch filling with multiple solvents from different ports.
        
        Args:
            vial: Target vial number
            solvent_ports: List of port numbers for different solvents
            volumes: List of volumes corresponding to each port
            air_push_volume: Air bubble volume between solvents
            transfer_line_volume: Volume for final air push
            speed: Default flow rate for liquid handling
            solvent_speeds: Optional list of speeds for each solvent
            air_speed: Flow rate for air aspiration
            flush_needle: Optional needle flush volume
            wash_vial: Vial for needle washing
            unload: Whether to unload vial after filling
            wait: Optional wait time after dispensing
            verbose: Show status messages
        """
        verbose = self.config.verbose if verbose is None else verbose
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_normal
        air_speed = air_speed or self.config.speed_air
        wash_vial = wash_vial or self.config.wash_vial
        
        # Validate input parameters
        if len(solvent_ports) != len(volumes):
            raise ValueError("Number of solvent ports and volumes must match")
        
        if not solvent_ports or not volumes:
            raise ValueError("At least one solvent port and volume must be specified")
        
        if solvent_speeds is not None:
            if len(solvent_speeds) != len(solvent_ports):
                raise ValueError("Number of solvent speeds must match number of solvent ports")
        else:
            solvent_speeds = [speed] * len(solvent_ports)
        
        # Validate individual volumes
        max_single_volume = max(volumes) + air_push_volume
        if max_single_volume > self.syringe_size:
            raise ValueError(f"Largest single volume ({max_single_volume} µL) exceeds syringe capacity")
        
        if verbose:
            total_volume = sum(volumes)
            print(f"\rMulti-solvent batch fill: Vial {vial}, Total volume {total_volume} µL from {len(solvent_ports)} ports      ", end='', flush=True)
        
        # Load vial
        self.load_to_replenishment(vial, verbose=verbose)
        
        # Sequential processing of solvents
        for idx, (port, volume, solvent_speed) in enumerate(zip(solvent_ports, volumes, solvent_speeds)):
            if verbose:
                print(f"\rSolvent {idx+1}/{len(solvent_ports)}: Aspirating {air_push_volume} µL air bubble...                        ", end='', flush=True)
            
            # Set speed for air aspiration
            self.syringe.set_speed_uL_min(air_speed)
            
            # Aspirate air bubble separator
            self.valve.position(self.config.air_port)
            self.syringe.aspirate(air_push_volume)
            
            if verbose:
                print(f"\rSolvent {idx+1}/{len(solvent_ports)}: Aspirating {volume} µL from port {port} at {solvent_speed} µL/min... ", end='', flush=True)
            
            # Set speed for this specific solvent
            self.syringe.set_speed_uL_min(solvent_speed)
            
            # Aspirate solvent from specified port
            self.valve.position(port)
            self.syringe.aspirate(volume)
            
            if verbose:
                print(f"\rSolvent {idx+1}/{len(solvent_ports)}: Transferring to line...                                               ", end='', flush=True)
            
            # Transfer to transfer line immediately
            self.valve.position(self.config.transfer_port)
            self.syringe.dispense()
        
        # Final air push to vial
        if verbose:
            print(f"\rFinal air push: {transfer_line_volume} µL at {air_speed} µL/min...                                          ", end='', flush=True)
        
        self.syringe.set_speed_uL_min(air_speed)
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_line_volume)
        
        # Change speed back to normal for dispensing
        self.syringe.set_speed_uL_min(speed)
        self.valve.position(self.config.transfer_port)
        
        # Final dispensing with optional needle cleaning
        if flush_needle is None:
            if verbose:
                print(f"\rDispensing mixture to vial {vial}...                                                                         ", end='', flush=True)
            self.syringe.dispense()
            if wait:
                time.sleep(wait)
        else:
            if verbose:
                print(f"\rDispensing mixture, keeping {flush_needle} µL for flush...                                                   ", end='', flush=True)
            self.syringe.dispense(transfer_line_volume - flush_needle)
            if wait:
                time.sleep(wait)
            self.clean_needle(flush_needle, wash_vial, verbose=verbose)
        
        # Unload vial if requested
        if unload:
            self.unload_from_replenishment(verbose=verbose)
        
        if verbose:
            total_volume = sum(volumes)
            print(f"\rMulti-solvent batch fill completed: {total_volume} µL total in vial {vial}                                   ", end='', flush=True)

    def prepare_batch_flow(self, 
                        solvent_port: int, 
                        waste_vial: Optional[int] = None,
                        bubble_volume: int = 10,
                        transfer_coil_volume: Optional[int] = None,
                        coil_flush: int = 150,
                        speed: Optional[int] = None,
                        verbose: Optional[bool] = None):
        """
        Prepare system for batch flow (discontinuous) filling operations.
        
        Sets up system for air-driven dispensing where transfer line is
        filled with air. Suitable for single fills or changing solvents
        between operations.
        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number
            bubble_volume: Air bubble volume in µL
            transfer_coil_volume: Transfer line volume in µL
            coil_flush: Volume for coil flushing in µL
            speed: Flow rate in µL/min
            verbose: Show status messages
            
        Example:
            >>> workflow.prepare_batch_flow(
            ...     solvent_port=3,  # DI water port
            ...     transfer_coil_volume=600
            ... )
        """
        verbose = self.config.verbose if verbose is None else verbose
        waste_vial = waste_vial or self.config.waste_vial
        transfer_coil_volume = transfer_coil_volume or self.config.default_transfer_line_volume
        speed = speed or self.config.speed_slow
        
        if verbose:
            print(f"\r{'='*80}", flush=True)
            print(f"\rPREPARING BATCH FLOW (Solvent Port: {solvent_port})", flush=True)
            print(f"\r{'='*80}", flush=True)
        
        # Load vial and set speed
        self.load_to_replenishment(waste_vial, verbose=verbose)
        self.syringe.set_speed_uL_min(speed)

        # Flush transfer loop
        if verbose:
            print(f"\rFlushing transfer loop with {coil_flush} µL...                                                               ", end='', flush=True)
        
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()

        # Create separating bubble
        self._create_separating_bubble(self.config.air_port, bubble_volume, verbose=verbose)

        # Fill transfer line with air
        if verbose:
            print(f"\rFilling transfer line with {transfer_coil_volume} µL air...                                                 ", end='', flush=True)
        
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(transfer_coil_volume)
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(self.config.transfer_port)
        self.syringe.dispense()
        
        if verbose:
            print(f"\rSystem ready for batch flow operations                                                                        ", end='', flush=True)


    def _split_volume_to_cycles(self, total_volume: int, max_volume: int) -> List[int]:
        """Split large volume into multiple syringe cycles."""
        return [max_volume] * (total_volume // max_volume) + \
               ([total_volume % max_volume] if total_volume % max_volume else [])


    def prepare_for_liquid_homogenization(self, 
                                        waste_vial: Optional[int] = None,
                                        transfer_line_volume: Optional[int] = None,
                                        meoh_flush_volume: Optional[int] = 20,
                                        air_bubble: Optional[int] = None,
                                        verbose: Optional[bool] = None) -> None:
        """
        Prepare system for liquid-based homogenization.
        
        Flushes transfer line and creates protective air bubble in holding coil.
        Used before liquid homogenization to ensure clean system.
        
        Args:
            waste_vial: Waste vial number (uses config default if None)
            transfer_line_volume: Volume to flush from transfer line (µL)
            meoh_flush_volume: Optional methanol flush volume (µL), None to skip
            air_bubble: Air bubble volume in holding coil (µL)
            verbose: Show status messages (uses global setting if None)
        
        Example:
            >>> workflow.prepare_for_liquid_homogenization(verbose=True)
            Preparing for liquid homogenization...
            Flushing transfer line (600 µL)...
            Creating air bubble (30 µL)...
            System ready for liquid homogenization
        """
        # Use global verbose if not specified
        verbose = self.config.verbose if verbose is None else verbose
        
        # Use config defaults
        waste_vial = waste_vial or self.config.waste_vial
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        air_bubble = air_bubble or self.config.default_air_flush
        
        if verbose:
            print(f"\rPreparing for liquid homogenization...                                                                        ", end='', flush=True)
        
        self.load_to_replenishment(waste_vial)
        self.valve.position(self.config.transfer_port)
        
        self.syringe.valve_in()
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        if verbose:
            print(f"\rFlushing transfer line ({transfer_line_volume} µL)...                                                        ", end='', flush=True)
        
        self.syringe.aspirate(transfer_line_volume)
        self.syringe.valve_out()
        
        # Optional methanol flush
        if meoh_flush_volume is not None:
            if verbose:
                print(f"\rAdding methanol flush ({meoh_flush_volume} µL)...                                                        ", end='', flush=True)
            self.valve.position(self.config.meoh_port)
            self.syringe.aspirate(meoh_flush_volume)
            self.valve.position(self.config.transfer_port)
        
        self.syringe.dispense()
        
        self.unload_from_replenishment()
        
        # Create air bubble in holding coil
        if verbose:
            print(f"\rCreating air bubble ({air_bubble} µL) in holding coil...                                                     ", end='', flush=True)
        
        self.syringe.aspirate(air_bubble)
        self.syringe.valve_in()
        self.syringe.dispense()
        self.syringe.valve_out()
        
        if verbose:
            print(f"\rSystem ready for liquid homogenization                                                                        ", end='', flush=True)


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
        
        Mixes sample by repeatedly aspirating and dispensing the liquid.
        More gentle than air mixing, suitable for sensitive samples.
        
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
            verbose: Show status messages
        
        Example:
            >>> workflow.homogenize_by_liquid_mixing(
            ...     vial=15,
            ...     volume_aspirate=400,
            ...     num_cycles=3,
            ...     verbose=True
            ... )
            Loading vial 15 for liquid homogenization...
            Cycle 1/3: Aspirating 400 µL...
            Cycle 1/3: Dispensing...
            ...
        """
        # Use config defaults
        verbose = self.config.verbose if verbose is None else verbose
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
        
        if verbose:
            print(f"\rLoading vial {vial} for liquid homogenization...                                                              ", end='', flush=True)
        
        self.load_to_replenishment(vial)
        
        self.syringe.valve_out()
        self.valve.position(self.config.transfer_port)
        
        # Mixing cycles
        for cycle in range(num_cycles):
            if verbose:
                print(f"\rCycle {cycle+1}/{num_cycles}: Aspirating {volume_aspirate} µL at {aspirate_speed} µL/min...                ", end='', flush=True)
            
            self.syringe.set_speed_uL_min(aspirate_speed)
            self.syringe.aspirate(volume_aspirate)
            
            if wait_after_aspirate > 0:
                time.sleep(wait_after_aspirate)
            
            if verbose:
                print(f"\rCycle {cycle+1}/{num_cycles}: Dispensing at {dispense_speed} µL/min...                                      ", end='', flush=True)
            
            self.syringe.set_speed_uL_min(dispense_speed)
            self.syringe.dispense()
            
            if wait_after_dispense > 0:
                time.sleep(wait_after_dispense)
        
        # Air flush to clear needle
        if air_flush is not None and air_flush > 0:
            if verbose:
                print(f"\rFlushing needle with {air_flush} µL air...                                                                   ", end='', flush=True)
            
            self.syringe.valve_in()
            self.syringe.aspirate(air_flush)
            self.syringe.valve_out()
            self.syringe.dispense()
        
        self.unload_from_replenishment()
        
        # Clean transfer line if requested
        if clean_after:
            if verbose:
                print(f"\rCleaning transfer line after homogenization...                                                               ", end='', flush=True)
            self.clean_transfer_line_after_homogenization(
                cleaning_solution_volume=cleaning_solution_volume,
                verbose=verbose
            )
        
        if verbose:
            print(f"\rLiquid homogenization of vial {vial} completed                                                               ", end='', flush=True)


    def homogenize_by_air_mixing(self,
                                vial: int,
                                volume_aspirate: Optional[int] = None,
                                num_cycles: Optional[int] = None,
                                aspirate_speed: Optional[int] = None,
                                dispense_speed: Optional[int] = None,
                                air_bubble_volume: Optional[int] = None,
                                wait_between_cycles: float = 5.0,
                                wait_after: float = 0,
                                verbose: Optional[bool] = None) -> None:
        """
        Homogenize sample using air bubble mixing.
        
        Creates air bubbles in liquid for vigorous mixing.
        More aggressive than liquid mixing, good for viscous samples.
        
        Args:
            vial: Target vial number (1-50)
            volume_aspirate: Liquid volume to aspirate per cycle (µL)
            num_cycles: Number of mixing cycles
            aspirate_speed: Speed for liquid aspiration (µL/min)
            dispense_speed: Speed for dispensing (µL/min)
            air_bubble_volume: Air volume per cycle (µL)
            wait_between_cycles: Wait time between cycles (seconds)
            wait_after: Final wait time (seconds)
            verbose: Show status messages
        
        Example:
            >>> workflow.homogenize_by_air_mixing(
            ...     vial=22,
            ...     volume_aspirate=300,
            ...     air_bubble_volume=50,
            ...     num_cycles=2,
            ...     verbose=True
            ... )
        """
        # Use config defaults
        verbose = self.config.verbose if verbose is None else verbose
        volume_aspirate = volume_aspirate or self.config.default_homogenization_volume
        num_cycles = num_cycles or self.config.homogenization_air_cycles
        aspirate_speed = aspirate_speed or self.config.speed_slow
        dispense_speed = dispense_speed or self.config.speed_slow
        air_bubble_volume = air_bubble_volume or 50
        
        # Validate
        if volume_aspirate + air_bubble_volume > self.syringe_size:
            raise ValueError(f"Total volume ({volume_aspirate + air_bubble_volume} µL) exceeds syringe capacity")
        
        if verbose:
            print(f"\rLoading vial {vial} for air bubble homogenization...                                                         ", end='', flush=True)
        
        self.load_to_replenishment(vial)
        
        self.syringe.valve_out()
        self.valve.position(self.config.transfer_port)
        
        for cycle in range(num_cycles):
            if verbose:
                print(f"\rCycle {cycle+1}/{num_cycles}: Aspirating {air_bubble_volume} µL air...                                      ", end='', flush=True)
            
            # Aspirate air bubble
            self.valve.position(self.config.air_port)
            self.syringe.set_speed_uL_min(self.config.speed_air)
            self.syringe.aspirate(air_bubble_volume)
            
            if verbose:
                print(f"\rCycle {cycle+1}/{num_cycles}: Aspirating {volume_aspirate} µL liquid at {aspirate_speed} µL/min...         ", end='', flush=True)
            
            # Aspirate liquid
            self.valve.position(self.config.transfer_port)
            self.syringe.set_speed_uL_min(aspirate_speed)
            self.syringe.aspirate(volume_aspirate)
            
            if wait_between_cycles > 0:
                if verbose:
                    print(f"\rCycle {cycle+1}/{num_cycles}: Waiting {wait_between_cycles} seconds for bubble mixing...                    ", end='', flush=True)
                time.sleep(wait_between_cycles)
            
            if verbose:
                print(f"\rCycle {cycle+1}/{num_cycles}: Dispensing mixture at {dispense_speed} µL/min...                              ", end='', flush=True)
            
            # Dispense everything
            self.syringe.set_speed_uL_min(dispense_speed)
            self.syringe.dispense()
        
        if wait_after > 0:
            if verbose:
                print(f"\rWaiting {wait_after} seconds after homogenization...                                                         ", end='', flush=True)
            time.sleep(wait_after)
        
        self.unload_from_replenishment()
        
        if verbose:
            print(f"\rAir bubble homogenization of vial {vial} completed                                                           ", end='', flush=True)


    def clean_transfer_line_after_homogenization(self,
                                                waste_vial: Optional[int] = None,
                                                flush_volume: Optional[int] = 70,
                                                air_bubble: Optional[int] = 50,
                                                cleaning_solution_volume: Optional[int] = None,
                                                cleaning_solution_vial: Optional[int] = None,
                                                verbose: Optional[bool] = None) -> None:
        """
        Clean transfer line after homogenization operations.
        
        Performs cleaning with optional NaOH or other cleaning solution,
        followed by flushing to waste and air bubble creation.
        
        Args:
            waste_vial: Waste vial number
            flush_volume: Volume to flush from syringe (µL)
            air_bubble: Air bubble volume for holding coil (µL)
            cleaning_solution_volume: Volume of cleaning solution (µL), None to skip
            cleaning_solution_vial: Vial with cleaning solution (e.g., NaOH)
            verbose: Show status messages
        
        Example:
            >>> workflow.clean_transfer_line_after_homogenization(
            ...     cleaning_solution_volume=350,
            ...     verbose=True
            ... )
        """
        # Use config defaults
        verbose = self.config.verbose if verbose is None else verbose
        waste_vial = waste_vial or self.config.waste_vial
        cleaning_solution_volume = cleaning_solution_volume or self.config.default_cleaning_solution_volume
        cleaning_solution_vial = cleaning_solution_vial or self.config.cleaning_solution_vial
        
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        # Chemical cleaning if requested
        if cleaning_solution_volume is not None and cleaning_solution_volume > 0:
            if verbose:
                print(f"\rAspirating air bubble before cleaning...                                                                     ", end='', flush=True)
            
            self.syringe.aspirate(20)
            
            if verbose:
                print(f"\rLoading cleaning solution vial {cleaning_solution_vial}...                                                   ", end='', flush=True)
            
            self.load_to_replenishment(cleaning_solution_vial)
            
            if verbose:
                print(f"\rCleaning with {cleaning_solution_volume} µL solution...                                                      ", end='', flush=True)
            
            self.syringe.aspirate(cleaning_solution_volume)
            
            if verbose:
                print(f"\rWaiting {self.config.wait_cleaning_reaction} seconds for cleaning reaction...                                ", end='', flush=True)
            
            time.sleep(self.config.wait_cleaning_reaction)
            self.syringe.dispense()
            
            self.unload_from_replenishment()
        
        # Flush to waste
        if verbose:
            print(f"\rFlushing {flush_volume} µL to waste...                                                                       ", end='', flush=True)
        
        self.syringe.valve_in()
        self.syringe.aspirate(flush_volume)
        self.syringe.valve_out()
        
        self.load_to_replenishment(waste_vial)
        self.syringe.dispense()
        self.unload_from_replenishment()
        
        # Create air bubble in holding coil
        if verbose:
            print(f"\rCreating {air_bubble} µL air bubble in holding coil...                                                       ", end='', flush=True)
        
        self.syringe.aspirate(air_bubble)
        self.syringe.valve_in()
        self.syringe.dispense()
        self.syringe.valve_out()
        
        if verbose:
            print(f"\rTransfer line cleaning completed                                                                              ", end='', flush=True)


    def flush_transfer_line_to_waste(self,
                                    transfer_line_volume: Optional[int] = None,
                                    air_push: int = 30,
                                    verbose: Optional[bool] = None) -> None:
        """
        Quick flush of transfer line contents to waste.
        
        Simple method to empty transfer line without cleaning.
        Useful between incompatible solvents or samples.
        
        Args:
            transfer_line_volume: Volume to flush (µL)
            air_push: Initial air volume (µL)
            verbose: Show status messages
        
        Example:
            >>> workflow.flush_transfer_line_to_waste(verbose=True)
        """
        verbose = self.config.verbose if verbose is None else verbose
        transfer_line_volume = transfer_line_volume or self.config.default_transfer_line_volume
        
        self.unload_from_replenishment()  # Ensure no vial loaded
        
        self.syringe.set_speed_uL_min(self.config.speed_cleaning)
        
        if verbose:
            print(f"\rFlushing transfer line to waste ({transfer_line_volume} µL)...                                               ", end='', flush=True)
        
        # Create small air bubble first
        self.valve.position(self.config.air_port)
        self.syringe.aspirate(air_push)
        
        # Move bubble to holding coil
        self.syringe.valve_in()
        self.syringe.dispense(air_push // 2)
        self.syringe.valve_out()
        
        # Aspirate from transfer line
        self.valve.position(self.config.transfer_port)
        self.syringe.aspirate(transfer_line_volume)
        
        # Dispense to waste
        self.valve.position(self.config.waste_port)
        self.syringe.dispense()
        
        if verbose:
            print(f"\rTransfer line flushed to waste                                                                                ", end='', flush=True)
