from dataclasses import dataclass
from typing import Optional
import logging


@dataclass
class ProcessorConfig:
    """Configuration for sample processing"""
    
    # Excel and DataFrame configuration
    excel_file_path: str = r"C:\Users\hpst\python\SIA-CE-1\final_program.xlsx"
    sheet_name: str = "Sheet1"
    
    # Column names in Excel file
    column_vial: str = "Vial"
    column_meoh: str = "MeOH"
    column_di: str = "DI" 
    column_method: str = "Method"
    column_name: str = "Name"
    
    # SIA system ports
    meoh_port: int = 5
    di_port: int = 3
    
    # Time parameters (seconds)
    waiting_time_after_meoh: int = 450  # 7,5 minutes
    time_prepare_and_homogenization: float = 2.0  # minutes
    
    # Homogenization parameters
    homogenization_volume: int = 320  # µL
    homogenization_cycles: int = 3
    homogenization_aspirate_speed: int = 1000  # µL/min
    homogenization_dispense_speed: int = 1000  # µL/min
    homogenization_clean_after: bool = False
    
    # Batch parameters - ROZDĚLENÉ RYCHLOSTI PRO MeOH a DI
    initial_batch_size: int = 3
    batch_fill_speed_meoh: int = 1000  # µL/min pro MeOH
    batch_fill_speed_di: int = 1200    # µL/min pro DI vodu
    
    # ChemStation parameters
    default_method_name: str = "Wait"
    ready_timeout: int = 10  # seconds
    
    # Logging configuration
    log_file: str = "sample_processor.log"
    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_console: bool = False  # Změněno na True pro lepší přehled
    
    # Other settings
    show_progress_bars: bool = True
    verbose_chemstation: bool = False
    verbose_SI_method: bool = True
    detailed_logging: bool = True  # Nový parametr pro detailní logování


def setup_logging(config: ProcessorConfig) -> logging.Logger:
    """Set up logging according to configuration"""
    
    # Create logger
    logger = logging.getLogger("SampleProcessor")
    logger.setLevel(getattr(logging, config.log_level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(config.log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(config.log_format))
    logger.addHandler(file_handler)
    
    # Console handler (if requested)
    if config.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(config.log_format))
        logger.addHandler(console_handler)
    
    return logger