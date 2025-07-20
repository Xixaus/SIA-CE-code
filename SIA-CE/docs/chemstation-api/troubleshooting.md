# ChemStation Troubleshooting Guide

Detailed troubleshooting for ChemStation-specific issues.

## Connection Issues

### Macro Not Running

**Symptoms:**
- `ConnectionError: Failed to establish communication with ChemStation`
- No response to commands
- Timeout errors on initialization

**Solutions:**

1. **Load the macro manually:**
   ```
   In ChemStation command line:
   macro "C:\full\path\to\ChemPyConnect.mac"; Python_Run
   ```

2. **Verify macro is running:**
   ```
   Check ChemStation command line for:
   "Start Python communication"
   ```

3. **Auto-load macro on startup:**
   - Edit ChemStation's `user.mac` file
   - Add macro load command
   - Restart ChemStation

### File Access Issues

**Symptoms:**
- `FileOperationError: Failed to write command`
- Permission denied errors
- Communication files not created

**Solutions:**

1. **Check directory permissions:**
   ```python
   import os
   comm_dir = r"...\ChemstationAPI\core\communication_files"
   print(f"Exists: {os.path.exists(comm_dir)}")
   print(f"Writable: {os.access(comm_dir, os.W_OK)}")
   ```

2. **Run as Administrator:**
   - Right-click Python/IDE
   - Select "Run as administrator"

3. **Antivirus interference:**
   - Add communication directory to exclusions
   - Disable real-time scanning temporarily

### Command Syntax Errors

**Symptoms:**
- `ChemstationError: Command failed: ERROR: ...`
- Invalid command messages
- Unexpected responses

**Solutions:**

1. **Check command syntax:**
   ```python
   # Correct: Quotes around string parameters
   api.send('LoadMethod _METHPATH$, "Method.M"')
   
   # Wrong: Missing quotes
   api.send('LoadMethod _METHPATH$, Method.M')
   ```

2. **Verify response variable:**
   ```python
   # For return values, use response$
   value = api.send("response$ = _METHPATH$")
   
   # Without response$, returns None
   api.send("LoadMethod ...")  # No return value
   ```

## Method Issues

### Method Not Found

**Symptoms:**
- `ValidationError: Method 'X' not found`
- Method loading fails
- Case sensitivity issues

**Solutions:**

1. **Check exact filename:**
   ```python
   import os
   method_path = api.send("response$ = _METHPATH$")
   methods = [f for f in os.listdir(method_path) if f.endswith('.M')]
   print("Available methods:", methods)
   ```

2. **Case-insensitive validation:**
   ```python
   # The API handles case-insensitive matching
   api.validation.validate_method_name("method_name")  # Without .M
   ```

3. **Path issues:**
   ```python
   # Use full path if needed
   api.method.load("MyMethod", method_path="C:\\Methods\\Special\\")
   ```

### Method Execution Failures

**Symptoms:**
- `MethodError: Method failed to start`
- Analysis doesn't begin
- System remains in STANDBY

**Solutions:**

1. **Check prerequisites:**
   ```python
   # Verify system ready
   print(f"Status: {api.system.status()}")
   print(f"Method on: {api.system.method_on()}")
   
   # Check vials loaded
   api.validation.vial_in_position("inlet")
   api.validation.vial_in_position("outlet")
   ```

2. **Clear previous errors:**
   ```python
   # Abort any stuck operations
   api.system.abort_run()
   time.sleep(5)
   
   # Wait for ready
   api.system.wait_for_ready(60)
   ```

## Sequence Problems

### Excel Import Failures

**Symptoms:**
- `SequenceError: Failed to import from Excel`
- Empty sequence after import
- Column mapping errors

**Solutions:**

1. **Verify Excel format:**
   ```python
   import pandas as pd
   
   # Check your Excel file
   df = pd.read_excel("samples.xlsx")
   print("Columns:", df.columns.tolist())
   print("First row:", df.iloc[0].to_dict())
   ```

2. **Column name matching:**
   ```python
   # Exact column names required
   api.sequence.prepare_sequence_table(
       excel_file_path="samples.xlsx",
       vial_column="Vial",         # Must match exactly
       method_column="Method",     # Case sensitive
       sample_name_column="Name"   # No extra spaces
   )
   ```

3. **Excel application issues:**
   - Close Excel before import
   - Ensure Excel is installed
   - Try saving as .xlsx (not .xls)

### Sequence Execution Issues

**Symptoms:**
- Sequence stops unexpectedly
- Skips samples
- Wrong vial loaded

**Solutions:**

1. **Monitor sequence state:**
   ```python
   # Check sequence progress
   while api.system.method_on():
       status = api.system.status()
       rc_status = api.system.RC_status()
       print(f"Status: {status}, RC: {rc_status}")
       time.sleep(30)
   ```

2. **Validate all vials:**
   ```python
   # Before starting sequence
   vials_needed = [1, 2, 3, 10, 11, 12]  # Your vial list
   api.validation.list_vial_validation(vials_needed)
   ```

