"""
Configuration module for ChemStation communication settings.

This module provides the CommunicationConfig dataclass that contains all necessary
configuration parameters for establishing and maintaining communication with
ChemStation software.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommunicationConfig:
    """Configuration settings for ChemStation communication.
    
    This dataclass contains all configuration parameters needed for file-based
    communication with ChemStation software, including paths, timeouts, and
    behavior settings.
    
    Attributes:
        comm_dir: Directory path for communication files.
        command_filename: Name of the command file.
        response_filename: Name of the response file.
        max_command_number: Maximum command number before wraparound.
        default_timeout: Default timeout for commands in seconds.
        retry_delay: Delay between retries in seconds.
        max_retries: Maximum number of retry attempts.
        test_on_init: Whether to test connection on initialization.
        verbose: Whether to enable verbose logging.
        base_macros_path: Base path to ChemStation macro files.
        main_macro_file: Name of the main macro file.
        chempy_connect_file: Name of the ChemPy connection macro file.
    """
    
    # Communication paths
    comm_dir: str = "core/communication_files"
    command_filename: str = "command"
    response_filename: str = "response"
    
    # Communication settings
    max_command_number: int = 256
    default_timeout: float = 5.0
    retry_delay: float = 0.1
    max_retries: int = 10
    
    # Behavior settings
    test_on_init: bool = True
    verbose: bool = False
    
    # Macro paths
    base_macros_path: str = "controllers/macros"
    main_macro_file: str = "macros.mac"
    reader_macro_file: str = "register_reader.mac"
    chempy_connect_file: str = "ChemPyConnect.mac"
    
    def _get_project_root(self) -> Path:
        """Get project root directory by finding the directory containing this file's parent."""
        return Path(__file__).resolve().parent.parent
    
    def get_comm_dir_path(self) -> Path:
        """Get the communication directory as a Path object.
        
        Returns:
            Path: Absolute path to the communication directory.
        """
        comm_path = self._get_project_root() / self.comm_dir
        comm_path.mkdir(parents=True, exist_ok=True)
        return comm_path
    
    def get_command_file_path(self) -> Path:
        """Get the command file path as a Path object.
        
        Returns:
            Path: Absolute path to the command file.
        """
        return self.get_comm_dir_path() / self.command_filename
    
    def get_response_file_path(self) -> Path:
        """Get the response file path as a Path object.
        
        Returns:
            Path: Absolute path to the response file.
        """
        return self.get_comm_dir_path() / self.response_filename
    
    def get_macros_path(self) -> Path:
        """Get the main macro file path as a Path object.
        
        Returns:
            Path: Absolute path to the main macro file.
        """
        macros_path = self._get_project_root() / self.base_macros_path / self.main_macro_file
        macros_path.parent.mkdir(parents=True, exist_ok=True)
        return macros_path
    
    def get_chempy_connect_path(self) -> Path:
        """Get the ChemPy connection macro path as a Path object.
        
        Returns:
            Path: Absolute path to the ChemPy connection macro file.
        """
        return self._get_project_root() / "core" / self.chempy_connect_file
    
    def get_temp_dir_path(self) -> Path:
        """Vrátí absolutní cestu ke složce 'temp' ve složce 'controllers'."""
        temp_path = self._get_project_root() / "controllers" / "temp"
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path