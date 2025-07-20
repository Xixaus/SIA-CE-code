# Getting Started

This guide will help you install the SIA-CE package and run your first automated analysis.

## Installation

### Prerequisites

Before installing SIA-CE, ensure you have:

- **Python 3.7 or higher** installed
- **Agilent ChemStation** software properly configured
- **Administrator privileges** for COM port access
- **Git** (optional, for development installation)

### Install from PyPI

The simplest way to install SIA-CE:

```bash
pip install sia-ce
```

### Development Installation

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/yourusername/SIA-CE.git
cd SIA-CE

# Install in development mode
pip install -e .
```

### Required Dependencies

The package will automatically install these dependencies:

```bash
pyserial>=3.5      # Serial communication
pandas>=1.3.0      # Data handling
pywin32>=300       # Windows COM interface
tqdm>=4.65.0       # Progress bars
```

## Initial Setup

### 1. ChemStation Configuration

Before using the ChemStation API, you need to start the communication macro:

1. Open ChemStation
2. Navigate to the command line
3. Execute the following command:

```
macro "C:\path\to\SIA-CE\ChemstationAPI\core\ChemPyConnect.mac"; Python_Run
```

!!! warning "Important"
    Replace `C:\path\to\` with your actual installation path!

### 2. Hardware Configuration

#### Find COM Ports

To identify your device COM ports:

```python
import serial.tools.list_ports

# List all available COM ports
ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"{port.device}: {port.description}")
```

#### Test Connections

Test syringe pump connection:

```python
from SIA_API.devices import SyringeController

syringe = SyringeController(port="COM3", syringe_size=1000)
syringe.send_command("?", get_response=True)  # Should return device info
```

Test valve selector connection:

```python
from SIA_API.devices import ValveSelector

valve = ValveSelector(port="COM4", num_positions=8)
valve.position(1)  # Should move to position 1
```

## Your First Analysis

### Basic ChemStation Control

```python
from ChemstationAPI import ChemstationAPI

# Initialize connection
api = ChemstationAPI()

# Load a vial to inlet position
api.ce.load_vial_to_position(vial=15, position="inlet")

# Load and run a method
api.method.load("CE_Standard_Method")
api.method.run("Test_Sample_001")

# Monitor progress
while api.system.method_on():
    remaining = api.system.get_remaining_analysis_time()
    print(f"Time remaining: {remaining:.1f} minutes")
    time.sleep(30)

print("Analysis complete!")
```

### Basic SIA Operations

```python
from SIA_API.devices import SyringeController, ValveSelector

# Initialize devices
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)

# Initialize syringe
syringe.initialize()
syringe.set_speed_uL_min(1500)  # 1.5 mL/min

# Simple liquid handling
valve.position(3)          # Switch to DI water port
syringe.aspirate(500)      # Draw 500 µL
valve.position(4)          # Switch to output port
syringe.dispense(500)      # Dispense 500 µL
```

### Combined SIA-CE Workflow

```python
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

# Initialize all components
ce_api = ChemstationAPI()
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)

# Create workflow controller
workflow = PreparedSIAMethods(
    chemstation_controller=ce_api,
    syringe_device=syringe,
    valve_device=valve
)

# Initialize and prepare system
workflow.system_initialization_and_cleaning()
workflow.prepare_continuous_flow(solvent_port=5)

# Process sample
sample_vial = 15
workflow.continuous_fill(
    vial=sample_vial,
    volume=1500,
    solvent_port=5
)

# Run CE analysis
ce_api.method.execution_method_with_parameters(
    vial=sample_vial,
    method_name="Standard_Method",
    sample_name="Test_Sample"
)
```

## Verification Steps

After installation, verify everything is working:

### 1. Check ChemStation Communication

```python
from ChemstationAPI import ChemstationAPI

api = ChemstationAPI()
print("ChemStation connected successfully!")
```

### 2. Check Hardware Communication

```python
# Test all devices respond
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)
print("Hardware devices connected successfully!")
```

### 3. Run Test Workflow

```python
# Simple test to verify integration
workflow = PreparedSIAMethods(api, syringe, valve)
workflow.system_initialization_and_cleaning()
print("System initialized successfully!")
```

## Common Installation Issues

### ChemStation Connection Failed

**Error**: `ConnectionError: Failed to establish communication with ChemStation`

**Solution**:
1. Ensure ChemStation is running
2. Execute the macro command in ChemStation
3. Check communication file paths in configuration

### COM Port Access Denied

**Error**: `PermissionError: Access is denied`

**Solution**:
1. Run Python as administrator
2. Close any other programs using the COM port
3. Check Windows Device Manager for port conflicts

### Module Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall with all dependencies
pip install --upgrade sia-ce
```

## Next Steps

Now that you have the system running:

1. Learn about the [ChemStation File Protocol](chemstation-api/file-protocol.md)
2. Explore [Basic CE Operations](chemstation-api/basic-operations.md)
3. Try the [First Analysis Tutorial](tutorials/first-analysis.md)
4. Read about [SIA Workflows](sia-api/workflows.md)

!!! success "Congratulations!"
    You've successfully installed SIA-CE and are ready to automate your analyses!