## System Status Issues

### Incorrect Status Reporting

**Symptoms:**
- Status doesn't update
- Wrong remaining time
- Method appears stuck

**Solutions:**

1. **Force status update:**
   ```python
   # Multiple status checks
   for _ in range(3):
       status = api.system.status()
       print(f"Status: {status}")
       time.sleep(1)
   ```

2. **Direct register access:**
   ```python
   # Get status from RC registers
   rc_state = api.send('response$ = ObjHdrText$(RCCE1Status[1], "RunState")')
   print(f"RC State: {rc_state}")
   ```

### Timing Discrepancies

**Symptoms:**
- Incorrect analysis time
- Progress calculation wrong
- Early termination

**Solutions:**

```python
# Robust time monitoring
def monitor_with_validation():
    last_remaining = float('inf')
    stuck_count = 0
    
    while api.system.method_on():
        remaining = api.system.get_remaining_analysis_time()
        
        # Check if time is updating
        if remaining == last_remaining:
            stuck_count += 1
            if stuck_count > 10:
                print("Warning: Time not updating")
        else:
            stuck_count = 0
            
        last_remaining = remaining
        time.sleep(10)
```

## Recovery Procedures

### Complete System Reset

```python
def full_system_reset():
    """Complete reset procedure."""
    
    print("Performing full system reset...")
    
    # 1. Abort any running operations
    try:
        api.system.abort_run()
    except:
        pass
    
    # 2. Unload all vials
    for position in ["inlet", "outlet", "replenishment"]:
        try:
            api.ce.unload_vial_from_position(position)
        except:
            pass
    
    # 3. Reinitialize communication
    time.sleep(5)
    api = ChemstationAPI()
    
    # 4. Verify ready state
    if api.system.wait_for_ready(60):
        print("System reset complete")
    else:
        print("System reset failed - manual intervention required")
    
    return api
```

### Communication Recovery

```python
def recover_communication():
    """Recover from communication failures."""
    
    # 1. Clear communication files
    import os
    comm_dir = "path/to/communication_files"
    
    for filename in ["command", "response"]:
        filepath = os.path.join(comm_dir, filename)
        try:
            os.remove(filepath)
        except:
            pass
    
    # 2. Restart macro in ChemStation
    print("In ChemStation, execute:")
    print('macro "path\\ChemPyConnect.mac"; Python_Stop')
    print('macro "path\\ChemPyConnect.mac"; Python_Run')
    input("Press Enter when complete...")
    
    # 3. Reconnect
    try:
        api = ChemstationAPI()
        print("Communication restored")
        return api
    except:
        print("Communication recovery failed")
        return None
```

## Performance Optimization

### Slow Command Response

**Solutions:**

1. **Reduce retry delay:**
   ```python
   config = CommunicationConfig(
       retry_delay=0.05,  # 50ms instead of 100ms
       max_retries=20     # More retries with shorter delay
   )
   ```

2. **Batch commands:**
   ```python
   # Instead of multiple calls
   # api.send("command1")
   # api.send("command2")
   
   # Use macro for batch operations
   api.send('macro "batch_commands.mac"; execute_all')
   ```

### Memory Issues

**Solutions:**

1. **Clear old data:**
   ```python
   # Periodically reinitialize
   if command_count > 1000:
       api = ChemstationAPI()  # Fresh connection
   ```

2. **Monitor file sizes:**
   ```python
   import os
   
   def check_comm_files():
       for file in ["command", "response"]:
           path = f"communication_files/{file}"
           size = os.path.getsize(path) / 1024  # KB
           if size > 100:
               print(f"Warning: {file} is {size:.1f} KB")
   ```

## Diagnostic Tools

### Communication Monitor

```python
def monitor_communication(duration=60):
    """Monitor communication for specified duration."""
    
    import time
    from datetime import datetime
    
    start = time.time()
    command_count = 0
    error_count = 0
    
    while time.time() - start < duration:
        try:
            # Test command
            result = api.send("response$ = ACQSTATUS$")
            command_count += 1
            print(f"\r{datetime.now()}: {result}", end="")
        except Exception as e:
            error_count += 1
            print(f"\nError: {e}")
        
        time.sleep(1)
    
    print(f"\n\nSummary: {command_count} commands, {error_count} errors")
    print(f"Success rate: {(command_count/(command_count+error_count))*100:.1f}%")
```

### Register Browser

```python
# Add register browser to ChemStation menu
api.system.add_register_reader()

# Then in ChemStation:
# Menu → Debug → Show Registers
# Browse all system registers and values
```

## Best Practices

1. **Always validate before operations**
2. **Use appropriate timeouts for different operations**
3. **Implement retry logic for critical operations**
4. **Monitor system state during long operations**
5. **Keep communication files clean**
6. **Document any custom macros or modifications**

!!! warning "When All Else Fails"
    If persistent issues:
    1. Restart ChemStation
    2. Reboot computer
    3. Check for ChemStation updates
    4. Verify hardware connections
    5. Contact Agilent support