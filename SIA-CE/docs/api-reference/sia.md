# SIA API Reference

Complete API documentation for Sequential Injection Analysis control.

## SyringeController

Syringe pump control for precise liquid handling.

### Constructor

```python
SyringeController(
    port: str,
    syringe_size: int,
    address: str = "/1",
    prefix: str = "",
    baudrate: int = 9600,
    print_info: bool = True
)
```

**Parameters:**
- `port`: COM port (e.g., "COM3")
- `syringe_size`: Volume in microliters (100-5000)
- `address`: Device address (default: "/1")
- `prefix`: Command prefix for protocols
- `baudrate`: Serial speed (default: 9600)
- `print_info`: Display specifications on init

**Example:**
```python
from SIA_API.devices import SyringeController

syringe = SyringeController(port="COM3", syringe_size=1000)
```

### Attributes

- `syringe_size`: Syringe capacity in µL
- `volume_counter`: Current volume in syringe
- `VALVE_TYPES_DICT`: Supported valve configurations

### Methods

#### initialize()

Initialize syringe to home position.

```python
syringe.initialize() -> None
```

**Effects:**
- Moves to absolute zero position
- Resets volume counter to 0
- Uses Z/Z1/Z2 command based on size

#### aspirate()

Draw fluid into syringe.

```python
syringe.aspirate(volume: Optional[float] = None, wait: bool = True) -> None
```

**Parameters:**
- `volume`: Volume in µL (None = fill completely)
- `wait`: Block until complete

**Raises:**
- `ValueError`: If volume exceeds capacity

**Example:**
```python
syringe.aspirate(500)    # Draw 500 µL
syringe.aspirate()       # Fill entire syringe
```

#### dispense()

Expel fluid from syringe.

```python
syringe.dispense(volume: Optional[float] = None, wait: bool = True) -> None
```

**Parameters:**
- `volume`: Volume in µL (None = empty completely)
- `wait`: Block until complete

**Raises:**
- `ValueError`: If volume exceeds current content

#### set_speed_uL_min()

Set flow rate.

```python
syringe.set_speed_uL_min(speed: float) -> None
```

**Parameters:**
- `speed`: Flow rate in µL/min

**Limits:**
- Minimum: 0.05 × syringe_size
- Maximum: 60 × syringe_size

#### configuration_valve_type()

Configure attached valve type.

```python
syringe.configuration_valve_type(valve_type: str) -> None
```

**Parameters:**
- `valve_type`: Type from VALVE_TYPES_DICT

**Options:**
- 'No', '3-Port', '4-Port', '6-Port distribution', etc.

#### Valve Control

```python
syringe.valve_in() -> None    # Switch to input
syringe.valve_out() -> None   # Switch to output  
syringe.valve_up() -> None    # Switch to up/bypass
```

#### Utility Methods

```python
syringe.wait_for_syringe()           # Wait for operation
syringe.print_volume_in_syringe()    # Display current volume
```

---

## ValveSelector

Multi-position valve control for fluid routing.

### Constructor

```python
ValveSelector(
    port: str,
    num_positions: int = 8,
    prefix: str = "/Z",
    address: str = "",
    baudrate: int = 9600
)
```

**Parameters:**
- `port`: COM port (e.g., "COM4")
- `num_positions`: Number of valve positions
- `prefix`: Command prefix (default: "/Z")
- `address`: Device address (usually empty)
- `baudrate`: Serial speed

**Example:**
```python
from SIA_API.devices import ValveSelector

valve = ValveSelector(port="COM4", num_positions=8)
```

### Methods

#### position()

Move valve to position.

```python
valve.position(position: int, num_attempts: int = 3) -> None
```

**Parameters:**
- `position`: Target position (1 to num_positions)
- `num_attempts`: Retry attempts for reliability

**Raises:**
- `ValueError`: If position out of range

---

## PreparedSIAMethods

High-level workflows for automated procedures.

### Constructor

