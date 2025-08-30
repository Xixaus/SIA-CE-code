"""
Automatizovaný systém pro zpracování vzorků s ChemStation a SIA

Použití:
1. Upravte konfiguraci v Config
2. Vytvořte soubor s komentářem (volitelné):
   - Musí být .txt soubor v UTF-8 kódování
   - Např. C:/ChemStation/comments/experiment_01.txt
   - Obsah: popis experimentu, podmínky, poznámky
3. Spusťte: python sample_processor.py
"""

import time
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from tqdm import tqdm

from ChemstationAPI import ChemstationAPI
from SIA_API.methods import PreparedSIMethods
from SIA_API.devices import SyringeController, ValveSelector


# =====================================================================
# KONFIGURACE
# =====================================================================

@dataclass
class Config:
    """Konfigurace systému"""
    # SIA nastavení
    sia_port: str = "COM7"
    syringe_size: int = 1000  # µL
    valve_positions: int = 8
    
    # Porty
    meoh_port: int = 5
    di_port: int = 3
    
    # Objemy (µL)
    meoh_volume: int = 400
    di_volume: int = 100
    
    # Rychlosti (µL/min)
    meoh_speed: int = 1000
    di_speed: int = 1200
    homog_speed: int = 1000
    
    # Homogenizace
    homog_volume: int = 290
    homog_cycles: int = 2
    
    # Časování
    wait_after_meoh: int = 400  # Sekundy - čekání po přidání MeOH
    homog_before_analysis_end: float = 2.0  # Minuty - kdy začít homogenizaci dalšího vzorku před koncem analýzy
    
    # ChemStation
    method_name: str = "Wait"
    comment_file: Optional[str] = None  # Cesta k souboru s komentářem
    
    # Názvy vzorků
    sample_name_template: str = "{i}_homogenization_test"  # {i} bude nahrazeno číslem
    sample_name_prefix: str = ""  # Prefix před číslem vzorku
    sample_name_suffix: str = "_B"  # Suffix za názvem vzorku
    standard_name: str = "STD"  # Název pro standardy
    full_homog_name_template: str = "{i}_DBS_full_homog_B"  # Pro plně homogenizované
    
    # Experiment
    vial_number: int = 10
    num_repetitions: int = 3
    sample_start_number: int = 1  # Počáteční číslo vzorku
    output_file: str = "time_elution.txt"
    
    # Logging
    log_file: str = "sample_processor.log"
    verbose: bool = False


# =====================================================================
# HLAVNÍ TŘÍDA
# =====================================================================

