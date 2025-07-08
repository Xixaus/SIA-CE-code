# Frequently Asked Questions

Common questions and solutions for SIA-CE integration.

## General Questions

### What is SIA-CE?

SIA-CE is a Python package that integrates Sequential Injection Analysis (SIA) with Capillary Electrophoresis (CE) through Agilent ChemStation. It enables:
- Automated sample preparation
- CE instrument control
- Batch analysis workflows
- Complete analytical automation

### Which hardware is supported?

**CE Systems:**
- Agilent 7100 Capillary Electrophoresis System
- Other ChemStation-compatible CE instruments

**SIA Components:**
- Hamilton MVP series syringe pumps
- VICI/Valco valve selectors
- Compatible third-party devices with similar command sets

### Do I need programming experience?

Basic Python knowledge is helpful but not required. The package provides:
- High-level workflow methods
- Pre-built analytical procedures
- Copy-paste examples
- Comprehensive documentation

## Installation Issues

### Q: ChemStation connection fails on startup

**A: Check these items in order:**

1. **Is ChemStation running?**
   ```
   ChemStation must be open before connecting
   ```

2. **Is the macro loaded?**
   ```
   In ChemStation command line:
   macro "C:\path\to\ChemPyConnect.mac"; Python_Run
   ```

3. **Are paths correct?**
   ```python
   # Check communication directory exists
   import os
   comm_dir = r"C:\...\ChemstationAPI\core\communication_files"
   print(os.path.exists(comm_dir))
   ```

### Q: ModuleNotFoundError when importing

**A: Install missing dependencies:**

```bash
# Install all required packages
pip install pyserial pandas pywin32 tqdm

# Or reinstall the complete package
pip install --upgrade sia-ce
```

### Q: COM port access denied

**A: Common solutions:**

1. **Run as Administrator**
   - Right-click Python/IDE
   - Select "Run as administrator"

2. **Close conflicting programs**
   - HyperTerminal
   - Other serial monitors
   - Device manufacturer software

3. **Check Windows permissions**
   ```python
   # List available ports
   import serial.tools.list_ports
   for port in serial.tools.list_ports.comports():
       print(port.device, port.description)
   ```

## ChemStation Communication

### Q: Commands timeout frequently

**A: Adjust timeout settings:**

```python
from ChemstationAPI.core.communication_config import CommunicationConfig

# Increase timeouts
config = CommunicationConfig(
    default_timeout=10.0,  # 10 seconds
    retry_delay=0.2,       # 200ms between retries
    max_retries=15         # More retries
)

api = ChemstationAPI(config)
```

### Q: How do I monitor communication?

**A: Enable verbose mode:**

```python
# See all commands and responses
config = CommunicationConfig(verbose=True)
api = ChemstationAPI(config)

# Or monitor files directly (PowerShell)
Get-Content "communication_files\command" -Wait
```

### Q: Can I send custom ChemStation commands?

**A: Yes, use the send() method:**

```python
# Any valid ChemStation command
response = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Temperature_actual"))')
print(f"Current temperature: {response}°C")
```

## CE Operations

### Q: Vial loading fails intermittently

**A: Common causes and solutions:**

1. **Vial not properly seated**
   ```python
   # Validate before loading
   api.validation.validate_vial_in_system(vial)
   api.ce.load_vial_to_position(vial, "inlet")
   ```

2. **Carousel busy**
   ```python
   # Wait for ready state
   api.validation.validate_use_carousel()
   ```

3. **Previous vial not unloaded**
   ```python
   # Always unload first
   try:
       api.ce.unload_vial_from_position("inlet")
   except:
       pass  # Ignore if already unloaded
   api.ce.load_vial_to_position(new_vial, "inlet")
   ```

### Q: How do I handle different vial types?

**A: The system supports multiple vial types:**

- 100 µL microvials: Best for precious samples
- 1 mL polypropylene: Standard operations
- 2 mL glass: Large volume or organic solvents

Use consistent vial type throughout analysis for best results.

### Q: Method execution fails to start

**A: Check these items:**

```python
# 1. Validate method exists
api.validation.validate_method_name("MethodName")

# 2. Check system is ready
if api.system.status() != "STANDBY":
    api.system.wait_for_ready(60)

# 3. Verify vials are loaded
api.validation.vial_in_position("inlet")
api.validation.vial_in_position("outlet")

# 4. Then run method
api.method.run("SampleName")
```

## SIA Operations

### Q: Syringe volume errors

**A: The API tracks volume automatically:**

```python
# Check current volume
syringe.print_volume_in_syringe()

# Reset if needed
syringe.dispense()  # Empty completely
syringe.volume_counter = 0  # Reset counter

# Or reinitialize
syringe.initialize()
```

### Q: Valve doesn't switch reliably

**A: Use multiple attempts:**

```python
# Increase attempts for reliability
valve.position(5, num_attempts=5)

# Or implement custom retry
def reliable_valve_switch(position, max_tries=5):
    for attempt in range(max_tries):
        valve.position(position)
        time.sleep(0.5)  # Allow settling
        # Could add position verification here
    return True
```

### Q: How to prevent cross-contamination?

**A: Follow these practices:**

```python
# 1. Wash between different samples
workflow.clean_needle(volume_flush=100)

# 2. Use air gaps
valve.position(air_port)
syringe.aspirate(20)  # Air gap
valve.position(sample_port)
syringe.aspirate(sample_volume)

# 3. Flush lines between solvents
workflow.prepare_batch_flow(new_solvent_port)
```

## Workflow Questions

### Q: Continuous vs Batch flow - when to use which?

