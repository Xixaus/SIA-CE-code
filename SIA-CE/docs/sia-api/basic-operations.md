# Basic SIA Operations

Learn how to control syringe pumps and valve selectors for automated liquid handling.

## Device Initialization

### Syringe Pump Setup

```python
from SIA_API.devices import SyringeController

# Initialize syringe pump
syringe = SyringeController(
    port="COM3",           # Serial port
    syringe_size=1000,     # 1000 µL syringe
    address="/1",          # Device address (default)
    baudrate=9600,         # Communication speed
    print_info=True        # Show syringe specifications
)

# Output:
# Syringe size: 1000 µL
# Syringe resolution: 0.33 µL
# Minimum flow rate: 50.0 µL/min
# Maximum flow rate: 60000.0 µL/min
```

### Valve Selector Setup

```python
from SIA_API.devices import ValveSelector

# Initialize valve selector
valve = ValveSelector(
    port="COM4",          # Serial port
    num_positions=8,      # 8-position valve
    prefix="/Z",          # Command prefix (VICI standard)
    baudrate=9600         # Communication speed
)
```

### Testing Communication

```python
# Test syringe communication
response = syringe.send_command("?", get_response=True)
print(f"Syringe response: {response}")

# Test valve - should move to position 1
valve.position(1)
print("Valve moved to position 1")
```

## Syringe Operations

### Initialization

Always initialize the syringe before use:

```python
# Initialize to home position
syringe.initialize()
print("Syringe initialized to zero position")
```

!!! warning "Initialization Behavior"
    - Syringe moves to absolute zero position
    - Volume counter resets to 0
    - May take several seconds for large syringes

### Flow Rate Control

```python
# Set flow rate in µL/min
syringe.set_speed_uL_min(1000)  # 1 mL/min

# Different speeds for different operations
SPEED_FAST = 3500      # Fast transfer
SPEED_NORMAL = 2000    # Normal dispensing
SPEED_SLOW = 1000      # Precise operations
SPEED_MIXING = 500     # Gentle mixing

# Example: Variable speed operation
syringe.set_speed_uL_min(SPEED_FAST)
syringe.aspirate(500)
syringe.set_speed_uL_min(SPEED_SLOW)
syringe.dispense(500)
```

### Aspiration (Drawing Fluid)

```python
# Aspirate specific volume
syringe.aspirate(500)  # Draw 500 µL

# Aspirate with non-blocking mode
syringe.aspirate(300, wait=False)  # Returns immediately

# Fill entire syringe
syringe.aspirate()  # Aspirates to full capacity

# Check current volume
syringe.print_volume_in_syringe()
# Output: The current volume in the syringe is: 500 µl
```

### Dispensing

```python
# Dispense specific volume
syringe.dispense(250)  # Dispense 250 µL

# Dispense all contents
syringe.dispense()  # Empties syringe completely

# Non-blocking dispense
syringe.dispense(100, wait=False)
```

### Volume Tracking

The API automatically tracks syringe contents:

```python
# Example with volume tracking
syringe.initialize()  # Volume: 0 µL
syringe.aspirate(600)  # Volume: 600 µL
syringe.dispense(200)  # Volume: 400 µL

# This would raise an error:
try:
    syringe.aspirate(800)  # Would exceed 1000 µL capacity!
except ValueError as e:
    print(f"Error: {e}")
```

## Valve Operations

### Basic Positioning

```python
# Move to specific port
valve.position(1)  # Move to port 1
valve.position(5)  # Move to port 5

# Multiple attempts for reliability
valve.position(3, num_attempts=5)  # Try up to 5 times
```

### Valve Configuration

```python
# Configure valve type (for syringe-mounted valves)
syringe.configuration_valve_type('3-Port')

# Available valve types:
# - 'No': No valve
# - '3-Port': Standard 3-way valve
# - '4-Port': 4-way valve
# - '6-Port distribution': 6-port distribution valve
# - '12-Port distribution': 12-port distribution valve
```

### Syringe Valve Control

For valves mounted on the syringe:

```python
# 3-way valve positions
syringe.valve_in()   # Input position
syringe.valve_out()  # Output position
syringe.valve_up()   # Up/bypass position
```

## Combined Operations

### Simple Transfer

```python
def transfer_liquid(source_port, dest_port, volume):
    """Transfer liquid between ports."""
    # Select source
    valve.position(source_port)
    
    # Aspirate
    syringe.aspirate(volume)
    
    # Select destination
    valve.position(dest_port)
    
    # Dispense
    syringe.dispense(volume)

# Example: Transfer 500 µL from port 3 to port 6
transfer_liquid(3, 6, 500)
```

### Mixing Operation

```python
def mix_by_aspiration(port, volume, cycles=3, speed=1000):
    """Mix solution by repeated aspiration/dispensing."""
    valve.position(port)
    syringe.set_speed_uL_min(speed)
    
    for _ in range(cycles):
        syringe.aspirate(volume)
        syringe.dispense(volume)
    
    print(f"Mixing complete at port {port}")

# Mix 200 µL at port 4
mix_by_aspiration(4, 200, cycles=5, speed=800)
```

### Dilution