```python
PreparedSIAMethods(
    chemstation_controller,
    syringe_device: SyringeController,
    valve_device: ValveSelector,
    ports_config: Optional[PortConfig] = None
)
```

**Parameters:**
- `chemstation_controller`: ChemStation API instance
- `syringe_device`: Initialized syringe controller
- `valve_device`: Initialized valve selector
- `ports_config`: Port configuration (default if None)

**Example:**
```python
from SIA_API.methods import PreparedSIAMethods

workflow = PreparedSIAMethods(ce_api, syringe, valve)
```

### System Methods

#### system_initialization_and_cleaning()

Complete system initialization.

```python
workflow.system_initialization_and_cleaning(
    waste_vial: int = 50,
    bubble: int = 20,
    **port_overrides
) -> None
```

**Parameters:**
- `waste_vial`: Vial for waste collection
- `bubble`: Separating bubble size (µL)
- `**port_overrides`: Override default ports

**Process:**
1. Syringe initialization
2. Loop flushing
3. Methanol cleaning
4. DI water rinse
5. Transfer line conditioning

### Continuous Flow Methods

#### prepare_continuous_flow()

Setup for continuous dispensing.

```python
workflow.prepare_continuous_flow(
    solvent_port: int,
    waste_vial: int = 50,
    bubble_volume: int = 10,
    solvent_holding_coil_volume: int = 10,
    transfer_coil_flush: int = 500,
    holding_coil_flush: int = 1000,
    speed: int = 1500,
    **port_overrides
) -> None
```

**Parameters:**
- `solvent_port`: Port with solvent
- `waste_vial`: Waste collection vial
- `bubble_volume`: Air bubble size
- `solvent_holding_coil_volume`: Solvent at coil end
- `transfer_coil_flush`: Transfer line flush volume
- `holding_coil_flush`: Holding coil flush volume
- `speed`: Flow rate (µL/min)

#### continuous_fill()

Execute continuous filling.

```python
workflow.continuous_fill(
    vial: int,
    volume: int,
    solvent_port: int,
    flush_needle: Optional[int] = None,
    wash_vial: int = 48,
    speed: int = 2000,
    **port_overrides
) -> None
```

**Parameters:**
- `vial`: Target vial (1-50)
- `volume`: Dispensing volume (µL)
- `solvent_port`: Solvent source port
- `flush_needle`: Needle wash volume
- `wash_vial`: Vial for washing
- `speed`: Dispensing speed

### Batch Flow Methods

#### prepare_batch_flow()

Setup for batch dispensing.

```python
workflow.prepare_batch_flow(
    solvent_port: int,
    waste_vial: int = 50,
    bubble_volume: int = 10,
    transfer_coil_volume: int = 300,
    coil_flush: int = 150,
    speed: int = 1500,
    **port_overrides
) -> None
```

#### batch_fill()

Execute batch filling.

```python
workflow.batch_fill(
    vial: int,
    volume: int,
    solvent_port: int,
    transfer_line_volume: int = 300,
    bubble_volume: int = 10,
    flush_needle: Optional[int] = None,
    speed: int = 2000,
    unload: bool = True,
    wait: Optional[int] = None,
    **port_overrides
) -> None
```

**Additional Parameters:**
- `transfer_line_volume`: Volume of transfer line
- `unload`: Return vial after filling
- `wait`: Wait time after dispensing (seconds)

### Sample Processing

#### homogenize_sample()

Mix sample using pneumatic agitation.

```python
workflow.homogenize_sample(
    vial: int,
    speed: int,
    homogenization_time: float,
    flush_needle: Optional[int] = None,
    unload: bool = True,
    air_speed: int = 5000,
    **port_overrides
) -> None
```

**Parameters:**
- `vial`: Target vial
- `speed`: Bubbling speed (µL/min)
- `homogenization_time`: Duration (seconds)
- `flush_needle`: Needle wash volume
- `unload`: Return vial when done
- `air_speed`: Air aspiration speed

