# Frequently Asked Questions

Common questions and solutions for SI-CE integration workflows.

## Overview

### What is SI-CE?

SI-CE is a comprehensive Python package that seamlessly integrates Sequential Injection (SI) with Capillary Electrophoresis (CE) through Agilent ChemStation. This powerful combination enables complete laboratory automation including:

- **Automated sample preparation** - Streamlined sample handling and preparation workflows
- **CE instrument control** - Direct communication with ChemStation for method execution
- **Batch analysis workflows** - Process multiple samples with minimal manual intervention  
- **Complete analytical automation** - End-to-end automation from sample prep to data analysis

### Hardware Compatibility

**Supported ChemStation Systems:**
- Agilent 7100 Capillary Electrophoresis System
- All ChemStation-compatible CE instruments  
- Future support planned for additional Agilent platforms

**SIA Components:**
- VICI/Valco valve selectors and switching systems
- Compatible third-party devices with similar command protocols
- Additional components can be integrated and will be supported in future releases

### Programming Requirements

While basic Python knowledge is helpful, extensive programming experience is not required. The package is designed for accessibility:

- **High-level workflow methods** - Simple functions for complex operations
- **Pre-built analytical procedures** - Ready-to-use templates for common analyses
- **Copy-paste examples** - Working code snippets you can adapt immediately
- **Comprehensive documentation** - Detailed guides and tutorials

**AI-Assisted Development:** You can leverage generative AI tools (ChatGPT, Claude, etc.) by providing them with the repository link. These tools can help you program custom methods tailored to your specific needs. However, always thoroughly test any AI-generated code before implementation in production workflows.

## Installation and Setup

### ChemStation Connection Issues

**Q: ChemStation connection fails on startup**

**A: Follow this troubleshooting sequence:**

1. **Verify ChemStation Status**
   ```
   ChemStation must be running and fully loaded before attempting connection
   ```

2. **Load the Required Macro**
   ```
   In ChemStation command line, execute:
   macro "C:\path\to\ChemPyConnect.mac"; Python_Run
   ```

3. **Check Communication Files**
   - Ensure the communication directory exists
   - Verify file permissions allow read/write access

### COM Port Access Problems

**Q: Getting "COM port access denied" errors**

**A: Systematic troubleshooting approach:**

1. **Close Conflicting Applications**
   - HyperTerminal or other serial terminal programs
   - Device manufacturer configuration software
   - Other Python scripts using serial ports

2. **Verify Port Availability**
   ```python
   import serial.tools.list_ports
   
   print("Available COM ports:")
   for port in serial.tools.list_ports.comports():
       print(f"  {port.device}: {port.description}")
   ```

3. **Check Windows Device Manager**
   - Ensure drivers are properly installed
   - Look for yellow warning icons on COM ports

## Communication and Control

### Monitoring ChemStation Communication

**Q: How can I monitor what commands are being sent to ChemStation?**

**A: Enable verbose logging for detailed monitoring:**

```python
# Enable detailed logging to see all commands and responses
config = CommunicationConfig(verbose=True)
api = ChemstationAPI(config)

# Alternative: Monitor communication files directly (PowerShell)
Get-Content "communication_files\command" -Wait
```

### Custom ChemStation Commands

**Q: Can I send custom commands directly to ChemStation?**

**A: Yes, use the send() method for any valid ChemStation command:**

```python
# Read current oven temperature
response = api.send('response$ = VAL$(ObjHdrVal(RCCE1Status[1], "Temperature_actual"))')
print(f"Current oven temperature: {response}°C")

# Get method path
method_path = api.send("response$ = _METHPATH$")
print(f"Active method: {method_path}")
```

## Capillary Electrophoresis Operations

### Vial Loading Issues

**Q: Unable to load vials into the carousel**

**A: Vial loading failures typically occur for two main reasons:**

**System State Issues:**
The CE system may not be in a state that allows carousel operation. Vial loading is blocked when the system is in certain states to prevent operational conflicts:
- **IDLE state**: Normal operation - carousel accessible
- **RUN state**: Analysis in progress - carousel may be locked
- **Other states**: Carousel typically locked for safety

**Solution:** Implement state checking in your workflows:
```python
# Wait for appropriate system state before vial operations
while not api.is_carousel_available():
    time.sleep(5)  # Wait for system to reach appropriate state

# Then proceed with vial loading
carousel.load_vial(position=1)
```

**Missing Vial Validation:**
The system cannot locate the specified vial in the carousel.

**Solution:** Implement vial validation at workflow start:
```python
# Validate all required vials are present before starting
required_positions = [1, 2, 3, 5, 8]
missing_vials = carousel.validate_vials(required_positions)
if missing_vials:
    raise ValueError(f"Missing vials at positions: {missing_vials}")
```

## Method Configuration

### Modifying Method Parameters

