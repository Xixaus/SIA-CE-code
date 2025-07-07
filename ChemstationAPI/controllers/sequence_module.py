"""
Sequence Module - ChemStation sequence management.

This module provides functionality for managing ChemStation sequences including
row editing, Excel file imports, sequence execution control, and file operations.

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
from .methods_module import MethodsModule


class SequenceModule():
    """Sequence management for editing, loading, and execution.
    
    Provides methods for sequence editing, Excel file imports,
    sequence execution control, and file management.
    
    Sequences define the order and parameters for multiple analyses,
    including vial positions, methods, sample names, and data file names.
    
    Attributes:
        Inherits all attributes from ChemstationCommunicator and MethodsModule.
    """
    
    def __init__(self, communicator: ChemstationCommunicator):
        """Initialize Sequence module.
        
        Args:
            config: Communication configuration for ChemStation connection.
        """
        self.comm = communicator
        self.method = MethodsModule(self.comm)
        
    
    def modify_sequence_row(self, row: int, vial_sample: str = "", 
                            method: str = "", sample_name: str = "",
                            sample_info: str = "",  data_file_name: str = "",
                            ) -> None:
        """Modify settings in the sequence table for a specified row.
        
        Modifies the currently loaded sequence with new parameters for the
        specified row number.
        
        Args:
            row: Row number in sequence table.
            vial_sample: Optional vial number for the sample.
            method: Optional method name to apply.
            sample_name: Optional sample name.
            sample_info: Optional sample information.
            data_file_name: Optional data file name.
            
        Raises:
            SequenceError: If sequence modification fails.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.modify_sequence_row(
            ...     row=1,
            ...     vial_sample="15",
            ...     method="TestMethod",
            ...     sample_name="Sample001"
            ... )
        """
        command = (f"macro {self.comm.config.get_macros_path()}; modify_row_sequence "
               f"{row}, {vial_sample}, {sample_name}, "
               f"{method}, {sample_info}, {data_file_name}")
        
        try:
            self.comm.send(command)
        except Exception as e:
            raise SequenceError(f"Failed to modify sequence: {str(e)}")

    def prepare_sequence_table(
        self,
        excel_file_path: str,
        sequence_name: str = None,
        sheet_name: int = 0,
        vial_column: str = None,
        method_column: str = None,
        filename_column: str = None,
        sample_name_column: str = None,
        sample_info_column: str = None,
        replicate_column: str = None,
    ) -> None:
        """Load and overwrite sequence table based on Excel file.
        
        User specifies column names corresponding to individual sequence parameters.
        Excel is briefly opened during processing for proper functionality.
        
        Args:
            excel_file_path: Path to Excel file containing sequence data.
            sequence_name: Optional sequence name to load before modification.
            sheet_name: Excel sheet index to read (default: 0).
            vial_column: Column name for vial positions.
            method_column: Column name for method names.
            filename_column: Column name for data file names.
            sample_name_column: Column name for sample names.
            sample_info_column: Column name for sample information.
            replicate_column: Column name for replicate information.
            
        Raises:
            FileNotFoundError: If Excel file doesn't exist.
            ValidationError: If methods don't exist.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.prepare_sequence_table(
            ...     excel_file_path="sequence.xlsx",
            ...     vial_column="Vial",
            ...     method_column="Method",
            ...     sample_name_column="Sample Name"
            ... )
        """
        # Column mapping from input to sequence table expected names
        column_map = {
            "Vial": vial_column,
            "Method": method_column,
            "SampleInfo": sample_info_column,
            "SampleName": sample_name_column,
            "DataFileName": filename_column,
            "InjVial": replicate_column
        }

        # Load data from Excel
        if not os.path.isfile(excel_file_path):
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")

        temp_excel_path = self.comm.config.get_temp_dir_path() / r"temp_excel.xlsx"
        shutil.copyfile(excel_file_path, temp_excel_path)
        excel_data = pd.read_excel(temp_excel_path, sheet_name=sheet_name)

        # Prepare result DataFrame
        result_df = pd.DataFrame({
            col: excel_data[src] if src in excel_data.columns else None
            for col, src in column_map.items()
        })

        # Validate methods
        for method in result_df[method_column].dropna().unique():
            self.method._method_validation(method=method)

        

        # Save and process sequence
        processed_file_path = self.comm.config.get_temp_dir_path() / r"temp.xlsx"
        result_df.to_excel(processed_file_path, header=False, index=False)

        self.save_sequence()

        if sequence_name:
            self._validate_sequence_exists(sequence=sequence_name)
            self.load_sequence(sequence_name)

        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True

        workbook = excel.Workbooks.Open(processed_file_path)

        self.comm.send(f"macro {self.comm.config.get_macros_path()}; modify_seq_table_by_excel {len(result_df)}")
        self.save_sequence()

        workbook.Close(SaveChanges=True)
        excel.Quit()

            
    def start(self) -> None:
        """Start the current sequence.
        
        Raises:
            SequenceError: If sequence fails to start.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.start()
        """
        self.comm.send("StartSequence")

    def pause(self) -> None:
        """Pause the current sequence.
        
        The sequence will pause after the current method completes.
        
        Raises:
            SequenceError: If sequence fails to pause.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.pause()
        """
        self.comm.send("PauseSequence")

    def resume(self) -> None:
        """Resume a paused sequence.
        
        Raises:
            SequenceError: If sequence fails to resume.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.resume()
        """
        self.comm.send("ResumeSequence")

    def load_sequence(self, seq_name: str, seq_dir: str = "_SEQPATH$") -> None:
        """Load a specified sequence.
        
        Args:
            seq_name: Name of the sequence to load.
            seq_dir: Directory containing sequences (default: ChemStation sequence path).
            
        Raises:
            SequenceError: If sequence cannot be loaded.
            ValidationError: If sequence doesn't exist.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.load_sequence("TestSequence")
        """
        self.comm.send(f"LoadSequence {seq_dir}, {seq_name}.S")

    def save_sequence(self, seq_name: str = "_SEQFILE$", seq_dir: str = "_SEQPATH$") -> None:
        """Save sequence.
        
        Args:
            seq_name: Sequence name (default: current sequence name).
            seq_dir: Directory for sequences (default: ChemStation sequence path).
            
        Raises:
            SequenceError: If sequence cannot be saved.
            
        Example:
            >>> seq = SequenceModule()
            >>> seq.save_sequence("MySequence")
        """
        if seq_name != "_SEQFILE$":
            seq_name += ".S"

        self.comm.send(f"SaveSequence {seq_dir}, {seq_name}")

    def _validate_sequence_exists(self, sequence: str, dir_path: str = "_SEQPATH$") -> None:
        """Validate sequence existence in specified directory.
        
        Args:
            sequence: Sequence name (without .S extension).
            dir_path: Path to sequence directory (default: ChemStation sequence path).
            
        Raises:
            ValidationError: If sequence doesn't exist in specified directory.
        """
        sequence += ".S"

        if dir_path == "_SEQPATH$":
            dir_path = Path(self.comm.send("response$ = _SEQPATH$"))
        
        if sequence in os.listdir(dir_path):
            return
        else:
            raise ValidationError(f"Sequence not found in directory {dir_path}")
