"""
Valve selector controller for multi-position valve automation.

Provides precise control of multi-position valve selectors commonly used
in analytical automation and flow injection systems.
"""
from ..core.command_sender import CommandSender


class ValveSelector(CommandSender):
    """
    Control multi-position valve selectors for automated fluid routing.
    
    Supports VICI and compatible valve selectors with 2-12 positions.
    Provides reliable positioning with automatic retry and validation.
    
    Attributes:
        num_positions (int): Number of valve positions available
    
    Examples:
        Basic valve control:
        
        >>> valve = ValveSelector(port="COM4", num_positions=8)
        >>> valve.position(1)  # Move to position 1
        >>> valve.position(5)  # Move to position 5
        
        Custom configuration:
        
        >>> valve = ValveSelector(
        ...     port="COM4", 
        ...     num_positions=6,
        ...     prefix="/Z",
        ...     baudrate=19200
        ... )
    """
    
    def __init__(self, port: str, num_positions: int = 8, prefix: str = "/Z", 
                 address: str = "", baudrate: int = 9600) -> None:
        """
        Initialize valve selector controller.
        
        Args:
            port: COM port for valve selector (e.g., "COM4")
            num_positions: Number of valve positions
            prefix: Command prefix for valve protocol (default: "/Z")
            address: Device address (usually empty for valve selectors)
            baudrate: Serial communication speed (default: 9600)
            
        Raises:
            ValueError: If num_positions is outside valid range
            SerialException: If COM port cannot be opened
            
        Note:
            Most VICI valve selectors use "/Z" prefix and empty address.
            Some models may require different communication parameters.
        """
        super().__init__(port=port, prefix=prefix, address=address, baudrate=baudrate)
        self.num_positions = num_positions

    def _set_number_positions(self):
        """
        Configure number of positions on valve device.
        
        Sends configuration command to valve to set the number of
        available positions. This may be required for some valve models.
        """
        self.send_command(f"NP{self.num_positions}")

    def position(self, position: int, num_attempts: int = 3) -> None:
        """
        Move valve to specified position.
        
        Args:
            position: Target position (1 to num_positions)
            num_attempts: Number of command attempts for reliability
            
        Raises:
            ValueError: If position is outside valid range
            
        Note:
            Multiple attempts help ensure reliable valve positioning,
            as some valves may not respond to the first command.
            
        Examples:
            >>> valve.position(1)          # Move to position 1
            >>> valve.position(8, num_attempts=5)  # Extra attempts for reliability
        """
        if position < 1 or position > self.num_positions:
            raise ValueError(f"Position {position} is out of range (1-{self.num_positions})")
          
        for _ in range(num_attempts):
            self.send_command(f"GO{position}")