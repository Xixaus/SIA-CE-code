# Hardware Setup Guide

Complete guide for setting up and configuring SIA-CE hardware components.

## System Requirements

### Computer Requirements

**Minimum:**
- Windows 7 SP1 (64-bit)
- 4 GB RAM
- 2.0 GHz processor
- 10 GB free disk space
- 2 available USB/Serial ports

**Recommended:**
- Windows 10/11 (64-bit)
- 8 GB RAM or more
- 3.0 GHz multi-core processor
- 50 GB free disk space
- Dedicated USB ports (not hub)

### Software Requirements

- Agilent ChemStation (version B.04.03 or higher)
- Python 3.7+ (64-bit recommended)
- Required Python packages (see installation guide)

## CE System Setup

### Agilent 7100 CE System

#### Initial Setup

1. **Power Connection**
   - Connect to appropriate voltage (100-240V)
   - Use surge protector
   - Ensure proper grounding

2. **Communication**
   - Connect USB cable to PC
   - Install ChemStation drivers
   - Configure in ChemStation

3. **Capillary Installation**
   - Use proper capillary cutting tool
   - Check window alignment
   - Verify detection path

#### Configuration in ChemStation

```
1. Open ChemStation
2. Go to Instrument → Configure
3. Select CE instrument
4. Set communication parameters:
   - Connection: USB
   - Timeout: 30 seconds
5. Test connection
```

### Carousel Setup

**Vial Positions:**
- Positions 1-48: Sample vials
- Position 49: Replenishment parking
- Position 50: Often used for waste

**Vial Types:**
- 100 µL microvials (recommended for small volumes)
- 1 mL polypropylene vials
- 2 mL glass vials

**Best Practices:**
- Use same vial type throughout analysis
- Check vial seating in carousel
- Replace damaged carousel positions

## SIA System Setup

### Syringe Pump Installation

#### Hamilton MVP Series

1. **Physical Setup**
   ```
   - Mount on stable surface
   - Level the pump
   - Install syringe (finger-tight only)
   - Connect valve assembly
   ```

2. **Electrical Connection**
   ```
   - Connect power supply (12-24V DC)
   - Connect RS-232 cable to PC
   - Set DIP switches if required
   ```

3. **Communication Settings**
   ```
   Port: COM3 (typical)
   Baud: 9600
   Data bits: 8
   Stop bits: 1
   Parity: None
   Flow control: None
   ```

#### Syringe Selection

| Volume Range | Syringe Size | Resolution | Best For |
|-------------|--------------|------------|----------|
| 10-100 µL | 100 µL | 0.03 µL | Precise small volumes |
| 50-500 µL | 500 µL | 0.17 µL | General use |
| 100-1000 µL | 1000 µL | 0.33 µL | Standard operations |
| 500-5000 µL | 5000 µL | 1.67 µL | Large volume prep |

### Valve Selector Installation

#### VICI/Valco Setup

1. **Mounting**
   ```
   - Secure to stable platform
   - Align ports horizontally
   - Minimize tubing lengths
   ```

2. **Port Connections**
   ```
   Port 1: Waste
   Port 2: Air/Gas
   Port 3: DI Water
   Port 4: Transfer to CE
   Port 5-8: Reagents/Solvents
   ```

3. **Communication**
   ```
   Port: COM4 (typical)
   Baud: 9600
   Protocol: VICI standard
   ```

### Tubing and Connections

#### Tubing Selection

| Application | ID (mm) | Material | Length |
|------------|---------|----------|---------|
| Syringe-Valve | 0.8 | PTFE | < 10 cm |
| Valve-Ports | 0.5 | PEEK | < 30 cm |
| To CE | 0.25 | Fused Silica | < 50 cm |
| Waste | 1.6 | PTFE | As needed |

#### Connection Best Practices

1. **Cutting Tubing**
   - Use sharp blade
   - Cut perpendicular
   - No burrs or deformation

2. **Fittings**
   - Finger-tight + 1/4 turn
   - Use appropriate ferrules
   - Check for leaks

3. **Dead Volume**
   - Minimize connection volume
   - Use zero-dead-volume fittings
   - Flush after installation

## System Integration

### Physical Layout

```
Recommended Setup:
┌─────────────┐     ┌──────────┐
│   CE System │     │ Computer │
│             │────>│          │
└─────────────┘     └──────────┘
       ^                  ^
       │                  │
┌──────┴─────┐     ┌─────┴────┐
│   Syringe  │────>│  Valve   │
│    Pump    │     │ Selector │
└────────────┘     └──────────┘
```

### Communication Architecture

1. **Serial Ports**
   ```python
   # Find available ports
   import serial.tools.list_ports
   
   ports = serial.tools.list_ports.comports()
   for port in ports:
       print(f"{port.device}: {port.description}")
   ```

2. **Port Assignment**
   - Use Device Manager to identify
   - Assign consistent port numbers
   - Document port mapping

### Power Management

1. **Power Sequence**
   ```
   1. Computer
   2. CE System
   3. Syringe Pump
   4. Valve Selector
   ```

2. **UPS Recommendations**
   - Minimum 1000 VA
   - Include all components
   - Test monthly

