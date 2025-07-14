# Getting Started

This guide will help you install the SIA-CE package and configure your system for automated CE analysis.

## Installation

### Prerequisites

- **Python 3.7 or higher** with pip package manager
- **Visual Studio Code** (recommended for Jupyter notebook support)
- **Agilent ChemStation** software running

### Package Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SIA-CE.git
cd SIA-CE

# Install dependencies
pip install pyserial pandas pywin32 tqdm openpyxl

# Configure ChemStation communication paths
python SIA-CE/ChemstationAPI/utils/macro_updater.py
```

The `macro_updater.py` script configures the correct file paths for ChemStation communication.

## System Configuration

### 1. ChemStation Setup

1. **Open ChemStation** and ensure it's fully loaded

2. **Find the command line** at the bottom of the interface
   
   !!! info "Command line missing?"
       Enable it from: `View → Command Line`

4. **Start the communication macro**:
   ```
   macro "C:\path\to\SIA-CE\ChemstationAPI\core\ChemPyConnect.mac"; Python_Run
   ```
   
   !!! info "Update the path"
       Replace with your actual installation path (shown by macro_updater)

5. **Verify success** - look for "Start Python communication" message

### 2. Hardware Setup

**Find COM ports** in Device Manager (`devmgmt.msc`) under "Ports (COM & LPT)" or:

```python
import serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(f"{port.device}: {port.description}")
```

## System Test

Run this complete test to verify everything works:

```python
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

def system_test():
    """Test all components."""
    print("=== SIA-CE System Test ===")
    
    # ChemStation
    try:
        ce_api = ChemstationAPI()
        status = ce_api.system.status()
        print(f"✓ ChemStation connected (Status: {status})")
    except Exception as e:
        print(f"✗ ChemStation failed: {e}")
        return False
    
    # SIA devices
    try:
        syringe = SyringeController(port="COM3", syringe_size=1000)
        valve = ValveSelector(port="COM4", num_positions=8)
        
        syringe.initialize()
        valve.position(1)
        print("✓ SIA devices connected")
    except Exception as e:
        print(f"✗ SIA devices failed: {e}")
        return False

# Run the test
system_test()
```

## Troubleshooting

**ChemStation Connection Failed**
- Ensure ChemStation is running
- Execute the macro command (exact command shown in error message)
- Check communication file paths

**COM Port Access Denied**
- Verify correct COM port numbers in Device Manager
- Close other programs using the ports
- Run Python as Administrator
- Check device power and cables

**Device Not Responding**
- Check power connections
- Verify cable connections (USB/RS232)
- Try different COM ports

**Missing Dependencies**
```bash
pip install pyserial pandas pywin32 tqdm openpyxl
```

## Development Tips

**Use Jupyter Notebooks** for interactive development:
- Step-by-step execution
- Real-time variable inspection  
- Easy debugging
- Available in VS Code or Jupyter Lab

**Basic workflow template**:
```python
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

# Initialize
ce_api = ChemstationAPI()
syringe = SyringeController(port="COM3", syringe_size=1000)  
valve = ValveSelector(port="COM4", num_positions=8)
workflow = PreparedSIAMethods(ce_api, syringe, valve)

# Your code here
```

## Next Steps

1. **[ChemStation File Protocol](chemstation-api/file-protocol.md)** - Understand the communication
2. **[Basic CE Operations](chemstation-api/basic-operations.md)** - Learn core functions
3. **[First Analysis Tutorial](tutorials/first-analysis.md)** - Complete walkthrough
4. **[SIA Workflows](sia-api/workflows.md)** - Advanced automation

!!! success "Ready to go!"
    Your SIA-CE system is configured. Start with the [First Analysis Tutorial](tutorials/first-analysis.md) for hands-on learning.
