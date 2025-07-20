# Error Handling Reference

Comprehensive guide to exception types and error handling strategies in SIA-CE.

## Exception Hierarchy

```
ChemstationError (base)
├── CommunicationError
├── CommandError
├── FileOperationError
├── SequenceError
├── MethodError
├── VialError
├── ConfigurationError
├── ValidationError
└── TimeoutError
```

## Exception Types

### ChemstationError

Base exception for all ChemStation-related errors.

```python
try:
    # Any ChemStation operation
    api.ce.load_vial_to_position(15, "inlet")
except ChemstationError as e:
    print(f"ChemStation error: {e}")
    # Catches any ChemStation-related exception
```

### CommunicationError

File-based communication system failures.

**Common Causes:**
- ChemStation macro not running
- Communication files not accessible
- Protocol synchronization errors

**Example:**
```python
try:
    api = ChemstationAPI()
except CommunicationError as e:
    print("Failed to connect to ChemStation")
    print("Check that macro is running")
    # Start macro: macro "path\ChemPyConnect.mac"; Python_Run
```

### CommandError

ChemStation command execution failures.

**Common Causes:**
- Invalid command syntax
- Wrong parameter values
- Instrument state conflicts

**Example:**
```python
try:
    api.send("InvalidCommand parameter")
except CommandError as e:
    print(f"Command rejected: {e}")
    # Check command syntax in ChemStation documentation
```

### FileOperationError

File system operation failures.

**Common Causes:**
- Insufficient permissions
- Disk space issues
- File locked by another process

**Example:**
```python
try:
    api.method.save("NewMethod")
except FileOperationError as e:
    print(f"Cannot save file: {e}")
    # Check disk space and permissions
```

### SequenceError

Sequence management failures.

**Common Causes:**
- Sequence file not found
- Invalid sequence parameters
- Excel import issues

**Example:**
```python
try:
    api.sequence.prepare_sequence_table("samples.xlsx")
except SequenceError as e:
    print(f"Sequence error: {e}")
    # Check Excel file format and accessibility
```

### MethodError

CE method operation failures.

**Common Causes:**
- Method file not found
- Method execution startup failure
- Invalid method parameters

**Example:**
```python
try:
    api.method.run("Sample001")
except MethodError as e:
    print(f"Method failed: {e}")
    # Check instrument status and method parameters
```

### VialError

Vial handling failures.

**Common Causes:**
- Vial not present in carousel
- Mechanical loading failure
- Position out of range

**Example:**
```python
try:
    api.ce.load_vial_to_position(99, "inlet")
except VialError as e:
    print(f"Vial error: {e}")
    # Check vial presence and position
```

### ConfigurationError

System configuration failures.

**Common Causes:**
- Invalid configuration parameters
- Directory creation failure
- Missing required files

**Example:**
```python
try:
    config = CommunicationConfig(comm_dir="/invalid/path")
    api = ChemstationAPI(config)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Check paths and permissions
```

### ValidationError

Input validation failures.

**Common Causes:**
- File not found
- Invalid parameter values
- System not ready

**Example:**
```python
try:
    api.validation.validate_method_name("NonexistentMethod")
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Check file existence and naming
```

### TimeoutError

Operation timeout failures.

**Common Causes:**
- ChemStation not responding
- Long operations exceeding timeout
- Communication delays

**Example:**
```python
try:
    response = api.send("LongCommand", timeout=5.0)
except TimeoutError as e:
    print(f"Timeout: {e}")
    # Increase timeout or check ChemStation status
```

## Error Handling Strategies

### 1. Defensive Programming

Always validate before operations:

```python
def safe_vial_load(api, vial, position):
    """Load vial with validation."""
    try:
        # Validate first
        api.validation.validate_vial_in_system(vial)
        api.validation.validate_use_carousel()
        
        # Then execute
        api.ce.load_vial_to_position(vial, position)
        return True
        
    except VialError as e:
        print(f"Vial {vial} not available: {e}")
        return False
    except SystemError as e:
        print(f"System not ready: {e}")
        return False
```

### 2. Retry Logic

Implement retry for transient failures:

```python
def retry_operation(func, max_attempts=3, delay=5):
    """Retry operation with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except (TimeoutError, CommunicationError) as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed, waiting {wait_time}s")
            time.sleep(wait_time)

# Usage
result = retry_operation(lambda: api.send("response$ = _METHPATH$"))
```

### 3. Context Managers

Use context managers for cleanup:

```python
class VialLoader:
    """Context manager for vial operations."""
    
    def __init__(self, api, vial, position):
        self.api = api
        self.vial = vial
        self.position = position
        
    def __enter__(self):
        self.api.ce.load_vial_to_position(self.vial, self.position)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always unload, even if error occurred
        try:
            self.api.ce.unload_vial_from_position(self.position)
        except:
            pass  # Best effort cleanup

# Usage
with VialLoader(api, 15, "inlet") as loader:
    # Vial operations
    api.ce.flush_capillary(60)
# Vial automatically unloaded
```