## Calibration and Testing

### Syringe Pump Calibration

```python
def calibrate_syringe_volume():
    """Calibrate syringe volume delivery."""
    
    # Initialize
    syringe.initialize()
    
    # Test volumes
    test_volumes = [100, 500, 900]
    
    for volume in test_volumes:
        # Dispense into tared vial
        syringe.aspirate(volume)
        input(f"Place tared vial at output. Press Enter...")
        syringe.dispense(volume)
        
        actual = float(input("Enter measured volume (µL): "))
        error = (actual - volume) / volume * 100
        print(f"Volume: {volume} µL, Error: {error:.2f}%")
```

### Valve Position Verification

```python
def verify_valve_positions():
    """Verify each valve position."""
    
    num_positions = 8
    
    for pos in range(1, num_positions + 1):
        valve.position(pos)
        input(f"Verify position {pos}. Press Enter...")
    
    print("Valve verification complete")
```

### CE System Tests

1. **Pressure Test**
   ```python
   # Test pressure system
   api.ce.apply_pressure_to_capillary(50, 10)  # 50 mbar, 10 sec
   api.ce.apply_pressure_to_capillary(-50, 10)  # -50 mbar, 10 sec
   ```

2. **Carousel Test**
   ```python
   # Test all positions
   for pos in range(1, 49):
       try:
           api.ce.load_vial_to_position(pos, "inlet")
           api.ce.unload_vial_from_position("inlet")
           print(f"Position {pos}: OK")
       except:
           print(f"Position {pos}: FAIL")
   ```

## Maintenance Schedule

### Daily
- Check for leaks
- Verify communication
- Clean needle/transfer line

### Weekly
- Flush all lines
- Check capillary condition
- Calibrate if needed

### Monthly
- Deep clean system
- Replace worn tubing
- Check electrical connections

### Annually
- Service syringe pump
- Replace seals
- Full system validation

## Troubleshooting

### Communication Issues

**Problem: COM port not found**
```
Solution:
1. Check Device Manager
2. Reinstall drivers
3. Try different USB port
4. Use USB-Serial adapter if needed
```

**Problem: Device not responding**
```python
# Test communication
try:
    syringe.send_command("?", get_response=True)
    print("Syringe communication OK")
except:
    print("Check connections and power")
```

### Mechanical Issues

**Problem: Syringe stalling**
```
Causes:
- Overpressure
- Mechanical binding
- Wrong syringe size configured

Solutions:
- Check for blockages
- Reduce speed
- Verify syringe size setting
```

**Problem: Valve not switching**
```
Causes:
- Mechanical obstruction
- Communication error
- Power issue

Solutions:
- Manual rotation check
- Increase switching attempts
- Check power supply
```

### System Integration Issues

**Problem: Timing conflicts**
```python
# Add delays between operations
def safe_operation_sequence():
    valve.position(1)
    time.sleep(0.5)  # Allow valve to settle
    syringe.aspirate(500)
    time.sleep(0.2)  # Allow pressure to stabilize
```

## Optimization Tips

### Speed Optimization

1. **Parallel Operations**
   - Prepare next sample during CE run
   - Use continuous flow for same solvent
   - Minimize valve switches

2. **Flow Rates**
   ```python
   # Optimized speeds
   SPEEDS = {
       'air': 5000,        # Fast
       'water': 3500,      # Medium-fast
       'organic': 2500,    # Medium
       'viscous': 1000,    # Slow
       'critical': 500     # Very slow
   }
   ```

### Volume Optimization

1. **Minimize Dead Volume**
   - Short tubing runs
   - Small ID tubing where possible
   - Zero-dead-volume fittings

2. **Efficient Aspiration**
   ```python
   # Aspirate in order of reactivity
   # 1. Buffer/diluent (least reactive)
   # 2. Sample (most reactive)
   # 3. Air gap (separation)
   ```

### Reliability Enhancement

1. **Error Recovery**
   ```python
   # Implement retry logic
   def reliable_operation(func, retries=3):
       for attempt in range(retries):
           try:
               return func()
           except:
               if attempt == retries - 1:
                   raise
               time.sleep(1)
   ```

2. **State Monitoring**
   ```python
   # Track system state
   class SystemMonitor:
       def __init__(self):
           self.syringe_volume = 0
           self.valve_position = 1
           self.last_operation = None
   ```

## Safety Considerations

### Chemical Safety
- Use fume hood for volatile solvents
- Proper waste disposal
- Material compatibility checks

### Electrical Safety
- Proper grounding
- No liquid near electronics
- Emergency stop procedures

### Pressure Safety
- Maximum 100 mbar for injection
- Maximum 950 mbar for flushing
- Pressure relief mechanisms

## Validation Protocols

### IQ/OQ/PQ

1. **Installation Qualification (IQ)**
   - Document all connections
   - Verify communication
   - Check safety features

2. **Operational Qualification (OQ)**
   - Test all functions
   - Verify accuracy
   - Document performance

3. **Performance Qualification (PQ)**
   - Run test methods
   - Verify reproducibility
   - Meet specifications

!!! success "Setup Complete"
    With proper hardware setup, your SIA-CE system is ready for automated analysis!