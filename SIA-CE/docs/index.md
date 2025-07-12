# SIA-CE Integration Package

## Automated Capillary Electrophoresis with Sequential Injection Analysis

Welcome to the SIA-CE Integration documentation. This package provides a unified Python interface for controlling Agilent ChemStation CE systems and Sequential Injection Analysis (SIA) hardware, enabling fully automated analytical workflows.

!!! info "Project Status"
    This project is actively developed. ChemStation API is fully functional, while SIA integration is in advanced development stage.

## What is SIA-CE?

SIA-CE combines two powerful analytical techniques:

- **Capillary Electrophoresis (CE)**: High-resolution separation technique for analyzing charged molecules
- **Sequential Injection Analysis (SIA)**: Automated sample preparation and liquid handling system

Together, they enable:

- ✅ Fully automated sample preparation and analysis
- ✅ Reduced manual intervention and human error
- ✅ Increased throughput and reproducibility
- ✅ Complex analytical workflows with minimal supervision

## Key Features

### ChemStation API
- **Universal ChemStation Control**: Compatible with any instrument controlled by ChemStation software
- **CE-Optimized Functions**: While universally applicable, functions are specifically designed and optimized for capillary electrophoresis operations
- **Direct Command Processor Access**: Commands sent directly to ChemStation command line for maximum flexibility
- **Robust Communication Protocol**: Simple and reliable file-based communication system
- **Comprehensive Method Management**: Complete CE method and sequence handling with advanced parameter control
- **Real-time Instrument Monitoring**: Live status and progress tracking with detailed analytics
- **Easy Customization**: Simple to extend or modify for specific applications and instrument configurations
- **Ready-to-Use Control Functions**: Pre-programmed operations for common CE tasks and workflows

### SIA API
- **Precise Syringe Pump Control**: Full automation of Cavro XP and Hamilton MVP series pumps with microliter precision
- **Multi-Position Valve Automation**: Complete control of VICI and compatible valve selectors for fluid routing
- **Advanced Liquid Handling**: Sophisticated aspiration, dispensing, and mixing operations with customizable parameters
- **Pre-Built Analytical Workflows**: Ready-to-use methods for sample preparation, dilution, and homogenization
- **Volume Tracking & Safety**: Automatic volume monitoring with overflow protection and error recovery
- **Flexible Configuration**: Customizable port assignments and operational parameters for different laboratory setups

### Integration Benefits
- Seamless coordination between sample preparation and analysis
- One unified Python interface for complete workflow control
- Reduced analysis time through parallel operations
- Consistent and reproducible analytical procedures

## Quick Example

```python
from ChemstationAPI import ChemstationAPI
from SIA_API.methods import PreparedSIAMethods
from SIA_API.devices import SyringeController, ValveSelector

# Initialize systems
chemstation = ChemstationAPI()
syringe = SyringeController(port="COM3", syringe_size=1000)  # Cavro XP or Hamilton MVP
valve = ValveSelector(port="COM4", num_positions=8)

sia = PreparedSIAMethods(chemstation, syringe, valve)

# Automated workflow
sia.system_initialization_and_cleaning()
sia.prepare_batch_flow()

sia.batch_fill(vial=15, volume=500, solvent_port=5)
sia.homogenize_sample(vial=15, speed=2000, homogenization_time=30)

chemstation.method.execution_method_with_parameters(
    vial=15, 
    method_name="Protein_Analysis",
    sample_name="BSA_Standard"
)
```

## Documentation Overview

This documentation is organized to help you quickly find what you need:

- **[Getting Started](getting-started.md)**: Installation and first steps
- **[ChemStation API](chemstation-api/introduction.md)**: Control your CE system
- **[SIA API](sia-api/introduction.md)**: Automate sample preparation
- **[Tutorials](tutorials/first-analysis.md)**: Step-by-step guides
- **[API Reference](api-reference/chemstation.md)**: Complete function documentation

## System Requirements

### Hardware
- Agilent 7100 Capillary Electrophoresis System (or other ChemStation-compatible instruments)
- Cavro XP or Hamilton MVP series syringe pump
- VICI or compatible valve selector
- Windows PC with available COM ports or USB-to-RS232 adapters

### Software
- Windows 7 or higher
- Agilent OpenLab CDS ChemStation Edition
- Python 3.7+
- Required Python packages (see [Getting Started](getting-started.md))

## Support and Contributing

- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/SIA-CE/issues)
- **Discussions**: Join our [community discussions](https://github.com/yourusername/SIA-CE/discussions)
- **Contributing**: See our [contribution guidelines](https://github.com/yourusername/SIA-CE/blob/main/CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/yourusername/SIA-CE/blob/main/LICENSE) file for details.

---

!!! tip "Ready to start?"
    Head to [Getting Started](getting-started.md) to install the package and run your first automated analysis!