#### clean_needle()

Clean dispensing needle.

```python
workflow.clean_needle(
    volume_flush: float,
    wash_vial: int = 48
) -> None
```

### Utility Methods

```python
workflow.load_to_replenishment(vial_number: int) -> None
workflow.unload_from_replenishment() -> None
```

---

## Configuration

### PortConfig

Port assignment configuration.

```python
from SIA_API.methods import PortConfig

@dataclass
class PortConfig:
    waste_port: int = 1
    air_port: int = 2  
    di_port: int = 3
    transfer_port: int = 4
    meoh_port: int = 5
```

### create_custom_config()

Create custom port configuration.

```python
from SIA_API.methods import create_custom_config

config = create_custom_config(
    waste_port=8,
    air_port=1,
    di_port=2,
    transfer_port=3,
    meoh_port=4
)
```

---

## CommandSender

Base class for serial communication.

### Constructor

```python
CommandSender(
    port: str,
    prefix: str = "",
    address: str = "",
    baudrate: int = 9600
)
```

### Methods

#### send_command()

Send command with optional response.

```python
send_command(
    command: str,
    wait_for_completion: callable = None,
    get_response: bool = False,
    response_timeout: float = 3
) -> Optional[str]
```

**Parameters:**
- `command`: Command string
- `wait_for_completion`: Function to call while waiting
- `get_response`: Capture device response
- `response_timeout`: Response wait time

---

## Common Usage Patterns

### Basic Liquid Transfer

```python
# Simple transfer
def transfer(source, dest, volume):
    valve.position(source)
    syringe.aspirate(volume)
    valve.position(dest)
    syringe.dispense(volume)

transfer(3, 6, 500)  # 500 µL from port 3 to 6
```

### Dilution Series

```python
# Create 1:2 dilution series
def dilution_series(stock_port, vials, diluent_port=3):
    for i, vial in enumerate(vials):
        # Add diluent
        workflow.batch_fill(
            vial=vial,
            volume=500,
            solvent_port=diluent_port
        )
        
        # Add stock (manual or automated)
        if i == 0:
            # First vial - add from stock
            stock_volume = 500
        else:
            # Serial dilution from previous
            stock_volume = 500
            # Transfer from vials[i-1]
```

### Multi-Solvent Preparation

```python
# Different solvents for different samples
preparations = [
    (10, 3, 1000),  # Vial 10: 1000 µL water
    (11, 5, 750),   # Vial 11: 750 µL methanol
    (12, 6, 500),   # Vial 12: 500 µL buffer
]

for vial, port, volume in preparations:
    workflow.prepare_batch_flow(solvent_port=port)
    workflow.batch_fill(vial=vial, volume=volume, solvent_port=port)
```

### Error Handling

```python
try:
    syringe.aspirate(1500)  # Too much!
except ValueError as e:
    print(f"Volume error: {e}")
    # Handle overflow
    
try:
    valve.position(15)  # Invalid position
except ValueError as e:
    print(f"Position error: {e}")
```

### System State Management

```python
class SIASystem:
    def __init__(self):
        self.syringe = SyringeController("COM3", 1000)
        self.valve = ValveSelector("COM4", 8)
        self.current_solvent = None
    
    def switch_solvent(self, new_solvent_port):
        if self.current_solvent != new_solvent_port:
            # Flush system
            self.flush_line()
            self.current_solvent = new_solvent_port
```

## Performance Tips

1. **Speed Optimization**
   - Air: 5000 µL/min
   - Water: 3500 µL/min
   - Organic: 2500 µL/min
   - Viscous: 1000 µL/min

2. **Volume Efficiency**
   - Minimize dead volumes
   - Use air gaps for separation
   - Plan aspiration order

3. **Error Prevention**
   - Always initialize first
   - Track volume state
   - Validate before operations

4. **Maintenance**
   - Regular system flush
   - Clean after viscous samples
   - Check for air bubbles