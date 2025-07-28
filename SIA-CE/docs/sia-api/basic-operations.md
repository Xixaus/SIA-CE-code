# Basic Operations

## Device Initialization

### Initial Setup

```python
from SIA_API.devices import SyringeController, ValveSelector

# Initialize syringe pump
syringe = SyringeController(
    port="COM3",           # Serial port
    syringe_size=1000,     # 1000 µL syringe
    address="/1",          # Device address (default)
    baudrate=9600          # Communication speed (default)
)

# Initialize valve selector
valve = ValveSelector(
    port="COM4",          # Serial port
    num_positions=8,      # 8-position valve
    prefix="/Z",          # Command prefix (VICI standard)
    baudrate=9600         # Communication speed (default)
)
```

### Testing Communication

```python
# Test syringe communication
response = syringe.send_command("?", get_response=True)
print(f"Syringe response: {response}")

# Test valve communication - move to position 1
valve.position(1)
print("Valve moved to position 1")
```

## Syringe Control

### Initialization
Always initialize the syringe before operations:

```python
# Move syringe to home position
syringe.initialize()
print("Syringe initialized")

# Check current volume tracking
syringe.print_volume_in_syringe()
# Output: The current volume in the syringe is: 0 µl
```

### Flow Rate Settings

```python
# Set flow rate in µL/min
syringe.set_speed_uL_min(1500)    # 1.5 mL/min

# Common speed settings
syringe.set_speed_uL_min(500)     # Slow/precise operations
syringe.set_speed_uL_min(2000)    # Normal operations  
syringe.set_speed_uL_min(5000)    # Fast transfers/air

# Get current speed setting
current_speed = syringe.get_actual_set_speed()
print(f"Current speed: {current_speed:.1f} µL/min")
```

### Aspiration (Drawing Fluid)

```python
# Aspirate specific volume
syringe.aspirate(500)             # Draw 500 µL

# Aspirate entire syringe capacity
syringe.aspirate()                # Fill to maximum

# Non-blocking aspiration
syringe.aspirate(300, wait=False) # Returns immediately

# Aspiration with progress bar
syringe.aspirate(800, show_progress=True)
```

### Dispensing

```python
# Dispense specific volume
syringe.dispense(250)             # Dispense 250 µL

# Dispense all contents
syringe.dispense()                # Empty syringe completely

# Non-blocking dispense
syringe.dispense(100, wait=False) # Returns immediately

# Dispensing with progress bar
syringe.dispense(500, show_progress=True)
```

### Volume Tracking

The API automatically tracks syringe contents:

```python
# Example sequence
syringe.initialize()              # Volume: 0 µL
syringe.aspirate(600)             # Volume: 600 µL
syringe.dispense(200)             # Volume: 400 µL

# Current volume status
syringe.print_volume_in_syringe()
# Output: The current volume in the syringe is: 400 µl

# Attempting to exceed capacity raises error
try:
    syringe.aspirate(800)         # Would exceed 1000 µL capacity!
except ValueError as e:
    print(f"Error: {e}")
```

## Valve Control

### Basic Positioning

```python
# Move to specific port
valve.position(1)                 # Move to port 1
valve.position(5)                 # Move to port 5

# Reliable positioning with retry attempts
valve.position(3, num_attempts=5) # Try up to 5 times for reliability
```

### Position Validation

```python
# Systematic position testing
print("Testing valve positions...")
for position in range(1, 9):     # Test positions 1-8
    valve.position(position)
    print(f"Moved to position {position}")
    input("Confirm position and press Enter...")
```

## Syringe-Mounted Valve Control

For 3-way valves mounted directly on syringe:

```python
# Configure valve type
syringe.configuration_valve_type('3-Port')

# Control valve positions
syringe.valve_in()                # Input position
syringe.valve_out()               # Output position  
syringe.valve_up()                # Up/bypass position
```

## Emergency Operations

### Emergency Stop
```python
# Immediate stop of all syringe operations
syringe.emergency_stop()
```

### System Reset
```python
# Complete system reset
syringe.initialize()              # Reset syringe to home
valve.position(1)                 # Move valve to safe position
```

## Basic Parameter Configuration

### Backlash Compensation
```python
# Set backlash steps (0-31 standard mode, 0-248 high resolution)
syringe.set_backlash(15)          # Adjust for mechanical play
```

### Communication Timeouts
```python
# Custom timeout for slow operations
response = syringe.send_command(
    "Z", 
    get_response=True, 
    response_timeout=10.0         # 10 second timeout
)
```

## Error Handling

### Communication Errors
```python
import serial

try:
    syringe.initialize()
except serial.SerialException as e:
    print(f"Communication error: {e}")
    # Check COM port, cable connection, device power
```

### Volume Validation Errors
```python
try:
    syringe.aspirate(2000)        # Exceeds 1000 µL capacity
except ValueError as e:
    print(f"Volume error: {e}")
    # Adjust volume or use multiple cycles
```

### Valve Position Errors
```python
try:
    valve.position(15)            # Exceeds 8 positions
except ValueError as e:
    print(f"Position error: {e}")
    # Check valve configuration
```

## Quick Reference

### Essential Commands
```python
# Syringe
syringe.initialize()                    # Required first step
syringe.set_speed_uL_min(speed)        # Set flow rate
syringe.aspirate(volume)               # Draw fluid
syringe.dispense(volume)               # Eject fluid

# Valve  
valve.position(port_number)            # Select port

# Status
syringe.print_volume_in_syringe()      # Check volume
syringe.get_actual_set_speed()         # Check speed
```

### Typical Operating Sequence
```python
# 1. Initialize devices
syringe.initialize()
valve.position(1)

# 2. Set operating parameters  
syringe.set_speed_uL_min(2000)

# 3. Perform operations
valve.position(3)                      # Select source
syringe.aspirate(500)                  # Draw fluid
valve.position(6)                      # Select destination  
syringe.dispense(500)                  # Deliver fluid
```

---

**For complex automated workflows and analytical procedures, see [SI Workflows](si-workflows.md).**