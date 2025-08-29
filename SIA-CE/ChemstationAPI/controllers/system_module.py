"""
System Module - ChemStation system monitoring and status management.

Comprehensive monitoring and control of ChemStation system status, method execution
tracking, and diagnostic capabilities for CE instrument operations.

System States Monitored:
- Acquisition Status: STANDBY, PRERUN, RUN, POSTRUN states
- Method Execution: Active/inactive method monitoring  
- Runtime Tracking: Elapsed and remaining analysis time
- Instrument Readiness: Ready state validation for new analyses
- RC Status: Real-time CE module status information

.. moduleauthor:: Richard Maršala
"""

import time
import os
import sys
from pathlib import Path

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator

class SystemModule():
    """System monitoring and diagnostic control for ChemStation CE operations.
    
    Provides comprehensive system status monitoring, method execution tracking,
    and diagnostic capabilities for the CE instrument. Essential for automated
    workflows, user interfaces, and system diagnostics.
    
    Key monitoring capabilities include real-time acquisition status tracking,
    method execution state monitoring, analysis timing information, and
    instrument readiness validation.
    
    Diagnostic Tools:
        - Register browser for system debugging and parameter inspection
        - Error condition monitoring and emergency abort capabilities
        - System readiness validation with timeout handling
        - Performance timing analysis for optimization
    
    RC Status Integration:
        Direct access to RC.NET status registers provides detailed instrument
        status including run states, error conditions, and operational modes
        for comprehensive system monitoring.
    
    Attributes:
        comm: ChemStation communicator for system command execution and status queries
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize system monitoring module with ChemStation communicator.
        
        Args:
            communicator: ChemStation communication interface for status queries
                         and system command execution
        """
        self.comm = communicator

        
    def method_on(self) -> bool:
        """Check if an analytical method is currently executing.
        
        Monitors ChemStation's _MethodOn system variable to determine if any
        analysis is actively running. Covers all method phases including
        preconditioning, injection, separation, detection, and postconditioning.
        
        Returns:
            True if a method is currently executing (any phase), False if idle
            
        Examples:
            >>> # Wait for method completion
            >>> while system.method_on():
            ...     print("Analysis in progress...")
            ...     time.sleep(30)
            >>> 
            >>> # Check before starting new analysis
            >>> if not system.method_on():
            ...     api.method.run("NewSample")
            
        Note:
            Essential for automation workflows to prevent overlapping analyses.
            Use with status() for detailed phase information.
        """
        state = self.comm.send("response$ = VAL$(_MethodOn)")
        return state == "1"

    def status(self) -> str:
        """Get current ChemStation acquisition status.
    
        Returns detailed acquisition status from ChemStation's ACQSTATUS$ system
        variable, providing specific information about the current operational
        state and analysis phase.
    
        Returns:
            Current acquisition status:
            - "STANDBY": System idle, ready for new analysis
            - "PRERUN": Pre-analysis conditioning and preparation  
            - "RUN": Active separation and detection phase
            - "POSTRUN": Post-analysis conditioning and cleanup
            - "ERROR": Error condition requiring attention
            - "ABORT": Analysis aborted or interrupted
        
        Examples:
            >>> # Monitor analysis phases
            >>> status = system.status()
            >>> if status == "RUN":
            ...     print("Separation in progress")
            >>> elif status == "STANDBY":
            ...     print("Ready for new sample")
            >>> 
            >>> # Wait for specific phase
            >>> while system.status() != "RUN":
            ...     time.sleep(5)
        
        Note:
            Status updates in real-time. STANDBY indicates readiness for new analysis.
            Includes automatic retry logic for communication reliability.
        """
        for attempt in range(3):
            try:
                return self.comm.send("response$ = ACQSTATUS$", 10)
            except TimeoutError:
                if attempt == 2:
                    raise

    def RC_status(self, module: str = "CE1") -> str:
        """Get current RC.NET module status for detailed instrument monitoring.
    
        Queries RC.NET status registers for detailed instrument status including
        run states, error conditions, and operational modes. Provides more
        granular status information than basic acquisition status.
    
        Args:
            module: RC.NET module identifier. Default "CE1" for CE instrument.
                   Other modules: "DAD1" (detector), "PUMP1", etc.
                
        Returns:
            Current RC module run state:
            - "Idle": Module ready and available for operations
            - "Run": Module actively executing operations
            - "NotReady": Module initializing or in error state
            - "Error": Module error condition requiring attention
            - "Maintenance": Module in maintenance mode
        
        Examples:
            >>> # Monitor CE instrument status
            >>> if system.RC_status("CE1") == "Idle":
            ...     print("CE instrument ready")
            >>> 
            >>> # Check multiple modules
            >>> for module in ["CE1", "DAD1"]:
            ...     print(f"{module}: {system.RC_status(module)}")
        
        Note:
            More detailed than acquisition status. Useful for troubleshooting
            and system diagnostics. Includes automatic retry logic.
        """
        for attempt in range(3):
            try:
                return self.comm.send(f'response$ = ObjHdrText$(RC{module}Status[1], "RunState")', 20)
            except TimeoutError:
                if attempt == 2:
                    raise


    def ready_to_start_analysis(self, modules=["CE1", "DAD1"], timeout=None, verbose=True):
        """Wait for all specified modules to reach ready state for analysis.
        
        Monitors multiple RC.NET modules until all reach "Idle" state with no
        "NotReady" conditions. Essential for ensuring instrument readiness before
        starting automated analysis sequences.
        
        The function continuously polls module status and displays real-time
        progress when verbose mode is enabled. Modules must have both RunState="Idle"
        and empty NotReadyState_Description to be considered ready.
        
        Args:
            modules: List of module identifiers to check (default: ["CE1", "DAD1"])
                    Common modules: "CE1" (capillary electrophoresis), "DAD1" (detector)
            timeout: Maximum waiting time in seconds. None = wait indefinitely
                    Typical values: 10s (quick check), 60s (standard), 300s (long methods)
            verbose: Display real-time status updates during waiting (default: True)
        
        Returns:
            None (function returns when all modules ready)
        
        Raises:
            TimeoutError: If modules not ready within specified timeout period
            
        Examples:
            >>> # Quick readiness check before analysis
            >>> system.ready_to_start_analysis(timeout=10, verbose=False)
            >>> 
            >>> # Wait for CE and detector with status updates
            >>> system.ready_to_start_analysis(["CE1", "DAD1"], timeout=60)
            >>> 
            >>> # Wait indefinitely with progress display
            >>> system.ready_to_start_analysis(verbose=True)
            
        Note:
            Displays progress in top menu bar area when verbose=True. Modules
            must be both "Idle" and have no NotReady conditions to pass validation.
        """
        # Build command to query multiple modules with "|" separator
        command_parts = []
        for i, module in enumerate(modules):
            if i > 0:
                command_parts.append('"|"')
            command_parts.append(f'ObjHdrText$(RC{module}Status[1], "RunState")')
            command_parts.append('"|"')
            command_parts.append(f'ObjHdrText$(RC{module}Status[1], "NotReadyState_Description")')
        
        command = "response$ = " + ' + '.join(command_parts)
        
        start_time = time.time()
        
        while True:
            # Send command with retry logic for reliability
            response = None
            for attempt in range(3):
                try:
                    response = self.comm.send(command, 10)
                    break
                except TimeoutError:
                    if attempt == 2:
                        raise
            
            # Parse response with "|" delimiter
            values = response.split("|") if response else []
            
            all_ready = True
            module_states = []
            
            for i, module in enumerate(modules):
                idx = i * 2  # Each module has 2 values
                run_state = values[idx].strip() if idx < len(values) else "Unknown"
                not_ready_desc = values[idx + 1].strip() if idx + 1 < len(values) else ""
                
                # Build status for module
                if not_ready_desc and not_ready_desc != "":
                    status = f"{module}: {run_state} (NotReady: {not_ready_desc})"
                    all_ready = False  # CRITICAL: If any description, module not ready
                else:
                    status = f"{module}: {run_state}"
                    # Check if RunState is "Idle"
                    if run_state != "Idle":
                        all_ready = False
                
                module_states.append(status)
            
            # Display status if verbose=True
            if verbose:
                status_msg = f"Waiting for modules: {', '.join(module_states)}"
                print(f"\r{status_msg:<120}", end='', flush=True)
            
            # Check if all modules are ready
            if all_ready:
                if verbose:
                    # Clear status line
                    print(f"\r{' ' * 120}\r", end='', flush=True)
                time.sleep(2)
                return
            
            # Check overall timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    if verbose:
                        print()  # New line before error
                    raise TimeoutError(f"Instrument not ready for analysis within {timeout} second timeout. "
                                    f"Module states: {', '.join(module_states)}")
            
            # Wait before next attempt
            time.sleep(1)

    def add_register_reader(self, register_reader_macro: str = r"ChemstationAPI\controllers\macros\register_reader.mac") -> None:
        """Add comprehensive register inspection tool to ChemStation Debug menu.
        
        Add a powerful register browser tool in ChemStation's top menu bar
        that enables interactive inspection and modification of ChemStation registers.
        Invaluable for debugging, system analysis, advanced parameter editing,
        and understanding ChemStation's internal data structures.
        
        The register browser provides a user-friendly interface for exploring
        complex register hierarchies including RC.NET objects, sequence tables,
        method parameters, and system variables.
        
        Register Browser Features:
            - Browse all ChemStation registers (RC.NET, sequence, method, system)
            - Inspect object structures and data tables interactively
            - View and modify header values and text fields
            - Navigate complex register hierarchies with tree view
            - Export register contents for analysis
        
        Args:
            register_reader_macro: Path to register reader macro file.
                                  Default uses included comprehensive register_reader.mac
                                  
        Examples:
            >>> # Add register browser with default comprehensive tool
            >>> system.add_register_reader()
            >>> 
            >>> # Use custom register reader
            >>> system.add_register_reader("C:\\Custom\\debug_tools.mac")
            
        Usage:
            After execution, look for "Show Registers" item in ChemStation's
            Debug menu (top menu bar). Tool provides full register browsing
            capabilities for advanced users and developers.
            
        Note:
            Tool remains available until ChemStation restart. Exercise caution
            when modifying system registers as changes affect instrument operation.
        """
        path = Path(register_reader_macro).absolute()
        self.comm.send(f"macro \"{path}\"")

    def abort_run(self) -> None:
        """Immediately abort current analysis or sequence execution.
        
        Sends emergency abort command to ChemStation that immediately terminates
        the current analysis, sequence, or operation. Used for emergency stops,
        error recovery, or when immediate termination is required.
        
        The abort process immediately stops the current analysis phase, disables
        high voltage and pressure systems, and returns the instrument to a safe
        idle state. All method execution flags are cleared.
        
        Raises:
            SystemError: If abort command fails to execute
            
        Examples:
            >>> # Emergency stop
            >>> system.abort_run()
            >>> 
            >>> # Conditional abort on error detection
            >>> if error_detected:
            ...     system.abort_run()
            ...     print("Analysis aborted due to error")
            
        Warning:
            Results in immediate termination without post-run conditioning.
            Data up to abort point may be saved. Instrument requires manual
            return to ready state after abort.
        """
        self.comm.send("AbortRun")
        # Brief wait for abort completion and system stabilization
        time.sleep(2)

    def wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait for ChemStation to reach ready state for new analysis.
        
        Continuously polls system status until it reaches a state ready for
        new analysis (STANDBY or PRERUN) or until timeout expires. Essential
        for automated workflows that need to wait for instrument availability
        between analyses.
        
        Args:
            timeout: Maximum waiting time in seconds. Default 60 seconds.
                    Increase for methods with long post-run conditioning.
                    Typical values: 60s (standard), 300s (long methods), 600s (very long)
                    
        Returns:
            True if system reaches ready state within timeout,
            False if timeout expires before ready state achieved
            
        Examples:
            >>> # Standard workflow with timeout
            >>> if system.wait_for_ready():
            ...     api.method.run("NextSample")
            ... else:
            ...     print("Timeout - check instrument status")
            >>> 
            >>> # Extended wait for long conditioning methods
            >>> if system.wait_for_ready(timeout=300):  # 5 minutes
            ...     start_next_analysis()
            >>> 
            >>> # Sequence automation
            >>> for sample in sample_list:
            ...     if system.wait_for_ready(timeout=120):
            ...         process_sample(sample)
            
        Note:
            Polls status every second to minimize system load. Both STANDBY and
            PRERUN are considered ready states. Returns immediately if already ready.
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
        
        Returns the time elapsed since the actual separation phase began
        in the current analysis. Excludes pre-run conditioning, injection,
        and preparation phases - measures only electrophoretic separation runtime.
        
        Returns:
            Elapsed separation time in minutes as float. Returns 0.0 if no
            analysis is running or separation hasn't started yet.
            
        Examples:
            >>> # Monitor analysis progress
            >>> elapsed = system.get_elapsed_analysis_time()
            >>> total = system.get_analysis_time()
            >>> progress = (elapsed / total) * 100
            >>> print(f"Analysis {progress:.1f}% complete")
            >>> 
            >>> # Real-time monitoring with updates
            >>> while system.method_on():
            ...     elapsed = system.get_elapsed_analysis_time()
            ...     print(f"Running for {elapsed:.2f} minutes")
            ...     time.sleep(30)
            
        Note:
            Measures only separation phase, not total method time including
            conditioning. Updates in real-time with precision to 0.01 minutes.
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)

    def get_analysis_time(self) -> float:
        """Get total expected separation duration for current method.
        
        Returns the programmed separation duration from the currently loaded
        method's stoptime parameter. This represents the expected separation
        runtime and is used for progress calculations and time estimation.
        
        Returns:
            Total separation duration in minutes as float
            
        Examples:
            >>> # Calculate remaining time
            >>> total_time = system.get_analysis_time()
            >>> elapsed_time = system.get_elapsed_analysis_time()
            >>> remaining = total_time - elapsed_time
            >>> print(f"Analysis completes in {remaining:.2f} minutes")
            >>> 
            >>> # Check method duration before starting
            >>> duration = system.get_analysis_time()
            >>> if duration > 60:  # More than 1 hour
            ...     confirm = input(f"Long analysis ({duration:.1f}min). Continue? ")
            
        Note:
            Based on method's programmed stoptime parameter. Does not include
            conditioning or injection time. Remains constant during execution.
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime"))')
        return float(time_response)

    def get_remaining_analysis_time(self) -> float:
        """Get remaining separation time until current analysis completes.
        
        Calculates time remaining until separation phase completes by subtracting
        elapsed time from total expected duration. Provides real-time countdown
        for analysis completion and progress monitoring.
        
        Returns:
            Remaining separation time in minutes as float. Returns 0.0 if no
            analysis running. May be negative if analysis exceeds expected duration.
            
        Examples:
            >>> # Display countdown
            >>> remaining = system.get_remaining_analysis_time()
            >>> print(f"Analysis completes in {remaining:.1f} minutes")
            >>> 
            >>> # Progress monitoring with updates
            >>> while system.method_on():
            ...     remaining = system.get_remaining_analysis_time()
            ...     if remaining > 0:
            ...         print(f"Time remaining: {remaining:.2f} minutes")
            ...     time.sleep(60)
            >>> 
            >>> # Automated scheduling
            >>> if system.get_remaining_analysis_time() < 5:  # Less than 5 minutes
            ...     prepare_next_sample()
            
        Note:
            Updates continuously during analysis. Useful for progress bars
            and time estimation in automated workflows.
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime") - ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)