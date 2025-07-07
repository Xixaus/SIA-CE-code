"""
Zjednodušená konfigurace portů pro SIA systém.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PortConfig:
    """Konfigurace portů pro SIA systém."""
    waste_port: int = 1          # Port pro odpad
    air_port: int = 2            # Port pro vzduch  
    di_port: int = 3             # Port pro deionizovanou vodu
    transfer_port: int = 4       # Port pro transfer linku
    meoh_port: int = 5           # Port pro methanol


# Výchozí konfigurace
DEFAULT_PORTS = PortConfig()


def create_custom_config(**kwargs) -> PortConfig:
    """
    Vytvoří vlastní konfiguraci portů.
    
    Args:
        **kwargs: Parametry pro nastavení portů (waste_port, air_port, di_port, 
                 transfer_port, meoh_port)
    
    Returns:
        PortConfig: Konfigurovaný objekt s porty
    
    Example:
        # Pro systém kde je MeOH na portu 6 a odpad na portu 8
        config = create_custom_config(waste_port=8, meoh_port=6)
    """
    return PortConfig(**kwargs)


def validate_config(config: PortConfig) -> bool:
    """
    Validuje konfiguraci portů.
    
    Args:
        config: Konfigurace k validaci
        
    Returns:
        bool: True pokud je konfigurace validní
        
    Raises:
        ValueError: Pokud konfigurace není validní
    """
    ports = [config.waste_port, config.air_port, config.di_port, 
             config.transfer_port, config.meoh_port]
    
    # Kontrola duplicitních portů
    if len(ports) != len(set(ports)):
        raise ValueError("Porty nesmí být duplicitní")
    
    # Kontrola rozsahu portů
    if not all(1 <= port <= 12 for port in ports):
        raise ValueError("Porty musí být v rozsahu 1-12")
    
    return True