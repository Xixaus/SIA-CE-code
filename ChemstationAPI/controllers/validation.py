import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator, CommunicationConfig


class ValidationModule():
    """Sequence management for editing, loading, and execution.
    
    Provides methods for sequence editing, Excel file imports,
    sequence execution control, and file management.
    
    Sequences define the order and parameters for multiple analyses,
    including vial positions, methods, sample names, and data file names.
    
    Attributes:
        Inherits all attributes from ChemstationCommunicator and MethodsModule.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Sequence module.
        
        Args:
            config: Communication configuration for ChemStation connection.
        """
        self.comm = communicator

    def validate_sequence_name(self, sequence: str, dir_path: str = "_SEQPATH$") -> None:
        """Validate sequence existence in specified directory (case-insensitive).
        
        Args:
            sequence: Sequence name (without .S extension).
            dir_path: Path to sequence directory (default: ChemStation sequence path).
            
        Raises:
            ValidationError: If sequence doesn't exist in specified directory.
        """
        sequence_upper = (sequence + ".S").upper()

        if dir_path == "_SEQPATH$":
            dir_path = Path(self.comm.send('response$ = _SEQPATH$'))

        filenames_upper = [file.upper() for file in os.listdir(dir_path)]

        if sequence_upper in filenames_upper:
            return
        else:
            raise ValidationError(f"Sequence '{sequence}' not found in directory {dir_path}")
        
    def validate_method_name(self, method: str, dir_path: str = "_METHPATH$") -> None:
        """Validate that method exists in the specified directory (case-insensitive).
        
        Args:
            method: Method name (without .M extension).
            dir_path: Path to method directory (default: ChemStation method path).
            
        Raises:
            ValidationError: If method doesn't exist in the specified directory.
        """
        method_upper = (method + ".M").upper()

        if dir_path == "_METHPATH$":
            dir_path = Path(self.comm.send("response$ = _METHPATH$"))

        filenames_upper = [file.upper() for file in os.listdir(dir_path)]

        if method_upper in filenames_upper:
            return
        else:
            raise ValidationError(f"Method '{method}' not found in directory {dir_path}")

    def validate_vial_in_system(self, vial):

        state = self.comm.send(f'response$ = SendModule$("CE1", "TRAY:GETVIALSTATE? {vial}")')[-1]

        allowed_states = {"0", "1", "2", "3"}

        if state not in allowed_states:
            raise VialError(f"Vial {vial} is not available in the system")
        else:
            return

    def validate_method_run(self):
        """Validate that method is running.
        
        Raises:
            MethodError: If method is not running, indicating an error occurred.
        """
        state = self.comm.send("response$ = VAL$(_MethodOn)")

        if state == "1":
            return
        else:
            raise MethodError("Method is not running, an error occurred")

    def vial_in_position(self, position: str):
        """Check if a vial is in the specified position.
        
        Args:
            position: Position to check (e.g., "inlet", "outlet", "replenishment").
            
        Returns:
            bool: True if a vial is in the specified position, False otherwise.
        """

        state_mapping = {
            "1": "inlet", 
            "2": "outlet",
            "3": "replenishment",
        }

        vial = self.comm.send(f'response$ = SendModule$("CE1", "LIFTER:OCCUPIED? {state_mapping[position]}")')

        if vial != "0":
            return
        else:
            raise VialError("On position is not load vial")

    def validate_use_carousel(self):
        """
        Check if the CE carousel is available for use.
        Returns:
        bool: True if the carousel is available, False otherwise.
        """

        state = self.comm.send(f'response$ = ObjHdrText$(RCCE1Status[1], "RunState")')
        
        if state == "Idle" or state == "Run":
            return
        else:
            raise SystemError("Carousel cnast use at the time")
        
    def get_vialtable(self) -> Dict[int, bool]:
        """Get information about all vials in the CE carousel.
        
        Gets the state of all vials and returns a dictionary with position numbers
        and their presence in the carousel.
        
        Returns:
            Dictionary mapping position numbers to vial presence in carousel.
            
        Raises:
            VialError: If vial table cannot be read.
            
        Example:
            >>> ce = CEModule()
            >>> vials = ce.get_vialtable()
            >>> for pos, present in vials.items():
            ...     if present:
            ...         print(f"Vial at position {pos}")
        """
        vials_string = self.comm.send(f"macro {self.comm.config.get_macros_path()}; response$ = vialtable_export$()", 10)

        return {
                int(pos): int(state) in [0, 1, 2, 3]
                for pos, state in (
                    item.split(":") 
                    for item in vials_string.strip(",").split(", ")
                )
            }
    
    def list_vial_validation(self, vials) -> None:

        """Validate that all vials are present in the CE carousel.
        
        Args:
            vials: List of vial positions to check.
            
        Raises:
            VialError: If any vial is not present in the carousel.
            
        Example:
            >>> ce = CEModule()
            >>> ce.list_vial_validation([1, 2, 3])
        """
        vial_table = self.get_vialtable()

        available_vials = {pos for pos, present in vial_table.items() if present}
        missing_vials = set(vials) - available_vials
        if missing_vials:
            raise VialError(f"Vials not present in carousel: {sorted(missing_vials)}")