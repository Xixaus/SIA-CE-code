import time
import pandas as pd
from pathlib import Path
from typing import Optional
from IPython.display import display
from tqdm import tqdm
import logging
from config import ProcessorConfig, setup_logging


class SampleProcessor:
    """Class for sample processing and analysis"""
    
    def __init__(self, config: ProcessorConfig, chemstation, sia_methods):
        """
        Initialize sample processor
        
        Args:
            config: Processor configuration
            chemstation: ChemStation API instance
            sia_methods: SIA methods instance
        """
        self.config = config
        self.chemstation = chemstation
        self.sia_methods = sia_methods
        
        # Set up logger
        self.logger = setup_logging(config)
        self.logger.info("="*60)
        self.logger.info("INICIALIZACE SAMPLE PROCESSOR")
        self.logger.info("="*60)
        
        # Load data from Excel
        self.df = self._load_excel_data()
        
        # Validate columns
        self._validate_dataframe()
        
        self.logger.info(f"✓ Načteno {len(self.df)} vzorků pro zpracování")
        self.logger.info(f"✓ Rychlost plnění MeOH: {config.batch_fill_speed_meoh} µL/min")
        self.logger.info(f"✓ Rychlost plnění DI: {config.batch_fill_speed_di} µL/min")
        
    def _load_excel_data(self) -> pd.DataFrame:
        """Load data from Excel file"""
        try:
            excel_path = Path(self.config.excel_file_path)
            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found: {excel_path}")
            
            self.logger.info(f"📁 Načítám data z: {excel_path}")
            df = pd.read_excel(
                excel_path,
                #sheet_name=self.config.sheet_name
            )
            
            display(df)
            #input("OK?")

            self.logger.info(f"✓ Načteno {len(df)} řádků z Excel souboru")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při načítání Excel souboru: {e}")
            raise
    
    def _validate_dataframe(self):
        """Validate that DataFrame contains all required columns"""
        required_columns = [
            self.config.column_vial,
            self.config.column_meoh,
            self.config.column_di,
            self.config.column_method,
            self.config.column_name
        ]
        
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            error_msg = f"Missing columns in Excel file: {missing_columns}"
            self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        self.logger.info("✓ Validace DataFrame úspěšná - všechny požadované sloupce nalezeny")
        
    def wait_for_time(self, duration: float, description: str = "Waiting"):
        """
        Wait for specified duration in seconds with progress bar
        
        Args:
            duration: Wait duration in seconds
            description: Description for progress bar
        """
        if self.config.detailed_logging:
            self.logger.debug(f"⏱️ Čekání {duration:.1f} sekund: {description}")
        
        if self.config.show_progress_bars:
            for _ in tqdm(range(int(duration)), desc=description):
                time.sleep(1)
        else:
            time.sleep(duration)
    
    def prepare_initial_batch(self):
        """Prepare initial batch of samples (MeOH and DI) with individual incubation timing"""
        self.logger.info("="*60)
        self.logger.info(f"PŘÍPRAVA PRVNÍCH {self.config.initial_batch_size} VZORKŮ")
        self.logger.info("="*60)
        
        # Prepare batch flow
        self.logger.info("🔧 Příprava batch flow systému")
        self.sia_methods.prepare_batch_flow(self.config.meoh_port)
        
        # Dictionary to store MeOH addition times for each sample
        meoh_addition_times = {}
        
        # Add MeOH to first samples
        self.logger.info(f"\n💧 PLNĚNÍ MeOH - Port {self.config.meoh_port}, Rychlost: {self.config.batch_fill_speed_meoh} µL/min")
        self.logger.info("-"*40)
        
        for i in tqdm(range(self.config.initial_batch_size), desc="Plnění MeOH"):
            sample = self.df.iloc[i]
            vial = sample[self.config.column_vial]
            meoh_volume = sample[self.config.column_meoh]
            
            self.logger.info(f"  → Vialka {vial}: přidávám {meoh_volume} µL MeOH")
            
            
            self.sia_methods.batch_fill(
                vial, 
                meoh_volume, 
                self.config.meoh_port, 
                speed=self.config.batch_fill_speed_meoh
            )
            
            # Store the time when MeOH addition was completed
            meoh_addition_times[i] = time.time()
        
        self.logger.info(f"✓ MeOH přidán do všech {self.config.initial_batch_size} vialek")
        
        # Add DI to first samples with individual waiting
        self.logger.info(f"\n💧 PLNĚNÍ DI VODY - Port {self.config.di_port}, Rychlost: {self.config.batch_fill_speed_di} µL/min")
        self.logger.info(f"   (s individuální inkubací MeOH: {self.config.waiting_time_after_meoh}s pro každý vzorek)")
        self.logger.info("-"*40)
        
        for i in tqdm(range(self.config.initial_batch_size), desc="Plnění DI vody"):
            sample = self.df.iloc[i]
            vial = sample[self.config.column_vial]
            di_volume = sample[self.config.column_di]
            
            # Calculate how much time has elapsed since MeOH was added to this specific sample
            elapsed_time = time.time() - meoh_addition_times[i]
            remaining_wait_time = self.config.waiting_time_after_meoh - elapsed_time
            
            if remaining_wait_time > 0:
                self.logger.info(f"  → Vialka {vial}: doba inkubace MeOH {self.config.waiting_time_after_meoh}s, uplynulo {elapsed_time:.1f}s, zbývá {remaining_wait_time:.1f}s")
                self.wait_for_time(remaining_wait_time, f"Inkubace MeOH pro vialku {vial} - zbývá {remaining_wait_time:.1f}s")
            else:
                self.logger.info(f"  → Vialka {vial}: doba inkubace MeOH {self.config.waiting_time_after_meoh}s už uplynula (celkem {elapsed_time:.1f}s)")
            
            self.logger.info(f"  → Vialka {vial}: přidávám {di_volume} µL DI vody")
            
            self.sia_methods.batch_fill(
                vial,
                di_volume,
                self.config.di_port,
                speed=self.config.batch_fill_speed_di
            )
        
        self.logger.info(f"✓ DI voda přidána do všech {self.config.initial_batch_size} vialek")

        # Prepare for homogenization
        self.logger.info("\n🌀 HOMOGENIZACE PRVNÍCH VZORKŮ")
        self.logger.info("-"*40)
        self.logger.info(f"Parametry homogenizace:")
        self.logger.info(f"  - Objem: {self.config.homogenization_volume} µL")
        self.logger.info(f"  - Cykly: {self.config.homogenization_cycles}")
        self.logger.info(f"  - Rychlost aspirace: {self.config.homogenization_aspirate_speed} µL/min")
        self.logger.info(f"  - Rychlost dispenzace: {self.config.homogenization_dispense_speed} µL/min")
        
        self.sia_methods.prepare_for_liquid_homogenization()

        # Homogenize first batch
        for i in tqdm(range(self.config.initial_batch_size), desc="Homogenizace"):
            sample = self.df.iloc[i]
            vial = sample[self.config.column_vial]
            name = sample[self.config.column_name]
            
            self.logger.info(f"  → Homogenizuji vialku {vial} ({name})")
            
            self.sia_methods.homogenize_by_liquid_mixing(
                vial,
                volume_aspirate=self.config.homogenization_volume,
                num_cycles=self.config.homogenization_cycles,
                dispense_speed=self.config.homogenization_dispense_speed,
                aspirate_speed=self.config.homogenization_aspirate_speed,
                clean_after=self.config.homogenization_clean_after
            )
        
        self.logger.info("✓ Příprava prvních vzorků dokončena")
        self.logger.info("="*60)
    
    def wait_for_run(self):
        """Wait until ChemStation starts running"""
        self.logger.debug("⏳ Čekání na spuštění analýzy v ChemStation...")
        
        while self.chemstation.system.RC_status() != "Run":
            time.sleep(2)
        
        self.logger.debug("▶️ ChemStation analýza běží")
    
    def prepare_next_sample(self, current_index: int) -> bool:
        """
        Prepare next sample if it exists
        
        Args:
            current_index: Current sample index
            
        Returns:
            True if next sample was prepared, False otherwise
        """
        next_index = current_index + self.config.initial_batch_size
        
        if next_index < len(self.df):
            next_sample = self.df.iloc[next_index]
            vial = next_sample[self.config.column_vial]
            meoh_volume = next_sample[self.config.column_meoh]
            di_volume = next_sample[self.config.column_di]
            name = next_sample[self.config.column_name]
            
            self.logger.info(f"\n🔄 PŘÍPRAVA DALŠÍHO VZORKU {next_index + 1}/{len(self.df)}")
            self.logger.info(f"   Vialka: {vial}, Název: {name}")
            
            # Flush transfer line
            self.logger.debug("  🚿 Proplach transfer line")
            self.sia_methods.flush_transfer_line_to_waste()

            # Add MeOH
            self.logger.info(f"  💧 Plnění MeOH: {meoh_volume} µL (rychlost: {self.config.batch_fill_speed_meoh} µL/min)")
            time_start_add_meoh = time.time()
            
            self.sia_methods.batch_fill(
                vial,
                meoh_volume,
                self.config.meoh_port,
                speed=self.config.batch_fill_speed_meoh
            )
            
            # Wait after adding MeOH
            time_wait = self.config.waiting_time_after_meoh - (time.time() - time_start_add_meoh)
            
            if time_wait > 0:
                self.logger.info(f"  ⏱️ Inkubace MeOH: {time_wait:.0f} sekund")
                self.wait_for_time(time_wait, f"Inkubace MeOH (vialka {vial})")
            
            # Add DI
            self.logger.info(f"  💧 Plnění DI vody: {di_volume} µL (rychlost: {self.config.batch_fill_speed_di} µL/min)")
            self.sia_methods.batch_fill(
                vial,
                di_volume,
                self.config.di_port,
                speed=self.config.batch_fill_speed_di
            )
            
            # Prepare and homogenize
            self.logger.info(f"  🌀 Homogenizace vzorku")
            self.sia_methods.prepare_for_liquid_homogenization()
            
            self.sia_methods.homogenize_by_liquid_mixing(
                vial,
                volume_aspirate=self.config.homogenization_volume,
                num_cycles=self.config.homogenization_cycles,
                dispense_speed=self.config.homogenization_dispense_speed,
                aspirate_speed=self.config.homogenization_aspirate_speed,
                clean_after=self.config.homogenization_clean_after
            )
            
            self.logger.info(f"  ✓ Vzorek {next_index + 1} připraven")
            return True
            
        self.logger.debug("ℹ️ Žádné další vzorky k přípravě")
        return False
    
    def analyze_sample(self, sample_index: int):
        """
        Start sample analysis
        
        Args:
            sample_index: Sample index in DataFrame
        """
        sample = self.df.iloc[sample_index]
        vial = sample[self.config.column_vial]
        method = sample[self.config.column_method]
        name = sample[self.config.column_name]
        
        self.logger.info(f"\n📊 SPUŠTĚNÍ ANALÝZY")
        self.logger.info(f"   Název: '{name}'")
        self.logger.info(f"   Vialka: {vial}")
        self.logger.info(f"   Metoda: {method}")
        
        self.chemstation.system.ready_to_start_analysis(
            verbose=self.config.verbose_chemstation
        )
        
        self.chemstation.method.execution_method_with_parameters(
            vial,
            method,
            name
        )
        
        self.wait_for_run()
        self.logger.info(f"   ▶️ Analýza vzorku '{name}' běží")
    
    def wait_for_next_homogenization(self):
        """Wait optimal time before homogenizing next sample"""
        remaining_time = self.chemstation.system.get_remaining_analysis_time()
        wait_time = (remaining_time - self.config.time_prepare_and_homogenization) * 60
        
        if wait_time > 0:
            self.logger.info(f"⏱️ Čekání {wait_time:.0f} sekund před přípravou dalšího vzorku")
            self.wait_for_time(wait_time, "Čekání na optimální čas homogenizace")
        else:
            self.logger.debug("ℹ️ Není potřeba čekat - připravuji další vzorek ihned")
    
    def process_all_samples(self):
        """Main method for processing all samples"""
        self.logger.info("="*70)
        self.logger.info("🚀 START ZPRACOVÁNÍ VŠECH VZORKŮ")
        self.logger.info(f"   Celkový počet vzorků: {len(self.df)}")
        self.logger.info(f"   Čas inkubace MeOH: {self.config.waiting_time_after_meoh/60:.1f} minut")
        self.logger.info(f"   Velikost první dávky: {self.config.initial_batch_size}")
        self.logger.info("="*70)
        
        try:
            # Validation and preparation
            self.logger.info("\n📋 VALIDACE A PŘÍPRAVA SYSTÉMU")
            self.logger.info("-"*40)
            
            self.logger.info("  🔍 Validace metody a vialek...")
            self.chemstation.validation.validate_method(
                self.config.default_method_name,
                check_vials=True
            )
            
            self.chemstation.method.load(self.config.default_method_name)
            
            # Get vial list for validation
            vial_list = self.df[self.config.column_vial].tolist()
            self.chemstation.validation.list_vial_validation(vial_list)
            
            self.chemstation.system.ready_to_start_analysis(
                timeout=self.config.ready_timeout,
                verbose=self.config.verbose_chemstation
            )
            
            self.logger.info("  🔧 Inicializace SI systému...")
            self.sia_methods.system_initialization_and_cleaning()
            self.logger.info("  ✓ Systém připraven")

            # Prepare initial batch (if needed)
            self.prepare_initial_batch()
            
            # Process all samples
            total_samples = len(self.df)
            
            for index in range(total_samples):
                sample = self.df.iloc[index]
                vial = sample[self.config.column_vial]
                name = sample[self.config.column_name]
                
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📌 ZPRACOVÁNÍ VZORKU {index + 1}/{total_samples}")
                self.logger.info(f"   Název: {name}")
                self.logger.info(f"   Vialka: {vial}")
                self.logger.info(f"{'='*60}")
                
                # Homogenize before analysis
                self.logger.info(f"\n🌀 HOMOGENIZACE PŘED ANALÝZOU")
                self.logger.info(f"   Vialka {vial}: {self.config.homogenization_cycles} cykly")
                self.logger.info(f"   Objem: {self.config.homogenization_volume} µL")
                
                self.sia_methods.homogenize_by_liquid_mixing(
                    vial,
                    volume_aspirate=self.config.homogenization_volume,
                    num_cycles=self.config.homogenization_cycles,
                    dispense_speed=self.config.homogenization_dispense_speed,
                    aspirate_speed=self.config.homogenization_aspirate_speed,
                    clean_after=self.config.homogenization_clean_after
                )
                
                self.logger.info(f"   ✓ Homogenizace dokončena")

                # Analyze current sample
                self.analyze_sample(index)
                
                # Prepare next sample during analysis
                if index < total_samples - 1:
                    has_next = self.prepare_next_sample(index)
                    if has_next:
                        self.logger.info(f"   ✓ Další vzorek připraven během analýzy")
                
                # Wait for optimal time
                if index < total_samples - 1:
                    self.wait_for_next_homogenization()
            
            self.logger.info("\n" + "="*70)
            self.logger.info("✅ VŠECHNY VZORKY ÚSPĚŠNĚ ZPRACOVÁNY")
            self.logger.info(f"   Zpracováno vzorků: {total_samples}")
            self.logger.info(f"   Čas dokončení: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("="*70)
            
        except Exception as e:
            self.logger.error(f"❌ KRITICKÁ CHYBA při zpracování vzorků: {e}", exc_info=True)
            raise

# Main function
def main(config_file: str = None):
    """
    Main function to run the process
    
    Args:
        config_file: Path to configuration file (optional)
    """
    # Load configuration
    if config_file:
        # Configuration could be loaded from JSON/YAML file here
        pass
    else:
        config = ProcessorConfig()
    
    # Set up logger for main
    logger = logging.getLogger("Main")
    logger.info("="*60)
    logger.info("🚀 SPUŠTĚNÍ HLAVNÍHO PROGRAMU")
    logger.info("="*60)
    
    try:
        # Import required modules (assuming they are available)
        from ChemstationAPI import ChemstationAPI
        from SIA_API.methods import PreparedSIMethods
        from SIA_API.devices import SyringeController, ValveSelector
        
        # Initialize devices
        logger.info("📡 Inicializace ChemStation API")
        chemstation = ChemstationAPI()
        
        logger.info("🔧 Inicializace SIA zařízení")
        logger.info(f"   Port: COM8")
        logger.info(f"   Velikost stříkačky: 1000 µL")
        logger.info(f"   Počet pozic ventilu: 8")
        
        syringe = SyringeController(port="COM8", syringe_size=1000, print_info=False)
        valve = ValveSelector(port="COM8", num_positions=8)
        
        sia_methods = PreparedSIMethods(
            chemstation_controller=chemstation,
            syringe_device=syringe,
            valve_device=valve
        )
        
        # Create and run processor
        processor = SampleProcessor(config, chemstation, sia_methods)
        processor.process_all_samples()
        
        logger.info("\n" + "="*60)
        logger.info("✅ PROGRAM ÚSPĚŠNĚ DOKONČEN")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ KRITICKÁ CHYBA v hlavním programu: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()