# Methods and Sequences

Learn how to work with CE methods and create automated sequences for batch analysis.

## Understanding Methods

CE methods define all analytical parameters:
- Voltage and current settings
- Temperature control
- Injection parameters
- Detection wavelengths
- Time programs
- Data acquisition settings

## Method Management

### Listing Available Methods

```python
# Get method directory path
method_path = api.send("response$ = _METHPATH$")
print(f"Method directory: {method_path}")

# List methods using Python
import os
methods = [f for f in os.listdir(method_path) if f.endswith('.M')]
print("Available methods:", methods)
```

### Loading Methods

```python
# Load from default directory
api.method.load("CE_Standard_Method")

# Load with full validation
try:
    api.validation.validate_method_name("CE_Protein_Analysis")
    api.method.load("CE_Protein_Analysis")
    print("Method loaded successfully")
except ValidationError:
    print("Method not found!")
```

### Modifying Method Parameters

While the API doesn't directly modify method parameters, you can:

1. Load a template method
2. Save with modifications via ChemStation
3. Use the modified method

```python
# Load template
api.method.load("Template_Method")

# Make changes in ChemStation UI...

# Save as new method
api.method.save("Modified_Method", comment="Voltage increased to 30kV")
```

### Running Methods with Custom Parameters

```python
# Simple run - uses current loaded method
api.method.run("Sample_001")

# Run specific method with all parameters
api.method.execution_method_with_parameters(
    vial=15,
    method_name="CE_Protein_Analysis",
    sample_name="BSA_Standard_1mg",
    comment="Validation run, fresh buffer",
    subdirectory_name="Validation_2024"
)

# The method creates a temporary register for custom parameters
# without modifying the original method file
```

## Understanding Sequences

Sequences automate the analysis of multiple samples with different parameters:

### Sequence Structure

| Column | Description | Example |
|--------|-------------|---------|
| Vial | Carousel position | 15 |
| Method | Method name | CE_Protein.M |
| SampleName | Sample identifier | BSA_001 |
| SampleInfo | Additional info | 1 mg/mL, pH 7.4 |
| DataFileName | Custom filename | Project_X_001 |
| InjVial | Injection parameters | 1 |

### Creating Sequences Manually

```python
# Load existing sequence
api.sequence.load_sequence("Daily_QC")

# Modify specific row
api.sequence.modify_sequence_row(
    row=1,
    vial_sample="10",
    method="CE_Standard",
    sample_name="QC_Standard_001",
    sample_info="Fresh preparation"
)

# Add more samples
for i in range(2, 6):
    api.sequence.modify_sequence_row(
        row=i,
        vial_sample=str(10 + i),
        method="CE_Standard",
        sample_name=f"QC_Standard_{i:03d}",
        sample_info="Replicate analysis"
    )

# Save sequence
api.sequence.save_sequence("Daily_QC_Modified")
```

## Excel Integration

### Preparing Excel File

Create an Excel file with columns matching your needs:

| Vial | Method | Sample | Info | Replicate |
|------|---------|---------|-------|-----------|
| 10 | CE_Standard | STD_001 | 1 mg/mL | 1 |
| 11 | CE_Standard | STD_002 | 2 mg/mL | 1 |
| 12 | CE_Modified | TEST_001 | Unknown | 1 |

### Importing from Excel

```python
# Basic import
api.sequence.prepare_sequence_table(
    excel_file_path="sample_list.xlsx",
    vial_column="Vial",
    method_column="Method",
    sample_name_column="Sample"
)

# Full import with all columns
api.sequence.prepare_sequence_table(
    excel_file_path="complex_sequence.xlsx",
    sequence_name="Research_Project_2024",  # Load this sequence first
    sheet_name=0,  # First worksheet
    vial_column="Vial_Position",
    method_column="CE_Method",
    sample_name_column="Sample_ID",
    sample_info_column="Description",
    filename_column="Data_Name",
    replicate_column="Rep_Number"
)
```

!!! warning "Excel Requirements"
    - Excel must be installed on the system
    - File should not be open during import
    - Column names must match exactly (case-sensitive)

## Sequence Execution

### Starting a Sequence

```python
# Load and start sequence
api.sequence.load_sequence("Daily_Analysis")
api.sequence.start()

# Monitor progress
while api.system.method_on():
    status = api.system.status()
    print(f"Status: {status}")
    time.sleep(60)
```

### Sequence Control

```python
# Pause after current sample
api.sequence.pause()
print("Sequence paused - current sample will complete")

# Resume sequence
api.sequence.resume()
print("Sequence resumed")

# Emergency stop
api.system.abort_run()
print("Sequence aborted!")
```

## Advanced Sequence Workflows

### Validation Sequence with Standards

