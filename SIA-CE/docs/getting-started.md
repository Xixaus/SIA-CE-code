# Getting Started with SIA-CE

This comprehensive guide will help you install the SIA-CE package and run your first automated Sequential Injection - Capillary Electrophoresis analysis.

## Prerequisites

Before installing SIA-CE, ensure your system meets these requirements:

### Software Requirements
- **Python 3.7 or higher** with pip package manager
- **Agilent ChemStation** software properly configured and licensed
- **VSCode** (recommended) - Provides enhanced code editing capabilities and debugging tools

### Hardware Requirements
- **Capillary Electrophoresis system** compatible with ChemStation
- **SIA components** (syringe pump, valve selector)
- **Serial communication ports** for device connectivity

---

## Installation Process

### Step 1: Install Required Python Packages

Install the essential Python dependencies:

```bash
python -m pip install pyserial tqdm pandas
```

Package descriptions:

- `pyserial` - Serial communication with SIA hardware
- `tqdm` - Progress bars for long-running operations  
- `pandas` - Data manipulation and analysis

### Step 2: Install Development Environment (Recommended)

For enhanced script development and testing, install Jupyter Notebook:

```bash
python -m pip install jupyter notebook
```

Benefits of Jupyter Notebook:

- Interactive code development and testing
- Step-by-step script execution
- Integrated data visualization
- Easy documentation alongside code

### Step 3: Download SIA-CE Package

1. **Download from GitHub:**
   Navigate to: https://github.com/Xixaus/SIA-CE-code

2. **Extract the package:**

    - Download the ZIP file or clone the repository.

    - Extract to a permanent location on your computer (e.g., `C:\SIA-CE\`)

3. **Initialize the package:**
   ```bash
   python macro_update.py
   ```
   This script configures file paths and initializes the package for your system.

---

## ChemStation Configuration

### Step 1: Load the Communication Macro

1. **Open ChemStation** and ensure it's fully loaded
2. **Navigate to the command line interface**
3. **Execute the macro loading command:**

```chemstation
macro "C:\path\to\SIA-CE\ChemstationAPI\core\ChemPyConnect.mac"; Python_Run
```

!!! warning "Critical Path Configuration"
    **Replace `C:\path\to\SIA-CE\` with your actual installation directory!**
    
    Example: If installed in `D:\Lab\SIA-CE\`, use:
    ```chemstation
    macro "D:\Lab\SIA-CE\ChemstationAPI\core\ChemPyConnect.mac"; Python_Run
    ```

### Step 2: Verify ChemStation Integration

Successful macro loading will display:
```
Macro loaded and executed successfully
Communication interface initialized
```

!!! info "Troubleshooting Tip"
    If you encounter initialization errors, the correct macro path will be displayed in the ChemstationAPI error message for easy correction.

### Step 3: Test Python-ChemStation Communication

In your Python environment, execute:

```python
from ChemstationAPI.ChemstationAPI import ChemstationAPI

# Initialize ChemStation communication
chemstation = ChemstationAPI()
print("ChemStation connection established successfully!")
```

If this executes without errors, your ChemStation integration is properly configured.

---

## Hardware Configuration

### Step 1: Identify COM Ports

Discover available serial communication ports on your system:

```python
import serial.tools.list_ports

print("Available COM Ports:")
print("-" * 40)

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"{port.device}: {port.description}")
    print(f"  Hardware ID: {port.hwid}")
    print()
```

Example output:
```
Available COM Ports:
----------------------------------------
COM3: USB Serial Device (COM3)
  Hardware ID: USB\VID_0403&PID_6001

COM4: Prolific USB-to-Serial Comm Port (COM4)  
  Hardware ID: USB\VID_067B&PID_2303
```

### Step 2: Configure Syringe Controller

Test and configure your syringe pump:

```python
from SIA_API.devices import SyringeController

# Initialize syringe with appropriate parameters
syringe = SyringeController(
    port="COM3",           # Use your identified COM port
    syringe_size=1000,     # Syringe volume in microliters
    baudrate=9600          # Match your device settings
)

# Perform initialization sequence
syringe.initialization()  # Initialize syringe pump
print("Syringe controller ready!")

# Test basic functionality
syringe.print_volume_in_syringe()  # Display current volume status
```

### Step 3: Configure Valve Selector

Test and configure your valve selector:

```python
from SIA_API.devices import ValveSelector

# Initialize valve selector
valve = ValveSelector(
    port="COM4",           # Use your identified COM port  
    num_positions=8,       # Number of valve positions
    baudrate=9600         # Match your device settings
)

