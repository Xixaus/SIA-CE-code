"""
MacroUpdater - Jednoduchý skript pro aktualizaci cest v ChemStation makru.
"""

import sys
from pathlib import Path


class MacroUpdater:
    """Aktualizuje cesty v ChemStation komunikačním makru."""
    
    def __init__(self):
        # Najít cestu k makru relativně k tomuto souboru
        if getattr(sys, 'frozen', False):
            # Spuštěno jako .exe
            current_dir = Path(sys.executable).parent.parent
        else:
            # Spuštěno jako .py skript
            current_dir = Path(__file__).parent.parent
            
        self.macro_path = current_dir / "core" / "ChemPyConnect.mac"
        self.comm_dir = self.macro_path.parent / "communication_files"
    
    def update_macro_paths(self):
        """Aktualizuje cesty v makru."""
        # Vytvořit komunikační adresář pokud neexistuje
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        
        # Přečíst makro
        with open(self.macro_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Najít a aktualizovat řádek s MonitorFile
        updated = False
        for i, line in enumerate(lines):
            if 'MonitorFile' in line and '"' in line:
                lines[i] = f'    MonitorFile "{self.comm_dir}"\n'
                updated = True
                break
        
        if not updated:
            raise Exception("Řádek s MonitorFile nebyl nalezen v makru!")
        
        # Zapsat zpět
        with open(self.macro_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    
    def run(self):
        """Spustí aktualizaci a vypíše instrukce."""
        print("=" * 60)
        print("CHEMSTATION MACRO UPDATER")
        print("=" * 60)
        print()
        print("Aktualizuji cesty v ChemStation makru...")
        print(f"Cesta k makru: {self.macro_path}")
        print()
        
        try:
            self.update_macro_paths()
            print("Cesty byly úspěšně aktualizovány!")
            print()
            print("INSTRUKCE PRO CHEMSTATION:")
            print("-" * 60)
            print("1. Otevřete ChemStation")
            print("2. Zkopírujte a vložte následující příkaz do příkazového řádku:")
            print()
            print(f'macro "{self.macro_path.absolute()}"; Python_run')
            print()
            print("-" * 60)
            
        except Exception as e:
            print(f"CHYBA: {e}")
            print()
            print("Možné příčiny:")
            print("- Skript není ve správné složce")
            print("- Soubor ChemPyConnect.mac nebyl nalezen")
            print("- Nemáte oprávnění k zápisu")


def main():
    """Hlavní funkce s čekáním na ukončení."""
    try:
        updater = MacroUpdater()
        updater.run()
    except Exception as e:
        print(f"KRITICKÁ CHYBA: {e}")
    
    print()
    print("=" * 60)
    input("Stiskněte ENTER pro ukončení...")


if __name__ == "__main__":
    main()