### 4. Error Recovery

Implement recovery procedures:

```python
class AnalysisRunner:
    """Run analysis with error recovery."""
    
    def __init__(self, api):
        self.api = api
        self.recovery_actions = {
            VialError: self.recover_from_vial_error,
            MethodError: self.recover_from_method_error,
            TimeoutError: self.recover_from_timeout
        }
    
    def run_analysis(self, vial, method, sample):
        try:
            self.api.method.execution_method_with_parameters(
                vial=vial,
                method_name=method,
                sample_name=sample
            )
        except tuple(self.recovery_actions.keys()) as e:
            # Try recovery
            recovery_func = self.recovery_actions[type(e)]
            if recovery_func(e):
                # Retry after recovery
                return self.run_analysis(vial, method, sample)
            else:
                raise
    
    def recover_from_vial_error(self, error):
        print("Attempting vial recovery...")
        # Check vial presence
        # Try reloading
        # Return True if recovered
        return False
    
    def recover_from_method_error(self, error):
        print("Attempting method recovery...")
        self.api.system.abort_run()
        time.sleep(30)
        return True
    
    def recover_from_timeout(self, error):
        print("Attempting timeout recovery...")
        # Check system status
        # Wait for ready
        return self.api.system.wait_for_ready(60)
```

### 5. Logging Errors

Comprehensive error logging:

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename=f'sia_ce_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def logged_operation(func):
    """Decorator for error logging."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logging.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logging.error(f"{func.__name__} failed: {type(e).__name__}: {e}")
            raise
    return wrapper

@logged_operation
def critical_analysis(api, vial, method):
    api.method.execution_method_with_parameters(
        vial=vial,
        method_name=method,
        sample_name="Critical_Sample"
    )
```

## Common Error Scenarios

### Scenario 1: ChemStation Not Responding

```python
def handle_chemstation_timeout():
    try:
        api = ChemstationAPI()
    except (ConnectionError, TimeoutError):
        print("ChemStation not responding")
        print("1. Check ChemStation is running")
        print("2. Execute macro command:")
        print('   macro "path\\ChemPyConnect.mac"; Python_Run')
        print("3. Check communication files accessible")
        return None
    return api
```

### Scenario 2: Batch Processing with Failures

```python
def robust_batch_processing(api, samples):
    """Process batch with failure tracking."""
    results = {
        'success': [],
        'failed': [],
        'errors': []
    }
    
    for sample in samples:
        try:
            # Process sample
            api.method.execution_method_with_parameters(**sample)
            results['success'].append(sample['sample_name'])
            
        except VialError as e:
            results['failed'].append(sample['sample_name'])
            results['errors'].append(f"Vial error: {e}")
            
        except MethodError as e:
            results['failed'].append(sample['sample_name'])
            results['errors'].append(f"Method error: {e}")
            # Try to recover for next sample
            api.system.abort_run()
            time.sleep(60)
            
        except Exception as e:
            results['failed'].append(sample['sample_name'])
            results['errors'].append(f"Unexpected: {e}")
    
    return results
```

### Scenario 3: SIA Volume Overflow

```python
def safe_volume_operations(syringe, operations):
    """Execute volume operations with overflow protection."""
    
    for op_type, volume in operations:
        try:
            if op_type == 'aspirate':
                # Check before aspirating
                if syringe.volume_counter + volume > syringe.syringe_size:
                    # Dispense first
                    syringe.dispense()
                syringe.aspirate(volume)
                
            elif op_type == 'dispense':
                if volume > syringe.volume_counter:
                    raise ValueError(f"Insufficient volume: {syringe.volume_counter} µL available")
                syringe.dispense(volume)
                
        except ValueError as e:
            print(f"Volume error: {e}")
            # Handle based on operation requirements
            raise
```

## Best Practices

1. **Specific Exception Handling**
   ```python
   # Good - Specific handling
   try:
       api.ce.load_vial_to_position(15, "inlet")
   except VialError:
       # Handle missing vial
   except SystemError:
       # Handle busy system
   
   # Bad - Too broad
   try:
       api.ce.load_vial_to_position(15, "inlet")
   except Exception:
       # Don't know what went wrong
   ```

2. **Always Clean Up**
   ```python
   try:
       # Operations
   finally:
       # Cleanup always executes
       api.ce.unload_vial_from_position("inlet")
   ```

3. **Fail Fast**
   ```python
   # Validate everything first
   api.validation.validate_vial_in_system(vial)
   api.validation.validate_method_name(method)
   api.validation.validate_use_carousel()
   
   # Then execute
   # ...
   ```

4. **Informative Error Messages**
   ```python
   if not vial_present:
       raise VialError(
           f"Vial {vial} not found in carousel. "
           f"Check position {vial} is occupied."
       )
   ```

5. **Document Expected Exceptions**
   ```python
   def load_vial(vial: int, position: str) -> None:
       """Load vial to position.
       
       Raises:
           VialError: If vial not present
           SystemError: If carousel busy
           ValueError: If invalid position
       """
   ```