**A: Use continuous flow when:**
- Multiple vials with same solvent
- Speed is priority
- Minimal contamination risk

**Use batch flow when:**
- Different solvents per vial
- Single vial operations
- Maximum contamination prevention

### Q: How to optimize for speed?

**A: Speed optimization strategies:**

```python
# 1. Prepare next sample during CE run
def parallel_preparation():
    # Start CE
    ce_api.method.run("Current_Sample")
    
    # While running, prepare next
    while ce_api.system.method_on():
        if ce_api.system.get_remaining_analysis_time() < 5:
            workflow.batch_fill(next_vial, volume, port)
            break
        time.sleep(30)

# 2. Use appropriate flow rates
syringe.set_speed_uL_min(5000)  # Air - fast
syringe.set_speed_uL_min(3500)  # Water - medium
syringe.set_speed_uL_min(1000)  # Viscous - slow

# 3. Minimize valve switches
# Group operations by port
```

### Q: How to handle errors in batch processing?

**A: Implement error recovery:**

```python
def robust_batch_analysis(samples):
    failed = []
    
    for sample in samples:
        try:
            # Process sample
            analyze_sample(sample)
        except VialError:
            failed.append(sample)
            continue  # Skip this sample
        except MethodError:
            # Try recovery
            api.system.abort_run()
            time.sleep(60)
            # Retry once
            try:
                analyze_sample(sample)
            except:
                failed.append(sample)
        except KeyboardInterrupt:
            # Allow user to stop
            print("Batch interrupted by user")
            break
    
    return failed
```

## Data Management

### Q: Where are data files stored?

**A: Default locations:**

```python
# Get current paths
data_path = api.send("response$ = _DATAPATH$")
method_path = api.send("response$ = _METHPATH$")
sequence_path = api.send("response$ = _SEQPATH$")

# Set custom subdirectory
api.method.execution_method_with_parameters(
    vial=15,
    method_name="Method",
    sample_name="Sample",
    subdirectory_name="Project_X_2024"
)
```

### Q: How to organize data from large studies?

**A: Use structured naming:**

```python
from datetime import datetime

# Create organized structure
project = "ProteinStability"
date = datetime.now().strftime("%Y%m%d")
condition = "pH7_25C"

sample_name = f"{project}_{date}_{condition}_Rep1"
subdirectory = f"{project}_{date}"

api.method.execution_method_with_parameters(
    vial=15,
    method_name="CE_Protein",
    sample_name=sample_name,
    subdirectory_name=subdirectory
)
```

## Performance Issues

### Q: Analysis takes too long

**A: Optimization strategies:**

1. **Parallel operations** - Prepare during CE run
2. **Continuous flow** - For same solvent
3. **Optimized methods** - Shorter CE runtime
4. **Batch operations** - Minimize overhead

### Q: System becomes unresponsive

**A: Recovery procedures:**

```python
# 1. Emergency stop
api.system.abort_run()

# 2. Reset communication
api = ChemstationAPI()  # Reconnect

# 3. Reinitialize hardware
syringe.initialize()
valve.position(1)

# 4. Check system state
print(api.system.status())
print(api.system.RC_status())
```

## Advanced Topics

### Q: Can I modify the communication protocol?

**A: Yes, but be careful:**

```python
# Custom configuration
config = CommunicationConfig(
    comm_dir="custom/path",
    max_command_number=1000,  # Larger command buffer
    command_filename="my_commands",
    response_filename="my_responses"
)
```

### Q: How to integrate with LIMS?

**A: Example LIMS integration:**

```python
class LIMSIntegration:
    def __init__(self, api):
        self.api = api
        self.lims_connection = None  # Your LIMS API
    
    def get_worklist(self):
        # Fetch from LIMS
        return self.lims_connection.get_pending_samples()
    
    def process_worklist(self):
        samples = self.get_worklist()
        
        for sample in samples:
            # Update LIMS status
            self.lims_connection.update_status(sample.id, "Processing")
            
            # Run analysis
            result = self.analyze_sample(sample)
            
            # Report back
            self.lims_connection.report_result(sample.id, result)
```

### Q: Can I extend the API?

**A: Yes, create custom modules:**

```python
class CustomWorkflow(PreparedSIAMethods):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def my_special_preparation(self, sample_info):
        """Custom sample preparation."""
        # Your implementation
        pass

# Use custom workflow
workflow = CustomWorkflow(ce_api, syringe, valve)
workflow.my_special_preparation(sample_info)
```

## Troubleshooting Checklist

### When things don't work:

1. **Check connections**
   - Power on all devices
   - Verify COM ports
   - Test communication

2. **Validate prerequisites**
   - ChemStation running
   - Macro loaded
   - Vials present
   - Methods exist

3. **Review error messages**
   - Check specific exception type
   - Look for error patterns
   - Enable verbose mode

4. **Test components individually**
   ```python
   # Test each component
   syringe.send_command("?", get_response=True)
   valve.position(1)
   api.send("response$ = _METHPATH$")
   ```

5. **Check the logs**
   - ChemStation logbook
   - Windows Event Viewer
   - Python console output

## Getting Help

### Resources:
- GitHub Issues: Report bugs and request features
- Documentation: Check all sections
- Examples: Review tutorial code
- Community: Discussion forums

### When reporting issues, include:
- Python version
- Package version
- Hardware details
- Error messages
- Minimal code example

!!! tip "Still stuck?"
    Most issues are related to:
    1. ChemStation macro not running
    2. Incorrect COM ports
    3. Missing vials or methods
    4. Timeout settings too short
    
    Check these first!