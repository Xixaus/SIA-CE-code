# Your First Automated Analysis

This tutorial will guide you through your first automated CE analysis using the SIA-CE system. We'll analyze a single sample with automated sample preparation.

## What We'll Do

1. Initialize the SIA system
2. Prepare a sample with automated dilution
3. Load the sample for CE analysis
4. Run the separation
5. Monitor the analysis progress

## Prerequisites

- ChemStation is running with the macro loaded
- SIA devices are connected and powered on
- You have identified your COM ports
- Sample and reagents are prepared

## Step 1: System Setup

```python
# Import required modules
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods
import time

# Initialize ChemStation connection
print("Connecting to ChemStation...")
ce_api = ChemstationAPI()
print("✓ ChemStation connected")

# Initialize SIA devices
print("Initializing SIA devices...")
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)
print("✓ SIA devices connected")

# Create workflow controller
workflow = PreparedSIAMethods(ce_api, syringe, valve)
print("✓ Workflow controller ready")
```

## Step 2: System Initialization

```python
# Perform complete system initialization
print("\nInitializing and cleaning system...")
print("This will take about 2 minutes")

workflow.system_initialization_and_cleaning(
    waste_vial=50,  # Vial 50 for waste collection
    bubble=20       # 20 µL separating bubble
)

print("✓ System initialized and ready")
```

## Step 3: Sample Information

```python
# Define our sample parameters
sample_info = {
    'vial': 15,
    'name': 'Protein_Sample_001',
    'method': 'CE_Protein_Analysis',
    'dilution': 10,  # 1:10 dilution
    'volume': 1500   # µL final volume
}

print(f"\nSample: {sample_info['name']}")
print(f"Location: Vial {sample_info['vial']}")
print(f"Dilution: 1:{sample_info['dilution']}")
```

## Step 4: Validate Prerequisites

```python
# Check everything is ready
print("\nValidating system...")

try:
    # Check sample vial exists
    ce_api.validation.validate_vial_in_system(sample_info['vial'])
    print("✓ Sample vial present")
    
    # Check waste vials
    ce_api.validation.validate_vial_in_system(48)  # Wash vial
    ce_api.validation.validate_vial_in_system(50)  # Waste vial
    print("✓ Wash and waste vials present")
    
    # Check method exists
    ce_api.validation.validate_method_name(sample_info['method'])
    print("✓ CE method found")
    
    # Check system is ready
    if ce_api.system.status() == "STANDBY":
        print("✓ CE system ready")
    else:
        print("⚠ Waiting for system...")
        ce_api.system.wait_for_ready(timeout=60)
        
except Exception as e:
    print(f"✗ Validation failed: {e}")
    print("Please fix the issue and restart")
    exit(1)

print("\nAll checks passed!")
```

## Step 5: Automated Sample Preparation

```python
# Prepare for sample dilution
print(f"\nPreparing 1:{sample_info['dilution']} dilution...")

# Calculate volumes
sample_volume = sample_info['volume'] / sample_info['dilution']
diluent_volume = sample_info['volume'] - sample_volume

print(f"Sample volume: {sample_volume:.0f} µL")
print(f"Diluent volume: {diluent_volume:.0f} µL")

# Prepare for continuous flow with DI water
workflow.prepare_continuous_flow(
    solvent_port=3,  # DI water port
    speed=2000       # 2 mL/min
)

# Note: In a real workflow, you would add the sample first,
# then diluent. For this demo, we'll add diluent to an empty vial
print("\nAdding diluent to vial...")
workflow.continuous_fill(
    vial=sample_info['vial'],
    volume=diluent_volume,
    solvent_port=3,
    flush_needle=50
)

print("✓ Diluent added")

# In practice, you would now add your sample
print("\n⚠ Add sample to vial manually or use liquid handling robot")
input("Press Enter when sample is added...")

# Homogenize the diluted sample
print("\nMixing sample...")
workflow.homogenize_sample(
    vial=sample_info['vial'],
    speed=1000,              # 1 mL/min bubbling
    homogenization_time=30,  # 30 seconds
    flush_needle=50
)

print("✓ Sample prepared and mixed")
```

## Step 6: CE Analysis Setup

```python
# Load vials for CE analysis
print("\nSetting up CE analysis...")

# Load sample vial to inlet
ce_api.ce.load_vial_to_position(sample_info['vial'], "inlet")
print("✓ Sample loaded to inlet")

# Load waste vial to outlet
ce_api.ce.load_vial_to_position(48, "outlet")
print("✓ Waste vial loaded to outlet")

# Condition capillary
print("\nConditioning capillary...")
ce_api.ce.flush_capillary(time_flush=60.0)
print("✓ Capillary conditioned")
```

## Step 7: Run Analysis

```python
# Start the CE analysis
print(f"\nStarting analysis: {sample_info['name']}")
print(f"Method: {sample_info['method']}")

ce_api.method.execution_method_with_parameters(
    vial=sample_info['vial'],
    method_name=sample_info['method'],
    sample_name=sample_info['name'],
    comment="Tutorial first analysis",
    subdirectory_name="Tutorial_Runs"
)

print("✓ Analysis started")
```

