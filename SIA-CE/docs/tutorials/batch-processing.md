# Batch Processing Tutorial

Learn how to analyze multiple samples automatically using sequences and SIA sample preparation.

## Overview

In this tutorial, we'll:
- Prepare multiple samples with different dilutions
- Create a sequence from Excel data
- Run automated batch analysis
- Handle different sample types
- Monitor batch progress

## Scenario

We'll analyze 10 protein samples:
- 2 standards (known concentration)
- 6 unknown samples
- 2 QC samples
- Each requires different dilution factors

## Step 1: Prepare Excel File

Create `batch_samples.xlsx` with this structure:

| Vial | Method | Sample_Name | Dilution | Type |
|------|---------|-------------|----------|-------|
| 10 | CE_Protein | STD_Low | 5 | Standard |
| 11 | CE_Protein | STD_High | 20 | Standard |
| 12 | CE_Protein | Sample_001 | 10 | Unknown |
| 13 | CE_Protein | Sample_002 | 10 | Unknown |
| 14 | CE_Protein | Sample_003 | 15 | Unknown |
| 15 | CE_Protein | QC_001 | 10 | QC |
| 16 | CE_Protein | Sample_004 | 10 | Unknown |
| 17 | CE_Protein | Sample_005 | 12 | Unknown |
| 18 | CE_Protein | Sample_006 | 8 | Unknown |
| 19 | CE_Protein | QC_002 | 10 | QC |

## Step 2: Initialize System

```python
import pandas as pd
import time
from datetime import datetime
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

# Initialize all components
print("=== Batch Processing Tutorial ===\n")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Connect to devices
ce_api = ChemstationAPI()
syringe = SyringeController(port="COM3", syringe_size=1000)
valve = ValveSelector(port="COM4", num_positions=8)
workflow = PreparedSIAMethods(ce_api, syringe, valve)

# System initialization
print("\nInitializing system...")
workflow.system_initialization_and_cleaning()
print("✓ System ready")
```

## Step 3: Load and Validate Sample Data

```python
# Load sample information
print("\nLoading sample data...")
samples_df = pd.read_excel("batch_samples.xlsx")
print(f"✓ Loaded {len(samples_df)} samples")

# Display sample summary
print("\nSample Summary:")
print(f"Standards: {len(samples_df[samples_df['Type'] == 'Standard'])}")
print(f"Unknowns: {len(samples_df[samples_df['Type'] == 'Unknown'])}")
print(f"QC: {len(samples_df[samples_df['Type'] == 'QC'])}")

# Validate all vials are present
print("\nValidating vials...")
missing_vials = []
for vial in samples_df['Vial']:
    try:
        ce_api.validation.validate_vial_in_system(int(vial))
    except:
        missing_vials.append(vial)

if missing_vials:
    print(f"✗ Missing vials: {missing_vials}")
    print("Please load all vials before continuing")
    exit(1)
else:
    print("✓ All vials present")

# Validate method
method_name = samples_df['Method'].iloc[0]
ce_api.validation.validate_method_name(method_name)
print(f"✓ Method '{method_name}' validated")
```

## Step 4: Automated Sample Preparation

