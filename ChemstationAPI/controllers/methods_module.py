"""
Methods Module - ChemStation method management.

This module provides functionality for loading, saving, and editing ChemStation
methods, including parameter management and method validation.

.. moduleauthor:: Richard Maršala
"""

import os
import time
from pathlib import Path

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator, CommunicationConfig
from .validation import ValidationModule

class MethodsModule():
    """Method management for loading, saving, and editing parameters.
    
    Provides methods for working with ChemStation methods including
    parameter editing in RC.NET registers.
    
    Methods can be loaded from files, saved with different names, executed
    with specific parameters, and validated for existence.
    
    Attributes:
        Inherits all attributes from ChemstationCommunicator.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Methods module.
        
        Args:
            config: Communication configuration for ChemStation connection.
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
    
    def load(self, method_name: str, method_path: str = "_METHPATH$") -> None:
        """Load a method from file.
        
        Args:
            method_name: Method name (without .M extension).
            method_path: Path to method directory (default: ChemStation method path).
            
        Raises:
            MethodError: If method cannot be loaded.
            ValidationError: If method doesn't exist.
            
        Example:
            >>> methods = MethodsModule()
            >>> methods.load("TestMethod")
        """
        self.validation.validate_method_name(method_name, method_path)

        command = f"LoadMethod {method_path}, {method_name}"
        self.comm.send(command)

        time.sleep(2)
                

    def save(self, method_name: str = "_METHFILE$", method_path: str = "_METHPATH$", comment: str = "\" \"") -> None:
        """Save the current method with specified name.
        
        Args:
            method_name: Name for saving (default: current method name).
            method_path: Path to method directory (default: ChemStation method path).
            comment: Optional comment for the method.
            
        Raises:
            MethodError: If method cannot be saved.
            ValidationError: If name is not valid.
            
        Example:
            >>> methods = MethodsModule()
            >>> methods.save("NewMethod", comment="Updated method")
        """
        command = f"SaveMethod {method_path}, {method_name}, {comment}"
        self.comm.send(command)
            
    def run(self, name: str, dir: str = "_DATAPATH") -> None:
        """Run the method and save with chosen name.
        
        Executes the method with current system parameters and saves
        the results under the specified name.
        
        Args:
            name: Name for the data file.
            dir: Directory for data storage (default: ChemStation data path).
            
        Example:
            >>> methods = MethodsModule()
            >>> methods.run("TestRun001")
        """
        command = f"RunMethod {dir},, {name}"
        self.comm.send(command)

        time.sleep(5)
        self.validation.validate_method_run()

    def execution_method_with_parameters(self, vial: int,
                                         method_name: str, sample_name: str = "", 
                                         comment: str = "", subdirectory_name: str = ""
                                         ) -> None:
        """Execute a method with specified parameters.
        
        Args:
            vial: Vial position to analyze.
            method_name: Method name (without .M extension).
            sample_name: Optional name for the analysis.
            comment: Optional comment.
            subdirectory_name: Optional subdirectory for results.
            
        Raises:
            MethodError: If method execution fails.
            ValidationError: If method doesn't exist or path is invalid.
            
        Example:
            >>> methods = MethodsModule()
            >>> methods.execution_method_with_parameters(
            ...     vial=15,
            ...     method_name="TestMethod",
            ...     sample_name="Sample001",
            ...     comment="Analysis run"
            ... )
        """
        self.validation.validate_method_name(method_name)

        command = (f"macro {self.comm.config.get_macros_path()}; modify_and_run_method "
                   f"{vial}, {sample_name}, {method_name}.M, {comment}, "
                   f"{subdirectory_name}")
        
        self.comm.send(command)

        time.sleep(5)
        
        self.validation.validate_method_run()