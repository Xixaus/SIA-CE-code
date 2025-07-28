# ChemStation API Reference

Complete API documentation for the ChemStation control interface.

## ChemstationAPI

Main API controller class providing unified access to all ChemStation functionality.

### Constructor

```python
ChemstationAPI(config: Optional[CommunicationConfig] = None)
```

**Parameters:**
- `config`: Communication configuration settings. If None, uses default configuration.

**Raises:**
- `ConfigurationError`: If communication setup fails
- `ConnectionError`: If ChemStation connection test fails

**Example:**
```python
from ChemstationAPI import ChemstationAPI

# Default configuration
api = ChemstationAPI()

# Custom configuration
from ChemstationAPI.core.communication_config import CommunicationConfig
config = CommunicationConfig(verbose=True, timeout=10.0)
api = ChemstationAPI(config)
```

### Attributes

- `ce`: CE module for instrument control
- `method`: Methods module for method management
- `sequence`: Sequence module for batch operations
- `system`: System module for status monitoring
- `validation`: Validation module for checks

### Core Method

#### send()

Send command directly to ChemStation Command Processor.

```python
send(command: str, timeout: float = 5.0) -> Optional[str]
```

**Parameters:**
- `command`: ChemStation CP command string
- `timeout`: Maximum wait time in seconds

**Returns:**
- Response string if command starts with "response$ = ", otherwise None

**Example:**
```python
# Get value
voltage = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Voltage_actual"))')

# Execute command
api.send('LoadMethod _METHPATH$, "MyMethod.M"')
```

---

## CE Module

Capillary Electrophoresis instrument control.

### Methods

#### load_vial_to_position()

Load vial from carousel to lift position.

```python
ce.load_vial_to_position(vial: int, position: str = "replenishment") -> None
```

**Parameters:**
- `vial`: Carousel position (1-49)
- `position`: Target position ("inlet", "outlet", "replenishment")

**Raises:**
- `VialError`: If vial not present
- `ValueError`: If invalid position

**Example:**
```python
api.ce.load_vial_to_position(15, "inlet")
```

#### unload_vial_from_position()

Return vial from lift position to carousel.

```python
ce.unload_vial_from_position(position: str = "replenishment") -> None
```

**Parameters:**
- `position`: Lift position to unload from

#### get_vial_state()

Get current vial location.

```python
ce.get_vial_state(vial: int) -> str
```

**Returns:**
- "carousel", "inlet", "outlet", "replenishment", or "out_system"

#### flush_capillary()

Perform high-pressure capillary flush.

```python
ce.flush_capillary(time_flush: float, wait: bool = True) -> None
```

**Parameters:**
- `time_flush`: Flush duration in seconds
- `wait`: Block until complete

#### apply_pressure_to_capillary()

Apply specific pressure for injection or conditioning.

```python
ce.apply_pressure_to_capillary(pressure: float, time_pressure: float, wait: bool = True) -> None
```

**Parameters:**
- `pressure`: Pressure in mbar (-100 to +100)
- `time_pressure`: Duration in seconds
- `wait`: Block until complete

---

## Methods Module

CE method management and execution.

### Methods

#### load()

Load CE method from file.

```python
method.load(method_name: str, method_path: str = "_METHPATH$") -> None
```

**Parameters:**
- `method_name`: Method filename without .M extension
- `method_path`: Directory path (default: ChemStation method directory)

**Raises:**
- `MethodError`: If method cannot be loaded
- `ValidationError`: If method doesn't exist

#### save()

Save current method.

```python
method.save(method_name: str = "_METHFILE$", method_path: str = "_METHPATH$", 
           comment: str = "\" \"") -> None
```

**Parameters:**
- `method_name`: Filename for saved method
- `method_path`: Save directory
- `comment`: Optional method comment

#### run()

Execute current method.

```python
method.run(data_name: str, data_dir: str = "_DATAPATH$") -> None
```

**Parameters:**
- `data_name`: Name for data file
- `data_dir`: Data storage directory

#### execution_method_with_parameters()

Execute method with custom parameters.

```python
method.execution_method_with_parameters(
    vial: int, 
    method_name: str,
    sample_name: str = "", 
    comment: str = "",
    subdirectory_name: str = ""
) -> None
```

**Parameters:**
- `vial`: Sample vial position
- `method_name`: Method to execute
- `sample_name`: Sample identifier
- `comment`: Analysis comment
- `subdirectory_name`: Data subdirectory

---

## Sequence Module

Batch analysis management.

### Methods

#### load_sequence()

Load sequence from file.

```python
sequence.load_sequence(seq_name: str, seq_dir: str = "_SEQPATH$") -> None
```

#### save_sequence()

Save current sequence.

```python
sequence.save_sequence(seq_name: str = "_SEQFILE$", seq_dir: str = "_SEQPATH$") -> None
```

#### modify_sequence_row()

Modify sequence table row.

```python
sequence.modify_sequence_row(
    row: int,
    vial_sample: str = "",
    method: str = "",
    sample_name: str = "",
    sample_info: str = "",
    data_file_name: str = ""
) -> None
```

**Parameters:**
- `row`: Row number (1-based)
- Other parameters: Optional updates (empty = no change)

#### prepare_sequence_table()

Import sequence from Excel.