## Step 8: Monitor Progress

```python
# Monitor the running analysis
print("\nMonitoring analysis...")
print("Press Ctrl+C to stop monitoring (analysis will continue)")

try:
    start_time = time.time()
    
    while ce_api.system.method_on():
        # Get progress information
        elapsed = ce_api.system.get_elapsed_analysis_time()
        total = ce_api.system.get_analysis_time()
        remaining = ce_api.system.get_remaining_analysis_time()
        status = ce_api.system.status()
        
        # Calculate percentage
        if total > 0:
            progress = (elapsed / total) * 100
        else:
            progress = 0
        
        # Display progress
        print(f"\rStatus: {status} | Progress: {progress:.1f}% | "
              f"Remaining: {remaining:.1f} min", end='')
        
        time.sleep(10)  # Update every 10 seconds
        
except KeyboardInterrupt:
    print("\n\nStopped monitoring (analysis continues)")

# Analysis complete
total_time = (time.time() - start_time) / 60
print(f"\n\n✓ Analysis complete! Total time: {total_time:.1f} minutes")
```

## Step 9: Cleanup

```python
# Return vials to carousel
print("\nCleaning up...")

ce_api.ce.unload_vial_from_position("inlet")
ce_api.ce.unload_vial_from_position("outlet")

print("✓ Vials returned to carousel")
print("\nFirst analysis tutorial complete!")
```

## Complete Script

Here's the complete script in one block:

```python
# First Analysis Tutorial - Complete Script
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods
import time

def first_analysis():
    """Run your first automated CE analysis with SIA sample prep."""
    
    # Initialize all systems
    print("=== SIA-CE First Analysis Tutorial ===\n")
    
    ce_api = ChemstationAPI()
    syringe = SyringeController(port="COM3", syringe_size=1000)
    valve = ValveSelector(port="COM4", num_positions=8)
    workflow = PreparedSIAMethods(ce_api, syringe, valve)
    
    # Sample parameters
    sample_vial = 15
    sample_name = "Tutorial_Sample_001"
    ce_method = "CE_Protein_Analysis"
    
    # Initialize system
    print("Initializing system...")
    workflow.system_initialization_and_cleaning()
    
    # Validate prerequisites
    print("\nValidating...")
    ce_api.validation.validate_vial_in_system(sample_vial)
    ce_api.validation.validate_method_name(ce_method)
    
    # Prepare sample (dilution)
    print("\nPreparing sample...")
    workflow.prepare_continuous_flow(solvent_port=3)
    workflow.continuous_fill(vial=sample_vial, volume=900, solvent_port=3)
    
    input("\nAdd 100 µL sample to vial and press Enter...")
    
    workflow.homogenize_sample(vial=sample_vial, speed=1000, 
                               homogenization_time=30)
    
    # Setup CE
    print("\nSetting up CE...")
    ce_api.ce.load_vial_to_position(sample_vial, "inlet")
    ce_api.ce.load_vial_to_position(48, "outlet")
    ce_api.ce.flush_capillary(60.0)
    
    # Run analysis
    print("\nStarting analysis...")
    ce_api.method.execution_method_with_parameters(
        vial=sample_vial,
        method_name=ce_method,
        sample_name=sample_name
    )
    
    # Monitor
    while ce_api.system.method_on():
        remaining = ce_api.system.get_remaining_analysis_time()
        print(f"\r{remaining:.1f} minutes remaining...", end='')
        time.sleep(30)
    
    # Cleanup
    print("\n\nCleaning up...")
    ce_api.ce.unload_vial_from_position("inlet")
    ce_api.ce.unload_vial_from_position("outlet")
    
    print("\n✓ Analysis complete!")

if __name__ == "__main__":
    first_analysis()
```

## What You Learned

In this tutorial, you:

1. ✓ Connected to ChemStation and SIA devices
2. ✓ Initialized the complete system
3. ✓ Validated all prerequisites
4. ✓ Performed automated sample dilution
5. ✓ Mixed samples using pneumatic homogenization
6. ✓ Set up and ran a CE analysis
7. ✓ Monitored analysis progress
8. ✓ Cleaned up after analysis

## Next Steps

- Try modifying the dilution ratio
- Run multiple samples in sequence
- Explore different CE methods
- Add more complex sample preparation

## Troubleshooting

**ChemStation Connection Failed**
- Is ChemStation running?
- Is the macro loaded? (`macro "path\ChemPyConnect.mac"; Python_Run`)

**SIA Device Not Responding**
- Check COM port numbers in Device Manager
- Verify power and cable connections
- Try `syringe.send_command("?", get_response=True)`

**Vial Not Found**
- Check vial is properly seated in carousel
- Verify vial number is correct (1-50)

**Method Not Found**
- Check method name spelling (case-sensitive)
- Verify method exists in ChemStation method directory

!!! success "Congratulations!"
    You've completed your first automated analysis! Continue to [Batch Processing](batch-processing.md) to learn about analyzing multiple samples.