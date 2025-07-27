"""
Validation Module - Input validation and system state checking for ChemStation API.

This module provides comprehensive validation capabilities for ChemStation operations
including file existence checking, system state validation, vial presence verification,
and operational readiness assessment. All validation methods raise specific exceptions
when validation fails, enabling robust error handling in automated workflows.

Validation Categories:
- File System: Method and sequence file existence validation
- Vial Management: Carousel vial presence and position validation
- System State: Instrument readiness and operational state checking
- Method Execution: Analysis startup and execution validation
- Batch Operations: Multi-vial validation for sequence operations

.. moduleauthor:: Richard Maršala
"""

import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator, CommunicationConfig


class ValidationModule():
    """Comprehensive validation and system state checking for ChemStation operations.
    
    Provides validation methods for all aspects of ChemStation operation including
    file system validation, instrument state checking, vial management validation,
    and method execution verification. All validation methods follow consistent
    patterns and raise specific exceptions for different failure modes.
    
    Validation Philosophy:
        - Fail fast: Detect problems before they cause system errors
        - Specific exceptions: Different failure modes have different exception types
        - Case-insensitive: File and method name checking handles case variations
        - Comprehensive checking: Validate all prerequisites before operations
    
    File System Validation:
        - Method file existence in ChemStation directories
        - Sequence file existence and accessibility
        - Case-insensitive filename matching
        - Path validation and accessibility checking
    
    Instrument State Validation:
        - System readiness for operations
        - Carousel availability and operational state
        - Method execution state verification
        - Error condition detection and reporting
    
    Vial Management Validation:
        - Individual vial presence checking
        - Batch vial validation for sequences
        - Position occupancy verification
        - Carousel state comprehensive monitoring
    
    Attributes:
        comm: ChemStation communicator for validation queries.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize validation module with ChemStation communicator.
        
        Args:
            communicator: ChemStation communication interface for validation queries.
        """
        self.comm = communicator

    def validate_sequence_name(self, sequence: str, dir_path: str = "_SEQPATH$") -> None:
        """Validate that sequence file exists in specified directory.
        
        Performs case-insensitive validation of sequence file existence in the
        ChemStation sequence directory. This prevents errors when loading
        sequences with different case variations in filenames.
        
        Args:
            sequence: Sequence name (without .S extension).
                     Examples: "protein_analysis", "DAILY_QC", "Method_Development"
            dir_path: Path to sequence directory. Defaults to ChemStation
                     sequence directory (_SEQPATH$). Can specify custom path.
                     
        Raises:
            ValidationError: If sequence file doesn't exist in specified directory.
                           Error message includes actual directory path for debugging.
            FileNotFoundError: If sequence directory doesn't exist or isn't accessible.
            
        Examples:
            Validate before loading:
            >>> validation.validate_sequence_name("Protein_Analysis")
            >>> seq.load_sequence("Protein_Analysis")  # Safe to load
            
            Validate custom directory:
            >>> validation.validate_sequence_name("TestSeq", "C:\\Custom\\Sequences\\")
            
        Note:
            - Case-insensitive matching (protein_analysis matches Protein_Analysis.S)
            - Automatically appends .S extension for checking
            - Validates directory accessibility before file checking
            - Essential for preventing sequence loading failures
        """
        sequence_upper = (sequence + ".S").upper()

        # Get actual directory path if using ChemStation variable
        if dir_path == "_SEQPATH$":
            dir_path = Path(self.comm.send('response$ = _SEQPATH$'))

        # Check directory accessibility
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Sequence directory not found: {dir_path}")

        # Perform case-insensitive filename matching
        filenames_upper = [file.upper() for file in os.listdir(dir_path)]

        if sequence_upper in filenames_upper:
            return
        else:
            raise ValidationError(f"Sequence '{sequence}' not found in directory {dir_path}")
        
    def validate_method_name(self, method: str, dir_path: str = "_METHPATH$") -> None:
        """Validate that CE method file exists in specified directory.
        
        Performs case-insensitive validation of method file existence in the
        ChemStation method directory. This is essential before method loading
        operations to prevent ChemStation errors.
        
        Args:
            method: Method name (without .M extension).
                   Examples: "CE_Protein_Analysis", "mekc_drugs", "CZE_Inorganics"
            dir_path: Path to method directory. Defaults to ChemStation
                     method directory (_METHPATH$). Can specify custom path.
                     
        Raises:
            ValidationError: If method file doesn't exist in specified directory.
                           Error message includes actual directory path.
            FileNotFoundError: If method directory doesn't exist or isn't accessible.
            
        Examples:
            Validate before method operations:
            >>> validation.validate_method_name("CE_Protein_Analysis")
            >>> method.load("CE_Protein_Analysis")  # Safe to load
            
            Validate multiple methods:
            >>> method_list = ["Method1", "Method2", "Method3"]
            >>> for method_name in method_list:
            ...     validation.validate_method_name(method_name)
            
        Note:
            - Case-insensitive matching for cross-platform compatibility
            - Automatically appends .M extension for checking
            - Validates directory exists before file checking
            - Critical for preventing method loading failures
        """
        method_upper = (method + ".M").upper()

        # Get actual directory path if using ChemStation variable
        if dir_path == "_METHPATH$":
            dir_path = Path(self.comm.send("response$ = _METHPATH$"))

        # Check directory accessibility
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Method directory not found: {dir_path}")

        # Perform case-insensitive filename matching
        filenames_upper = [file.upper() for file in os.listdir(dir_path)]

        if method_upper in filenames_upper:
            return
        else:
            raise ValidationError(f"Method '{method}' not found in directory {dir_path}")

    def validate_vial_in_system(self, vial: int) -> None:
        """Validate that specified vial is present somewhere in the CE system.
        
        Checks that a vial is physically present in the CE system, either in
        the carousel or loaded at one of the lift positions. This prevents
        operations on missing vials that would cause instrument errors.
        
        Args:
            vial: Vial position number to check (1-49).
                 Position 49 is typically reserved for replenishment parking.
                 
        Raises:
            VialError: If vial is not detected anywhere in the system.
                      This indicates the vial is missing or not properly seated.
            SystemError: If unable to query vial state from instrument.
            
        Examples:
            Validate before loading:
            >>> validation.validate_vial_in_system(15)
            >>> ce.load_vial_to_position(15, "inlet")  # Safe to load
            
            Validate sample list:
            >>> sample_vials = [10, 11, 12, 15, 20]
            >>> for vial in sample_vials:
            ...     validation.validate_vial_in_system(vial)
            
        Note:
            - Checks all possible vial locations (carousel + lift positions)
            - State "4" (out_system) indicates vial not detected
            - Essential before any vial manipulation operations
            - Prevents instrument errors from missing vials
        """
        # Query vial state from CE instrument
        state = self.comm.send(f'response$ = SendModule$("CE1", "TRAY:GETVIALSTATE? {vial}")')[-1]

        # Valid states: 0=carousel, 1=inlet, 2=outlet, 3=replenishment
        allowed_states = {"0", "1", "2", "3"}

        if state not in allowed_states:
            raise VialError(f"Vial {vial} is not present in the system (state: {state})")

    def validate_method_run(self) -> None:
        """Validate that method execution started successfully.
        
        Checks the ChemStation _MethodOn system variable to verify that
        method execution actually started after a run command. This catches
        method startup failures that would otherwise go undetected.
        
        Raises:
            MethodError: If method is not running, indicating startup failure.
                        This could be due to instrument not ready, parameter errors,
                        or system conflicts.
            
        Examples:
            Validate after method start:
            >>> method.run("Sample001")
            >>> validation.validate_method_run()  # Confirm it started
            
            Use in automated workflows:
            >>> try:
            ...     method.execution_method_with_parameters(15, "CE_Method", "Sample")
            ...     validation.validate_method_run()
            ...     print("Method started successfully")
            ... except MethodError:
            ...     print("Method failed to start - check instrument status")
            
        Note:
            - Should be called shortly after method start commands
            - _MethodOn=1 indicates successful method execution
            - Essential for detecting silent method startup failures
            - Allows early detection of configuration problems
        """
        state = self.comm.send("response$ = VAL$(_MethodOn)")

        if state == "1":
            return
        else:
            raise MethodError("Method failed to start - check instrument status and parameters")

    def vial_in_position(self, position: str) -> None:
        """Validate that a vial is loaded at the specified lift position.
        
        Checks that a vial is actually present at the specified lift position
        before operations that require vial contact (injection, electrode contact).
        This prevents operations that would fail due to missing vials.
        
        Args:
            position: Lift position to check. Valid positions:
                     - "inlet": Sample injection position
                     - "outlet": Waste/collection position
                     - "replenishment": Buffer replenishment position
                     
        Raises:
            VialError: If no vial is loaded at the specified position.
            ValueError: If invalid position is specified.
            
        Examples:
            Check before injection:
            >>> validation.vial_in_position("inlet")
            >>> ce.apply_pressure_to_capillary(50.0, 5.0)  # Safe injection
            
            Verify setup before analysis:
            >>> validation.vial_in_position("inlet")   # Sample vial
            >>> validation.vial_in_position("outlet")  # Waste vial
            >>> method.run("Analysis")  # Safe to run
            
        Note:
            - Essential before operations requiring vial contact
            - Lift must have vial loaded, not just carousel presence
            - Different from vial_in_system which checks any location
            - Prevents electrode contact failures and injection errors
        """
        # Map position names to numeric codes for LIFTER query
        position_mapping = {
            "inlet": "1", 
            "outlet": "2",
            "replenishment": "3",
        }

        if position not in position_mapping:
            raise ValueError(f"Invalid position: {position}. Valid: {list(position_mapping.keys())}")

        # Query if lift position is occupied (returns vial number or 0)
        occupied_vial = self.comm.send(f'response$ = SendModule$("CE1", "LIFTER:OCCUPIED? {position_mapping[position]}")')

        if occupied_vial != "0":
            return
        else:
            raise VialError(f"No vial loaded at {position} position")

    def validate_use_carousel(self) -> None:
        """Validate that carousel is available for vial operations.
        
        Checks the CE instrument RC status to ensure the carousel system
        is available for vial loading/unloading operations. This prevents
        carousel operations during incompatible instrument states.
        
        Raises:
            SystemError: If carousel is not available for use.
                        This occurs during method execution, error states,
                        or maintenance modes that lock carousel access.
            
        Examples:
            Check before vial operations:
            >>> validation.validate_use_carousel()
            >>> ce.load_vial_to_position(15, "inlet")  # Safe to load
            
            Validate before batch operations:
            >>> validation.validate_use_carousel()
            >>> for vial in vial_list:
            ...     ce.load_vial_to_position(vial, "inlet")
            
        Note:
            - "Idle" state allows carousel operations
            - "Run" state may allow limited carousel access
            - Other states (Error, Maintenance) block carousel use
            - Essential before any automated vial handling
        """
        state = self.comm.send('response$ = ObjHdrText$(RCCE1Status[1], "RunState")')
        
        # States that allow carousel operations
        allowed_states = ["Idle", "Run"]
        
        if state in allowed_states:
            return
        else:
            raise SystemError(f"Carousel not available for use - instrument state: {state}")
        
    def get_vialtable(self) -> Dict[int, bool]:
        """Get comprehensive status of all carousel positions.
        
        Queries the CE instrument for the presence status of all 48 carousel
        positions and returns a dictionary mapping position numbers to presence
        status. This provides a complete overview of vial distribution.
        
        Returns:
            Dictionary mapping position numbers (1-48) to boolean presence status.
            True indicates vial is present (in carousel or at lift position),
            False indicates position is empty.
            
        Raises:
            VialError: If vial table cannot be read from instrument.
            SystemError: If communication with carousel system fails.
            
        Examples:
            Get complete vial overview:
            >>> vial_table = validation.get_vialtable()
            >>> occupied_positions = [pos for pos, present in vial_table.items() if present]
            >>> print(f"Vials present at positions: {occupied_positions}")
            
            Check specific positions:
            >>> vial_table = validation.get_vialtable()
            >>> for pos in [10, 11, 12]:
            ...     if vial_table[pos]:
            ...         print(f"Vial at position {pos} ready")
            
            Find empty positions:
            >>> vial_table = validation.get_vialtable()
            >>> empty_positions = [pos for pos, present in vial_table.items() if not present]
            
        Note:
            - Includes positions 1-48 (position 49 handled separately)
            - True means vial detected (any location in system)
            - Useful for sequence planning and vial management
            - Updates reflect real-time carousel status
        """
        # Execute macro to get complete vial status table
        vials_string = self.comm.send(f"macro \"{self.comm.config.get_macros_path()}\"; response$ = vialtable_export$()", 10)

        # Parse response string format: "pos:state, pos:state, ..."
        return {
                int(pos): int(state) in [0, 1, 2, 3]  # 0-3 are "in system" states
                for pos, state in (
                    item.split(":") 
                    for item in vials_string.strip(",").split(", ")
                )
            }
    
    def list_vial_validation(self, vials: list) -> None:
        """Validate that all vials in list are present in carousel system.
        
        Performs batch validation of multiple vials for sequence operations
        or batch analysis. This ensures all required vials are present before
        starting automated workflows that would fail on missing vials.
        
        Args:
            vials: List of vial position numbers to validate.
                  Examples: [1, 2, 3], [10, 15, 20, 25], range(1, 49)
                  
        Raises:
            VialError: If any vials are missing from the carousel.
                      Error message lists all missing vial positions for
                      easy identification and correction.
            
        Examples:
            Validate sequence vials:
            >>> sequence_vials = [10, 11, 12, 15, 20]
            >>> validation.list_vial_validation(sequence_vials)
            >>> # Safe to start sequence with these vials
            
            Validate range of positions:
            >>> validation.list_vial_validation(list(range(1, 25)))  # Check 1-24
            
            Handle validation errors:
            >>> try:
            ...     validation.list_vial_validation([1, 2, 3, 4, 5])
            ... except VialError as e:
            ...     print(f"Missing vials: {e}")
            ...     # Load missing vials before continuing
            
        Note:
            - Efficient batch checking using single carousel query
            - Reports all missing vials simultaneously
            - Essential before sequence execution
            - Prevents partial sequence failures due to missing vials
        """
        # Get current vial table status
        vial_table = self.get_vialtable()

        # Find vials that are present in system
        available_vials = {pos for pos, present in vial_table.items() if present}
        
        # Identify missing vials
        missing_vials = set(vials) - available_vials
        
        if missing_vials:
            raise VialError(f"Vials not present in carousel: {sorted(missing_vials)}")