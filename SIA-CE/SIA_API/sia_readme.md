# SIA API - Sequential Injection Analysis Controller

Python library for automated control of syringe pumps and valve selectors in analytical chemistry workflows.

## Overview

The SIA API provides complete automation for Sequential Injection Analysis systems, integrating syringe pumps, valve selectors, and ChemStation CE for analytical workflows.

**Inspired by:** [CoCoSoft framework](https://sites.google.com/view/cocovisolberglab/cocosoft)

## Quick Start

```python
from SIA_API.devices import syringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

# Initialize devices
syringe = syringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)

# Create workflow system
workflow = PreparedSIAMethods(
    chemstation_controller=chemstation_api,
    syringe_device=syringe,
    valve_device=valve
)

# Initialize and clean system
workflow.system_initialization_and_cleaning()

# Prepare for continuous filling
workflow.prepare_continuous_flow(solvent_port=5)

# Fill vials
workflow.continuous_fill(vial=15, volume=1500, solvent_port=5)
```

## Installation

```bash
pip install pyserial pandas win32com
```

## Features

### Device Control
- **syringeController**: Complete syringe pump control (Hamilton MVP series compatible)
- **ValveSelector**: Multi-position valve control (VICI compatible)
- **CommandSender**: Base serial communication class

### Workflow Automation
- **System initialization and cleaning**
- **Continuous flow filling** (fast, same solvent)
- **Batch flow filling** (air-driven, solvent changeover)
- **Sample homogenization** (pneumatic mixing)
- **Automatic needle cleaning**

### ChemStation Integration
- Automatic vial loading/unloading
- CE carousel management
- Synchronized analysis execution

## Basic Usage

### Device Setup

```python
# syringe pump
syringe = syringeController(port="COM3", syringe_size=1000)
syringe.initialize()
syringe.set_speed_uL_min(1500)
syringe.aspirate(500)
syringe.dispense(250)

# Valve selector
valve = ValveSelector(port="COM4", num_positions=8)
valve.position(1)  # Move to position 1
```

### System Configuration

```python
from SIA_API.methods import create_custom_config

# Default ports: waste=1, air=2, di=3, transfer=4, meoh=5
config = create_custom_config(waste_port=8, meoh_port=6)
```

### Workflows

```python
# System initialization
workflow.system_initialization_and_cleaning()

# Continuous flow (fast, multiple vials, same solvent)
workflow.prepare_continuous_flow(solvent_port=5)
for vial in [10, 11, 12]:
    workflow.continuous_fill(vial=vial, volume=1500, solvent_port=5)

# Batch flow (single vial, changeable solvent)
workflow.prepare_batch_flow(solvent_port=3)
workflow.batch_fill(vial=22, volume=750, solvent_port=3)

# Sample homogenization
workflow.homogenize_sample(vial=15, speed=1000, homogenization_time=30)
```

## Hardware Requirements

### Supported Devices
- Hamilton MVP syringe pumps (or compatible)
- VICI valve selectors (or compatible)
- Agilent ChemStation CE systems

### Communication
- RS-232/USB serial ports
- Standard baud rates (9600, 19200)
- Windows COM port support

## System Architecture

```
SIA_API/
├── core/
│   └── command_sender.py     # Base serial communication
├── devices/
│   ├── syringe_controller.py # syringe pump control
│   └── valve_selector.py     # Valve selector control
└── methods/
    ├── config.py             # Port configuration
    └── prepared_methods.py   # High-level workflows
```

## Configuration

### Default Port Mapping
- Port 1: Waste line
- Port 2: Air/gas line
- Port 3: DI water
- Port 4: Transfer line to CE
- Port 5: Methanol/organic solvent

### Vial Assignments
- Vial 48: Wash vial (needle cleaning)
- Vial 50: Waste vial

## Examples

### Complete Analysis Workflow

```python
# Initialize system
workflow.system_initialization_and_cleaning()
workflow.prepare_continuous_flow(solvent_port=5)

# Process samples
samples = [10, 11, 12, 13, 14]
for i, vial in enumerate(samples):
    # Fill vial
    workflow.continuous_fill(
        vial=vial,
        volume=1500,
        solvent_port=5,
        flush_needle=50 if i < len(samples)-1 else None
    )
    
    # Start CE analysis
    chemstation_api.method.execution_method_with_parameters(
        vial=vial,
        method_name="standard_method",
        sample_name=f"Sample_{i+1:03d}"
    )
```

### Multiple Solvent Workflow

```python
# Prepare different solvents for different vials
solvents = [(10, 3), (11, 5), (12, 3)]  # (vial, solvent_port)

for vial, solvent_port in solvents:
    workflow.prepare_batch_flow(solvent_port=solvent_port)
    workflow.batch_fill(vial=vial, volume=1000, solvent_port=solvent_port)
```

## Error Handling

```python
try:
    workflow.continuous_fill(vial=15, volume=1500, solvent_port=5)
except VialError as e:
    print(f"Vial error: {e}")
except SerialException as e:
    print(f"Communication error: {e}")
```

## Safety Features

- Automatic volume tracking and overflow prevention
- Vial presence validation in CE carousel
- Port configuration validation
- Serial communication error recovery
- Command retry mechanisms

## Troubleshooting

### Common Issues

**Communication Errors:**
```python
# Check COM port in Device Manager
# Verify baud rate and device address
# Test with simple command:
syringe.send_command("QR", get_response=True)
```

**Volume Errors:**
```python
# Always initialize syringe first
syringe.initialize()
# Check current volume
syringe.print_volume_in_syringe()
```

**Valve Position Errors:**
```python
# Use multiple attempts for reliability
valve.position(1, num_attempts=5)
```

## License

This project builds upon analytical automation concepts from the CoCoSoft framework and the analytical chemistry community.