**Q: Can I modify method parameters like temperature, voltage, etc. programmatically?**

**A: Yes, method parameters can be modified using ChemStation registry commands:**

Method parameters are stored in RC{module}Method[1] registers and can be modified directly:

```python
# Example: Modify separation voltage
api.send('RCCEMethod[1].Separation.Voltage = 25000')

# Example: Change capillary temperature  
api.send('RCCEMethod[1].Separation.Temperature = 25')

# Example: Modify injection time
api.send('RCCEMethod[1].Injection.Time = 5')
```

**Additional Resources:**
- See tutorial/chemstation_scripting section on Registry RCNET for comprehensive parameter lists
- Reference implementation: [HPLC Method Optimization GUI](https://github.com/Bourne-Group/HPLCMethodOptimisationGUI/blob/main/MACROS(1)/editMeth.MAC)

## Sequential Injection Operations

### Syringe Volume Management

**Q: Getting syringe volume tracking errors**

**A: The API automatically tracks syringe volume, but errors can occur:**

```python
# Check current syringe contents
syringe.print_volume_in_syringe()

# Reset volume tracking if needed
syringe.dispense()  # Empty syringe completely
syringe.volume_counter = 0  # Reset internal counter

# Or perform complete reinitialization
syringe.initialize()
```

**Best Practices:**
- Always initialize the syringe at workflow start
- Use `syringe.check_volume()` before critical operations
- Implement volume validation in loops

## Workflow Design

### Flow Strategy Selection

**Q: When should I use continuous flow vs. batch flow?**

**A: Choose based on your specific requirements:**

**Continuous Flow - Recommended when:**
- Processing multiple vials with the same solvent system
- Speed and throughput are priorities  
- Contamination risk between samples is minimal
- Running routine analyses with established methods

**Batch Flow - Recommended when:**
- Using different solvents or buffer systems per vial
- Processing single vials or small sample sets
- Maximum contamination prevention is required
- Method development or troubleshooting workflows

```python
# Continuous flow example
workflow = ContinuousFlow(
    samples=['sample1', 'sample2', 'sample3'],
    solvent='buffer_A',
    method='routine_analysis'
)

# Batch flow example  
workflow = BatchFlow(
    samples=[
        {'name': 'sample1', 'solvent': 'buffer_A'},
        {'name': 'sample2', 'solvent': 'buffer_B'},
    ]
)
```

## Troubleshooting Guide

### Systematic Diagnosis Approach

When encountering issues, follow this diagnostic sequence:

**1. Verify Physical Connections**
- Confirm power status on all devices
- Check cable connections and COM port assignments
- Test basic communication with each component

**2. Validate Software Prerequisites**
- ChemStation running and responsive
- Required macros loaded and active
- All specified vials present in carousel
- Target methods exist and are accessible

**3. Analyze Error Messages**
- Note specific exception types and error codes
- Look for recurring error patterns
- Enable verbose mode for detailed diagnostics

**4. Component-Level Testing**
```python
# Test individual components in isolation
try:
    syringe.initialize()
    print("✓ Syringe communication OK")
except Exception as e:
    print(f"✗ Syringe error: {e}")

try:
    valve.position(1)
    print("✓ Valve communication OK")
except Exception as e:
    print(f"✗ Valve error: {e}")

try:
    response = api.send("response$ = _METHPATH$")
    print(f"✓ ChemStation communication OK: {response}")
except Exception as e:
    print(f"✗ ChemStation error: {e}")
```

### Common Issues Quick Reference

**Most frequent problems and solutions:**

1. **ChemStation macro not running** → Reload macro in ChemStation command line
2. **Incorrect COM port configuration** → Use device manager to verify port assignments  
3. **Missing vials or methods** → Implement validation checks at workflow start
4. **Timeout settings too short** → Increase timeout values for complex operations
5. **Volume tracking errors** → Reset syringe and reinitialize volume counter

## Getting Support

### Available Resources

- **GitHub Issues**: Report bugs, request features, and track development
- **Documentation**: Comprehensive guides covering all package functionality
- **Tutorial Examples**: Working code examples for common workflows
- **Community Forums**: Connect with other users and developers

### Reporting Issues Effectively

When requesting support, please include:

- **Environment Details**: Python version, package version, operating system
- **Hardware Configuration**: CE model, SIA components, COM port assignments  
- **Error Information**: Complete error messages and stack traces
- **Minimal Example**: Simplified code that reproduces the issue
- **Context**: What you were trying to accomplish and what happened instead

---

!!! tip "Quick Resolution Tips"
    
    **90% of issues stem from these common causes:**
    
    1. **ChemStation macro not properly loaded or running**
    2. **COM port conflicts or incorrect assignments** 
    3. **Missing physical components (vials, methods)**
    4. **Insufficient timeout values for complex operations**
    
    **Always check these fundamentals first before diving into complex troubleshooting!**