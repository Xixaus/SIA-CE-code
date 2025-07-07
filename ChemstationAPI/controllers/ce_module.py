"""
CE Module - Capillary Electrophoresis instrument control.

This module provides functionality for managing CE instrument vial positions,
loading/unloading vials to different positions (inlet, outlet, replenishment),
and monitoring carousel status.

.. moduleauthor:: Richard Maršala
"""

import time
from tqdm import tqdm
from typing import Dict

from ..core.chemstation_communication import ChemstationCommunicator
from ..exceptions import *
from .validation import ValidationModule

MODULE = "CE1"


class CEModule():
    """CE instrument management for vial handling and positions.
    
    Provides methods for loading and unloading vials to various positions
    in the CE instrument and monitoring carousel status.
    
    The CE module supports three main positions:
    - Inlet: For sample introduction
    - Outlet: For sample collection
    - Replenishment: For buffer replenishment
    
    Attributes:
        Inherits all attributes from ChemstationCommunicator.
    """
    def __init__(self, communicator: ChemstationCommunicator):
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
    
    def load_vial_to_position(self, vial: int, position: str = "replenishment") -> None:
        """Load a selected vial to the chosen position in CE carousel.
        
        Args:
            vial: Vial number to load.
            position: Target position for the vial (default: replenishment).

        Raises:
            VialError: If vial is not in system or failed to load to position.
            ValueError: If invalid position is specified.
            
        """
        # Position to command mapping
        position_commands = {
            "inlet": "INLT",
            "outlet": "OUTL",
            "replenishment": "LRPL",
        }
        
        # Validate position
        if position not in position_commands:
            raise ValueError(f"Invalid position: {position}. Allowed positions: {list(position_commands.keys())}")

        start_position = self.get_vial_state(vial)
        
        # Check that vial is in system
        if start_position == "out_system":
            raise VialError("Vial is not in the system")
        elif start_position == position:
            return
        
        self.validation.validate_use_carousel()

        # Send command to load vial
        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command} {vial}"')
        
        for _ in range(10):
            if self.get_vial_state(vial) == position:
                time.sleep(1.5)  # Additional wait for stabilization
                return
            else:
                time.sleep(1)

        raise VialError(f"Failed to load vial to position {position}")

    def unload_vial_from_position(self, position: str = "replenishment") -> None:
        """Unload vial from the specified position in CE carousel.
        
        Args:
            position: Position from which to unload the vial.
            
        """
        # Position to command mapping
        position_commands = {
            "inlet": "RINL",
            "outlet": "ROUT",
            "replenishment": "RRPL",
        }
        
        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command}"')
        time.sleep(3)

    def get_vial_state(self, vial: int) -> str:
        """Get the state of a vial in the CE carousel.
        
        Args:
            vial: Vial number to check.
            
        Returns:
            Vial state: "carousel", "inlet", "outlet", "replenishment", or "out_system".
            
        Raises:
            NameError: If validation error occurs.
            
        Example:
            >>> ce = CEModule()
            >>> state = ce.get_vial_state(15)
            >>> print(f"Vial 15 is in: {state}")
        """
        state = self.comm.send(f'response$ = SendModule$("{MODULE}", "TRAY:GETVIALSTATE? {vial}")')[-1]
        
        # State mapping
        state_mapping = {
            "0": "carousel",
            "1": "inlet", 
            "2": "outlet",
            "3": "replenishment",
            "4": "out_system"
        }
        
        return state_mapping[state]

    
    def flush_capillary(self, time_flush: float, wait: bool = True) -> None:
        """Perform capillary flush for specified time.
        
        Args:
            time_flush: Flush duration in seconds.
            wait: Whether to wait for completion.
            
        Example:
            >>> ce = CEModule()
            >>> ce.flush_capillary(30.0, wait=True)
        """
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_flush},-2,-2"')


        if wait:
            for _ in tqdm(range(int(time_flush)), desc="Flushing", unit="sec"):
                time.sleep(1)

    def apply_pressure_to_capillary(self, pressure: float, time_pressure: float, wait: bool = True) -> None:
        """Apply pressure to CE instrument for specified time.
        
        Args:
            pressure: Pressure in mbar (can be negative).
            time_pressure: Duration of pressure application in seconds.
            wait: Whether to wait for completion.
            
        Example:
            >>> ce = CEModule()
            >>> ce.apply_pressure_to_capillary(50.0, 10.0, wait=True)
        """
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_pressure}, {pressure},-2,-2"')
        
        if wait:
            for _ in tqdm(range(int(time_pressure)), desc="Applying pressure", unit="sec"):
                time.sleep(1)

    # def load_vial_at_height(self, vial, height):

    #     start_position = self.get_vial_state(vial)
        
    #     # Check that vial is in system
    #     if start_position == "out_system":
    #         raise VialError("Vial is not in the system")

    #     self.comm.send(f'WriteModule "{MODULE}", "REPL:EMTY {vial}"')

    #     self.comm.send('WriteModule "CE1", "COSY:STOP 42; ABRT"')