# Port Configuration Guide

Detailed guide for configuring and optimizing SIA valve port assignments.

## Default Port Configuration

The standard port assignments are designed for typical analytical workflows:

```python
from SIA_API.methods import PortConfig, DEFAULT_PORTS

# Default configuration
print(f"Waste: Port {DEFAULT_PORTS.waste_port}")        # Port 1
print(f"Air: Port {DEFAULT_PORTS.air_port}")            # Port 2
print(f"DI Water: Port {DEFAULT_PORTS.di_port}")        # Port 3
print(f"Transfer: Port {DEFAULT_PORTS.transfer_port}")  # Port 4
print(f"Methanol: Port {DEFAULT_PORTS.meoh_port}")      # Port 5
```

## Port Assignment Principles

### Priority Positions

1. **Port 1 - Waste**
   - Always accessible
   - Shortest path from syringe
   - Frequent use

2. **Port 2 - Air/Gas**
   - Used for segmentation
   - Cleaning operations
   - Second most frequent

3. **Port 3 - Primary Diluent**
   - Usually DI water
   - High volume usage
   - Easy access

4. **Port 4 - Transfer Line**
   - Connection to CE
   - Critical path
   - Minimize dead volume

### Optimization Strategies

```python
# Optimize for specific workflow
class WorkflowOptimizedPorts(PortConfig):
    """Ports optimized for protein analysis."""
    
    waste_port = 1          # Always waste
    air_port = 2            # Air for segments
    di_port = 3             # Water for dilution
    transfer_port = 8       # Last port - shortest CE path
    meoh_port = 4           # Organic cleanup
    buffer_ph7_port = 5     # Running buffer
    buffer_ph5_port = 6     # Acidic buffer
    standard_port = 7       # Internal standard
```

## Custom Configurations

### Method 1: Using create_custom_config()

```python
from SIA_API.methods import create_custom_config

# Simple customization
config = create_custom_config(
    waste_port=8,
    meoh_port=6
)

# Use in workflow
workflow = PreparedSIAMethods(
    ce_api, syringe, valve,
    ports_config=config
)
```

### Method 2: Direct PortConfig Creation

```python
from dataclasses import dataclass
from SIA_API.methods import PortConfig

@dataclass
class BiochemistryPorts(PortConfig):
    """Port configuration for biochemistry lab."""
    
    # Standard ports
    waste_port: int = 1
    air_port: int = 2
    di_port: int = 3
    transfer_port: int = 12  # 12-port valve
    
    # Additional reagents
    meoh_port: int = 4
    acn_port: int = 5        # Acetonitrile
    buffer_a_port: int = 6   # Buffer A
    buffer_b_port: int = 7   # Buffer B
    enzyme_port: int = 8     # Enzyme solution
    substrate_port: int = 9  # Substrate
    quench_port: int = 10    # Reaction quench
    standard_port: int = 11  # Internal standard

# Use custom configuration
config = BiochemistryPorts()
workflow = PreparedSIAMethods(ce_api, syringe, valve, config)
```

### Method 3: Runtime Configuration

```python
def configure_for_experiment(experiment_type):
    """Dynamic port configuration based on experiment."""
    
    if experiment_type == "protein":
        return create_custom_config(
            waste_port=1,
            air_port=2,
            di_port=3,
            transfer_port=8,
            meoh_port=4
        )
    
    elif experiment_type == "small_molecule":
        return create_custom_config(
            waste_port=1,
            air_port=2,
            di_port=4,      # Swap water and transfer
            transfer_port=3,  # Shorter path for organics
            meoh_port=5
        )
    
    else:
        return DEFAULT_PORTS
```

## Port Usage in Workflows

### Accessing Ports in Methods

```python
# Using configured ports
workflow.prepare_continuous_flow(
    solvent_port=workflow.ports.meoh_port  # Uses configured port
)

# Override specific port
workflow.continuous_fill(
    vial=15,
    volume=1000,
    solvent_port=7,  # Direct port specification
    waste_port=1     # Override default
)
```

### Adding Custom Ports

```python
class ExtendedWorkflow(PreparedSIAMethods):
    """Workflow with additional reagent ports."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom port definitions
        self.custom_ports = {
            'enzyme': 8,
            'substrate': 9,
            'inhibitor': 10
        }
    
    def add_enzyme(self, vial, enzyme_volume):
        """Add enzyme using custom port."""
        self.batch_fill(
            vial=vial,
            volume=enzyme_volume,
            solvent_port=self.custom_ports['enzyme']
        )
```

## Multi-Valve Systems

### Dual Valve Configuration

```python
class DualValveSystem:
    """System with two selection valves."""
    
    def __init__(self, ce_api, syringe, valve1, valve2):
        self.ce = ce_api
        self.syringe = syringe
        self.valve_main = valve1    # 8-port for common reagents
        self.valve_special = valve2  # 12-port for samples
        
        # Port mapping
        self.main_ports = PortConfig()  # Standard configuration
        self.sample_ports = {
            f'sample_{i}': i for i in range(1, 13)
        }
    
    def select_sample(self, sample_number):
        """Switch to sample valve and position."""
        # In practice, add valve switching logic
        self.valve_special.position(sample_number)
```

## Physical Setup Considerations

### Tubing Length Optimization

