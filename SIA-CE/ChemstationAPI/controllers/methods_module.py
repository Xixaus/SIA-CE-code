"""
Methods Module - ChemStation CE method management and execution.

Comprehensive management of ChemStation CE methods including loading, saving,
parameter modification, and execution. Methods define all analytical conditions
for capillary electrophoresis separations.

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
    
    Provides comprehensive method management for ChemStation CE methods including
    file operations, parameter editing, and execution with custom parameters.
    Methods are stored as .M files containing instrument parameters, acquisition 
    settings, and data analysis rules.
    
    Method Execution Modes:
        1. Direct execution: Run current method with existing parameters
        2. Custom execution: Run method with specified data filename  
        3. Parameterized execution: Run method with custom vial/sample information
    
    File Management:
        - Methods stored as .M files in ChemStation method directory
        - Runtime parameter access through RC.NET registers
        - Template execution with parameter modification
    
    Attributes:
        comm: ChemStation communicator for command execution
        validation: Method existence and parameter validation
        system: System state monitoring and control
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Methods module with ChemStation communicator.
        
        Args:
            communicator: ChemStation communication interface for method operations
                         and system commands
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
        self.system = SystemModule(self.comm)
    
    def load(self, method_name: str, method_path: str = "_METHODPATHS$") -> None:
        """Load CE method from file into ChemStation active memory.
        
        Loads the specified method file and makes it the current active method.
        All instrument parameters are updated including voltage, temperature, 
        vial assignments, and detection settings. Previous unsaved changes are lost.
        
        Args:
            method_name: Method filename without .M extension
                        Examples: "CE_Protein_Analysis", "MEKC_SmallMolecules"
            method_path: Directory containing methods. Defaults to ChemStation
                        method directory (_METHPATH$)
                        
        Raises:
            MethodError: If method file cannot be loaded or is corrupted
            ValidationError: If method file doesn't exist in specified directory
            FileNotFoundError: If method path is invalid
            
        Examples:
            >>> # Load standard analysis method
            >>> methods.load("CE_Protein_Analysis")
            >>> # Load method from custom directory  
            >>> methods.load("TestMethod", "C:\\Custom\\Methods\\")
            
        Note:
            Method loading overwrites current instrument settings and includes
            automatic validation of method file existence before loading.
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
        Comment is stored in method file metadata for documentation purposes.
        
        Args:
            method_name: Filename for saved method (without .M extension)
                        Defaults to current method name (_METHFILE$)
                        Examples: "Modified_CE_Method", "Optimized_Analysis_v3"
            method_path: Directory for saving method. Defaults to ChemStation
                        method directory (_METHPATH$)
            comment: Optional comment describing method changes or purpose.
                    Use quotes for multi-word comments
                    
        Raises:
            MethodError: If method cannot be saved due to file permissions
            ValidationError: If method name contains invalid characters
            PermissionError: If insufficient write permissions to directory
            
        Examples:
            >>> # Save current method with new name
            >>> methods.save("Optimized_CE_Method", comment="Improved resolution")
            >>> # Overwrite current method
            >>> methods.save()
            
        Note:
            Existing files with same name are overwritten without warning.
            Method name should follow Windows filename conventions.
        """
        # Construct SaveMethod command with parameters
        command = f"SaveMethod {method_path}, {method_name}, {comment}"
        self.comm.send(command)
            
    def run(self, data_name: str, data_dir: str = "_DATAPATH$") -> None:
        """Execute current method and save data with specified name.
        
        Runs the currently loaded method using existing method parameters including
        vial assignments, sample information, and all analytical conditions from
        the previous analysis setup. Only the output data filename is changed.
        
        Args:
            data_name: Name for the data file (without extension)
                      Examples: "Sample001", "QC_Standard_20240315", "Blank_Run"
            data_dir: Directory for data storage. Defaults to ChemStation
                     data directory (_DATAPATH$)
                     
        Raises:
            MethodError: If method execution fails or cannot start
            ValidationError: If data directory is invalid or required vials missing
            SystemError: If instrument is not ready for analysis
            
        Examples:
            >>> # Run analysis with descriptive name
            >>> methods.run("Protein_Sample_001")
            >>> # Run QC standard with custom directory
            >>> methods.run("QC_Standard_Daily", "C:\\QC_Data\\")
            
        Requirements:
            - Method must be loaded before execution
            - Required vials must be present and positioned
            - Instrument must be in ready state
            
        Note:
            All other parameters (vials, method settings, sample info) remain the same
            as previous analysis. Progress can be monitored via system.method_on().
        """
        # Execute method with data file naming
        self.validation.validate_vials_in_method()

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
        method register, modifying sample information, and running the analysis.
        Allows running the same method on different samples without manually
        editing method files.
        
        Process workflow:
        1. Creates temporary register (TemporaryRegisterMethod)
        2. Loads specified method and copies parameters  
        3. Modifies vial number and sample information
        4. Executes analysis with custom parameters
        5. Data saved with automatic filename generation
        
        Args:
            vial: Carousel position for sample (1-48). Must contain sample vial
            method_name: Method to execute (without .M extension)
                        Examples: "CE_Protein", "MEKC_Drugs", "CZE_Inorganics"
            sample_name: Descriptive sample name for data file and records
                        Examples: "BSA_1mg_ml", "Drug_Standard_Mix", "Unknown_001"
            comment: Path to text file containing method comment/description.
                    File content will be embedded in the method documentation
            subdirectory_name: Optional subdirectory for data organization.
                             If empty, uses current data subdirectory
                             
        Raises:
            MethodError: If method execution fails or method not found
            VialError: If specified vial is not present in carousel
            ValidationError: If method name is invalid or doesn't exist
            
        Examples:
            >>> # Analyze protein sample with comment file
            >>> methods.execution_method_with_parameters(
            ...     vial=15,
            ...     method_name="CE_Protein_Analysis", 
            ...     sample_name="BSA_Standard_1mg_ml",
            ...     comment="C:\\Comments\\protein_method.txt"
            ... )
            >>> 
            >>> # Run development sample in organized subdirectory
            >>> methods.execution_method_with_parameters(
            ...     vial=22,
            ...     method_name="Development_CZE",
            ...     sample_name="Test_Sample_v3",
            ...     subdirectory_name="Method_Development"
            ... )
            
        Requirements:
            - Method file must exist in method directory
            - Vial must be physically present in carousel
            - Instrument must be ready for analysis
            
        Note:
            Data filename generated automatically with timestamp. Sample information
            stored in data file metadata. Temporary register cleaned up after execution.
            Comment file validation needs to be implemented.
        """
        # Validate method exists before execution
        # TODO: Add validation for comment file existence
        self.validation.validate_method(method_name, check_vials=True)

        self.validation.validate_vial_in_system(vial)

        self.system.ready_to_start_analysis(timeout=10, verbose=False)

        # Execute macro for parameterized method run
        command = (f"macro \"{self.comm.config.get_macros_path()}\"; modify_and_run_method "
                   f"{vial}, \"{sample_name}\", {method_name}.M, \"{comment}\", "
                   f"{subdirectory_name}")
        
        self.comm.send(command)

        # Wait for method startup
        time.sleep(3)
        
        # Validate method execution started successfully
        self.validation.validate_method_run()