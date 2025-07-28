# ChemStation Scripting and Macros - Complete Guide

This comprehensive guide covers the practical fundamentals of scripting in Agilent ChemStation, including detailed registry operations and RC.NET module interactions.

## Overview

ChemStation's built-in scripting capabilities enable powerful automation of analytical workflows. This guide provides hands-on examples and best practices for creating automation solutions.

---

## 1. ChemStation Commands

ChemStation includes a command processor (CP) that interprets and executes commands interactively or through scripts.

### Basic Command Syntax

**Display Messages:**
```chemstation
Print "This is a message"
```

**Multiple Commands per Line:**
Separate commands with semicolons (`;`):
```chemstation
Print "Starting"; Sleep 2; Print "Complete"
```

**Comments:**
Text after `!` is ignored:
```chemstation
! This is a comment
Print "Active command"  ! End-of-line comment
```

**Command History:**
Use `↑` and `↓` arrow keys to navigate through previous commands in the command processor.

---

## 2. Macro Structure and Parameters

Macros are named collections of commands that automate repetitive tasks and complex workflows.

### Basic Macro Structure

```chemstation
Name MyMessage
    Print "Hello World!"
EndMacro
```

### Macro Parameters

Macros can accept parameters for flexible operation. Parameters are declared using the `Parameter` statement:

```chemstation
Name InjectSample
    Parameter SampleName$, VialPos, InjVol
    Print "Sample=", SampleName$, ", Vial=", VialPos, ", InjVol=", InjVol
EndMacro
```

**Calling the macro:**
```chemstation
InjectSample "Std_1", 5, 10
```

### Local Variables

Define local variables within macros using the `Local` statement:

```chemstation
Name CalculateVolume
    Local Area, Volume, Concentration
    Area = 2.5
    Concentration = 0.1
    Volume = Area * Concentration * 10
    Print "Calculated Volume =", Volume
EndMacro
```

**Variable Scope:**
- Local variables exist only within the macro
- Global variables persist throughout the ChemStation session
- Use local variables to prevent naming conflicts

---

## 3. Loading and Managing Macros

### Loading Macros

**Load from relative path:**
```chemstation
Macro "mymacro.mac"
```

**Load from absolute path:**
```chemstation
Macro "D:\projects\chem\automation\mymacro.mac"
```

### Executing Macros

**Run without parameters:**
```chemstation
MyMessage
```

**Run with parameters:**
```chemstation
InjectSample "Sample_A", 3, 5.0
```

### Macro Management

**Remove macro from memory:**
```chemstation
Remove MyMessage
```

**List loaded macros:**
```chemstation
Show Macros
```

---

## 4. Variables and Data Types

ChemStation supports several variable types for different data handling needs.

### Variable Types

**String Variables:**
```chemstation
Sample$ = "Test_Sample_001"
DataPath$ = "C:\ChemStation\Data\"
```

**Numeric Variables:**
```chemstation
Flow = 1.5
Temperature = 25.0
InjectionVolume = 10
```

### System Variables

ChemStation provides built-in system variables for accessing current state information:

**Common System Variables:**
- `_DataFile$` - Current data file name
- `_MethodOn` - Method status (0=off, 1=on)
- `_SequenceOn` - Sequence status (0=off, 1=on)
- `_AutoPath$` - Automatic data path
- `_Instrument$` - Current instrument configuration

**Display all system variables:**
```chemstation
Show Variables
```

---

## 5. Registry Operations

Registries are ChemStation's primary data containers, storing complex information about analyses, methods, chromatograms, and spectra.

### Understanding Registry Structure

**Registry Hierarchy:**
- **Registry** - Top-level container (e.g., ChromReg for chromatograms)
- **Objects** - Individual data items within registry (e.g., ChromReg[1])
- **Headers** - Metadata about objects
- **Data Blocks** - Raw analytical data
- **Tables** - Processed results (peaks, quantification)

### Basic Registry Operations

**Check registry size:**
```chemstation
Print RegSize(ChromReg)
```

**List registry contents:**
```chemstation
Print RegCont$(ChromReg)
```

**Access specific registry object:**
```chemstation
ChromReg[1]  ! Access first chromatogram
```

### Reading Data from Registries

**Extract raw data points:**
```chemstation
Data(ChromReg[1], 0, 10)  ! X-axis value at point 10
Data(ChromReg[1], 1, 10)  ! Y-axis value at point 10
```

**Read header information:**
```chemstation
Print ObjHdrVal$(ChromReg[1], "SampleName")
Print ObjHdrVal(ChromReg[1], "InjectionVolume")
```

### Working with Tables

**Read text from tables:**
```chemstation
TabText$(ChromRes[1], "Peak", 2, "Name")    ! Peak name for peak #2
```

**Read numeric values from tables:**
```chemstation
TabVal(ChromRes[1], "Peak", 2, "Area")      ! Peak area for peak #2
TabVal(ChromRes[1], "Peak", 2, "RT")        ! Retention time for peak #2
```

### Modifying Registry Data

**Update header values:**
```chemstation
SetObjHdrVal ChromReg[1], "Title", "My Custom Chromatogram"
SetObjHdrVal ChromReg[1], "SampleInfo", "Batch_2024_001"
```

