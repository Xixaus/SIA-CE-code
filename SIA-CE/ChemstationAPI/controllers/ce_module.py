"""
CE Module - Agilent 7100 Capillary Electrophoresis instrument control.

This module provides comprehensive control of the CE instrument's physical components
including the 50-position carousel, three lift positions, capillary conditioning,
and pressure system operations.

The Agilent 7100 CE system components controlled by this module:
- Sample Carousel: 50 positions
- Lift Positions: Inlet (sample introduction), Outlet (waste/collection), Replenishment
- Pressure System: ±100 mbar for injection, up to 950 mbar for flushing
- Capillary System: Fused silica capillaries with temperature-controlled cassette

.. moduleauthor:: Richard Maršala
"""

import time
from tqdm import tqdm
from typing import Dict

from ..core.chemstation_communication import ChemstationCommunicator
from ..exceptions import *
from .validation import ValidationModule

MODULE = "CE1"  # ChemStation module identifier for CE instrument


class CEModule():
    """Capillary Electrophoresis instrument control for vial handling and operations.
    
    Provides methods for managing the CE instrument's sample handling system,
    including carousel vial management, lift position control, capillary conditioning,
    and pressure operations. This module interfaces directly with the CE1 module
    in ChemStation to control the physical instrument.
    
    Carousel System:
        - 50 numbered positions (1-48 for samples, 49 for replenishment parking)
        - Supports 100µL microvials, 1mL polypropylene, and 2mL glass vials
        - Automatic vial detection and position tracking
        - Random access to any vial position
    
    Lift Positions:
        - Inlet: For sample injection and buffer contact (positive electrode)
        - Outlet: For waste collection and grounding (negative electrode) 
        - Replenishment: For automatic buffer refreshing system
    
    Vial States:
        - "carousel": Vial is in tray position
        - "inlet": Vial loaded at inlet lift position
        - "outlet": Vial loaded at outlet lift position  
        - "replenishment": Vial loaded at replenishment lift position
        - "out_system": Vial not detected in system
    
    Attributes:
        comm: ChemStation communicator instance for sending commands.
        validation: Validation module for input checking and system state validation.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize CE module with communicator and validation.
        
        Args:
            communicator: ChemStation communication interface for command execution.
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
    
    def load_vial_to_position(self, vial: int, position: str = "replenishment") -> None:
        """Load a vial from carousel to specified lift position.
        
        Moves a vial from its current carousel position to one of the three lift positions.
        The system will automatically move the carousel to bring the vial to the front,
        then lift it to the specified position for CE operations.
        
        Args:
            vial: Carousel position number (1-48, or 49 for replenishment parking).
                 Position 49 is reserved for replenishment needle parking.
            position: Target lift position. Options:
                     - "inlet": Sample injection position (positive electrode contact)
                     - "outlet": Waste/collection position (negative electrode contact)  
                     - "replenishment": Buffer replenishment position
                     
        Raises:
            VialError: If vial is not present in the carousel or loading fails.
            ValueError: If invalid position is specified.
            SystemError: If carousel is not available for use (instrument busy).
            
        Examples:
            Load sample vial for analysis:
            >>> ce.load_vial_to_position(15, "inlet")
            
            Load waste vial for collection:
            >>> ce.load_vial_to_position(20, "outlet")
            
            Load buffer vial for replenishment:
            >>> ce.load_vial_to_position(49, "replenishment")
            
        Note:
            - Vial must be physically present in the carousel position
            - System checks vial presence before attempting to load
            - If vial is already in target position, no action is taken
            - Loading includes automatic stabilization wait time
        """
        
        # Map position names to ChemStation module commands
        position_commands = {
            "inlet": "INLT",           # Load to inlet lift position
            "outlet": "OUTL",          # Load to outlet lift position  
            "replenishment": "LRPL",   # Load to replenishment lift position
        }
        
        # Validate position parameter
        if position not in position_commands:
            raise ValueError(f"Invalid position: {position}. Allowed positions: {list(position_commands.keys())}")

        # Check current vial state
        start_position = self.get_vial_state(vial)
        
        # Verify vial is in system
        if start_position == "out_system":
            raise VialError(f"Vial {vial} is not present in the carousel")
        elif start_position == position:
            return  # Already in target position
        
        # Ensure carousel is available for use
        self.validation.validate_use_carousel()

        # Send load command to CE module
        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command} {vial}"')
        
        # Wait for loading completion with timeout
        for _ in range(10):
            if self.get_vial_state(vial) == position:
                time.sleep(1.5)  # Additional stabilization time
                return
            else:
                time.sleep(1)

        raise VialError(f"Failed to load vial {vial} to {position} position after 10 seconds")

    def unload_vial_from_position(self, position: str = "replenishment") -> None:
        """Return vial from lift position back to carousel.
        
        Lowers the vial from the specified lift position back to its original
        carousel position. The vial will be automatically returned to the same
        numbered position it was loaded from.
        
        Args:
            position: Lift position to unload from:
                     - "inlet": Return vial from inlet position
                     - "outlet": Return vial from outlet position
                     - "replenishment": Return vial from replenishment position
                     
        Raises:
            ValueError: If invalid position is specified.
            VialError: If no vial is present at the specified position.
            
        Examples:
            Return sample vial after analysis:
            >>> ce.unload_vial_from_position("inlet")
            
            Return waste vial after collection:
            >>> ce.unload_vial_from_position("outlet")
            
        Note:
            - System automatically detects which vial number to return
            - Includes stabilization wait time after unloading
            - Safe to call even if no vial is present (no error)
        """
        # Map position names to return commands
        position_commands = {
            "inlet": "RINL",       # Return from inlet
            "outlet": "ROUT",      # Return from outlet
            "replenishment": "RRPL", # Return from replenishment
        }
        
        if position not in position_commands:
            raise ValueError(f"Invalid position: {position}. Allowed positions: {list(position_commands.keys())}")
        
        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command}"')
        time.sleep(3)  # Wait for unloading completion

    def get_vial_state(self, vial: int) -> str:
        """Get current state/position of a vial in the CE system.
        
        Queries the CE instrument to determine where a specific vial is currently
        located within the system. This includes carousel positions and lift positions.
        
        Args:
            vial: Vial position number to check (1-49).
            
        Returns:
            Current vial state as string:
            - "carousel": Vial is in its carousel position (available for loading)
            - "inlet": Vial is loaded at inlet lift position 
            - "outlet": Vial is loaded at outlet lift position
            - "replenishment": Vial is loaded at replenishment lift position
            - "out_system": Vial is not detected anywhere in the system
            
        Raises:
            SystemError: If unable to query vial state from instrument.
            
        Examples:
            Check if sample is ready for analysis:
            >>> state = ce.get_vial_state(15)
            >>> if state == "inlet":
            ...     print("Sample is ready for injection")
            >>> elif state == "carousel":
            ...     print("Sample needs to be loaded to inlet")
            
            Monitor vial locations:
            >>> for vial_num in [10, 11, 12]:
            ...     state = ce.get_vial_state(vial_num)
            ...     print(f"Vial {vial_num}: {state}")
        """
        # Query vial state from CE module
        state_response = self.comm.send(f'response$ = SendModule$("{MODULE}", "TRAY:GETVIALSTATE? {vial}")')
        state_code = state_response[-1]  # Extract state code from response
        
        # Map numerical state codes to descriptive strings
        state_mapping = {
            "0": "carousel",      # In carousel position
            "1": "inlet",         # At inlet lift
            "2": "outlet",        # At outlet lift  
            "3": "replenishment", # At replenishment lift
            "4": "out_system"     # Not detected in system
        }
        
        return state_mapping.get(state_code, "unknown")

    def flush_capillary(self, time_flush: float, wait: bool = True) -> None:
        """Perform capillary conditioning flush with high pressure.
        
        Flushes the capillary with buffer from the inlet vial using the instrument's
        internal pressure system (~950 mbar). This is used for capillary conditioning,
        cleaning, and removing air bubbles between analyses.
        
        Args:
            time_flush: Flush duration in seconds. Typical values:
                       - 30-60s: Routine conditioning between analyses
                       - 120-300s: Deep cleaning or new capillary preparation
                       - 5-10s: Quick air bubble removal
            wait: If True, blocks execution until flush completes with progress display.
                 If False, starts flush and returns immediately.
                 
        Examples:
            Standard capillary conditioning:
            >>> ce.flush_capillary(60.0)  # 1 minute flush with progress bar
            
            Quick bubble removal:
            >>> ce.flush_capillary(10.0, wait=False)  # Start 10s flush, don't wait
            
        Note:
            - Requires buffer vial loaded at inlet position
            - Uses maximum internal pressure (~950 mbar)
            - Progress bar shown when wait=True
            - Flush time affects capillary conditioning quality
        """
        # Send flush command: time, pressure(-2=max), outlet pressure(-2=atmospheric)
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_flush},-2,-2"')

        # Show progress bar if waiting for completion
        if wait:
            for _ in tqdm(range(int(time_flush)), desc="Flushing capillary", unit="sec"):
                time.sleep(1)

    def apply_pressure_to_capillary(self, pressure: float, time_pressure: float, wait: bool = True) -> None:
        """Apply specific pressure to capillary for controlled operations.
        
        Applies precise pressure to the capillary inlet for sample injection,
        gentle conditioning, or vacuum operations. Unlike flush_capillary(),
        this method allows precise pressure control.
        
        Args:
            pressure: Pressure in mbar. Range: -100 to +100 mbar
                     - Positive: Pushes sample/buffer from inlet to outlet
                     - Negative: Creates vacuum, pulls from outlet to inlet
                     - Typical injection: 20-50 mbar for 1-10 seconds
            time_pressure: Duration of pressure application in seconds.
            wait: If True, blocks execution with progress display.
                 If False, starts pressure application and returns immediately.
                 
        Examples:
            Hydrodynamic sample injection:
            >>> ce.apply_pressure_to_capillary(50.0, 5.0)  # 50 mbar for 5 seconds
            
            Gentle capillary conditioning:
            >>> ce.apply_pressure_to_capillary(25.0, 30.0)  # 25 mbar for 30 seconds
            
            Vacuum conditioning:
            >>> ce.apply_pressure_to_capillary(-50.0, 10.0)  # -50 mbar vacuum
            
        Note:
            - Pressure range limited to ±100 mbar for safety
            - Injection pressure affects sample volume introduced
            - Negative pressure can be used for special applications
            - Requires appropriate vials at inlet/outlet positions
        """
        # Send pressure command: time, pressure, outlet pressure(-2=atmospheric)
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_pressure}, {pressure},-2,-2"')
        
        # Show progress bar if waiting for completion
        if wait:
            pressure_type = "vacuum" if pressure < 0 else "pressure"
            for _ in tqdm(range(int(time_pressure)), desc=f"Applying {pressure_type} ({pressure} mbar)", unit="sec"):
                time.sleep(1)