```python
sequence.prepare_sequence_table(
    excel_file_path: str,
    sequence_name: str = None,
    sheet_name: int = 0,
    vial_column: str = None,
    method_column: str = None,
    sample_name_column: str = None,
    sample_info_column: str = None,
    filename_column: str = None,
    replicate_column: str = None
) -> None
```

**Parameters:**
- `excel_file_path`: Path to Excel file
- `sequence_name`: Sequence to load first
- `sheet_name`: Worksheet index
- Column parameters: Excel column names

#### Sequence Control

```python
sequence.start() -> None     # Start sequence execution
sequence.pause() -> None     # Pause after current sample
sequence.resume() -> None    # Resume paused sequence
```

---

## System Module

System status monitoring and control.

### Methods

#### method_on()

Check if method is running.

```python
system.method_on() -> bool
```

**Returns:**
- True if method executing, False if idle

#### status()

Get acquisition status.

```python
system.status() -> str
```

**Returns:**
- "STANDBY", "PRERUN", "RUN", "POSTRUN", "ERROR", "ABORT"

#### RC_status()

Get RC module status.

```python
system.RC_status(module: str = "CE1") -> str
```

**Returns:**
- "Idle", "Run", "NotReady", "Error", "Maintenance"

#### wait_for_ready()

Wait for system ready state.

```python
system.wait_for_ready(timeout: int = 60) -> bool
```

**Parameters:**
- `timeout`: Maximum wait time in seconds

**Returns:**
- True if ready within timeout, False otherwise

#### Time Monitoring

```python
system.get_elapsed_analysis_time() -> float    # Minutes elapsed
system.get_analysis_time() -> float             # Total expected minutes
system.get_remaining_analysis_time() -> float   # Minutes remaining
```

#### abort_run()

Emergency stop current operation.

```python
system.abort_run() -> None
```

#### add_register_reader()

Add register inspection tool to ChemStation menu.

```python
system.add_register_reader(register_reader_macro: str = "...") -> None
```

---

## Validation Module

Input validation and system checks.

### Methods

#### validate_method_name()

Check method file exists.

```python
validation.validate_method_name(method: str, dir_path: str = "_METHPATH$") -> None
```

**Raises:**
- `ValidationError`: If method not found

#### validate_sequence_name()

Check sequence file exists.

```python
validation.validate_sequence_name(sequence: str, dir_path: str = "_SEQPATH$") -> None
```

#### validate_vial_in_system()

Check vial presence.

```python
validation.validate_vial_in_system(vial: int) -> None
```

**Raises:**
- `VialError`: If vial not detected

#### vial_in_position()

Check vial at lift position.

```python
validation.vial_in_position(position: str) -> None
```

**Parameters:**
- `position`: "inlet", "outlet", or "replenishment"

#### validate_use_carousel()

Check carousel availability.

```python
validation.validate_use_carousel() -> None
```

**Raises:**
- `SystemError`: If carousel not available

#### validate_method_run()

Check method started successfully.

```python
validation.validate_method_run() -> None
```

**Raises:**
- `MethodError`: If method not running

#### get_vialtable()

Get all vial positions status.

```python
validation.get_vialtable() -> Dict[int, bool]
```

**Returns:**
- Dictionary mapping position (1-48) to presence (True/False)

#### list_vial_validation()

Validate multiple vials.

```python
validation.list_vial_validation(vials: list) -> None
```

**Raises:**
- `VialError`: Lists all missing vials

---

## Configuration

### CommunicationConfig

Configuration class for ChemStation communication.

```python
@dataclass
class CommunicationConfig:
    comm_dir: str = "core/communication_files"
    command_filename: str = "command"
    response_filename: str = "response"
    max_command_number: int = 256
    default_timeout: float = 5.0
    retry_delay: float = 0.1
    max_retries: int = 10
    test_on_init: bool = True
    verbose: bool = False
```

**Example:**
```python
config = CommunicationConfig(
    verbose=True,
    default_timeout=10.0,
    test_on_init=False
)
api = ChemstationAPI(config)
```

---

## Common Patterns

### Complete Analysis

```python
# Standard analysis workflow
def analyze_sample(vial, method, name):
    # Validate
    api.validation.validate_vial_in_system(vial)
    api.validation.validate_method_name(method)
    
    # Load vials
    api.ce.load_vial_to_position(vial, "inlet")
    api.ce.load_vial_to_position(48, "outlet")
    
    # Condition
    api.ce.flush_capillary(60)
    
    # Run
    api.method.load(method)
    api.method.run(name)
    
    # Monitor
    while api.system.method_on():
        print(f"{api.system.get_remaining_analysis_time():.1f} min remaining")
        time.sleep(30)
    
    # Cleanup
    api.ce.unload_vial_from_position("inlet")
    api.ce.unload_vial_from_position("outlet")
```

### Error Handling

```python
try:
    api.ce.load_vial_to_position(15, "inlet")
except VialError:
    print("Vial not found - check carousel")
except SystemError:
    print("System busy - wait and retry")
except Exception as e:
    print(f"Unexpected error: {e}")
    api.system.abort_run()
```

### Sequence Creation

```python
# Create sequence from data
samples = [
    (10, "Method1", "Sample1"),
    (11, "Method2", "Sample2"),
    (12, "Method1", "Sample3")
]

for row, (vial, method, name) in enumerate(samples, 1):
    api.sequence.modify_sequence_row(
        row=row,
        vial_sample=str(vial),
        method=method,
        sample_name=name
    )

api.sequence.save_sequence("MySequence")
api.sequence.start()
```