**Modify data points:**
```chemstation
SetData ChromReg[1], 1, 10, 1500.5  ! Set Y-value at point 10
```

**Advanced Registry Exploration:**
For comprehensive registry exploration, use the `register_reader.mac` utility to examine all available registry structures and data.

---

## 6. RC.NET Module Control

RC.NET provides standardized communication with ChemStation modules like pumps, detectors, and autosamplers.

### RC.NET Registry Structure

Each module maintains three primary registries:

**Registry Types:**
- `RC<ModID><#>Method` - Method parameters and settings
- `RC<ModID><#>Status` - Real-time status information (pressures, temperatures)
- `RC<ModID><#>Config` - Module configuration (type, firmware version, serial number)

**Example Module Identifiers:**
- `PMP1` - Quaternary Pump
- `WLS1` - UV-Vis Detector  
- `ALS1` - Autosampler
- `CE1` - Capillary Electrophoresis

### Method Parameter Modification

**Standard method parameter workflow:**
```chemstation
! Upload current method to memory
UploadRCMethod PMP1

! Modify parameters
SetObjHdrVal RCPMP1Method[1], "StopTime_Time", 10
SetObjHdrVal RCPMP1Method[1], "Flow", 1.0

! Download modified method to instrument
DownloadRCMethod PMP1
```

**Common Method Parameters:**
- Flow rates: `"Flow"`, `"Flow_A"`, `"Flow_B"`
- Temperatures: `"Temperature"`, `"ColTemp"`
- Times: `"StopTime_Time"`, `"PostTime"`
- Volumes: `"InjVol"`, `"MaxInjVol"`

### Reading Module Status

**Current operational parameters:**
```chemstation
Print ObjHdrVal(RCPMP1Status[1], "Pressure")     ! Current pressure
Print ObjHdrVal(RCPMP1Status[1], "Flow_actual")  ! Actual flow rate
Print ObjHdrVal(RCWLS1Status[1], "Lamp")         ! Lamp status
```

**Module configuration information:**
```chemstation
Print ObjHdrVal(RCPMP1Config[1], "SerialNumber")   ! Serial number
Print ObjHdrVal(RCPMP1Config[1], "FirmwareRev")    ! Firmware version
```

### Direct Module Communication

**Send command without response:**
```chemstation
WriteModule "WLS1", "LRPL 10"  ! Set reference wavelength
```

**Send command and get response:**
```chemstation
Response$ = SendModule$("WLS1", "LIFTER:OCCUPIED? 3")  ! Check vial position
Print "Vial occupied:", Response$
```

**Advanced module interrogation:**
```chemstation
Print SendModule$("PMP1", "PRES?")     ! Query current pressure
Print SendModule$("ALS1", "INJ:STAT?")  ! Query injection status
```

---

## 7. Discovering Module Commands Through Trace Logs

Module-specific commands can be discovered by monitoring ChemStation's communication logs.

### Practical Example - Vial Loading

**Sample log entry for loading vial 50 to replenishment position:**
```
EventId: 228808;Timestamp: 22/07/2025 8:21:16.851;Thread Id: 25;
Message: LDT SendInstruction: Module:[G7150A:DEDAD01310]; 
Instruction:[RRPL]; Reply:[[G7150A:DEDAD01310:IN]: RA 00000 RRPL];
Category: Agilent.LCDrivers.Common.ModuleAccess, Debug;Priority: 3;
Process Name: C:\Chem32\CORE\ChemMain.exe;
Extended Properties: ModuleShortname - Agilent.LCDrivers.Common.ModuleAccess;
```

Key Information:

- **Module ID**: `G7150A:DEDAD01310` (CE1)
- **Command**: `LRPL 50` (Load Replenishment Position 50)
- **Response**: `RA 00000` (Response Acknowledge - Success)

### Trace Analysis Workflow

1. **Monitor during operations:**
   - Perform action in ChemStation interface (load vial, change parameter)
   - Check `C:\Chem32\1\TEMP\rcdriver.trc`

2. **Extract commands:**
   - Look for `Instruction:` entries
   - Note the exact module ID and command syntax

3. **Test in Command Processor:**
   ```chemstation
   WriteModule "CE1", "LRPL 50"  ! Load vial 50 to replenishment
   ```

**Common Commands Discovered:**
- `LRPL n` - Load replenishment position
- `LIFTER:OCCUPIED? n` - Check if vial n is present
---

## 10. Quick Troubleshooting

### Common Issues

**Module communication fails:**
- Verify module is online: `Print RCModuleReady("PMP1")`
- Restart ChemStation if persistent errors

**Registry errors:**
- Check registry exists: `Print RegSize(ChromReg)`  
- Verify object number: `Print RegCont$(ChromReg)`

**Command not working:**
- Test in Command Processor first
- Check trace logs for exact syntax
- Verify module ID matches your system

### Quick Reference Commands
```chemstation
Show                          ! List all variables
RCListDevices$()             ! List RC.NET modules  
Print RegCont$(ChromReg)     ! Show registry contents
Remove MacroName             ! Unload macro
```

---

**For detailed registry exploration, use the provided `register_reader.mac` utility.**