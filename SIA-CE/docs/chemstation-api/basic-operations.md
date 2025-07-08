# Basic ChemStation Operations

This guide covers the most common operations for controlling your CE system through ChemStation.

## Initializing the API

```python
from ChemstationAPI import ChemstationAPI

# Basic initialization
api = ChemstationAPI()

# With custom configuration
from ChemstationAPI.core.communication_config import CommunicationConfig

config = CommunicationConfig(verbose=True, test_on_init=False)
api = ChemstationAPI(config)
```

## Vial Management

### Understanding Vial Positions

The CE system has several vial locations:

- **Carousel**: 48 positions for samples (1-48) + special positions
- **Inlet**: Sample injection position (positive electrode)
- **Outlet**: Waste collection position (negative electrode)
- **Replenishment**: Buffer replenishment position

### Loading and Unloading Vials

```python
# Load vial to inlet for analysis
api.ce.load_vial_to_position(vial=15, position="inlet")

# Load waste vial to outlet
api.ce.load_vial_to_position(vial=48, position="outlet")

# Load buffer vial for replenishment
api.ce.load_vial_to_position(vial=49, position="replenishment")

# Return vial to carousel
api.ce.unload_vial_from_position("inlet")
```

### Checking Vial Status

```python
# Check where a vial is located
state = api.ce.get_vial_state(15)
print(f"Vial 15 is at: {state}")
# Possible states: "carousel", "inlet", "outlet", "replenishment", "out_system"

# Check all vial positions
vial_table = api.validation.get_vialtable()
for position, present in vial_table.items():
    if present:
        print(f"Vial present at position {position}")
```

## Capillary Operations

### Capillary Conditioning

```python
# Standard 1-minute flush at high pressure
api.ce.flush_capillary(time_flush=60.0)

# Quick bubble removal
api.ce.flush_capillary(time_flush=10.0)

# Long conditioning for new capillary
api.ce.flush_capillary(time_flush=300.0)  # 5 minutes
```

### Pressure Operations

```python
# Hydrodynamic injection (50 mbar for 5 seconds)
api.ce.apply_pressure_to_capillary(pressure=50.0, time_pressure=5.0)

# Gentle conditioning
api.ce.apply_pressure_to_capillary(pressure=25.0, time_pressure=30.0)

# Vacuum application
api.ce.apply_pressure_to_capillary(pressure=-50.0, time_pressure=10.0)
```

## Method Operations

### Loading Methods

```python
# Load method from default directory
api.method.load("CE_Standard_Method")

# Load from specific directory
api.method.load("TestMethod", method_path="C:\\Methods\\Development\\")
```

### Running Methods

```python
# Simple method execution
api.method.run("Sample_001")

# Run with custom data directory
api.method.run("Sample_001", data_dir="C:\\Data\\Project_X\\")

# Run with all parameters
api.method.execution_method_with_parameters(
    vial=15,
    method_name="CE_Protein_Analysis",
    sample_name="BSA_1mg_ml",
    comment="pH 8.5 buffer",
    subdirectory_name="Protein_Study"
)
```

### Saving Methods

```python
# Save current method with new name
api.method.save("Modified_Method", comment="Increased voltage to 25kV")

# Overwrite current method
api.method.save()
```

## System Monitoring

### Check System Status

```python
# Is method running?
if api.system.method_on():
    print("Analysis in progress")
else:
    print("System idle")

# Get detailed status
status = api.system.status()
print(f"Current status: {status}")
# Returns: "STANDBY", "PRERUN", "RUN", "POSTRUN", etc.

# Check CE module status
rc_status = api.system.RC_status()
print(f"CE module: {rc_status}")
# Returns: "Idle", "Run", "NotReady", "Error"
```

### Monitor Analysis Progress

```python
# Real-time monitoring
while api.system.method_on():
    elapsed = api.system.get_elapsed_analysis_time()
    total = api.system.get_analysis_time()
    remaining = api.system.get_remaining_analysis_time()
    
    progress = (elapsed / total) * 100 if total > 0 else 0
    print(f"Progress: {progress:.1f}% - {remaining:.1f} min remaining")
    
    time.sleep(30)  # Update every 30 seconds

print("Analysis complete!")
```

