# File-Based Communication Protocol

Understanding how Python communicates with ChemStation is crucial for troubleshooting and advanced usage. This page explains the file-based protocol that enables reliable command execution.

## How It Works

### Communication Flow

tady popiš jak to funguje, mám na to obrázek, nějak tam napiš že je to převzato a upraveno z https://github.com/croningp/analyticallabware/tree/master/AnalyticalLabware/devices/Agilent, mám to anpsáno i v k´du

```mermaid
sequenceDiagram
    participant Python
    participant CommandFile
    participant ResponseFile
    participant Macro
    participant ChemStation
    
    Python->>CommandFile: Write "1 LoadMethod MyMethod.M"
    Macro->>CommandFile: Read command
    Macro->>ChemStation: Execute LoadMethod
    ChemStation-->>Macro: Return result
    Macro->>ResponseFile: Write "1 None"
    Python->>ResponseFile: Read response
```



## Command Format

### Basic Commands

Commands without return values:

```python
# Python code
api.send("LoadMethod _METHPATH$, MyMethod.M")

# Command file content
123 LoadMethod _METHPATH$, MyMethod.M

# Response file content
123 None
```

### Commands with Return Values

To capture a return value, prefix with `response$ = `:

```python
# Python code
path = api.send("response$ = _METHPATH$")

# Command file content
124 response$ = _METHPATH$

# Response file content
124 C:\Chem32\1\Methods\CE\
```

## Command Numbering

The protocol uses sequential command numbers to match responses with requests:

- Numbers increment from 1 to 256 (configurable)
- Automatically wraps around at maximum
- Ensures each command gets its correct response
- Prevents mixing responses from multiple commands

```python
# Example of command numbering in action
1 response$ = _METHPATH$
2 LoadMethod _METHPATH$, Test.M
3 response$ = VAL$(_MethodOn)
...
256 response$ = ACQSTATUS$
1 response$ = _DATAPATH$  # Wraps around
```

## File Locations

Default file locations:

```
SIA-CE/
└── ChemstationAPI/
    └── core/
        ├── ChemPyConnect.mac          # Macro file
        └── communication_files/       # Communication directory
            ├── command               # Command file
            └── response              # Response file
```

## Monitoring Communication

### Enable Verbose Mode

```python
from ChemstationAPI.core.communication_config import CommunicationConfig

config = CommunicationConfig(verbose=True)
api = ChemstationAPI(config)

# Now all commands and responses are printed
api.send("response$ = _METHPATH$")
# Output:
# Sending command 1: response$ = _METHPATH$
# Received response 1: C:\Chem32\1\Methods\CE\
```

## Error Handling

### Timeout Handling

```python
# Increase timeout for long operations
api.send("RunMethod _DATAPATH$,, Sample001", timeout=30.0)
```

### Error Responses

ChemStation errors are detected and raised as exceptions:
tady hod ukázku, ž když napíšeš blbost, tak ti to vyhodí chybu

```python
try:
    api.send("InvalidCommand")
except ChemstationError as e:
    print(f"Error: {e}")
    # Output: Error: ChemStation command failed: ERROR: The command InvalidCommand failed to execute
```

## Macro Initialization

The ChemStation macro must be running for communication to work:

ChemStation command processor:
```vb
macro "C:\path\to\ChemPyConnect.mac"; Python_Run
```

The macro runs in a continuous loop:
1. Reads command file every 200ms
2. Executes new commands (higher number than last)
3. Writes responses
4. Continues until "Exit" command

## Advanced Configuration

### Custom Configuration

```python
from ChemstationAPI.core.communication_config import CommunicationConfig

config = CommunicationConfig(
    comm_dir="custom/path",
    max_command_number=1000,
    retry_delay=0.2,
    max_retries=5,
    default_timeout=10.0
)

api = ChemstationAPI(config)
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `comm_dir` | `"core/communication_files"` | Communication directory |
| `max_command_number` | `256` | Maximum before wraparound |
| `retry_delay` | `0.1` | Seconds between retries |
| `max_retries` | `10` | Maximum retry attempts |
| `default_timeout` | `5.0` | Default command timeout |
| `verbose` | `False` | Enable debug output |

## Troubleshooting Protocol Issues

### No Response Received

**Symptoms**: TimeoutError after sending command

**Check**:
1. Is ChemStation macro running?
2. Are file paths correct?
3. Can Python write to communication directory?

### Wrong Response Received

**Symptoms**: Response doesn't match command

**Check**:
1. Command numbering synchronization
2. Multiple Python instances running?
3. Old responses in response file?

### Slow Communication

**Symptoms**: Commands take long to execute

**Solutions**:
1. Reduce retry_delay in configuration
2. Check disk performance
3. Ensure antivirus isn't scanning communication files

!!! tip "Understanding the Protocol"
    The file-based protocol might seem complex, but it's very reliable once properly configured. Most issues come from macro not running or incorrect file paths.