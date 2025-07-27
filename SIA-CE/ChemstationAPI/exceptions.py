"""
ChemStation API Exception Classes - Specialized error handling for CE operations.

This module defines a hierarchy of exception classes for precise error handling
in ChemStation operations. Each exception type represents a specific category
of failure, enabling targeted error handling and clear diagnostic messages.

Exception Hierarchy:
    ChemstationError (base)
    ├── CommunicationError - File-based communication failures
    ├── CommandError - ChemStation command execution failures  
    ├── FileOperationError - File system operation failures
    ├── SequenceError - Sequence management and execution failures
    ├── MethodError - CE method operation failures
    ├── VialError - Vial handling and validation failures
    ├── ConfigurationError - System configuration failures
    ├── ValidationError - Input validation and prerequisite failures
    └── TimeoutError - Operation timeout failures

Error Categories:
- Communication: Protocol-level failures between Python and ChemStation
- Validation: Pre-operation checking failures (missing files, invalid parameters)
- Instrument: Physical instrument operation failures (vial loading, method execution)
- System: Configuration and setup failures
- Timing: Timeout and synchronization failures

.. moduleauthor:: Richard Maršala
"""

class ChemstationError(Exception):
    """Base exception class for all ChemStation-related errors.
    
    This is the root exception class that all other ChemStation exceptions
    inherit from. It can be used to catch any ChemStation-related error
    in broad exception handling scenarios.
    
    Usage:
        try:
            # ChemStation operations
            api.ce.load_vial_to_position(15, "inlet")
            api.method.run("Sample001")
        except ChemstationError as e:
            print(f"ChemStation operation failed: {e}")
            # Handle any ChemStation-related error
    """
    pass

class CommunicationError(ChemstationError):
    """Raised when file-based communication system fails.
    
    This exception indicates problems with the underlying communication
    protocol between Python and ChemStation, including file access issues,
    protocol synchronization failures, and communication setup problems.
    
    Common Causes:
        - ChemStation communication macro not running
        - Communication files directory not accessible
        - File permission issues
        - Protocol synchronization errors
        - ChemStation not responding to commands
    
    Examples:
        Communication setup failure:
        >>> try:
        ...     api = ChemstationAPI()
        ... except CommunicationError as e:
        ...     print("Failed to establish ChemStation communication")
        ...     print("Ensure ChemStation is running and macro is loaded")
        
        Protocol synchronization error:
        >>> try:
        ...     response = api.send("complex_command", timeout=1.0)
        ... except CommunicationError:
        ...     print("Communication protocol error - try restarting connection")
    """
    pass

class CommandError(ChemstationError):
    """Raised when ChemStation Command Processor reports command failure.
    
    This exception occurs when ChemStation successfully receives a command
    but cannot execute it due to syntax errors, invalid parameters, or
    instrument state conflicts.
    
    Common Causes:
        - Invalid ChemStation command syntax
        - Wrong parameter values or types
        - Command not available in current ChemStation mode
        - Instrument state conflicts (e.g., method running)
        - Module-specific command failures
    
    Examples:
        Invalid command syntax:
        >>> try:
        ...     api.send("InvalidCommand parameter")
        ... except CommandError as e:
        ...     print(f"ChemStation rejected command: {e}")
        
        Instrument state conflict:
        >>> try:
        ...     api.send('WriteModule "CE1", "INVALID_COMMAND"')
        ... except CommandError:
        ...     print("CE module rejected command - check instrument state")
    """
    pass

class FileOperationError(ChemstationError):
    """Raised when file system operations fail during communication.
    
    This exception covers failures in reading from or writing to the
    command and response files used for ChemStation communication,
    as well as other file operations like method and sequence file access.
    
    Common Causes:
        - Insufficient file system permissions
        - Disk space exhaustion
        - File locked by another process
        - Network drive connectivity issues
        - File corruption or access conflicts
    
    Examples:
        File write failure:
        >>> try:
        ...     api.method.save("NewMethod")
        ... except FileOperationError as e:
        ...     print(f"Cannot save method file: {e}")
        ...     print("Check disk space and file permissions")
        
        Communication file access:
        >>> try:
        ...     api.send("response$ = _METHPATH$")
        ... except FileOperationError:
        ...     print("Communication file access failed")
        ...     print("Check communication directory permissions")
    """
    pass

class SequenceError(ChemstationError):
    """Raised when sequence management or execution operations fail.
    
    This exception covers failures in sequence file operations, sequence
    table editing, Excel import operations, and sequence execution control.
    
    Common Causes:
        - Sequence file not found or corrupted
        - Invalid sequence table parameters
        - Excel file format or access issues
        - Sequence execution state conflicts
        - Row index out of range
        - Missing method files referenced in sequence
    
    Examples:
        Sequence loading failure:
        >>> try:
        ...     api.sequence.load_sequence("MissingSequence")
        ... except SequenceError as e:
        ...     print(f"Cannot load sequence: {e}")
        
        Excel import failure:
        >>> try:
        ...     api.sequence.prepare_sequence_table("invalid.xlsx")
        ... except SequenceError as e:
        ...     print(f"Excel import failed: {e}")
        ...     print("Check Excel file format and accessibility")
        
        Sequence execution control:
        >>> try:
        ...     api.sequence.start()
        ... except SequenceError:
        ...     print("Cannot start sequence - check instrument status")
    """
    pass

