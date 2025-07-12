"""
System Module - ChemStation system monitoring and status management.

This module provides comprehensive monitoring and control of the ChemStation system
status, method execution tracking, and diagnostic capabilities. It enables monitoring
of CE instrument states, analysis progress, and system readiness.

System States Monitored:
- Acquisition Status: STANDBY, PRERUN, RUN, POSTRUN states
- Method Execution: Active/inactive method monitoring
- Runtime Tracking: Elapsed and remaining analysis time
- Instrument Readiness: Ready state validation for new analyses
- RC Status: Real-time CE module status information

Diagnostic Features:
- Register inspection tools for debugging
- Error monitoring and system abort capabilities  
- Connection testing and validation
- Performance monitoring and timing analysis

.. moduleauthor:: Richard Maršala
"""

import time
import os
from pathlib import Path

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator

class SystemModule():
    """System monitoring and diagnostic control for ChemStation CE operations.
    
    Provides comprehensive system status monitoring, method execution tracking,
    and diagnostic capabilities for the CE instrument. This module enables
    monitoring of instrument states, analysis progress, and system readiness
    for automated workflows and user interfaces.
    
    Status Monitoring:
        - Real-time acquisition status tracking
        - Method execution state monitoring  
        - Analysis timing and progress information
        - Instrument readiness validation
    
    Diagnostic Tools:
        - Register browser for system debugging
        - Error condition monitoring and reporting
        - System abort and recovery capabilities
        - Performance timing analysis
    
    RC Status Integration:
        - Direct access to RC.NET status registers
        - Real-time CE module status information
        - Hardware state monitoring
        - Error condition detection
    
    Attributes:
        comm: ChemStation communicator for system command execution.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize system monitoring module.
        
        Args:
            communicator: ChemStation communication interface for status queries.
        """
        self.comm = communicator

        
    def method_on(self) -> bool:
        """Check if an analytical method is currently executing.
        
        Monitors the ChemStation _MethodOn system variable to determine
        if an analysis is actively running. This includes all phases:
        preconditioning, injection, separation, detection, and postconditioning.
        
        Returns:
            True if a method is currently executing, False if system is idle.
            
        Examples:
            Wait for method completion:
            >>> while system.method_on():
            ...     print("Analysis in progress...")
            ...     time.sleep(30)
            >>> print("Analysis completed")
            
            Check before starting new analysis:
            >>> if not system.method_on():
            ...     api.method.run("NewSample")
            ... else:
            ...     print("Wait for current analysis to finish")
            
        Note:
            - Returns True during all method phases including conditioning
            - False indicates system is ready for new analysis
            - Use in conjunction with status() for detailed state information
        """
        state = self.comm.send("response$ = VAL$(_MethodOn)")
        return state == "1"

    def status(self) -> str:
        """Get current ChemStation acquisition status.
        
        Returns the detailed acquisition status from ChemStation's ACQSTATUS$
        system variable, providing specific information about the current
        operational state of the instrument.
        
        Returns:
            Current acquisition status string with possible values:
            - "STANDBY": System idle, ready for new analysis
            - "PRERUN": Pre-analysis conditioning and preparation  
            - "RUN": Active separation and detection phase
            - "POSTRUN": Post-analysis conditioning and cleanup
            - "ERROR": Error condition requiring attention
            - "ABORT": Analysis aborted or interrupted
            
        Examples:
            Monitor analysis phases:
            >>> status = system.status()
            >>> if status == "RUN":
            ...     print("Separation in progress")
            >>> elif status == "PRERUN": 
            ...     print("Preparing for analysis")
            >>> elif status == "STANDBY":
            ...     print("Ready for new sample")
            
            Wait for specific phase:
            >>> while system.status() != "RUN":
            ...     time.sleep(5)  # Wait for separation to start
            >>> print("Separation phase started")
            
        Note:
            - Status updates in real-time during analysis
            - STANDBY indicates readiness for new analysis
            - ERROR status requires investigation and clearing
        """
        return self.comm.send("response$ = ACQSTATUS$")

    def RC_status(self, module: str = "CE1") -> str:
        """Get current RC.NET module status for detailed instrument monitoring.
        
        Queries the RC.NET status register for the specified module to obtain
        detailed instrument status information including run states, error
        conditions, and operational modes.
        
        Args:
            module: RC.NET module identifier. Default "CE1" for CE instrument.
                   Other modules might include pumps, detectors, autosamplers.
                   
        Returns:
            Current RC module run state string with possible values:
            - "Idle": Module ready and available
            - "Run": Module actively executing operations
            - "NotReady": Module initializing or in error state
            - "Error": Module error condition
            - "Maintenance": Module in maintenance mode
            
        Examples:
            Monitor CE instrument status:
            >>> rc_status = system.RC_status("CE1")
            >>> if rc_status == "Idle":
            ...     print("CE instrument ready")
            >>> elif rc_status == "Error":
            ...     print("CE instrument error - check diagnostics")
            
            Check multiple modules:
            >>> for module in ["CE1", "DAD1"]:
            ...     status = system.RC_status(module)
            ...     print(f"{module}: {status}")
            
        Note:
            - Provides more detailed status than basic acquisition status
            - Useful for troubleshooting and system diagnostics
            - RC status may differ from acquisition status during transitions
        """
        return self.comm.send(f'response$ = ObjHdrText$(RC{module}Status[1], "RunState")')

    def add_register_reader(self, register_reader_macro: str = r"ChemstationAPI\controllers\macros\register_reader.mac") -> None:
        """Add register inspection tool to ChemStation Debug menu.
        
        Installs a comprehensive register browser tool in ChemStation's menu system
        that allows interactive inspection and modification of ChemStation registers.
        This is invaluable for debugging, system analysis, and advanced parameter editing.
        
        Register Browser Features:
            - Browse all ChemStation registers (RC.NET, sequence, method, etc.)
            - Inspect object structures and data tables
            - View and modify header values and text fields
            - Navigate complex register hierarchies
        
        Args:
            register_reader_macro: Path to register reader macro file.
                                Default uses included register_reader.mac.
                                
        Examples:
            Add register browser with default path:
            >>> system.add_register_reader()
            
            Use custom register reader:
            >>> system.add_register_reader("C:\\Custom\\debug_tools.mac")
            
        Note:
            - Adds "Show Registers" item to Debug menu in ChemStation
            - Tool remains available until ChemStation restart
            - Extremely useful for advanced debugging and development
            - Exercise caution when modifying system registers
        """
        path = Path(register_reader_macro).absolute()
        self.comm.send(f"macro \"{path}\"")

    def abort_run(self) -> None:
        """Immediately abort the current analysis or sequence.
        
        Sends an abort command to ChemStation that immediately terminates
        the current analysis, sequence, or operation. This is used for
        emergency stops, error recovery, or when immediate termination is required.
        
        Abort Process:
            1. Immediately stops current analysis phase
            2. Disables high voltage and pressure systems
            3. Returns instrument to safe idle state
            4. Clears method execution flags
            
        Raises:
            SystemError: If abort command fails to execute.
            
        Examples:
            Emergency stop:
            >>> system.abort_run()
            
            Conditional abort on error:
            >>> if error_detected:
            ...     system.abort_run()
            ...     print("Analysis aborted due to error")
            
        Note:
            - Immediate termination without post-run conditioning
            - Data up to abort point may be saved
            - Instrument requires manual return to ready state
            - Use for emergency situations or error recovery
        """
        self.comm.send("AbortRun")
        # Brief wait for abort completion and system stabilization
        time.sleep(2)

    def wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait for ChemStation to reach ready state for new analysis.
        
        Polls the system status until it reaches a state ready for new analysis
        (STANDBY or PRERUN) or until timeout expires. Useful for automated
        workflows that need to wait for instrument availability.
        
        Args:
            timeout: Maximum waiting time in seconds. Default 60 seconds.
                    Increase for methods with long post-run conditioning.
                    
        Returns:
            True if system reaches ready state within timeout,
            False if timeout expires before ready state.
            
        Examples:
            Wait with default timeout:
            >>> if system.wait_for_ready():
            ...     api.method.run("NextSample")
            ... else:
            ...     print("Timeout waiting for instrument")
            
            Wait with extended timeout for long methods:
            >>> if system.wait_for_ready(timeout=300):  # 5 minutes
            ...     start_next_analysis()
            
            Use in sequence automation:
            >>> for sample in sample_list:
            ...     if system.wait_for_ready(timeout=120):
            ...         process_sample(sample)
            ...     else:
            ...         log_error("Instrument timeout")
            
        Note:
            - Polls status every second to minimize system load
            - STANDBY and PRERUN both considered ready states
            - Timeout should account for longest expected conditioning
            - Returns immediately if already in ready state
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.status()
            if current_status in ["STANDBY", "PRERUN"]:
                return True
            time.sleep(1)
        return False

    def get_elapsed_analysis_time(self) -> float:
        """Get elapsed separation time since current analysis started.
        
        Returns the time that has elapsed since the actual separation phase
        began in the current analysis. This excludes pre-run conditioning,
        injection, and other preparation phases, measuring only the
        electrophoretic separation runtime.
        
        Returns:
            Elapsed separation time in minutes as float.
            Returns 0.0 if no analysis is running.
            
        Examples:
            Monitor analysis progress:
            >>> elapsed = system.get_elapsed_analysis_time()
            >>> total = system.get_analysis_time()
            >>> progress = (elapsed / total) * 100
            >>> print(f"Analysis {progress:.1f}% complete")
            
            Real-time monitoring:
            >>> while system.method_on():
            ...     elapsed = system.get_elapsed_analysis_time()
            ...     print(f"Running for {elapsed:.2f} minutes")
            ...     time.sleep(30)
            
        Note:
            - Measures only separation phase, not total method time
            - Updates in real-time during analysis
            - Precision typically to 0.01 minutes (0.6 seconds)
            - Returns 0.0 when no separation is active
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)

    def get_analysis_time(self) -> float:
        """Get total expected separation duration for current method.
        
        Returns the total expected duration of the separation phase for
        the currently loaded method. This is the method's programmed
        stoptime and represents the expected separation runtime.
        
        Returns:
            Total separation duration in minutes as float.
            
        Examples:
            Calculate remaining time:
            >>> total_time = system.get_analysis_time()
            >>> elapsed_time = system.get_elapsed_analysis_time()
            >>> remaining = total_time - elapsed_time
            >>> print(f"Analysis will complete in {remaining:.2f} minutes")
            
            Check method duration before starting:
            >>> duration = system.get_analysis_time()
            >>> if duration > 60:  # More than 1 hour
            ...     print(f"Long analysis: {duration:.1f} minutes")
            ...     confirm = input("Continue? (y/n): ")
            
        Note:
            - Based on method's programmed stoptime parameter
            - Does not include conditioning or injection time
            - May differ from actual runtime due to early termination
            - Remains constant during analysis execution
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime"))')
        return float(time_response)

    def get_remaining_analysis_time(self) -> float:
        """Get remaining separation time until current analysis completes.
        
        Calculates the time remaining until the separation phase completes
        by subtracting elapsed time from total expected separation duration.
        Provides real-time countdown for analysis completion.
        
        Returns:
            Remaining separation time in minutes as float.
            Returns 0.0 if no analysis running or analysis completed.
            
        Examples:
            Display countdown:
            >>> remaining = system.get_remaining_analysis_time()
            >>> print(f"Analysis completes in {remaining:.1f} minutes")
            
            Wait with progress updates:
            >>> while system.method_on():
            ...     remaining = system.get_remaining_analysis_time()
            ...     if remaining > 0:
            ...         print(f"Time remaining: {remaining:.2f} minutes")
            ...     time.sleep(60)  # Update every minute
            
            Automated scheduling:
            >>> remaining = system.get_remaining_analysis_time()
            >>> if remaining < 5:  # Less than 5 minutes left
            ...     prepare_next_sample()
            
        Note:
            - Updates continuously during analysis
            - Becomes negative if analysis runs longer than expected
            - Returns 0.0 when separation phase not active
            - Useful for progress bars and time estimation
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime") - ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)