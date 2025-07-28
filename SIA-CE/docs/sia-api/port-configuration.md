# System Configuration

## Overview

System configuration centralizes all operational parameters - port assignments, volumes, flow rates, and vial positions - in one place for consistent settings across all workflow methods.

## Default Configuration

```python
@dataclass
class SystemConfig:
    # Port assignments
    waste_port: int = 1
    air_port: int = 2
    di_port: int = 3
    transfer_port: int = 4
    meoh_port: int = 5
    
    # System volumes (µL)
    holding_coil_volume: int = 1000
    transfer_line_volume: int = 550
    bubble_volume: int = 15
    
    # Flow rates (µL/min)
    speed_air: int = 5000
    speed_fast: int = 3500
    speed_normal: int = 2000
    speed_slow: int = 1500
    
    # Standard vial positions
    wash_vial: int = 48
    dry_vial: int = 49
    waste_vial: int = 50
```

## Custom Configuration

```python
from SIA_API.methods import create_custom_config

# Override specific parameters
custom_config = create_custom_config(
    waste_port=8,
    transfer_port=1,
    holding_coil_volume=1500,
    speed_normal=1800,
    wash_vial=47
)

# Use in workflow
workflow = PreparedSIAMethods(
    chemstation_controller=ce_api,
    syringe_device=syringe,
    valve_device=valve,
    ports_config=custom_config
)
```

## Key Parameters

**Ports:**
    - waste_port: Most frequent access (position 1 recommended)
    - air_port: Segmentation and cleaning
    - transfer_port: Connection to analytical instrument
    - di_port/meoh_port: Primary solvents

**Volumes:**
- holding_coil_volume: Tube between syringe and valve (500-2000 µL)
- transfer_line_volume: Dead volume to dispensing point (measure experimentally)
- bubble_volume: Air separation bubbles (10-50 µL)

**Speeds:**
- speed_air: Fast air operations (5000 µL/min)
- speed_fast: Rapid transfers (3500 µL/min) 
- speed_normal: Standard dispensing (2000 µL/min)
- speed_slow: Precise operations (1500 µL/min)

**Vials:**
- wash_vial: Needle cleaning (typically 48)
- waste_vial: System waste collection (typically 50)

## Configuration Validation

```python
from SIA_API.methods import validate_config

try:
    validate_config(custom_config)
except ValueError as e:
    print(f"Configuration error: {e}")
```

Checks for duplicate ports, valid ranges, and parameter consistency.