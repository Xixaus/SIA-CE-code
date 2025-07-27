# File-Based Communication Protocol

Understanding how Python communicates with ChemStation is essential for troubleshooting, optimization, and advanced usage. This guide explains the robust file-based protocol that enables reliable command execution between Python and ChemStation.

## Protocol Overview

The ChemStation API uses a file-based communication protocol to ensure reliable, bidirectional communication between Python and ChemStation. This approach provides superior reliability compared to direct socket connections, especially in Windows environments where COM interfaces can be unstable.

### Design Inspiration

This communication protocol is adapted and enhanced from the excellent work by the Cronin Group at the University of Glasgow. The original implementation can be found at: [https://github.com/croningp/analyticallabware/tree/master/AnalyticalLabware/devices/Agilent](https://github.com/croningp/analyticallabware/tree/master/AnalyticalLabware/devices/Agilent)

Our implementation extends this foundation with additional error handling, timeout management, and CE-specific optimizations.

---

## How It Works

### Communication Architecture

The protocol operates through two files that act as communication channels between Python and ChemStation:

- **Command File** - Python writes commands here
- **Response File** - ChemStation writes responses here  
- **ChemStation Macro** - Monitors and executes commands continuously


### Step-by-Step Process

1. **Command Writing**: Python formats the command with a unique number and writes it to the command file
2. **Macro Polling**: The ChemStation macro continuously monitors the command file every 200 milliseconds
3. **Command Detection**: When a new command is detected (higher number than previous), the macro reads it
4. **Execution**: The macro sends the command to ChemStation's Command Processor for execution
5. **Response Writing**: Results are written to the response file with the matching command number
6. **Response Reading**: Python reads the response file and matches the response to the original command

---

## Command Format and Structure

### Basic Commands (No Return Value)

For commands that perform actions without returning data:

```python
# Python code
api.send("LoadMethod _METHPATH$, MyMethod.M")

# Command file content
123 LoadMethod _METHPATH$, MyMethod.M

# Response file content (indicates successful execution)
123 None
```

### Commands with Return Values

To capture return values, prefix the command with `response$ = `:

```python
# Python code
method_path = api.send("response$ = _METHPATH$")
print(f"Current method path: {method_path}")

# Command file content
124 response$ = _METHPATH$

# Response file content
124 C:\Chem32\1\Methods\CE\Default\
```

### Complex Commands with Parameters

```python
# Setting system variables
api.send('_SAMPLE$ = "Sample_001"')

# Executing methods with parameters  
api.send('RunMethod _DATAPATH$,, _SAMPLE$')

# Querying instrument status
status = api.send("response$ = VAL$(_MethodOn)")
is_running = bool(int(status))
```

---

## Command Numbering System

### Sequential Numbering

The protocol uses sequential command numbers to ensure proper command-response matching:

- **Range**: Numbers increment from 1 to a configurable maximum (default: 256)
- **Wraparound**: Automatically resets to 1 after reaching maximum
- **Uniqueness**: Each command gets a unique number within the cycle
- **Synchronization**: Prevents response mixing from multiple concurrent commands

### Numbering Example

```python
# Example command sequence
1 response$ = _METHPATH$                    # Get method path
2 LoadMethod _METHPATH$, Test.M            # Load method
3 response$ = VAL$(_MethodOn)              # Check method status
4 RunMethod _DATAPATH$,, Sample001         # Run analysis
...
255 response$ = ACQSTATUS$                 # Check acquisition
256 Print "Analysis complete"               # Final command
1 response$ = _DATAPATH$                   # Wraps back to 1
```

### Synchronization Benefits

- **Prevents confusion** when multiple commands are sent rapidly
- **Enables debugging** by tracking specific command execution
- **Supports concurrent operations** without response mixing
- **Provides error isolation** for failed commands

---

## File Locations and Structure

### Default File Structure

```
SIA-CE/
└── ChemstationAPI/
    └── core/
        ├── ChemPyConnect.mac              # ChemStation macro
        ├── communication_config.py        # Configuration module
        └── communication_files/           # Communication directory
            ├── command                   # Commands from Python → ChemStation
            └── response                  # Responses from ChemStation → Python
```

### File Content Examples

**Command File Format:**
```
125 response$ = _METHPATH$
```

**Response File Format:**
```
125 C:\Chem32\1\Methods\CE\Migration\
```

---

## Monitoring and Debugging

### Enable Verbose Communication Logging

```python
from ChemstationAPI.core.communication_config import CommunicationConfig
from ChemstationAPI import ChemstationAPI

# Create configuration with verbose output
config = CommunicationConfig(verbose=True)
api = ChemstationAPI(config)

# All commands and responses will be logged
method_path = api.send("response$ = _METHPATH$")

# Console output:
# Sending command 1: response$ = _METHPATH$
# Received response 1: C:\Chem32\1\Methods\CE\Migration\
```


## Error Handling and Recovery

### Timeout Management

```python
# Standard timeout (5 seconds default)
api.send("LoadMethod _METHPATH$, MyMethod.M")

# Extended timeout for long operations
api.send("RunMethod _DATAPATH$,, Sample001", timeout=300.0)  # 5 minutes

# Short timeout for quick checks
status = api.send("response$ = VAL$(_MethodOn)", timeout=1.0)
```

### ChemStation Error Detection

The API automatically detects and handles ChemStation errors:

```python
try:
    # Attempt to load non-existent method
    api.send("LoadMethod _METHPATH$, NonExistentMethod.M")
    
except ChemstationError as e:
    print(f"ChemStation Error: {e}")
    # Output: ChemStation Error: ERROR: Method file 'NonExistentMethod.M' not found
    
try:
    # Invalid command syntax
    api.send("InvalidCommandSyntax parameter1 parameter2")
    
except ChemstationError as e:
    print(f"Command Error: {e}")
    # Output: Command Error: ERROR: Command 'InvalidCommandSyntax' not recognized
```

---

## Troubleshooting Common Issues

### No Response Received (TimeoutError)

**Symptoms:**
- Commands timeout without receiving responses
- `TimeoutError: No response received within X seconds`

**Diagnostic Steps:**
1. **Verify macro status:**
   ```python
   # Test basic communication
   try:
       api.send("Print 'Test'", timeout=1.0)
       print("✓ Macro is running")
   except TimeoutError:
       print("✗ Macro not responding")
   ```

2. **Check file permissions:**
   ```python
   import os
   
   comm_dir = "core/communication_files"
   cmd_file = os.path.join(comm_dir, "command")
   resp_file = os.path.join(comm_dir, "response")
   
   print(f"Command file writable: {os.access(cmd_file, os.W_OK)}")
   print(f"Response file readable: {os.access(resp_file, os.R_OK)}")
   ```

### Wrong Response Received

**Symptoms:**
- Responses don't match sent commands
- Intermittent incorrect data

**Solutions:**
1. **Reset command numbering:**
   ```python
   # Force reset communication state
   api = ChemstationAPI()  # Creates fresh instance
   ```

2. **Check for multiple Python instances:**
   - Ensure only one Python script is communicating with ChemStation
   - Close other instances that might be interfering

### Slow Communication Performance

**Symptoms:**
- Commands take longer than expected
- Overall system feels sluggish

**Optimization Steps:**
1. **Reduce polling delay:**
   ```python
   config = CommunicationConfig(retry_delay=0.05)  # Faster polling
   ```

2. **Check system performance:**
   - Monitor disk I/O during communication
   - Ensure antivirus isn't scanning communication files
   - Check ChemStation system resource usage

### File Access Issues

**Symptoms:**
- Permission denied errors
- Unable to create communication files

**Solutions:**
1. **Run as Administrator:** Right-click Python IDE and select "Run as administrator"
2. **Check directory permissions:** Ensure communication directory has full read/write access
3. **Antivirus exclusion:** Add communication directory to antivirus exclusions

---

## Protocol Best Practices

### Efficient Command Execution

```python
# Batch related commands together
api.send("LoadMethod _METHPATH$, MyMethod.M")
api.send('_SAMPLE$ = "Sample_001"')  
api.send("RunMethod _DATAPATH$,, _SAMPLE$")

# Use appropriate timeouts
quick_status = api.send("response$ = VAL$(_MethodOn)", timeout=1.0)
method_result = api.send("RunMethod _DATAPATH$,, Sample", timeout=300.0)
```

### Error Prevention

```python
# Always validate before execution
def safe_method_execution(api, method_name, sample_name):
    """Safely execute method with validation"""
    
    # Check if method exists
    try:
        api.send(f"LoadMethod _METHPATH$, {method_name}")
    except ChemstationError:
        raise ValueError(f"Method '{method_name}' not found")
    
    # Set sample name
    api.send(f'_SAMPLE$ = "{sample_name}"')
    
    # Execute with extended timeout
    api.send("RunMethod _DATAPATH$,, _SAMPLE$", timeout=1800.0)
    
    return True
```

---

!!! tip "Protocol Reliability"
    The file-based protocol is extremely reliable once properly configured. Most communication issues stem from:
    1. **Macro not running** - Always verify macro status first
    2. **File permission problems** - Ensure proper directory access
    3. **Multiple Python instances** - Avoid concurrent communication attempts

!!! info "Performance Considerations"
    While file-based communication adds slight overhead compared to direct connections, the reliability benefits far outweigh the minimal performance impact. Typical command execution times are 50-200ms depending on command complexity.