```python
def dilute_sample(sample_port, diluent_port, output_port, 
                  sample_vol, diluent_vol):
    """Perform sample dilution."""
    # Aspirate diluent first (reverse order prevents contamination)
    valve.position(diluent_port)
    syringe.aspirate(diluent_vol)
    
    # Aspirate sample
    valve.position(sample_port)
    syringe.aspirate(sample_vol)
    
    # Dispense mixture
    valve.position(output_port)
    syringe.dispense()

# Example: 1:10 dilution
dilute_sample(
    sample_port=4,
    diluent_port=3,  # DI water
    output_port=6,
    sample_vol=100,
    diluent_vol=900
)
```

### Multi-Segment Aspiration

```python
def create_sample_sandwich(sample_port, buffer_port, volume_each=50):
    """Create buffer-sample-buffer sandwich."""
    # First buffer segment
    valve.position(buffer_port)
    syringe.aspirate(volume_each)
    
    # Sample segment
    valve.position(sample_port)
    syringe.aspirate(volume_each)
    
    # Second buffer segment
    valve.position(buffer_port)
    syringe.aspirate(volume_each)
    
    print("Sample sandwich created")

create_sample_sandwich(sample_port=4, buffer_port=3)
```

## Practical Examples

### System Priming

```python
def prime_system(ports_to_prime, prime_volume=200):
    """Prime all system lines."""
    waste_port = 1
    
    for port in ports_to_prime:
        print(f"Priming port {port}...")
        
        # Flush line
        valve.position(port)
        syringe.aspirate(prime_volume)
        
        # Discard to waste
        valve.position(waste_port)
        syringe.dispense()
    
    print("System priming complete")

# Prime all reagent lines
prime_system([2, 3, 4, 5])
```

### Automated Cleaning

```python
def clean_system(rinse_volume=500, rinse_cycles=3):
    """Automated system cleaning procedure."""
    water_port = 3
    waste_port = 1
    
    for cycle in range(rinse_cycles):
        print(f"Rinse cycle {cycle + 1}/{rinse_cycles}")
        
        # Aspirate rinse solution
        valve.position(water_port)
        syringe.aspirate(rinse_volume)
        
        # Flush through system
        valve.position(waste_port)
        syringe.dispense(rinse_volume)
    
    # Final air purge
    valve.position(2)  # Air port
    syringe.aspirate(200)
    valve.position(waste_port)
    syringe.dispense()
    
    print("Cleaning complete")

clean_system()
```

### Reagent Addition

```python
def add_internal_standard(sample_ports, is_port, is_volume=10):
    """Add internal standard to multiple samples."""
    
    for port in sample_ports:
        # Aspirate internal standard
        valve.position(is_port)
        syringe.aspirate(is_volume)
        
        # Add to sample
        valve.position(port)
        syringe.dispense(is_volume)
        
        # Mix
        syringe.aspirate(50)
        syringe.dispense(50)
    
    print(f"Added {is_volume} µL IS to {len(sample_ports)} samples")

# Add to samples in ports 6-10
add_internal_standard(range(6, 11), is_port=5)
```

## Error Handling

### Communication Errors

```python
try:
    syringe.initialize()
except serial.SerialException as e:
    print(f"Communication error: {e}")
    # Check COM port, cable connection, device power
```

### Volume Errors

```python
try:
    syringe.aspirate(2000)  # Exceeds 1000 µL syringe
except ValueError as e:
    print(f"Volume error: {e}")
    # Adjust volume or use multiple cycles
```

### Safe Operations

```python
def safe_aspirate(volume):
    """Aspirate with overflow protection."""
    available = syringe.syringe_size - syringe.volume_counter
    
    if volume > available:
        print(f"Requested {volume} µL, only {available} µL available")
        print("Dispensing current contents first...")
        valve.position(1)  # Waste
        syringe.dispense()
    
    syringe.aspirate(volume)

# Use safe aspiration
safe_aspirate(800)
```

## Best Practices

### 1. Always Initialize

```python
# Start every session with initialization
syringe.initialize()
print("Ready for operations")
```

### 2. Use Appropriate Speeds

```python
# Match speed to operation
syringe.set_speed_uL_min(5000)  # Air moves fast
syringe.set_speed_uL_min(1000)  # Liquids move slower
syringe.set_speed_uL_min(500)   # Viscous liquids move slowly
```

### 3. Prevent Cross-Contamination

```python
# Aspirate in reverse order of reactivity
# 1. Diluent/buffer (least reactive)
# 2. Sample (most reactive)
```

### 4. Include Air Gaps

```python
# Separate different liquids with air
valve.position(air_port)
syringe.aspirate(10)  # Small air gap
valve.position(reagent_port)
syringe.aspirate(100)
```

### 5. Regular Maintenance

```python
def daily_maintenance():
    """Daily system maintenance routine."""
    # Initialize
    syringe.initialize()
    
    # Flush all lines
    for port in range(1, 9):
        valve.position(port)
        syringe.aspirate(200)
        valve.position(1)  # Waste
        syringe.dispense()
    
    print("Daily maintenance complete")
```

!!! tip "Next Steps"
    Learn about [Pre-built Workflows](workflows.md) for complex automated procedures.