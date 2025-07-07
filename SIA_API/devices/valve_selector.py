"""
Valve selector controller - preserved from original implementation.
"""
from ..core.command_sender import CommandSender


class ValveSelector(CommandSender):
    """
    Class for controlling a valve selector via serial communication.
    
    Preserved from original implementation with minimal changes.
    """
    
    def __init__(self, port: str, num_positions: int = 8, prefix: str = "/Z", 
                 address: str = "", baudrate: int = 9600) -> None:
        """
        Initialize valve selector.
        
        Args:
            port (str): COM port for the selector connection.
            num_positions (int): Number of available positions.
            prefix (str): Command prefix used for communication.
            address (str): Device address.
            baudrate (int): Communication speed (default: 9600).
        """
        super().__init__(port=port, prefix=prefix, address=address, baudrate=baudrate)
        self.num_positions = num_positions

    def _set_number_positions(self):
        """Set number of positions on device."""
        self.send_command(f"NP{self.num_positions}")

    def position(self, position: int, num_attempts:int = 3) -> None:
        """
        Sets the valve to the specified position.
        
        Args:
            position (int): The target position for the valve.
            num_attepmt (int): Počet poslaných příkazů, někdy to dělá problém ,že se ototčí ventil až po 2 příkazu
        """
        if position < 1 or position > self.num_positions:
            raise ValueError(f"Position {position} is out of range (1-{self.num_positions})")
          
        for _ in range(num_attempts):
            self.send_command(f"GO{position}")