## Validation Operations

### Pre-flight Checks

```python
# Validate before starting analysis
def prepare_for_analysis(sample_vial, waste_vial, method_name):
    # Check vials are present
    api.validation.validate_vial_in_system(sample_vial)
    api.validation.validate_vial_in_system(waste_vial)
    
    # Check method exists
    api.validation.validate_method_name(method_name)
    
    # Check carousel is available
    api.validation.validate_use_carousel()
    
    # Check system is ready
    if api.system.status() != "STANDBY":
        raise SystemError("System not ready")
    
    print("All checks passed - ready for analysis!")

# Use the validation
prepare_for_analysis(15, 48, "CE_Standard_Method")
```

### Batch Validation

```python
# Validate multiple vials for sequence
sample_vials = [10, 11, 12, 13, 14, 15]
api.validation.list_vial_validation(sample_vials)
print("All sample vials present")
```

## Direct ChemStation Commands

For advanced operations, send commands directly:

```python
# Get system paths
method_path = api.send("response$ = _METHPATH$")
data_path = api.send("response$ = _DATAPATH$")
print(f"Methods: {method_path}")
print(f"Data: {data_path}")

# Get current voltage
voltage = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Voltage_actual"))')
print(f"Current voltage: {voltage} kV")

# Execute custom macro
api.send('macro "C:\\custom_macro.mac"; custom_procedure 15, "parameter"')
```

## Complete Analysis Example

Here's a complete workflow for a single sample:

```python
def analyze_sample(sample_vial, sample_name, method_name):
    """Complete analysis workflow for a single sample."""
    
    # 1. Validate prerequisites
    print("Validating system...")
    api.validation.validate_vial_in_system(sample_vial)
    api.validation.validate_vial_in_system(48)  # waste vial
    api.validation.validate_method_name(method_name)
    
    # 2. Wait for system ready
    print("Waiting for system...")
    if not api.system.wait_for_ready(timeout=60):
        raise TimeoutError("System not ready")
    
    # 3. Load vials
    print("Loading vials...")
    api.ce.load_vial_to_position(sample_vial, "inlet")
    api.ce.load_vial_to_position(48, "outlet")
    
    # 4. Condition capillary
    print("Conditioning capillary...")
    api.ce.flush_capillary(30.0)
    
    # 5. Load and run method
    print(f"Running analysis for {sample_name}...")
    api.method.load(method_name)
    api.method.run(sample_name)
    
    # 6. Monitor progress
    while api.system.method_on():
        remaining = api.system.get_remaining_analysis_time()
        print(f"  {remaining:.1f} minutes remaining", end='\r')
        time.sleep(10)
    
    # 7. Return vials
    print("\nCleaning up...")
    api.ce.unload_vial_from_position("inlet")
    api.ce.unload_vial_from_position("outlet")
    
    print(f"Analysis of {sample_name} complete!")

# Run the analysis
analyze_sample(
    sample_vial=15,
    sample_name="Test_Sample_001",
    method_name="CE_Standard_Method"
)
```

## Error Handling Best Practices

Always wrap operations in try-except blocks:

```python
try:
    api.ce.load_vial_to_position(15, "inlet")
except VialError as e:
    print(f"Vial error: {e}")
    # Check if vial is present and properly seated
except SystemError as e:
    print(f"System error: {e}")
    # Check if system is in correct state
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error and notify operator
```

## Tips for Efficient Operation

1. **Always validate before operations**
   ```python
   # Good practice
   api.validation.validate_vial_in_system(vial)
   api.ce.load_vial_to_position(vial, "inlet")
   ```

2. **Use appropriate timeouts**
   ```python
   # Long operation
   api.send("RunMethod ...", timeout=300.0)  # 5 minutes
   ```

3. **Monitor system state**
   ```python
   # Wait between operations
   while api.system.status() != "STANDBY":
       time.sleep(5)
   ```

4. **Clean up after errors**
   ```python
   try:
       # Your analysis code
   except:
       # Emergency cleanup
       api.system.abort_run()
       api.ce.unload_vial_from_position("inlet")
       raise
   ```

!!! tip "Next Steps"
    Learn about [Methods and Sequences](methods-sequences.md) for batch analysis automation.