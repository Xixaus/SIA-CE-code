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
- Direct control of Agilent 7100 CE systems through ChemStation
- File-based communication protocol for reliable command execution
- Comprehensive method and sequence management
- Real-time instrument status monitoring
- Automated vial handling and capillary operations

### SIA API
- Precise syringe pump control (Hamilton MVP compatible)
- Multi-position valve automation (VICI compatible)
- Pre-built workflows for common operations
- Volume tracking and safety features
- Flexible port configuration

### Integration Benefits
- Seamless coordination between sample preparation and analysis
- One unified Python interface for complete workflow control
- Reduced analysis time through parallel operations
- Consistent and reproducible analytical procedures

## Quick Example

```python
from ChemstationAPI import ChemstationAPI
from SIA_API.methods import PreparedSIAMethods

# Initialize systems
ce = ChemstationAPI()
sia = PreparedSIAMethods(ce, syringe, valve)

# Automated workflow
sia.system_initialization_and_cleaning()
sia.continuous_fill(vial=15, volume=1500, solvent_port=5)
ce.method.execution_method_with_parameters(
    vial=15, 
    method_name="Protein_Analysis",
    sample_name="BSA_Standard"
)
```

## Who Should Use This Package?

This package is designed for:

- **Analytical Chemists** working with CE and automated sample preparation
- **Research Scientists** needing reproducible analytical workflows
- **Laboratory Managers** looking to increase throughput and efficiency
- **Method Developers** creating new analytical procedures

## Documentation Overview

This documentation is organized to help you quickly find what you need:

- **[Getting Started](getting-started.md)**: Installation and first steps
- **[ChemStation API](chemstation-api/introduction.md)**: Control your CE system
- **[SIA API](sia-api/introduction.md)**: Automate sample preparation
- **[Tutorials](tutorials/first-analysis.md)**: Step-by-step guides
- **[API Reference](api-reference/chemstation.md)**: Complete function documentation

## System Requirements

### Hardware
- Agilent 7100 Capillary Electrophoresis System
- Hamilton MVP or compatible syringe pump
- VICI or compatible valve selector
- Windows PC with available COM ports

### Software
- Windows 7 or higher
- Agilent ChemStation software
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