# Test valve movement
print("Testing valve positions...")
for position in range(1, 4):  # Test first 3 positions
    valve.position(position)
    print(f"Moved to position {position}")
    time.sleep(1)  # Brief pause between movements

print("Valve selector configured successfully!")
```

---

## Verification and Testing

### Complete System Test

Run this comprehensive test to verify all components:

```python
import time
from ChemstationAPI.ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector

def system_test():
    """Complete system functionality test"""
    
    print("=== SIA-CE System Test ===")
    
    # Test 1: ChemStation Communication
    print("\n1. Testing ChemStation communication...")
    try:
        chemstation = ChemstationAPI()
        response = chemstation.send("response$ = _METHPATH$")
        print(f"✓ ChemStation connected. Method path: {response}")
    except Exception as e:
        print(f"✗ ChemStation error: {e}")
        return False
    
    # Test 2: Syringe Controller
    print("\n2. Testing syringe controller...")
    try:
        syringe = SyringeController(port="COM3", syringe_size=1000)
        syringe.initialization()
        print("✓ Syringe controller ready")
    except Exception as e:
        print(f"✗ Syringe error: {e}")
        return False
    
    # Test 3: Valve Selector  
    print("\n3. Testing valve selector...")
    try:
        valve = ValveSelector(port="COM4", num_positions=8)
        valve.position(1)
        print("✓ Valve selector operational")
    except Exception as e:
        print(f"✗ Valve error: {e}")
        return False
    
    print("\n🎉 All systems operational! Ready for automated analysis.")
    return True

# Run the test
system_test()
```

---

## Common Installation Issues

### ChemStation Connection Problems

Error: `ConnectionError: Failed to establish communication with ChemStation`

**Solutions:**

1. **Verify ChemStation is running** and fully loaded
2. **Re-execute the macro command** in ChemStation command line  
3. **Check file permissions** in the ChemStation installation directory
4. **Restart ChemStation** if communication files become corrupted

### COM Port Access Issues

Error: `PermissionError: Access is denied` or `SerialException: could not open port`

**Solutions:**

1. **Run Python as Administrator** (right-click → "Run as administrator")
2. **Close conflicting applications** (HyperTerminal, Arduino IDE, other serial monitors)
3. **Check Device Manager** for yellow warning icons on COM ports
4. **Verify correct COM port numbers** using the port detection script

### Package Import Errors

Error: `ModuleNotFoundError: No module named 'SIA_API'` or similar

**Solutions:**

1. **Verify package installation path** in Python's sys.path
2. **Run `macro_update.py`** to configure paths correctly
3. **Check Python environment** (virtual environments may need separate package installation)
4. **Restart Python IDE** after path configuration changes

### Hardware Communication Timeouts

Error: `TimeoutError: Device did not respond within expected time`

**Solutions:**

1. **Check physical connections** (cables, power supplies)
2. **Verify baudrate settings** match device specifications
3. **Increase timeout values** in device configuration
4. **Test with device manufacturer software** to confirm hardware functionality

---

## Next Steps

Now that you have SIA-CE installed and configured, explore these resources:

### **Learn the Fundamentals:**
1. **[ChemStation File Protocol](chemstation-api/file-protocol.md)** - Understanding communication mechanisms
2. **[Basic CE Operations](chemstation-api/basic-operations.md)** - Essential capillary electrophoresis functions
3. **[SIA Device Control](sia-api/device-control.md)** - Sequential injection automation

### **Hands-On Tutorials:**
1. **[First Analysis Tutorial](tutorials/first-analysis.md)** - Complete walkthrough of automated analysis
2. **[SIA Workflows](sia-api/workflows.md)** - Advanced automation patterns
3. **[Method Development](tutorials/method-development.md)** - Optimizing analytical procedures

### **Advanced Topics:**
1. **[Batch Processing](tutorials/batch-analysis.md)** - High-throughput sample processing
2. **[Custom Workflows](tutorials/custom-workflows.md)** - Creating specialized automation sequences
3. **[Troubleshooting Guide](troubleshooting.md)** - Solving common operational issues

---

!!! success "Installation Complete!"
    
    **Congratulations!** You've successfully installed and configured SIA-CE for automated analytical workflows.
    
    **Your system is now ready for:**
    - Automated sample preparation via Sequential Injection
    - Integrated Capillary Electrophoresis analysis  
    - Complete workflow automation from sample to results
    
    **Ready to begin? Start with the [First Analysis Tutorial](tutorials/first-analysis.md) for a guided introduction to automated CE analysis.**