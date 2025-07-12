# Getting Started

This guide will help you install the SIA-CE package
## Installation

### Prerequisites

Before installing SIA-CE, ensure you have:

- **Python 3.7 or higher** installed with packages
- **VSCode** pro lepší úpravu k´du s jupyter notebookem
- **Agilent ChemStation** software properly configured

### Instalace balíčků

```bash
# Clone the repository
python -m pip install 
```

### Jupyter notebooku

Pro lepší obsluhu skriptů doporučuji využívat jupyternotebook

### Installation

Pro instalaci bude zvoleno klonování balíčků z githubu do zvolené složky. Poté je nutné spuštění skriptu macro_updater pro nastavení cest.
```bash
# Clone the repository
git clone https://github.com/yourusername/SIA-CE.git

python spuštění macro_updater pro úpravu cest v ovládacím makru
```

## Initial Setup

### 1. ChemStation Configuration

Before using the ChemStation API, you need to start the communication macro:

1. Open ChemStation
2. Navigate to the command line který je ve spodní části
tip, pokud zde není musí se zapnout v nabídce
3. Execute the following command:

```
macro "C:\path\to\SIA-CE\ChemstationAPI\core\ChemPyConnect.mac"; Python_Run
```

!!! warning "Important"
    Replace `C:\path\to\` with your actual installation path!

tip: příkaz pro chemstation se zobrazí při chbě při iniciaci ChemstationAPI

4. V pythonu naimportujte Chemstation třídu a iniciujte, pokud vše proběhne v pořádku, máte hotovo
```
from ChemstationAPI import ChemstationAPI

chemstation = ChemstationAPI()
```

Zde udělej

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

nebo ve správci zařízení

#### Test Connections

Test syringe pump connection:

```python
from SIA_API.devices import SyringeController

syringe = SyringeController(port="COM3", syringe_size=1000)
syringe.iniciation()  # iniciace stříkačky
```

Test valve selector connection:

```python
from SIA_API.devices import ValveSelector

valve = ValveSelector(port="COM4", num_positions=8)
valve.position(1)  # Should move to position 1
```

## Common Installation Issues

### ChemStation Connection Failed

**Error**: `ConnectionError: Failed to establish communication with ChemStation`

**Solution**:

1. Ensure ChemStation is running
2. Execute the macro command in ChemStation
tip: v chybě se nachází příkaz přímo pro chemstation s cestou
3. Check communication file paths in configuration

### COM Port Access Denied

**Error**: `PermissionError: Access is denied`

**Solution**:
1. Ujistětese, že jste nastavili správné COM porty
2. Close any other programs using the COM port
3. Check Windows Device Manager for port conflicts


## Next Steps

Now that you have the system running:

1. Learn about the [ChemStation File Protocol](chemstation-api/file-protocol.md)
2. Explore [Basic CE Operations](chemstation-api/basic-operations.md)
3. Try the [First Analysis Tutorial](tutorials/first-analysis.md)
4. Read about [SIA Workflows](sia-api/workflows.md)