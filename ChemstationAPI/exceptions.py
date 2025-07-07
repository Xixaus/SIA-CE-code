"""
Custom exceptions for the ChemStation control interface.

This module defines specific exceptions that can occur when interacting with
Agilent ChemStation software. Having dedicated exception classes makes error
handling more precise and helps distinguish between different types of failures.

.. moduleauthor:: Richard Maršala
"""

class ChemstationError(Exception):
    """Base exception class for all ChemStation-related errors."""
    pass

class CommunicationError(ChemstationError):
    """Raised when there are problems with the file-based communication system."""
    pass

class CommandError(ChemstationError):
    """Raised when ChemStation returns an error response to a command."""
    pass

class FileOperationError(ChemstationError):
    """Raised when there are issues with file operations (reading/writing command files)."""
    pass

class SequenceError(ChemstationError):
    """Raised when there are issues with sequence operations."""
    pass

class MethodError(ChemstationError):
    """Raised when there are issues with method operations."""
    pass

class VialError(ChemstationError):
    """Raised when there are issues with vial operations or validation."""
    pass

class ConfigurationError(ChemstationError):
    """Raised when there are issues with system configuration."""
    pass

class ValidationError(ChemstationError):
    """Raised when input validation fails."""
    pass

class TimeoutError(ChemstationError):
    """Raised when an operation times out."""
    pass