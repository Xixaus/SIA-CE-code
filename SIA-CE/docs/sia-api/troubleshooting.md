# Troubleshooting

## Communication Errors

### SerialException: Could not open port
**Cause:** COM port access issues
```python
# Error message
SerialException: could not open port 'COM3': Access is denied
```

**Solutions:**
    - Close other applications using the port (HyperTerminal, Arduino IDE)
    - Run Python as Administrator
    - Check Device Manager for port conflicts
    - Verify correct COM port number
    - Check cable connections and device power

### TimeoutError: No response from device
**Cause:** Device not responding within timeout period

**Solutions:**
- Check device power and connections
- Verify baud rate settings (9600 vs 19200)
- Increase timeout in send_command()
- Test with device manufacturer software
- Check for loose serial connections

### Communication Test
```python
# Test syringe communication
try:
    response = syringe.send_command("?", get_response=True)
    print(f"Syringe OK: {response}")
except Exception as e:
    print(f"Syringe error: {e}")

# Test valve communication  
try:
    valve.position(1)
    print("Valve OK")
except Exception as e:
    print(f"Valve error: {e}")
```

## Volume Tracking Issues

### Volume Counter Mismatch
**Problem:** Syringe contains liquid but volume counter shows 0 after initialization

**Cause:** Manual operations or interrupted sequences leave liquid in syringe, but initialization resets counter to 0

**How initialization works:**
```python
syringe.initialize()  # Automatically sets valve to position 1 (waste)
                     # Dispenses any existing content to waste
                     # Moves syringe to home position
                     # Resets volume counter to 0
```

**Solutions:**

**Option 1: Normal initialization (recommended)**
```python
valve.position(1)     # Ensure waste position (done automatically)
syringe.initialize()  # This handles everything automatically
```

**Option 2: Manual pre-emptying if unsure**
```python
valve.position(1)     # Waste port
syringe.dispense()    # Empty completely first
```

**Option 3: Manual volume correction (if known)**
```python
# If you know actual contents, manually set counter
syringe.volume_counter = actual_volume  # Set to known value
```

### Volume Overflow Errors
```python
# Error message
ValueError: The drawn volume in the syringe would be 1200 µl, which exceeds the syringe capacity of 1000 µl!
```

**Solutions:**
- Check current volume: `syringe.print_volume_in_syringe()`
- Use multiple cycles for large volumes
- Empty syringe before large aspiration: `syringe.dispense()`

### Volume Underflow Errors
```python
# Error message  
ValueError: The expelled volume in the syringe would be negative!
```

**Solutions:**
- Check actual syringe contents
- Re-initialize if counter is wrong: `syringe.initialize()`
- Use `syringe.dispense()` without volume to empty completely

## Flow Rate Errors

### Speed Out of Range
```python
# Error messages
ValueError: Set flow rate too small! Minimum allowed rate is 50.0 µL/min
ValueError: Set flow rate too large! Maximum allowed rate is 60000.0 µL/min
```

**Solutions:**
- Check syringe size - limits depend on capacity
- Use appropriate speed for syringe size:
  - 100 µL syringe: 5-6000 µL/min
  - 1000 µL syringe: 50-60000 µL/min
  - 5000 µL syringe: 250-300000 µL/min

## Valve Position Errors

### Invalid Position
```python
# Error message
ValueError: Position 10 is out of range (1-8)
```

**Solutions:**
- Check valve configuration: number of positions
- Verify position commands are within range
- Use `valve.position(pos, num_attempts=5)` for reliability

### Valve Not Moving
**Symptoms:** No error but valve doesn't change position

**Solutions:**
- Increase number of attempts: `valve.position(1, num_attempts=5)`
- Check valve power supply
- Test with manufacturer software
- Verify command protocol (prefix/suffix)

## System Performance Issues

### Slow Operations
**Causes:** 

- Transfer lines too long (air compression)
- Speed set too low
- Air bubbles in liquid lines

**Solutions:**

- Minimize air in transfer lines
- Replace air with liquid for long lines  
- Increase speed for non-critical operations
- Use shorter tubing when possible

### Inaccurate Volumes
**Causes:**

- Air compression in long lines
- Dead volume not accounted for
- Speed too fast for viscous liquids

**Solutions:**
- Measure actual transfer volumes experimentally
- Use appropriate speeds for liquid viscosity
- Account for dead volumes in calculations
- Minimize air gaps in liquid lines

### Cross-Contamination
**Causes:**
- Insufficient cleaning between samples
- Air bubbles not separating liquids properly
- Inadequate flushing volumes

**Solutions:**
- Increase bubble sizes between incompatible liquids
- Use adequate cleaning volumes
- Clean needle between sample types
- Sequence from cleanest to dirtiest samples

### Quick Fixes
**Emergency Reset**
```python
# Complete system reset
syringe.emergency_stop()  # Stop all operations
valve.position(1)         # Safe position
syringe.initialize()      # Reset to home
```