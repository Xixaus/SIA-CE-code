"""
Methods Module - ChemStation CE method management and execution.

This module provides comprehensive management of ChemStation CE methods including
loading, saving, parameter modification, and method execution with custom parameters.
CE methods define all analytical conditions for capillary electrophoresis separations.

.. moduleauthor:: Richard Maršala
"""

import os
import time
from pathlib import Path

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator, CommunicationConfig
from .validation import ValidationModule
from .system_module import SystemModule

class MethodsModule():
    """CE method management for analytical method control and execution.
    
    Provides comprehensive method management capabilities for ChemStation CE methods,
    including file operations, parameter editing through RC.NET registers, method
    execution with custom parameters, and validation of method existence and integrity.
    
    Method File Structure:
        - Methods stored as .M files in ChemStation method directory
        - Contains instrument parameters, acquisition settings, data analysis rules
        - Methods can be loaded, modified, saved with new names
        - RC.NET registers provide runtime parameter access
    
    Method Execution Modes:
        1. Direct execution: Run current method with system defaults
        2. Parameterized execution: Run method with custom vial/sample info
        3. Template execution: Modify register and execute custom analysis
    
    Attributes:
        comm: ChemStation communicator for command execution.
        validation: Validation module for method existence and parameter checking.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Methods module with communicator.
        
        Args:
            communicator: ChemStation communication interface for method operations.
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
        self.system = SystemModule(self.comm)
    
    def load(self, method_name: str, method_path: str = "_METHODPATHS$") -> None:
        """Load a CE method from file into ChemStation memory.
        
        Loads the specified method file and makes it the current active method.
        All instrument parameters are updated to match the method settings,
        including voltage, temperature, vial assignments, and detection parameters.
        
        Args:
            method_name: Method filename without .M extension. Examples:
                        - "CE_Protein_Analysis": Standard protein separation
                        - "MEKC_SmallMolecules": Micellar electrokinetic chromatography  
                        - "CZE_Inorganics": Capillary zone electrophoresis for ions
            method_path: Directory path containing methods. Defaults to ChemStation
                        method directory (_METHPATH$). Can specify custom path.
                        
        Raises:
            MethodError: If method file cannot be loaded or is corrupted.
            ValidationError: If method file doesn't exist in specified directory.
            FileNotFoundError: If method path is invalid.
            
        Examples:
            Load standard analysis method:
            >>> methods.load("CE_Protein_Analysis")
            
            Load method from custom directory:
            >>> methods.load("TestMethod", "C:\\Custom\\Methods\\")
            
            Load development method:
            >>> methods.load("Development_CZE_v2")
            
        Note:
            - Method loading overwrites current instrument settings
            - Previous unsaved changes will be lost
            - Method validation occurs before loading
            - Instrument parameters updated automatically after loading
        """
        # Validate method exists before attempting to load
        self.validation.validate_method(method_name, method_path)

        # Send LoadMethod command to ChemStation
        command = f"LoadMethod {method_path}, {method_name}.M"
        self.comm.send(command)

        # Allow time for method loading and parameter updates
        time.sleep(2)
                

    def save(self, method_name: str = "_METHFILE$", method_path: str = "_METHODPATHS$", 
             comment: str = "\" \"") -> None:
        """Save current method with specified name and optional comment.
        
        Saves the currently loaded method with all current parameter settings
        to a .M file. If no name specified, overwrites the current method file.
        
        Args:
            method_name: Filename for saved method (without .M extension).
                        Defaults to current method name (_METHFILE$).
                        Examples: "Modified_CE_Method", "Optimized_Analysis_v3"
            method_path: Directory for saving method. Defaults to ChemStation
                        method directory (_METHPATH$).
            comment: Optional comment describing method changes or purpose.
                    Stored in method file metadata. Use quotes for multi-word comments.
                    
        Raises:
            MethodError: If method cannot be saved due to file permissions or disk space.
            ValidationError: If method name contains invalid characters.
            PermissionError: If insufficient write permissions to method directory.
            
        Examples:
            Save current method with new name:
            >>> methods.save("Optimized_CE_Method", comment="Improved resolution")
            
            Overwrite current method:
            >>> methods.save()  # Saves to current method file
            
            Save to custom directory:
            >>> methods.save("Backup_Method", "C:\\Backup\\Methods\\")
            
        Note:
            - Saved method includes all current parameter settings
            - Comment appears in method file properties
            - Method name should follow Windows filename conventions
            - Existing files with same name are overwritten without warning
        """
        # Construct SaveMethod command with parameters
        command = f"SaveMethod {method_path}, {method_name}, {comment}"
        self.comm.send(command)
            
    def run(self, data_name: str, data_dir: str = "_DATAPATH$") -> None:
        """Execute current method and save data with specified name.
        
        Runs the currently loaded method with all its parameters and saves
        the analytical data to a file. The method executes through all phases:
        preconditioning, injection, separation, detection, and postconditioning.
        
        Args:
            data_name: Name for the data file (without extension).
                      Examples: "Sample001", "QC_Standard_20240315", "Blank_Run"
            data_dir: Directory for data storage. Defaults to ChemStation
                     data directory (_DATAPATH$).
                     
        Raises:
            MethodError: If method execution fails or cannot start.
            ValidationError: If data directory is invalid or inaccessible.
            SystemError: If instrument is not ready for analysis.
            
        Examples:
            Run analysis with descriptive name:
            >>> methods.run("Protein_Sample_001")
            
            Run blank analysis:
            >>> methods.run("Blank_Buffer_Analysis")
            
            Run QC standard:
            >>> methods.run("QC_Standard_Daily", "C:\\QC_Data\\")
            
        Note:
            - Method must be loaded before execution
            - Instrument must be in ready state
            - Data file created automatically with timestamp
            - Progress can be monitored via system.method_on()
        """
        # Execute method with data file naming
        command = f"RunMethod {data_dir},, {data_name}"
        self.comm.send(command)

        # Brief wait for method startup
        time.sleep(5)
        
        # Validate method started successfully
        self.validation.validate_method_run()

    def execution_method_with_parameters(self, vial: int, method_name: str, 
                                         sample_name: str = "", comment: str = "", 
                                         subdirectory_name: str = "") -> None:
        """Execute CE method with custom vial and sample parameters.
        
        Executes a method with specified sample parameters by creating a temporary
        method register, modifying the sample information, and running the analysis.
        This allows running the same method on different samples without manually
        editing method files.
        
        Execution Process:
            1. Creates temporary register (TemporaryRegisterMethod)
            2. Loads specified method and copies parameters
            3. Modifies vial number and sample information
            4. Executes analysis with custom parameters
            5. Data saved with automatic filename generation
        
        Args:
            vial: Carousel position for sample (1-48). Must contain sample vial.
            method_name: Method to execute (without .M extension).
                        Examples: "CE_Protein", "MEKC_Drugs", "CZE_Inorganics"
            sample_name: Descriptive sample name for data file and records.
                        Examples: "BSA_1mg_ml", "Drug_Standard_Mix", "Unknown_001"
            comment: Optional analysis comment stored in data file metadata.
                    Useful for experimental conditions or notes.
            subdirectory_name: Optional subdirectory for data organization.
                             If empty, uses current data subdirectory.
                             
        Raises:
            MethodError: If method execution fails or method not found.
            VialError: If specified vial is not present in carousel.
            ValidationError: If method name is invalid or doesn't exist.
            
        Examples:
            Analyze protein sample:
            >>> methods.execution_method_with_parameters(
            ...     vial=15,
            ...     method_name="CE_Protein_Analysis", 
            ...     sample_name="BSA_Standard_1mg_ml",
            ...     comment="pH 8.5 buffer system"
            ... )
            
            Run method development sample:
            >>> methods.execution_method_with_parameters(
            ...     vial=22,
            ...     method_name="Development_CZE",
            ...     sample_name="Test_Sample_v3",
            ...     subdirectory_name="Method_Development"
            ... )
            
            Analyze unknown sample:
            >>> methods.execution_method_with_parameters(
            ...     vial=8,
            ...     method_name="Standard_CE_Method",
            ...     sample_name="Unknown_Sample_001"
            ... )
            
        Note:
            - Method file must exist in method directory
            - Vial must be physically present in carousel
            - Data filename generated automatically with timestamp
            - Temporary register cleaned up after execution
            - Sample information stored in data file metadata
        """
        # Validate method exists before execution
        self.validation.validate_method(method_name, check_vials=True)

        self.system.ready_to_start_analysis(timeout=10, verbose=False)

        # Execute macro for parameterized method run
        command = (f"macro \"{self.comm.config.get_macros_path()}\"; modify_and_run_method "
                   f"{vial}, \"{sample_name}\", {method_name}.M, \"{comment}\", "
                   f"{subdirectory_name}")
        
        self.comm.send(command)

        # Wait for method startup
        time.sleep(5)
        
        # Validate method execution started successfully
        self.validation.validate_method_run()