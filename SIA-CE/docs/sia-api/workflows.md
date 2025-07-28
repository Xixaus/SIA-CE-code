# SI Workflows

## Overview

SI Workflows provide high-level automation through the `PreparedSIAMethods` class. These pre-built methods combine syringe and valve operations into complete procedures and integrate with ChemStation CE systems.

## Setup

```python
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

# Initialize components
ce_api = ChemstationAPI()
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)

# Create workflow controller
workflow = PreparedSIAMethods(
    chemstation_controller=ce_api,
    syringe_device=syringe,
    valve_device=valve
)
```

## Available Methods

### System Operations

**`system_initialization_and_cleaning(waste_vial=50, bubble=20)`**
Complete system preparation and cleaning procedure:
- Syringe initialization to home position
- Loop flushing with air
- Methanol cleaning cycle followed by DI water rinsing
- Transfer line conditioning
- Creation of separating bubbles for contamination prevention

**`load_to_replenishment(vial_number)`**
Load specified vial from carousel to CE replenishment position for filling operations. Essential for automated vial handling.

**`unload_from_replenishment()`**
Return vial from replenishment position back to carousel after processing is complete.

**`clean_needle(volume_flush, wash_vial=48)`**
Clean dispensing needle to prevent cross-contamination:
- Partial dispensing in wash vial to remove sample residue
- Remainder dispensed in air to clear needle completely
- Critical for preventing carryover between different samples

### Continuous Flow Operations

**`prepare_continuous_flow(solvent_port, waste_vial=50, bubble_volume=10, transfer_coil_flush=500, speed=1500)`**
Prepare system for continuous flow operations:
- Fill holding coil and transfer line with solvent
- Create separating bubbles to prevent contamination
- Optimize system for rapid sequential dispensing of same solvent
- One-time setup for processing multiple vials

**`continuous_fill(vial, volume, solvent_port, flush_needle=None, speed=2000)`**
Execute continuous flow filling operation:
- Fast dispensing through pre-filled solvent line
- Automatic volume management with multiple cycles for large volumes
- Optional needle cleaning between vials
- Ideal for high-throughput operations

**Key advantages:** Fastest method for multiple vials with same solvent. Transfer line pre-filled with solvent eliminates air compression issues and enables rapid sequential dispensing.

### Batch Flow Operations

**`prepare_batch_flow(solvent_port, waste_vial=50, bubble_volume=10, transfer_coil_volume=550, speed=1500)`**
Prepare system for batch operations:
- Fill transfer line with air instead of solvent
- Set up for independent, air-driven dispensing operations
- Each operation is completely separate from previous ones
- Easy solvent changeover between operations

**`batch_fill(vial, volume, solvent_port, transfer_line_volume=550, bubble_volume=10, flush_needle=None, unload=True, wait=None)`**
Execute single batch filling operation:
- Air-driven dispensing where air pushes solvent through transfer line
- Complete independence between operations
- Automatic air bubble creation for solvent isolation
- Optional wait time after dispensing for settling

**`batch_fill_multiple_solvents(vial, solvent_ports, volumes, air_push_volume=15, solvent_speeds=None, flush_needle=None)`**
Fill single vial with multiple solvents in sequence:

- Sequential aspiration of different solvents from multiple ports
- Air bubbles automatically separate each solvent in holding coil
- Final high-speed air push delivers complete mixture to vial
- Individual speed control for each solvent type (viscosity compensation)

**Key advantages:** Complete contamination prevention, easy solvent changeover, ideal for different solvents per vial or single operations.

### Sample Processing

**`homogenize_sample(vial, speed, homogenization_time, flush_needle=None, air_speed=5000)`**
Pneumatic mixing of sample in vial:
- Controlled air bubbling through sample for thorough mixing
- Adjustable speed (bubbling rate) and duration
- Particularly effective for viscous samples or protein solutions
- Air-driven mixing prevents mechanical contamination
- Optional needle cleaning after mixing

**Parameters:**
- `speed`: Bubbling rate in µL/min (typically 500-2000)
- `homogenization_time`: Duration in seconds (typically 15-60)
- `air_speed`: Rate for air aspiration (typically 5000 µL/min for fast air handling)

## CE Integration

**Carousel Control:**
- Automatic vial loading/unloading
- Precise positioning for filling
- Collision avoidance

**Analysis Control:**
- Start CE analysis after sample preparation  
- Method selection and sample tracking
- Automated sequence execution

## Method Selection

| Operation | Continuous Flow | Batch Flow |
|-----------|----------------|------------|
| **Multiple vials, same solvent** | ✓ Fast | ✗ Slower |
| **Different solvents** | ✗ Difficult | ✓ Easy |
| **Contamination sensitive** | ✗ Higher risk | ✓ Lower risk |
| **Single vial** | ✗ Overkill | ✓ Ideal |