```python
def prepare_samples(samples_df):
    """Prepare all samples with specified dilutions."""
    
    print("\n=== Sample Preparation ===")
    
    # Prepare for continuous flow with DI water
    workflow.prepare_continuous_flow(solvent_port=3, speed=2000)
    
    preparation_log = []
    
    for idx, row in samples_df.iterrows():
        vial = int(row['Vial'])
        dilution = int(row['Dilution'])
        sample_name = row['Sample_Name']
        sample_type = row['Type']
        
        print(f"\nPreparing {sample_name} (Vial {vial})")
        print(f"Type: {sample_type}, Dilution: 1:{dilution}")
        
        # Calculate volumes (1500 µL final volume)
        final_volume = 1500
        sample_volume = final_volume / dilution
        diluent_volume = final_volume - sample_volume
        
        # Add diluent
        workflow.continuous_fill(
            vial=vial,
            volume=diluent_volume,
            solvent_port=3,
            flush_needle=None  # No wash between same solvent
        )
        
        # Log preparation
        prep_info = {
            'vial': vial,
            'sample': sample_name,
            'sample_vol': sample_volume,
            'diluent_vol': diluent_volume,
            'time': datetime.now()
        }
        preparation_log.append(prep_info)
        
        print(f"✓ Added {diluent_volume:.0f} µL diluent")
        print(f"  → Add {sample_volume:.0f} µL sample manually")
    
    # Clean needle after all dilutions
    workflow.clean_needle(volume_flush=100, wash_vial=48)
    
    return preparation_log

# Prepare all samples
prep_log = prepare_samples(samples_df)

print("\n⚠ Add samples to vials according to the volumes shown above")
input("Press Enter when all samples are added...")
```

## Step 5: Mix All Samples

```python
# Homogenize all samples
print("\n=== Sample Mixing ===")

for idx, row in samples_df.iterrows():
    vial = int(row['Vial'])
    sample_name = row['Sample_Name']
    
    print(f"Mixing {sample_name}...", end='')
    
    workflow.homogenize_sample(
        vial=vial,
        speed=1000,
        homogenization_time=20,
        flush_needle=None,  # Wash at end
        unload=True
    )
    
    print(" ✓")

# Final needle wash
workflow.clean_needle(volume_flush=100, wash_vial=48)
print("\n✓ All samples prepared and mixed")
```

## Step 6: Create CE Sequence

```python
# Create sequence in ChemStation
print("\n=== Creating CE Sequence ===")

# Import sequence from Excel
ce_api.sequence.prepare_sequence_table(
    excel_file_path="batch_samples.xlsx",
    sequence_name="Batch_Tutorial",
    vial_column="Vial",
    method_column="Method",
    sample_name_column="Sample_Name"
)

print("✓ Sequence created from Excel")

# Add sample info to sequence
for idx, row in samples_df.iterrows():
    ce_api.sequence.modify_sequence_row(
        row=idx + 1,
        sample_info=f"Type: {row['Type']}, Dilution: 1:{row['Dilution']}"
    )

# Save sequence
sequence_name = f"Batch_{datetime.now().strftime('%Y%m%d_%H%M')}"
ce_api.sequence.save_sequence(sequence_name)
print(f"✓ Sequence saved as: {sequence_name}")
```

## Step 7: Pre-Analysis Setup

```python
# Condition system before batch run
print("\n=== Pre-Analysis Setup ===")

# Load buffer vials
print("Loading buffer vials...")
ce_api.ce.load_vial_to_position(1, "inlet")  # Running buffer
ce_api.ce.load_vial_to_position(48, "outlet")  # Waste

# Extended conditioning for batch run
print("Conditioning capillary (3 minutes)...")
ce_api.ce.flush_capillary(time_flush=180.0)

# Return vials
ce_api.ce.unload_vial_from_position("inlet")
ce_api.ce.unload_vial_from_position("outlet")

print("✓ System conditioned and ready")
```

## Step 8: Run Batch Analysis

```python
# Start batch analysis
print("\n=== Starting Batch Analysis ===")
print(f"Sequence: {sequence_name}")
print(f"Samples: {len(samples_df)}")
print(f"Estimated time: {len(samples_df) * 15} minutes")

# Start sequence
ce_api.sequence.start()
print("✓ Sequence started")

# Create analysis log
analysis_log = {
    'start_time': datetime.now(),
    'samples_completed': 0,
    'current_sample': '',
    'errors': []
}
```

## Step 9: Monitor Batch Progress