```python
# Port usage frequency analysis
def analyze_port_usage(workflow_steps):
    """Analyze port access patterns."""
    
    port_counts = {}
    
    for step in workflow_steps:
        port = step.get('port')
        port_counts[port] = port_counts.get(port, 0) + 1
    
    # Sort by frequency
    sorted_ports = sorted(
        port_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    print("Port usage frequency:")
    for port, count in sorted_ports:
        print(f"  Port {port}: {count} accesses")
    
    return sorted_ports

# Optimize physical layout based on usage
```

### Dead Volume Minimization

```python
# Calculate dead volumes
def calculate_dead_volumes(port_config, tubing_specs):
    """Calculate dead volume for each port."""
    
    dead_volumes = {}
    
    for port_name, port_num in vars(port_config).items():
        if port_name.endswith('_port'):
            # Calculate based on tubing
            length_cm = tubing_specs[port_num]['length']
            id_mm = tubing_specs[port_num]['id']
            
            # Volume in µL
            volume = 3.14159 * (id_mm/2)**2 * length_cm * 10
            dead_volumes[port_name] = round(volume, 2)
    
    return dead_volumes
```

## Validation Tools

### Port Configuration Validator

```python
from SIA_API.methods import validate_config

def comprehensive_port_validation(config, valve_positions=8):
    """Validate port configuration thoroughly."""
    
    # Basic validation
    try:
        validate_config(config)
        print("✓ Basic validation passed")
    except ValueError as e:
        print(f"✗ Basic validation failed: {e}")
        return False
    
    # Check port range
    ports = [
        config.waste_port, config.air_port, 
        config.di_port, config.transfer_port, 
        config.meoh_port
    ]
    
    if max(ports) > valve_positions:
        print(f"✗ Port {max(ports)} exceeds valve positions ({valve_positions})")
        return False
    
    # Check critical ports
    if config.waste_port != 1:
        print("⚠ Warning: Waste not on port 1 (non-standard)")
    
    if config.transfer_port == config.waste_port:
        print("✗ Error: Transfer and waste on same port!")
        return False
    
    print("✓ Comprehensive validation passed")
    return True

# Test configuration
custom = create_custom_config(waste_port=8, transfer_port=8)
comprehensive_port_validation(custom)
```

### Runtime Port Verification

```python
def verify_port_contents(valve, expected_contents):
    """Verify correct solutions at each port."""
    
    print("Port verification procedure:")
    print("Place pH paper at output")
    
    for port, content in expected_contents.items():
        valve.position(port)
        print(f"\nPort {port} - Expected: {content}")
        
        # Dispense small amount
        syringe.aspirate(50)
        input("Check output and press Enter...")
        
        # Record result
        result = input("Correct? (y/n): ")
        if result.lower() != 'y':
            print(f"⚠ Port {port} mismatch!")
```

## Common Configurations

### Analytical Chemistry Lab

```python
ANALYTICAL_CONFIG = create_custom_config(
    waste_port=1,
    air_port=2,
    di_port=3,
    transfer_port=8,  # Last port for CE
    meoh_port=4       # Organic solvent
)
```

### Biochemistry Lab

```python
BIOCHEM_CONFIG = create_custom_config(
    waste_port=1,
    air_port=2,
    di_port=3,        # PBS buffer
    transfer_port=6,  # Middle port
    meoh_port=7       # Rarely used
)
```

### High-Throughput Lab

```python
HIGH_THROUGHPUT_CONFIG = create_custom_config(
    waste_port=1,     # Frequent access
    air_port=2,       # Segmentation
    di_port=8,        # Opposite side
    transfer_port=4,  # Central
    meoh_port=5       # Adjacent to transfer
)
```

## Troubleshooting Port Issues

### Wrong Port Selected

```python
def debug_port_selection():
    """Debug valve port selection."""
    
    print("Valve position test:")
    
    for port in range(1, 9):
        print(f"\nMoving to port {port}")
        valve.position(port)
        
        # Visual confirmation
        confirmed = input("Correct position? (y/n): ")
        if confirmed.lower() != 'y':
            print(f"ERROR: Port {port} mismatch")
            
            # Try multiple attempts
            for attempt in range(3):
                valve.position(port, num_attempts=5)
                if input("Correct now? (y/n): ").lower() == 'y':
                    print(f"Fixed after {attempt+1} attempts")
                    break
```

### Port Contamination

```python
def clean_specific_port(port, flush_volume=1000):
    """Deep clean a specific port."""
    
    print(f"Cleaning port {port}")
    
    # Flush with air
    valve.position(2)  # Air
    syringe.aspirate(200)
    valve.position(port)
    syringe.dispense()
    
    # Flush with solvent
    valve.position(3)  # Water
    syringe.aspirate(flush_volume)
    valve.position(port)
    syringe.dispense()
    
    # Final air purge
    valve.position(2)
    syringe.aspirate(200)
    valve.position(port)
    syringe.dispense()
```

## Best Practices

1. **Document your configuration**
   ```python
   # Always document port assignments
   """
   Port Configuration for Project X:
   1 - Waste (red tubing)
   2 - Air
   3 - DI Water (clear tubing)
   4 - Transfer to CE (PEEK, 0.25mm ID)
   5 - Methanol (yellow tubing)
   6 - Buffer pH 7.4 (blue tubing)
   7 - Internal Standard (green tubing)
   8 - Unused
   """
   ```

2. **Use consistent color coding for tubing**

3. **Label all reservoirs clearly**

4. **Regular validation of port contents**

5. **Keep spare fittings for each port type**

!!! tip "Configuration Management"
    Save your port configurations in a separate file for easy reuse and sharing with team members.