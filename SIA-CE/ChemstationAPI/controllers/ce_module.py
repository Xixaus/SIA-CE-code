"""
CE Module - Agilent 7100 Capillary Electrophoresis Instrument Control.

Controls sample handling, capillary conditioning, and pressure operations.

Hardware:
    - Carousel: 50 positions (1-48 samples, 49-50 parking)
    - Lift positions: inlet (positive electrode), outlet (ground), replenishment
    - Pressure: ±100 mbar injection, ~950 mbar flushing

Operational Constraints:
    - Carousel blocked when: doors open, pressure operations active
    - Carousel available only during: voltage application (analysis runtime)
    - DANGER: Never remove inlet/outlet vials during voltage - instrument damage risk

.. moduleauthor:: Richard Maršala
"""

import time
from tqdm import tqdm

from ..core.chemstation_communication import ChemstationCommunicator
from ..exceptions import *
from .validation import ValidationModule

MODULE = "CE1"


class CEModule():
    """Agilent 7100 CE instrument control for vial handling and capillary operations.
    
    Provides high-level interface for controlling the CE instrument's sample handling
    system, capillary conditioning, and pressure operations. Manages the 50-position
    carousel and three lift positions through ChemStation communication.
    
    The system operates under strict safety constraints where carousel operations
    are only available during voltage application (analysis runtime) and completely
    blocked during pressure operations or when instrument doors are open.
    
    Vial States:
        - "carousel": In tray position, ready for loading
        - "inlet": At inlet lift (sample/buffer introduction, positive electrode)
        - "outlet": At outlet lift (waste/collection, ground electrode)  
        - "replenishment": At replenishment lift (buffer system maintenance)
        - "out_system": Not detected in system
    
    Attributes:
        comm: ChemStation communicator for sending commands to CE1 module
        validation: Input validation and system state checking module
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize CE module with ChemStation communicator.
        
        Args:
            communicator: ChemStation communication interface for sending
                         commands and receiving responses from CE1 module
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
    
    def load_vial_to_position(self, vial: int, position: str = "replenishment") -> None:
        """Load vial from carousel to specified lift position.
        
        Transfers a vial from its carousel slot to one of the three lift positions
        for CE operations. The system automatically rotates the carousel to bring
        the vial to the front and lifts it to the target position. Includes
        automatic vial presence verification and mechanical stabilization time.
        
        Args:
            vial: Carousel position number (1-48 for samples, 49 for parking)
            position: Target lift position:
                     - "inlet": Sample injection, positive electrode contact
                     - "outlet": Waste collection, negative electrode (ground)
                     - "replenishment": Buffer system maintenance
                     
        Raises:
            VialError: If vial not present in carousel or loading operation fails
            ValueError: If invalid position specified
            SystemError: If carousel unavailable (doors open or pressure operations active)
            
        Examples:
            >>> # Load sample for analysis
            >>> ce.load_vial_to_position(15, "inlet")
            >>> # Load waste collection vial  
            >>> ce.load_vial_to_position(20, "outlet")
            
        Note: 
            Carousel operations only work during voltage application (analysis runtime).
            Completely blocked during pressure operations (injection, conditioning, flushing).
        """
        position_commands = {
            "inlet": "INLT", "outlet": "OUTL", "replenishment": "LRPL"
        }
        
        if position not in position_commands:
            raise ValueError(f"Invalid position: {position}")

        start_position = self.get_vial_state(vial)
        if start_position == "out_system":
            raise VialError(f"Vial {vial} not present in carousel")
        elif start_position == position:
            return
        
        self.validation.validate_use_carousel()

        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command} {vial}"')
        
        # Wait for completion with timeout
        for _ in range(10):
            if self.get_vial_state(vial) == position:
                time.sleep(1.5)
                return
            time.sleep(1)

        raise VialError(f"Failed to load vial {vial} to {position}")

    def unload_vial_from_position(self, position: str = "replenishment") -> None:
        """Return vial from lift position back to its original carousel slot.
        
        Lowers the vial from the specified lift position and returns it to its
        original carousel position. The system automatically identifies which
        vial number to return based on the current lift position contents.
        
        Args:
            position: Lift position to unload from:
                     - "inlet": Return sample vial
                     - "outlet": Return waste vial  
                     - "replenishment": Return buffer vial
        
        Raises:
            ValueError: If invalid position specified
                     
        Examples:
            >>> # Return vials after analysis completion
            >>> ce.unload_vial_from_position("inlet")
            >>> ce.unload_vial_from_position("outlet")
            
        Warning: 
            NEVER unload inlet or outlet vials during voltage application!
            This can cause severe electrical damage to the instrument's electrode system.
            Replenishment vials can be safely unloaded during voltage application.
        """
        position_commands = {
            "inlet": "RINL", "outlet": "ROUT", "replenishment": "RRPL"
        }
        
        if position not in position_commands:
            raise ValueError(f"Invalid position: {position}")
        
        command = position_commands[position]
        self.comm.send(f'WriteModule "{MODULE}", "{command}"')
        time.sleep(3)

    def get_vial_state(self, vial: int) -> str:
        """Get current position and state of a vial within the CE system.
        
        Queries the instrument hardware to determine the real-time location
        of a specific vial. Essential for tracking sample positions and
        validating system state before operations.
        
        Args:
            vial: Vial position number to check (1-50)
            
        Returns:
            Current vial state:
            - "carousel": Available in tray position, ready for loading
            - "inlet": At inlet lift (sample/buffer introduction)
            - "outlet": At outlet lift (waste/collection)
            - "replenishment": At replenishment lift (buffer maintenance)
            - "out_system": Not detected anywhere in the system
            
        Raises:
            ValueError: If vial number outside valid range (1-50)
            SystemError: If unable to query vial state from instrument
            
        Examples:
            >>> # Check sample preparation status
            >>> if ce.get_vial_state(15) == "inlet":
            ...     print("Sample ready for injection")
            >>> # Monitor multiple vials
            >>> for vial in [10, 11, 12]:
            ...     print(f"Vial {vial}: {ce.get_vial_state(vial)}")
        """
        if not (1 <= vial <= 50):
            raise ValueError(f"Vial {vial} outside range 1-50")
        
        state_response = self.comm.send(f'response$ = SendModule$("{MODULE}", "TRAY:GETVIALSTATE? {vial}")')
        state_code = state_response[-1]
        
        state_mapping = {
            "0": "carousel", "1": "inlet", "2": "outlet", 
            "3": "replenishment", "4": "out_system"
        }
        
        return state_mapping.get(state_code, "unknown")

    def flush_capillary(self, time_flush: float, wait: bool = True) -> None:
        """Perform high-pressure capillary conditioning flush.
        
        Executes capillary conditioning using maximum internal pressure (~950 mbar)
        to remove air bubbles, clean contaminants, and condition the capillary surface.
        Buffer is drawn from the inlet vial and expelled through the outlet.
        
        Args:
            time_flush: Flush duration in seconds.
            wait: If True, shows progress bar and waits for completion.
                  If False, starts flush operation and returns immediately.
                  
        Raises:
            ValueError: If flush time is not positive

        Requirements:
            - Buffer vial must be loaded at inlet position
            - Adequate buffer volume for specified flush duration
            
        Note: 
            Uses maximum system pressure (~950 mbar). Carousel completely
            blocked during operation due to active pressure application.
        """
        if time_flush <= 0:
            raise ValueError("Flush time must be positive")
        
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_flush},-2,-2"')

        if wait:
            for _ in tqdm(range(int(time_flush)), desc="Flushing capillary", unit="sec"):
                time.sleep(1)

    def apply_pressure_to_capillary(self, pressure: float, time_pressure: float, wait: bool = True) -> None:
        """Apply precise pressure to capillary for controlled operations.
        
        Provides exact pressure control for sample injection, gentle conditioning,
        or specialized treatments. Unlike flush_capillary(), allows precise pressure
        specification within the safe operating range. Commonly used for hydrodynamic
        sample injection where pressure directly affects injected sample volume.
        
        Args:
            pressure: Pressure in mbar (range: -100 to +100)
                     - Positive: Pushes liquid from inlet toward outlet
                     - Negative: Creates vacuum, pulls liquid toward inlet
            time_pressure: Duration of pressure application in seconds
            wait: If True, shows progress bar and waits for completion.
                  If False, starts pressure and returns immediately.
                 
        Raises:
            ValueError: If pressure outside safe range (±100 mbar) or time not positive
            
        Note: 
            Injection pressure directly affects sample volume and peak shape.
            Carousel blocked during pressure application - position vials beforehand.
        """
        if not (-100 <= pressure <= 100):
            raise ValueError(f"Pressure {pressure} outside range ±100 mbar")
        if time_pressure <= 0:
            raise ValueError("Pressure time must be positive")
        
        self.comm.send(f'WriteModule "{MODULE}", "FLSH {time_pressure}, {pressure},-2,-2"')
        
        if wait:
            pressure_type = "vacuum" if pressure < 0 else "pressure"
            desc = f"Applying {pressure_type} ({pressure:+.0f} mbar)"
            for _ in tqdm(range(int(time_pressure)), desc=desc, unit="sec"):
                time.sleep(1)