"""
ChemStation Module - System monitoring and status management.

This module provides functionality for monitoring ChemStation system status,
getting information about current methods and sequences, and waiting for
analysis completion.

.. moduleauthor:: Richard Maršala
"""

import time
import os

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator

class SystemModule():
    """System monitoring and status management for ChemStation.
    
    Provides information about system status and adds tools for working with
    registers. This module allows monitoring of method execution, system status,
    and provides utilities for debugging and system control.
    
    Attributes:
        Inherits all attributes from ChemstationCommunicator.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize the system monitoring module.
        
        Args:
            config: Communication configuration for ChemStation connection.
        """
        self.comm = communicator

        
    def method_on(self) -> bool:
        """Check if a method is currently running.
        
        Returns:
            True if a method is running, False otherwise.
            
        Example:
            >>> system = SystemModule()
            >>> if system.method_on():
            ...     print("Method is running")
        """
        state = self.comm.send("response$ = VAL$(_MethodOn)")
        return state == "1"

    def status(self) -> str:
        """Get the current acquisition status.
        
        Returns:
            Current acquisition status string (e.g., "STANDBY", "PRERUN", "RUN").
            
        Example:
            >>> system = SystemModule()
            >>> status = system.status()
            >>> print(f"Current status: {status}")
        """
        return self.comm.send("response$ = ACQSTATUS$")

    def RC_status(self, module="CE1"):

        return self.comm.send(f'response$ = ObjHdrText$(RC{module}Status[1], "RunState")')

    def add_register_reader(self, register_reader_macro: str = r"controllers\macros\register_reader.mac") -> None:
        """Add a register reader tool to the top menu.
        
        Adds a Debug/Show Registers tool to the ChemStation interface for
        browsing and modifying registers.
        
        Args:
            register_reader_macro: Path to the register reader macro file.
            
        Example:
            >>> system = SystemModule()
            >>> system.add_register_reader()
        """
        path = os.path.abspath(register_reader_macro)
        self.comm.send(f"macro {path}")

    def abort_run(self) -> None:
        """Immediately abort the running analysis or sequence.
        
        Sends an abort command to ChemStation and waits for completion.
        
        Example:
            >>> system = SystemModule()
            >>> system.abort_run()
        """
        self.comm.send("AbortRun")
        # Wait for abort completion
        time.sleep(2)

    def wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait until ChemStation is ready for analysis.
        
        Args:
            timeout: Maximum waiting time in seconds.
            
        Returns:
            True if system is ready, False on timeout.
            
        Example:
            >>> system = SystemModule()
            >>> if system.wait_for_ready(timeout=120):
            ...     print("System is ready")
            ... else:
            ...     print("Timeout waiting for system")
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.status() in ["STANDBY", "PRERUN"]:
                return True
            time.sleep(1)
        return False

    def get_elapsed_analysis_time(self) -> float:
        """Get the elapsed time since analysis started.
        
        Returns the time that has passed since the actual analysis began,
        excluding preparation, injection, and other pre-analysis steps.
        Only measures the separation/analysis phase runtime.
        
        Returns:
            float: Elapsed analysis time in minutes.
            
        Example:
            >>> system = SystemModule()
            >>> elapsed = system.get_elapsed_analysis_time()
            >>> print(f"Analysis has been running for {elapsed:.2f} minutes")
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)

    def get_analysis_time(self) -> float:
        """Get the total expected duration of the current analysis.
        
        Returns the total time that the current analysis method is expected
        to take for completion. This covers only the separation/analysis phase,
        excluding preparation, injection, and post-processing steps.
        
        Returns:
            float: Total analysis duration in minutes.
            
        Example:
            >>> system = SystemModule()
            >>> total_time = system.get_total_analysis_time()
            >>> elapsed_time = system.get_elapsed_analysis_time()
            >>> remaining = total_time - elapsed_time
            >>> print(f"Analysis will complete in {remaining:.2f} minutes")
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime"))')
        return float(time_response)

    def get_remaining_analysis_time(self) -> float:
        """Get the remaining time until analysis completion.
        
        Calculates the time remaining until the current analysis is finished
        by subtracting elapsed time from total analysis duration.
        
        Returns:
            float: Remaining analysis time in minutes.
            
        Example:
            >>> system = SystemModule()
            >>> remaining = system.get_remaining_analysis_time()
            >>> print(f"Analysis will complete in {remaining:.2f} minutes")
        """
        time_response = self.comm.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "MethodRuntime") - ObjHdrVal(RCCE1Status[1], "Runtime"))')
        return float(time_response)