class MethodError(ChemstationError):
    """Raised when CE method operations fail.
    
    This exception covers failures in method file operations, method
    execution, parameter modification, and method validation.
    
    Common Causes:
        - Method file not found or corrupted
        - Method execution startup failure
        - Invalid method parameters
        - Instrument not ready for method execution
        - Method file access or permission issues
        - Parameter validation failures
    
    Examples:
        Method loading failure:
        >>> try:
        ...     api.method.load("NonexistentMethod")
        ... except MethodError as e:
        ...     print(f"Method loading failed: {e}")
        
        Method execution failure:
        >>> try:
        ...     api.method.run("Sample001")
        ... except MethodError as e:
        ...     print(f"Method execution failed: {e}")
        ...     print("Check instrument status and method parameters")
        
        Parameterized execution failure:
        >>> try:
        ...     api.method.execution_method_with_parameters(99, "Method", "Sample")
        ... except MethodError:
        ...     print("Method execution with parameters failed")
        ...     print("Check vial presence and method validity")
    """
    pass

class VialError(ChemstationError):
    """Raised when vial handling or validation operations fail.
    
    This exception covers failures in vial presence checking, carousel
    operations, lift position management, and vial state validation.
    
    Common Causes:
        - Vial not present in specified carousel position
        - Vial loading/unloading mechanical failure
        - Carousel position out of range
        - Lift position occupied when expected empty
        - Vial sensor malfunction or calibration issues
        - Multiple vials missing for batch operations
    
    Examples:
        Vial presence failure:
        >>> try:
        ...     api.ce.load_vial_to_position(15, "inlet")
        ... except VialError as e:
        ...     print(f"Vial operation failed: {e}")
        ...     print("Check vial is properly seated in carousel")
        
        Batch vial validation failure:
        >>> try:
        ...     api.validation.list_vial_validation([1, 2, 3, 4, 5])
        ... except VialError as e:
        ...     print(f"Missing vials detected: {e}")
        ...     print("Load missing vials before starting sequence")
        
        Position validation failure:
        >>> try:
        ...     api.validation.vial_in_position("inlet")
        ... except VialError:
        ...     print("No vial at inlet position")
        ...     print("Load sample vial before injection")
    """
    pass

class ConfigurationError(ChemstationError):
    """Raised when system configuration or setup fails.
    
    This exception covers failures in API configuration, communication
    setup, directory creation, and system initialization.
    
    Common Causes:
        - Invalid configuration parameters
        - Communication directory creation failure
        - Path configuration errors
        - System permission issues
        - Missing required files or directories
        - Configuration file corruption
    
    Examples:
        API initialization failure:
        >>> try:
        ...     api = ChemstationAPI(invalid_config)
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
        ...     print("Check configuration parameters and paths")
        
        Directory access failure:
        >>> try:
        ...     config = CommunicationConfig(comm_dir="/invalid/path")
        ...     api = ChemstationAPI(config)
        ... except ConfigurationError:
        ...     print("Cannot access communication directory")
        ...     print("Check path and permissions")
    """
    pass

class ValidationError(ChemstationError):
    """Raised when input validation or prerequisite checking fails.
    
    This exception covers failures in parameter validation, file existence
    checking, system state validation, and prerequisite verification.
    
    Common Causes:
        - Method or sequence file not found
        - Invalid parameter values or ranges
        - System state not ready for operation
        - Missing prerequisites for operations
        - File name or path validation failures
        - Case-sensitive filename issues
    
    Examples:
        File existence validation:
        >>> try:
        ...     api.validation.validate_method_name("NonexistentMethod")
        ... except ValidationError as e:
        ...     print(f"Method validation failed: {e}")
        ...     print("Check method name and directory")
        
        System state validation:
        >>> try:
        ...     api.validation.validate_use_carousel()
        ... except ValidationError as e:
        ...     print(f"Carousel not available: {e}")
        ...     print("Wait for instrument to reach ready state")
        
        Parameter validation:
        >>> try:
        ...     api.ce.load_vial_to_position(15, "invalid_position")
        ... except ValidationError:
        ...     print("Invalid position specified")
        ...     print("Use 'inlet', 'outlet', or 'replenishment'")
    """
    pass

class TimeoutError(ChemstationError):
    """Raised when operations exceed specified timeout periods.
    
    This exception covers timeouts in communication, method execution
    monitoring, system status polling, and other time-sensitive operations.
    
    Common Causes:
        - ChemStation not responding to commands
        - Long-running operations exceeding timeout
        - Communication protocol delays
        - System busy with other operations
        - Network or file system delays
        - Instrument hardware response delays
    
    Examples:
        Communication timeout:
        >>> try:
        ...     response = api.send("complex_command", timeout=1.0)
        ... except TimeoutError as e:
        ...     print(f"Command timeout: {e}")
        ...     print("Increase timeout or check ChemStation status")
        
        System ready timeout:
        >>> try:
        ...     ready = api.system.wait_for_ready(timeout=30)
        ... except TimeoutError:
        ...     print("System did not reach ready state")
        ...     print("Check for instrument errors or long conditioning")
        
        Method execution timeout:
        >>> try:
        ...     api.method.run("LongAnalysis")
        ...     # Wait with timeout monitoring
        ... except TimeoutError:
        ...     print("Method execution monitoring timeout")
        ...     print("Check method status manually")
    """
    pass