```python
def monitor_batch_analysis(ce_api, samples_df, analysis_log):
    """Monitor batch analysis with progress tracking."""
    
    print("\n=== Monitoring Progress ===")
    print("Press Ctrl+C to stop monitoring (analysis continues)\n")
    
    try:
        last_status = ""
        sample_start_time = time.time()
        
        while True:
            # Get current status
            status = ce_api.system.status()
            rc_status = ce_api.system.RC_status()
            
            # Detect sample changes
            if status == "RUN" and last_status != "RUN":
                analysis_log['samples_completed'] += 1
                sample_start_time = time.time()
                
                if analysis_log['samples_completed'] <= len(samples_df):
                    current_sample = samples_df.iloc[
                        analysis_log['samples_completed'] - 1
                    ]['Sample_Name']
                    analysis_log['current_sample'] = current_sample
                    print(f"\n→ Analyzing {current_sample}")
            
            # Display progress
            if ce_api.system.method_on():
                remaining = ce_api.system.get_remaining_analysis_time()
                elapsed = (time.time() - sample_start_time) / 60
                
                print(f"\r[{analysis_log['samples_completed']}/{len(samples_df)}] "
                      f"{analysis_log['current_sample']} - "
                      f"Status: {status} - "
                      f"Remaining: {remaining:.1f} min", end='')
            else:
                # Check if sequence is complete
                if analysis_log['samples_completed'] >= len(samples_df):
                    print("\n\n✓ Batch analysis complete!")
                    break
                else:
                    print(f"\rWaiting for next sample...", end='')
            
            last_status = status
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped (analysis continues)")
    
    return analysis_log

# Monitor the batch
analysis_log = monitor_batch_analysis(ce_api, samples_df, analysis_log)
```

## Step 10: Post-Analysis Summary

```python
# Generate analysis summary
print("\n=== Analysis Summary ===")

analysis_log['end_time'] = datetime.now()
total_time = (analysis_log['end_time'] - analysis_log['start_time']).seconds / 60

print(f"Start Time: {analysis_log['start_time'].strftime('%H:%M')}")
print(f"End Time: {analysis_log['end_time'].strftime('%H:%M')}")
print(f"Total Duration: {total_time:.1f} minutes")
print(f"Samples Completed: {analysis_log['samples_completed']}/{len(samples_df)}")

# Calculate statistics
avg_time = total_time / analysis_log['samples_completed'] if analysis_log['samples_completed'] > 0 else 0
print(f"Average Time per Sample: {avg_time:.1f} minutes")

# Sample type breakdown
if analysis_log['samples_completed'] == len(samples_df):
    print("\nSamples Analyzed:")
    for sample_type in samples_df['Type'].unique():
        count = len(samples_df[samples_df['Type'] == sample_type])
        print(f"  {sample_type}: {count}")

# Save summary report
report_filename = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
with open(report_filename, 'w') as f:
    f.write("Batch Analysis Report\n")
    f.write("=" * 50 + "\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    f.write(f"Sequence: {sequence_name}\n")
    f.write(f"Total Samples: {len(samples_df)}\n")
    f.write(f"Duration: {total_time:.1f} minutes\n")
    f.write("\nSample Details:\n")
    for _, row in samples_df.iterrows():
        f.write(f"  {row['Sample_Name']} - Vial {row['Vial']} - "
                f"Dilution 1:{row['Dilution']}\n")

print(f"\n✓ Report saved as: {report_filename}")
```

## Complete Batch Processing Script