class SampleProcessor:
    """Procesor pro automatizované zpracování vzorků"""
    
    def __init__(self, config: Config = None):
        """Inicializace procesoru"""
        self.config = config or Config()
        self.time_zero = None
        
        # Nastavení logování
        self._setup_logging()
        
        # Validace konfigurace
        self._validate_config()
        
        # Inicializace zařízení
        self._init_devices()
        
    def _setup_logging(self):
        """Nastavení logování"""
        logging.basicConfig(
            level=logging.DEBUG if self.config.verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _validate_config(self):
        """Validace konfigurace"""
        # Validace comment souboru pokud je zadán
        if self.config.comment_file:
            self._validate_comment_file(self.config.comment_file)
            
    def _validate_comment_file(self, filepath: str) -> bool:
        """
        Validace souboru s komentářem
        
        Args:
            filepath: Cesta k souboru
            
        Returns:
            True pokud je soubor validní
            
        Raises:
            FileNotFoundError: Pokud soubor neexistuje
            ValueError: Pokud soubor není .txt nebo je prázdný
        """
        path = Path(filepath)
        
        # Kontrola existence
        if not path.exists():
            raise FileNotFoundError(f"❌ Soubor s komentářem nenalezen: {filepath}")
        
        # Kontrola přípony
        if path.suffix.lower() != '.txt':
            raise ValueError(f"❌ Soubor s komentářem musí být .txt, ne {path.suffix}")
        
        # Kontrola že není prázdný
        if path.stat().st_size == 0:
            raise ValueError(f"❌ Soubor s komentářem je prázdný: {filepath}")
        
        # Kontrola čitelnosti
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError(f"❌ Soubor s komentářem obsahuje pouze prázdné znaky")
        except UnicodeDecodeError:
            raise ValueError(f"❌ Soubor s komentářem není v UTF-8 kódování: {filepath}")
        
        self.logger.info(f"✅ Soubor s komentářem validován: {filepath}")
        self.logger.debug(f"   Velikost: {path.stat().st_size} bajtů")
        self.logger.debug(f"   První řádek: {content.split(chr(10))[0][:50]}...")
        
        return True
        
    def _init_devices(self):
        """Inicializace ChemStation a SIA zařízení"""
        self.logger.info("=" * 60)
        self.logger.info("🚀 INICIALIZACE SYSTÉMU")
        self.logger.info("=" * 60)
        
        # ChemStation
        self.logger.info("📡 Připojování k ChemStation...")
        self.chemstation = ChemstationAPI()
        
        # SIA zařízení
        self.logger.info(f"🔧 Inicializace SIA (port: {self.config.sia_port})")
        self.syringe = SyringeController(
            port=self.config.sia_port,
            syringe_size=self.config.syringe_size,
            print_info=self.config.verbose
        )
        
        self.valve = ValveSelector(
            port=self.config.sia_port,
            num_positions=self.config.valve_positions
        )
        
        self.sia = PreparedSIMethods(
            chemstation_controller=self.chemstation,
            syringe_device=self.syringe,
            valve_device=self.valve
        )
        
        self.logger.info("✅ Systém připraven")
        
    def save_time_record(self, sample_name: str, elapsed_time: float):
        """Uložení časového záznamu"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"{timestamp}\t{sample_name}\t{elapsed_time:.2f}\n"
        
        with open(self.config.output_file, 'a', encoding='utf-8') as f:
            f.write(record)
        
        print(record.strip())
        
    def wait_for_status(self, target_status: str):
        """Čekání na požadovaný status ChemStation"""
        while self.chemstation.system.RC_status() != target_status:
            time.sleep(2)
            
    def prepare_batch(self, vial: int):
        """Příprava dávky - plnění MeOH a DI vody"""
        self.logger.info(f"\n🔄 PŘÍPRAVA DÁVKY (vialka {vial})")
        
        # Příprava průtoku
        self.sia.prepare_batch_flow(self.config.meoh_port, speed=self.config.meoh_speed)
        
        # MeOH
        self.logger.info(f"💧 Plnění MeOH: {self.config.meoh_volume} µL")
        self.sia.batch_fill(
            vial,
            self.config.meoh_volume,
            self.config.meoh_port,
            speed=self.config.meoh_speed
        )
        
        # Čekání
        self.logger.info(f"⏳ Čekání {self.config.wait_after_meoh} s...")
        for _ in tqdm(range(self.config.wait_after_meoh), desc="Čekání po MeOH"):
            time.sleep(1)
        
        # DI voda
        self.logger.info(f"💧 Plnění DI vody: {self.config.di_volume} µL")
        self.sia.batch_fill(
            vial,
            self.config.di_volume,
            self.config.di_port,
            speed=self.config.di_speed
        )
        
        # Start časovače
        self.time_zero = time.time()
        self.logger.info("⏱️ Časovač spuštěn")

        self.logger.info("Příprava systému pro homogenizaci")
        self.sia.prepare_for_liquid_homogenization()
        
    def homogenize(self, vial: int, sample_name: str = None):
        """Homogenizace vzorku"""
        
        self.logger.info(f"🌀 Homogenizace: {sample_name}")
        
        # Zde by byla skutečná homogenizace
        self.sia.homogenize_by_liquid_mixing(
            vial,
            volume_aspirate=self.config.homog_volume,
            num_cycles=self.config.homog_cycles,
            aspirate_speed=self.config.homog_speed, 
            dispense_speed=self.config.homog_speed,
            
        )
        
        # Placeholder
        time.sleep(5)
        
    def run_analysis(self, vial: int, sample_name: str, comment_file: Optional[str] = None):
        """
        Spuštění analýzy v ChemStation
        
        Args:
            vial: Číslo vialky
            sample_name: Název vzorku
            comment_file: Cesta k souboru s komentářem (volitelné)
        """
        self.logger.info(f"🔬 Analýza: {sample_name}")
        
        # Použít comment file z konfigurace pokud není specifikován
        comment_to_use = comment_file or self.config.comment_file
        
        # Validace comment souboru pokud existuje
        if comment_to_use:
            try:
                self._validate_comment_file(comment_to_use)
                self.logger.info(f"📝 Používám komentář: {comment_to_use}")
            except (FileNotFoundError, ValueError) as e:
                self.logger.warning(f"⚠️ Problém s komentářem: {e}")
                comment_to_use = None
        
        # Čekání na připravenost
        self.chemstation.system.ready_to_start_analysis()
        
        # Spuštění metody s nebo bez komentáře
        if comment_to_use:
            self.chemstation.method.execution_method_with_parameters(
                vial,
                self.config.method_name,
                sample_name,
                comment=comment_to_use  # Přidán parametr comment
            )
        else:
            self.chemstation.method.execution_method_with_parameters(
                vial,
                self.config.method_name,
                sample_name
            )
        
        time.sleep(5)
        
        # Čekání na injekci
        self.wait_for_status("Injecting")
        
        # Uložení času
        if self.time_zero:
            elapsed = time.time() - self.time_zero
            self.save_time_record(sample_name, elapsed)
        
        # Čekání na běh
        self.wait_for_status("Run")
        
        # Čekání na dokončení
        analysis_time = self.chemstation.system.get_analysis_time()
        wait_time = max(0, (analysis_time - self.config.homog_before_analysis_end) * 60)
        
        self.logger.info(f"⏳ Čekání {wait_time:.0f} s na dokončení")
        if self.config.homog_before_analysis_end > 0:
            self.logger.info(f"   (Další homogenizace začne {self.config.homog_before_analysis_end} min před koncem)")
        time.sleep(wait_time)
        
    def prepare_for_homogenization(self, volume: int, speed: int):
        """Příprava na homogenizaci"""
        self.logger.info(f"🔄 Příprava homogenizace (objem: {volume} µL)")
        # Zde by byla implementace
        # prepare_to_homogenization(volume, speed)
        time.sleep(2)
    
    def create_comment_file(self, filepath: str, content: str):
        """
        Vytvoření souboru s komentářem
        
        Args:
            filepath: Cesta k souboru
            content: Obsah komentáře
        """
        path = Path(filepath)
        
        # Vytvoření adresáře pokud neexistuje
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Zápis komentáře
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"📝 Vytvořen soubor s komentářem: {filepath}")
        
        # Validace vytvořeného souboru
        self._validate_comment_file(filepath)


# =====================================================================
# EXPERIMENTY
# =====================================================================

def run_time_elution_experiment(processor: SampleProcessor):
    """Experiment časové eluce s homogenizací"""
    config = processor.config
    
    processor.logger.info("\n" + "=" * 60)
    processor.logger.info("🧪 EXPERIMENT: ČASOVÁ ELUCE")
    processor.logger.info("=" * 60)
    
    # Validace metody
    processor.chemstation.validation.validate_method(config.method_name)
    
    # Příprava dávky
    processor.prepare_batch(config.vial_number)
    
    # Příprava homogenizace
    processor.prepare_for_homogenization(50, 550)
    
    # Hlavní smyčka
    for i in tqdm(range(config.num_repetitions), desc="Celkový postup"):
        # Generování názvu vzorku podle šablony
        sample_number = config.sample_start_number + i
        
        if "{i}" in config.sample_name_template:
            sample_name = config.sample_name_template.format(i=sample_number)
        else:
            # Pokud šablona neobsahuje {i}, použij prefix a suffix
            sample_name = f"{config.sample_name_prefix}{sample_number}{config.sample_name_suffix}"
        
        processor.logger.info(f"\n--- Měření {i+1}/{config.num_repetitions} ---")
        processor.logger.info(f"    Vzorek: {sample_name}")
        
        # Homogenizace
        processor.homogenize(config.vial_number, sample_name)
        
        # Analýza (použije comment_file z konfigurace pokud je zadán)
        processor.run_analysis(config.vial_number, sample_name)
    
    processor.logger.info("\n✅ Časová studie dokončena")


def run_standards(processor: SampleProcessor, count: int = 2):
    """Měření standardů"""
    config = processor.config
    
    processor.logger.info("\n" + "=" * 60)
    processor.logger.info("📊 MĚŘENÍ STANDARDŮ")
    processor.logger.info("=" * 60)
    
    for i in range(count):
        processor.wait_for_status("Idle")
        
        # Název standardu
        standard_name = f"{config.standard_name}_{i+1}" if count > 1 else config.standard_name
        
        processor.logger.info(f"📊 Spouštím standard: {standard_name}")
        
        if config.comment_file:
            processor.chemstation.method.execution_method_with_parameters(
                config.vial_number + 1,
                config.method_name,
                standard_name,
                comment=config.comment_file
            )
        else:
            processor.chemstation.method.execution_method_with_parameters(
                config.vial_number + 1,
                config.method_name,
                standard_name
            )
        
        processor.logger.info(f"✅ Standard {i+1}/{count} spuštěn")


def run_full_homogenization_samples(processor: SampleProcessor, count: int = 3):
    """Měření plně homogenizovaných vzorků"""
    config = processor.config
    
    processor.logger.info("\n" + "=" * 60)
    processor.logger.info("🧪 PLNĚ HOMOGENIZOVANÉ VZORKY")
    processor.logger.info("=" * 60)
    
    input("\n📋 Vložte homogenizovaný vzorek a stiskněte Enter...")
    
    for i in range(count):
        sample_name = f"{i+1}_DBS_full_homog_B"
        
        processor.logger.info(f"\n--- Vzorek {i+1}/{count}: {sample_name} ---")
        
        processor.run_analysis(config.vial_number, sample_name)
        processor.wait_for_status("Idle")
    
    processor.logger.info("\n✅ Měření dokončeno")


def run_full_homogenization_samples(processor: SampleProcessor, count: int = 3):
    """Měření plně homogenizovaných vzorků"""
    config = processor.config
    
    processor.logger.info("\n" + "=" * 60)
    processor.logger.info("🧪 PLNĚ HOMOGENIZOVANÉ VZORKY")
    processor.logger.info("=" * 60)
    
    input("\n📋 Vložte homogenizovaný vzorek a stiskněte Enter...")
    
    for i in range(count):
        sample_name = f"{i+1}_DBS_full_homog_B"
        
        processor.logger.info(f"\n--- Vzorek {i+1}/{count}: {sample_name} ---")
        
        processor.run_analysis(config.vial_number, sample_name)
        processor.wait_for_status("Idle")
    
    processor.logger.info("\n✅ Měření dokončeno")


# =====================================================================
# HLAVNÍ PROGRAM
# =====================================================================

def main():
    """Hlavní funkce programu"""
    
    # Vytvoření konfigurace (zde můžete upravit parametry)
    config = Config()
    
    try:
        # Inicializace procesoru
        processor = SampleProcessor(config)
        
        # === VOLITELNÉ: Vytvoření komentáře pro experiment ===
        # processor.create_comment_file(
        #     "comments/experiment_01.txt",
        #     f"""Experiment: Časová studie homogenizace
        # Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        # Metoda: {config.method_name}
        # Počet vzorků: {config.num_repetitions}
        # MeOH objem: {config.meoh_volume} µL
        # DI objem: {config.di_volume} µL
        # Homogenizace: {config.homog_cycles} cykly, {config.homog_volume} µL
        # Poznámky: Test nového protokolu
        # """
        # )
        
        # === VÝBĚR EXPERIMENTŮ (odkomentujte co chcete spustit) ===
        
        # 1. Časová studie s homogenizací
        run_time_elution_experiment(processor)
        
        # 2. Standardy (odkomentujte pokud chcete)
        # run_standards(processor, count=2)
        
        # 3. Plně homogenizované vzorky (odkomentujte pokud chcete)
        # run_full_homogenization_samples(processor, count=3)
        
        processor.logger.info("\n" + "=" * 60)
        processor.logger.info("🎉 VŠECHNY EXPERIMENTY DOKONČENY!")
        processor.logger.info("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Program přerušen uživatelem (Ctrl+C)")
        return 1
        
    except Exception as e:
        print(f"\n\n Kritická chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())