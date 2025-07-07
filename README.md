# SIA-CE Integration Package

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

Python package for automated capillary electrophoresis (CE) analysis programming with Agilent Chemstation integration. Future versions will include Sequential Injection Analysis (SIA) system integration for complete sample preparation and analysis automation.

## Overview

This package provides a Python interface for programming and controlling capillary electrophoresis instruments through Agilent Chemstation. It enables scientists and researchers to create automated analytical workflows without extensive programming knowledge.

### Key Features

- **Chemstation Integration**: Direct communication with Agilent Chemstation software
- **User-Friendly API**: Simplified interface designed for analytical scientists
- **Automated Workflows**: Program complex analytical sequences with minimal code
- **Data Management**: Streamlined data acquisition and processing
- **Future SIA Support**: Planned integration with Sequential Injection Analysis systems for complete automation

## Installation

### Standard Installation

Install the package using pip:

```bash
pip install sia-ce-code
```

### Development Installation

For development or testing purposes:

```bash
# Clone the repository
git clone https://github.com/your-username/SIA-CE-code.git
cd SIA-CE-code
```

### Prerequisites

- Python 3.7 or higher
- Agilent Chemstation software (compatible versions to be specified)
- Windows 7 or higher (required for Chemstation integration)
- Properly configured CE instrument connected to Chemstation

## System Requirements

### Software Requirements
- Windows 7+
- Agilent Chemstation (specific version compatibility documentation in progress)
- Python 3.7+

### Hardware Requirements
- Agilent CE instrument (CE 7100)
- Chemstation
- Proper instrument-computer connectivity

## API Overview

The package provides classes and methods for:

- **Instrument Control**: Direct CE instrument communication through Chemstation
- **Method Management**: Loading, modifying, and executing analytical methods
- **Data Acquisition**: Automated data collection and initial processing
- **Workflow Automation**: Chaining multiple analytical steps

*Detailed API documentation and examples are currently in development and will be added in future updates.*

## Chemstation Integration

This package communicates with CE instruments through Agilent Chemstation software. Proper Chemstation installation and configuration is required for package functionality.

### Setup Requirements
- Licensed Chemstation installation
- Instrument drivers properly installed
- Communication protocols configured

*Detailed setup instructions will be provided in future documentation updates.*

## Contributing

This is an open-source project. Contributions from the analytical chemistry community are welcome.

### How to Contribute
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

*Detailed contribution guidelines will be added as the project matures.*

## Documentation

Comprehensive documentation including:
- Complete API reference
- Tutorial examples
- Best practices guide
- Troubleshooting section

*Documentation is currently being developed alongside the codebase.*

## Support

For questions, issues, or feature requests, please open an issue on the project repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Analytical chemistry community for feedback and requirements
- Open-source Python ecosystem
- Agilent Technologies for Chemstation platform

---

**Note**: This project is in active development. Features and API may change as development progresses. Check back regularly for updates and new releases.