```python
def create_validation_sequence(standard_vials, sample_vials):
    """Create sequence with bracketing standards."""
    
    row = 1
    
    # Initial standards
    for vial in standard_vials[:2]:
        api.sequence.modify_sequence_row(
            row=row,
            vial_sample=str(vial),
            method="CE_Standard",
            sample_name=f"STD_{row:03d}",
            sample_info="System suitability"
        )
        row += 1
    
    # Samples with bracketing standards
    for i, vial in enumerate(sample_vials):
        # Sample
        api.sequence.modify_sequence_row(
            row=row,
            vial_sample=str(vial),
            method="CE_Analysis",
            sample_name=f"Sample_{i+1:03d}",
            sample_info="Test sample"
        )
        row += 1
        
        # Bracket standard every 5 samples
        if (i + 1) % 5 == 0:
            api.sequence.modify_sequence_row(
                row=row,
                vial_sample=str(standard_vials[0]),
                method="CE_Standard",
                sample_name=f"STD_B{row:03d}",
                sample_info="Bracket standard"
            )
            row += 1
    
    # Final standards
    for vial in standard_vials[:2]:
        api.sequence.modify_sequence_row(
            row=row,
            vial_sample=str(vial),
            method="CE_Standard",
            sample_name=f"STD_F{row:03d}",
            sample_info="Final check"
        )
        row += 1
    
    api.sequence.save_sequence("Validation_Sequence")

# Create the sequence
create_validation_sequence(
    standard_vials=[1, 2],
    sample_vials=list(range(10, 25))
)
```

### Multi-Method Sequence

```python
def create_screening_sequence(samples_info):
    """Create sequence with different methods for screening."""
    
    for row, (vial, sample_type, sample_name) in enumerate(samples_info, 1):
        # Select method based on sample type
        if sample_type == "protein":
            method = "CE_Protein_SDS"
        elif sample_type == "small_molecule":
            method = "MEKC_General"
        elif sample_type == "anion":
            method = "CE_Anions"
        else:
            method = "CE_Screening"
        
        api.sequence.modify_sequence_row(
            row=row,
            vial_sample=str(vial),
            method=method,
            sample_name=sample_name,
            sample_info=f"Type: {sample_type}"
        )
    
    api.sequence.save_sequence("Screening_Sequence")

# Define samples
samples = [
    (10, "protein", "BSA_Test"),
    (11, "small_molecule", "Caffeine_Std"),
    (12, "anion", "Chloride_Mix"),
    (13, "protein", "Antibody_001"),
    (14, "unknown", "Customer_Sample_X")
]

create_screening_sequence(samples)
```

## Sequence Data Management

### Organizing Data Files

```python
# Set up data organization
from datetime import datetime

# Create project-specific subdirectory
project_name = "Protein_Stability_Study"
date_stamp = datetime.now().strftime("%Y%m%d")

# Use in sequence
api.method.execution_method_with_parameters(
    vial=15,
    method_name="CE_Protein",
    sample_name="BSA_T0",
    subdirectory_name=f"{project_name}_{date_stamp}"
)
```

### Sequence Templates

Create reusable sequence templates:

```python
def create_qc_sequence_template():
    """Create standard QC sequence template."""
    
    qc_positions = {
        1: ("System_Suitability", "CE_QC"),
        2: ("Blank", "CE_QC"),
        3: ("Standard_Low", "CE_QC"),
        4: ("Standard_Mid", "CE_QC"),
        5: ("Standard_High", "CE_QC"),
    }
    
    for row, (vial, (sample_type, method)) in enumerate(qc_positions.items(), 1):
        api.sequence.modify_sequence_row(
            row=row,
            vial_sample=str(vial),
            method=method,
            sample_name=f"QC_{sample_type}",
            sample_info="Daily QC"
        )
    
    api.sequence.save_sequence("QC_Template")
    print("QC template created - modify dates/info before running")

create_qc_sequence_template()
```

## Best Practices

### 1. Validate Before Execution

```python
def validate_sequence_ready(sequence_name):
    """Validate all sequence requirements before starting."""
    
    # Load sequence
    api.sequence.load_sequence(sequence_name)
    
    # Get vial list from sequence (manual check needed)
    # For now, validate known vials
    required_vials = [1, 2, 3, 10, 11, 12]  # Example
    
    try:
        # Check all vials present
        api.validation.list_vial_validation(required_vials)
        
        # Check all methods exist
        methods = ["CE_QC", "CE_Analysis"]  # Example
        for method in methods:
            api.validation.validate_method_name(method)
        
        # Check system ready
        if api.system.status() != "STANDBY":
            raise SystemError("System not in standby")
        
        print(f"Sequence {sequence_name} ready to run!")
        return True
        
    except Exception as e:
        print(f"Sequence validation failed: {e}")
        return False
```

### 2. Error Recovery

```python
def run_sequence_with_recovery(sequence_name):
    """Run sequence with error recovery."""
    
    try:
        api.sequence.load_sequence(sequence_name)
        api.sequence.start()
        
        while api.system.method_on():
            status = api.system.status()
            
            if status == "ERROR":
                print("Error detected - attempting recovery")
                api.system.abort_run()
                time.sleep(30)
                
                # Try to resume
                api.sequence.resume()
                
            time.sleep(30)
            
    except Exception as e:
        print(f"Sequence failed: {e}")
        api.system.abort_run()
```

### 3. Progress Tracking

```python
def track_sequence_progress():
    """Track and log sequence progress."""
    
    sample_count = 0
    start_time = time.time()
    
    while api.system.method_on():
        if api.system.status() == "RUN":
            sample_count += 1
            elapsed = (time.time() - start_time) / 60
            remaining = api.system.get_remaining_analysis_time()
            
            print(f"Sample {sample_count} - "
                  f"Elapsed: {elapsed:.1f} min - "
                  f"Current remaining: {remaining:.1f} min")
        
        time.sleep(60)
    
    total_time = (time.time() - start_time) / 60
    print(f"Sequence complete! {sample_count} samples in {total_time:.1f} minutes")
```

!!! success "You're ready!"
    You now know how to create and run complex analytical sequences. Check out the [Tutorials](../tutorials/first-analysis.md) for complete workflow examples.