```python
# Complete Batch Processing Script
import pandas as pd
import time
from datetime import datetime
from ChemstationAPI import ChemstationAPI
from SIA_API.devices import SyringeController, ValveSelector
from SIA_API.methods import PreparedSIAMethods

def run_batch_analysis(excel_file="batch_samples.xlsx"):
    """Complete batch analysis with SIA preparation."""
    
    # Initialize
    ce_api = ChemstationAPI()
    syringe = SyringeController(port="COM3", syringe_size=1000)
    valve = ValveSelector(port="COM4", num_positions=8)
    workflow = PreparedSIAMethods(ce_api, syringe, valve)
    
    # System preparation
    workflow.system_initialization_and_cleaning()
    
    # Load samples
    samples_df = pd.read_excel(excel_file)
    
    # Validate
    for vial in samples_df['Vial']:
        ce_api.validation.validate_vial_in_system(int(vial))
    
    # Prepare samples
    workflow.prepare_continuous_flow(solvent_port=3)
    
    for _, row in samples_df.iterrows():
        vial = int(row['Vial'])
        dilution = int(row['Dilution'])
        diluent_volume = 1500 * (dilution - 1) / dilution
        
        workflow.continuous_fill(
            vial=vial,
            volume=diluent_volume,
            solvent_port=3
        )
    
    input("\nAdd samples and press Enter...")
    
    # Mix all samples
    for vial in samples_df['Vial']:
        workflow.homogenize_sample(
            vial=int(vial),
            speed=1000,
            homogenization_time=20
        )
    
    # Create and run sequence
    ce_api.sequence.prepare_sequence_table(
        excel_file_path=excel_file,
        vial_column="Vial",
        method_column="Method",
        sample_name_column="Sample_Name"
    )
    
    ce_api.sequence.start()
    
    # Monitor
    samples_done = 0
    while samples_done < len(samples_df):
        if ce_api.system.method_on():
            remaining = ce_api.system.get_remaining_analysis_time()
            print(f"\r[{samples_done + 1}/{len(samples_df)}] "
                  f"Remaining: {remaining:.1f} min", end='')
        time.sleep(10)
    
    print("\n✓ Batch complete!")

if __name__ == "__main__":
    run_batch_analysis()
```

## Advanced Batch Processing

### Intelligent Sample Grouping

```python
def group_samples_by_dilution(samples_df):
    """Group samples by dilution to optimize preparation."""
    
    grouped = samples_df.groupby('Dilution')
    
    for dilution, group in grouped:
        print(f"\nDilution 1:{dilution} ({len(group)} samples):")
        
        # Prepare all samples with same dilution together
        workflow.prepare_continuous_flow(solvent_port=3)
        
        for _, sample in group.iterrows():
            vial = int(sample['Vial'])
            volume = 1500 * (dilution - 1) / dilution
            
            workflow.continuous_fill(
                vial=vial,
                volume=volume,
                solvent_port=3,
                flush_needle=None
            )
        
        # Wash between dilution groups
        workflow.clean_needle(100)
```

### Error Recovery

```python
def batch_with_error_recovery():
    """Run batch with automatic error recovery."""
    
    max_retries = 3
    failed_samples = []
    
    for _, sample in samples_df.iterrows():
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                ce_api.method.execution_method_with_parameters(
                    vial=int(sample['Vial']),
                    method_name=sample['Method'],
                    sample_name=sample['Sample_Name']
                )
                
                # Wait for completion
                while ce_api.system.method_on():
                    time.sleep(30)
                
                success = True
                
            except Exception as e:
                retry_count += 1
                print(f"\nError with {sample['Sample_Name']}: {e}")
                
                if retry_count < max_retries:
                    print(f"Retrying ({retry_count}/{max_retries})...")
                    ce_api.system.abort_run()
                    time.sleep(60)
                else:
                    failed_samples.append(sample['Sample_Name'])
    
    if failed_samples:
        print(f"\nFailed samples: {failed_samples}")
```

## Tips for Efficient Batch Processing

1. **Group Similar Samples**
   - Process samples with same dilution together
   - Minimize solvent changes

2. **Optimize Timing**
   - Prepare next samples during current analysis
   - Use parallel operations when possible

3. **Quality Control**
   - Include QC samples at regular intervals
   - Monitor system suitability

4. **Error Handling**
   - Plan for sample failures
   - Include retry logic

5. **Documentation**
   - Log all preparation steps
   - Generate comprehensive reports

!!! success "Batch Processing Mastered!"
    You can now process multiple samples efficiently. Continue to [SIA-CE Integration](sia-ce-integration.md) for advanced workflows.