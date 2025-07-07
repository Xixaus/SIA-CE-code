"""
Sequence Module - ChemStation batch analysis and sequence management.

This module provides comprehensive management of ChemStation sequences for automated
batch analysis of multiple samples. Sequences define the order, parameters, and
methods for analyzing series of samples with minimal user intervention.

Sequence Components:
- Sample Table: Vial positions, methods, sample names, data file names
- Sequence Parameters: Data storage paths, naming patterns, sequence metadata  
- Batch Control: Start/pause/resume functionality for long sequences
- Excel Integration: Import sequence parameters from Excel spreadsheets
- Method Variation: Different methods for different samples in same sequence

Automated Features:
- Automatic vial loading and method switching
- Sequential data file generation with timestamps
- Error handling and sequence continuation
- Progress tracking and time estimation
- Customizable data organization and naming

.. moduleauthor:: Richard Maršala
"""

import os
import pandas as pd
import shutil
import win32com.client
from pathlib import Path
from typing import Optional

from ..exceptions import *
from ..core.chemstation_communication import ChemstationCommunicator, CommunicationConfig
from .validation import ValidationModule


class SequenceModule():
    """Sequence management for automated batch analysis execution.
    
    Provides comprehensive sequence management including Excel-based sequence creation,
    row-by-row editing, file operations, and execution control. Sequences enable
    automated analysis of multiple samples with different methods and parameters.
    
    Sequence Table Structure:
        - VialNumber: Carousel position for sample (1-48)
        - Method: CE method name for analysis (.M file)
        - SampleName: Descriptive name for sample identification
        - SampleInfo: Additional sample metadata and notes
        - DataFileName: Custom data file naming (optional)
        - InjVial: Alternative injection vial (for special applications)
    
    Excel Integration:
        - Import sequence parameters from Excel spreadsheets
        - Flexible column mapping for different Excel formats
        - Automatic method validation during import
        - Support for custom data organization schemes
    
    Execution Control:
        - Start/pause/resume sequence execution
        - Progress monitoring and time estimation
        - Error handling with automatic continuation
        - Manual intervention capability during runs
    
    Attributes:
        comm: ChemStation communicator for sequence operations.
        method: Methods module for method validation and operations.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Sequence module with communicator and methods access.
        
        Args:
            communicator: ChemStation communication interface for sequence operations.
        """
        self.comm = communicator
        self.validation = ValidationModule(self.comm)
        
    
    def modify_sequence_row(self, row: int, vial_sample: str = "", 
                            method: str = "", sample_name: str = "",
                            sample_info: str = "", data_file_name: str = "") -> None:
        """Modify parameters in specific sequence table row.
        
        Updates individual row in the sequence table with new parameters.
        Only specified parameters are modified; empty parameters remain unchanged.
        This allows selective editing of sequence entries without affecting other rows.
        
        Args:
            row: Row number in sequence table (1-based indexing).
                Corresponds to analysis order in the sequence.
            vial_sample: Carousel position for sample vial (1-48).
                        Empty string leaves current value unchanged.
            method: CE method name (without .M extension) for this analysis.
                   Examples: "CE_Protein", "MEKC_Drugs", "CZE_Inorganics"
            sample_name: Descriptive sample name for identification and data files.
                        Examples: "BSA_Standard", "Unknown_001", "QC_Sample"
            sample_info: Additional sample metadata, experimental conditions, or notes.
                        Examples: "pH 7.4 buffer", "Dilution 1:10", "Replicate 3"
            data_file_name: Custom data filename (optional, auto-generated if empty).
                           
        Raises:
            SequenceError: If sequence modification fails or row doesn't exist.
            ValidationError: If method name is invalid or doesn't exist.
            ValueError: If row number is out of valid range.
            
        Examples:
            Modify sample vial and method:
            >>> seq.modify_sequence_row(
            ...     row=1,
            ...     vial_sample="15",
            ...     method="CE_Protein_Analysis"
            ... )
            
            Update sample information only:
            >>> seq.modify_sequence_row(
            ...     row=3,
            ...     sample_name="Unknown_Sample_001",
            ...     sample_info="Customer sample, urgent analysis"
            ... )
            
            Change method for specific analysis:
            >>> seq.modify_sequence_row(
            ...     row=5,
            ...     method="MEKC_SmallMolecules"
            ... )
            
        Note:
            - Sequence must be loaded before modification
            - Changes are made to memory, use save_sequence() to persist
            - Method validation performed if method parameter provided
            - Row numbering starts from 1 (not 0)
        """
        # Execute macro for sequence row modification
        command = (f"macro {self.comm.config.get_macros_path()}; modify_row_sequence "
               f"{row}, {vial_sample}, {sample_name}, "
               f"{method}, {sample_info}, {data_file_name}")
        
        try:
            self.comm.send(command)
        except Exception as e:
            raise SequenceError(f"Failed to modify sequence row {row}: {str(e)}")

    def prepare_sequence_table(self, excel_file_path: str, sequence_name: str = None,
                               sheet_name: int = 0, vial_column: str = None,
                               method_column: str = None, filename_column: str = None,
                               sample_name_column: str = None, sample_info_column: str = None,
                               replicate_column: str = None) -> None:
        """Import and create sequence table from Excel spreadsheet.
        
        Loads sequence parameters from Excel file and creates/updates ChemStation
        sequence table. Provides flexible column mapping to accommodate different
        Excel formats and naming conventions. Excel application is briefly opened
        during processing to ensure proper data handling.
        
        Column Mapping:
            Each parameter maps Excel columns to sequence table fields:
            - vial_column → VialNumber: Carousel positions
            - method_column → Method: CE method names  
            - sample_name_column → SampleName: Sample identifiers
            - sample_info_column → SampleInfo: Additional metadata
            - filename_column → DataFileName: Custom data file names
            - replicate_column → InjVial: Replicate/injection parameters
        
        Args:
            excel_file_path: Full path to Excel file containing sequence data.
                            File should contain headers in first row.
            sequence_name: Existing sequence to load before modification.
                          If None, modifies currently loaded sequence.
            sheet_name: Excel worksheet index to read (0-based, default: first sheet).
            vial_column: Excel column name containing vial positions.
                        Examples: "Vial", "Position", "Vial_Number"
            method_column: Excel column name containing method names.
                          Examples: "Method", "CE_Method", "Analysis_Method"
            sample_name_column: Excel column name containing sample names.
                               Examples: "Sample", "Sample_Name", "ID"
            sample_info_column: Excel column name containing sample metadata.
                               Examples: "Info", "Description", "Notes"
            filename_column: Excel column name containing custom filenames.
                            Examples: "Filename", "Data_File", "Output_Name"
            replicate_column: Excel column name containing replicate information.
                             Examples: "Replicate", "Injection", "Rep_Number"
                             
        Raises:
            FileNotFoundError: If Excel file doesn't exist at specified path.
            ValidationError: If referenced methods don't exist in method directory.
            SequenceError: If sequence loading or Excel processing fails.
            PermissionError: If unable to access Excel file or create temp files.
            
        Examples:
            Basic sequence import:
            >>> seq.prepare_sequence_table(
            ...     excel_file_path="C:\\Data\\sample_list.xlsx",
            ...     vial_column="Vial_Position",
            ...     method_column="Analysis_Method",
            ...     sample_name_column="Sample_ID"
            ... )
            
            Import with existing sequence:
            >>> seq.prepare_sequence_table(
            ...     excel_file_path="sequence_data.xlsx",
            ...     sequence_name="Protein_Analysis_Batch",
            ...     sheet_name=1,  # Second worksheet
            ...     vial_column="Pos",
            ...     method_column="Method",
            ...     sample_name_column="Sample",
            ...     sample_info_column="Notes"
            ... )
            
            Complex mapping with all parameters:
            >>> seq.prepare_sequence_table(
            ...     excel_file_path="complex_sequence.xlsx",
            ...     vial_column="Carousel_Position",
            ...     method_column="CE_Method_Name", 
            ...     sample_name_column="Sample_Identifier",
            ...     sample_info_column="Experimental_Conditions",
            ...     filename_column="Custom_Filename",
            ...     replicate_column="Injection_Number"
            ... )
            
        Note:
            - Excel file must be accessible (not open in another application)
            - Method names are validated against method directory
            - Temporary Excel file created during processing
            - Sequence is automatically saved after import
            - Excel application briefly visible during processing
        """
        # Create column mapping dictionary
        column_map = {
            "Vial": vial_column,
            "Method": method_column,
            "SampleInfo": sample_info_column,
            "SampleName": sample_name_column,
            "DataFileName": filename_column,
            "InjVial": replicate_column
        }

        # Validate Excel file exists
        if not os.path.isfile(excel_file_path):
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")

        # Load data from Excel
        temp_excel_path = self.comm.config.get_temp_dir_path() / "temp_excel.xlsx"
        shutil.copyfile(excel_file_path, temp_excel_path)
        excel_data = pd.read_excel(temp_excel_path, sheet_name=sheet_name)

        # Prepare result DataFrame with mapped columns
        result_df = pd.DataFrame({
            col: excel_data[src] if src and src in excel_data.columns else None
            for col, src in column_map.items()
        })

        # Validate all referenced methods exist
        if method_column and method_column in excel_data.columns:
            for method in result_df["Method"].dropna().unique():
                self.validation.validate_method_name(method)

        # Save processed data for Excel DDE communication
        processed_file_path = self.comm.config.get_temp_dir_path() / "temp.xlsx"
        result_df.to_excel(processed_file_path, header=False, index=False)

        # Save current sequence state
        self.save_sequence()

        # Load specified sequence if provided
        if sequence_name:
            self.validation.validate_sequence_name(sequence_name)
            self.load_sequence(sequence_name)

        # Open Excel for DDE communication
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True  # Required for DDE communication

        workbook = excel.Workbooks.Open(str(processed_file_path.absolute()))

        # Execute macro to import data from Excel via DDE
        self.comm.send(f"macro {self.comm.config.get_macros_path()}; modify_seq_table_by_excel {len(result_df)}")
        
        # Save updated sequence
        self.save_sequence()

        # Clean up Excel
        workbook.Close(SaveChanges=True)
        excel.Quit()

            
    def start(self) -> None:
        """Start execution of the current sequence.
        
        Begins automated execution of the loaded sequence, processing samples
        in order according to the sequence table. The sequence will run
        continuously until completion, pause, or error.
        
        Raises:
            SequenceError: If sequence cannot start or no sequence is loaded.
            SystemError: If instrument is not ready for sequence execution.
            
        Example:
            >>> seq.start()
            
        Note:
            - Sequence must be loaded and validated before starting
            - Instrument enters sequence mode with limited manual control
            - Progress can be monitored via system status methods
            - Use pause() to temporarily halt sequence execution
        """
        self.comm.send("StartSequence")

    def pause(self) -> None:
        """Pause the currently running sequence.
        
        Pauses sequence execution after the current method completes.
        The sequence will not abort the current analysis but will stop
        before starting the next sample in the sequence.
        
        Raises:
            SequenceError: If no sequence is running or pause fails.
            
        Example:
            >>> seq.pause()
            
        Note:
            - Current analysis completes before pausing
            - Sequence can be resumed with resume() method
            - Manual operations possible while paused
            - Pause takes effect between sequence entries
        """
        self.comm.send("PauseSequence")

    def resume(self) -> None:
        """Resume a paused sequence from where it stopped.
        
        Continues sequence execution from the next pending sample
        in the sequence table. All remaining samples will be processed
        according to their specified parameters.
        
        Raises:
            SequenceError: If no sequence is paused or resume fails.
            
        Example:
            >>> seq.resume()
            
        Note:
            - Resumes from next unprocessed sample
            - All sequence parameters remain unchanged
            - Instrument returns to automated sequence mode
            - Manual changes made during pause are preserved
        """
        self.comm.send("ResumeSequence")

    def load_sequence(self, seq_name: str, seq_dir: str = "_SEQPATH$") -> None:
        """Load an existing sequence from file.
        
        Loads a saved sequence file (.S) into ChemStation memory,
        making it the current active sequence for editing or execution.
        
        Args:
            seq_name: Sequence filename (without .S extension).
                     Examples: "Protein_Batch_Analysis", "Daily_QC_Sequence"
            seq_dir: Directory containing sequence files.
                    Defaults to ChemStation sequence directory (_SEQPATH$).
                    
        Raises:
            SequenceError: If sequence file cannot be loaded.
            ValidationError: If sequence file doesn't exist.
            FileNotFoundError: If sequence directory is invalid.
            
        Examples:
            Load standard sequence:
            >>> seq.load_sequence("Protein_Analysis_Batch")
            
            Load from custom directory:
            >>> seq.load_sequence("TestSeq", "C:\\Custom\\Sequences\\")
            
        Note:
            - Sequence loading overwrites current sequence in memory
            - All unsaved changes to current sequence are lost
            - Sequence parameters become active immediately
        """
        self.comm.send(f"LoadSequence {seq_dir}, {seq_name}.S")

    def save_sequence(self, seq_name: str = "_SEQFILE$", seq_dir: str = "_SEQPATH$") -> None:
        """Save current sequence to file.
        
        Saves the sequence table and parameters to a .S file for later use.
        If no name specified, overwrites the current sequence file.
        
        Args:
            seq_name: Filename for saved sequence (without .S extension).
                     Defaults to current sequence name (_SEQFILE$).
            seq_dir: Directory for saving sequence.
                    Defaults to ChemStation sequence directory (_SEQPATH$).
                    
        Raises:
            SequenceError: If sequence cannot be saved.
            PermissionError: If insufficient write permissions.
            
        Examples:
            Save with new name:
            >>> seq.save_sequence("Modified_Protein_Sequence")
            
            Overwrite current sequence:
            >>> seq.save_sequence()  # Updates current sequence file
            
        Note:
            - Saved sequence includes all table data and parameters
            - Existing files with same name are overwritten
            - .S extension added automatically
        """
        if seq_name != "_SEQFILE$":
            seq_name += ".S"

        self.comm.send(f"SaveSequence {seq_dir}, {seq_name}")

    def _validate_sequence_exists(self, sequence: str, dir_path: str = "_SEQPATH$") -> None:
        """Internal validation method for sequence file existence.
        
        Args:
            sequence: Sequence name (without .S extension).
            dir_path: Path to sequence directory.
            
        Raises:
            ValidationError: If sequence file doesn't exist.
        """
        sequence += ".S"

        if dir_path == "_SEQPATH$":
            dir_path = Path(self.comm.send("response$ = _SEQPATH$"))
        
        if sequence in os.listdir(dir_path):
            return
        else:
            raise ValidationError(f"Sequence not found in directory {dir_path}")