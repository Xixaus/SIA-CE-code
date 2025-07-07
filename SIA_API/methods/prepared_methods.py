"""
SIA Workflows - High-level automated procedures for SIA system operations.

Provides comprehensive workflows for sample preparation, filling operations,
and system maintenance procedures.
"""

import time
from typing import Optional, Dict, Any, List
from ..devices.syringe_controller import SyringeController
from ..devices.valve_selector import ValveSelector
from .config import PortConfig, DEFAULT_PORTS


# Default configuration constants
DEFAULT_WASH_VIAL = 48
DEFAULT_DRY_VIAL = 49
DEFAULT_WASTE_VIAL = 50

DEFAULT_BUBBLE_VOLUME = 15
DEFAULT_TRANSFER_LINE_VOLUME = 300
DEFAULT_HOLDING_COIL_VOLUME = 1000

DEFAULT_SPEED_AIR = 5000
DEFAULT_SPEED_FAST = 3500
DEFAULT_SPEED_NORMAL = 2000
DEFAULT_SPEED_SLOW = 1500


class PreparedSIAMethods:
    """
    Předpřipravené metody pro systém SIA-CE. Zahrnuje přípravu, kontinuální a diskontinuální plnění. Možnost pneumatické homogenizace roztoku ve vilace v CE. Možnosti oplachu jehly mezi plněními.
    
    Attributes:
        chemstation: ChemStation controller instance
        ports: Port configuration for the system
        syringe: Syringe controller device
        valve: Valve selector device
        syringe_size: Size of the syringe in microliters
    """
    
    def __init__(self, chemstation_controller, syringe_device: SyringeController, 
                 valve_device: ValveSelector, ports_config: Optional[PortConfig] = None):
        """
        Initialize SIA workflow operations with mandatory device instances.
        
        Args:
            chemstation_controller: ChemStation controller instance
            syringe_device: Initialized SyringeController instance (required)
            valve_device: Initialized ValveSelector instance (required)
            ports_config: PortConfig instance (uses DEFAULT_PORTS if None)
        
        Example:
            >>> syringe = SyringeController(port="COM3", syringe_size=1000)
            >>> valve = ValveSelector(port="COM4", num_positions=8)
            >>> workflow = PreparedMethods(controller, syringe_device=syringe, valve_device=valve)
        """
        self.chemstation = chemstation_controller
        self.ports = ports_config or DEFAULT_PORTS
        self.syringe = syringe_device
        self.valve = valve_device
        self.syringe_size = syringe_device.syringe_size

        self.chemstation.validation.validate_vial_in_system(DEFAULT_WASH_VIAL)
        #self.chemstation.validation.validate_vial_in_system(DEFAULT_DRY_VIAL)
        self.chemstation.validation.validate_vial_in_system(DEFAULT_WASTE_VIAL)

    def _resolve_ports(self, **kwargs) -> Dict[str, int]:
        """
        Resolve port assignments using config defaults and optional overrides.
        
        Args:
            **kwargs: Port overrides (waste_port, air_port, di_port, transfer_port, meoh_port)
            
        Returns:
            Dict with resolved port assignments
        """
        return {
            'waste_port': kwargs.get('waste_port') or self.ports.waste_port,
            'air_port': kwargs.get('air_port') or self.ports.air_port,
            'di_port': kwargs.get('di_port') or self.ports.di_port,
            'transfer_port': kwargs.get('transfer_port') or self.ports.transfer_port,
            'meoh_port': kwargs.get('meoh_port') or self.ports.meoh_port,
        }

    def _split_volume_to_cycles(self, total_volume: int, max_volume: int) -> List[int]:
        """
        Split large volume into multiple syringe cycles.
        
        Args:
            total_volume: Total volume to dispense (µL)
            max_volume: Maximum volume per cycle (µL)
            
        Returns:
            List of volumes for each cycle
            
        Example:
            >>> _split_volume_to_cycles(2500, 1000)
            [1000, 1000, 500]
        """
        return [max_volume] * (total_volume // max_volume) + \
               ([total_volume % max_volume] if total_volume % max_volume else [])

    def load_to_replenishment(self, vial_number: int) -> None:
        """
        Load vial to replenishment position in CE carousel.
        
        Args:
            vial_number: Vial position number (1-50)
        """
        self.chemstation.ce.load_vial_to_position(vial_number, "replenishment")

    def unload_from_replenishment(self) -> None:
        """Unload vial from replenishment position back to carousel."""
        self.chemstation.ce.unload_vial_from_position()

    def _flush_syringe_loop(self) -> None:
        """
        Flush and prime syringe holding loop.
        
        Performs a complete flush cycle to remove any residual liquid
        from the syringe and holding loop.
        """
        self.syringe.valve_in()
        self.syringe.aspirate(150)
        self.syringe.valve_up()
        self.syringe.aspirate(150)
        self.syringe.valve_out()
        self.syringe.dispense()
        self.syringe.valve_in()
        self.syringe.aspirate()
        self.syringe.valve_out()
        self.syringe.dispense()

    def _create_separating_bubble(self, port: int, bubble_volume: int) -> None:
        """
        Vytvoření vzduchové bublinky na konci holding coily. Zabranuje promíchání  kontaminaci mezi natahnovaou kapalinou a kapalinou v holding coil.
        
        Args:
            port: Port number to aspirate from (typically air port)
            bubble_volume: Volume of air bubble in microliters
        """
        self.syringe.valve_out()
        self.valve.position(port)
        self.syringe.aspirate(bubble_volume)
        self.syringe.valve_up()
        self.syringe.dispense()
        self.syringe.valve_out()

    def clean_needle(self,volume_flush, wash_vial=DEFAULT_WASH_VIAL):
        """
        Oplach jehly v oplachovací vialce pro zabránění křížové kontaminace. Následně je vyfouknuta zbytková kapalina do vzduchu.
        """

        self.load_to_replenishment(wash_vial)
        time.sleep(2)
        self.syringe.dispense(volume_flush/2)

        self.unload_from_replenishment()
        time.sleep(1)
        self.syringe.dispense(volume_flush/2)


    def system_initialization_and_cleaning(self, waste_vial: int = DEFAULT_WASTE_VIAL, 
                                         bubble: int = 20, **port_overrides):
        """
        Complete system initialization and cleaning procedure.
        
        Performs comprehensive system preparation including:
        - Syringe initialization
        - Loop flushing with air
        - Methanol cleaning
        - DI water rinsing
        - Transfer line conditioning
        
        Args:
            waste_vial: Waste vial number (default: 50)
            bubble: Separating bubble volume in µL (default: 20)
            **port_overrides: Optional port overrides
            
        Example:
            >>> workflow.system_initialization_and_cleaning(waste_vial=48, bubble=25)
        """
        ports = self._resolve_ports(**port_overrides)
        
        # Load vial and set waste position
        self.load_to_replenishment(waste_vial)
        self.valve.position(ports['waste_port'])

        # Initialize and set speed
        self.syringe.initialize()
        self.syringe.set_speed_uL_min(DEFAULT_SPEED_FAST)

        # Flush and prime loop
        self._flush_syringe_loop()
        time.sleep(1)

        # Create separating bubble
        self._create_separating_bubble(ports['air_port'], bubble)

        # Flush with methanol
        time.sleep(1)
        self.valve.position(ports['air_port'])
        self.syringe.aspirate(20)
        self.valve.position(ports['meoh_port'])
        self.syringe.aspirate(250)
        self.valve.position(ports['air_port'])
        self.syringe.aspirate()
        self.valve.position(ports['waste_port'])
        self.syringe.dispense()

        # Flush and prime DI loop
        time.sleep(1)
        self.valve.position(ports['air_port'])
        self.syringe.aspirate(50)
        self.valve.position(ports['di_port'])
        self.syringe.aspirate()
        self.valve.position(ports['waste_port'])
        self.syringe.dispense()

        # Flush transfer line
        self.valve.position(ports['air_port'])
        self.syringe.aspirate(500)
        self.valve.position(ports['di_port'])
        self.syringe.aspirate(100)
        self.valve.position(ports['transfer_port'])
        self.syringe.dispense()

    def prepare_continuous_flow(self, solvent_port: int, waste_vial: int = DEFAULT_WASTE_VIAL, 
                               bubble_volume: int = 10,
                               solvent_holding_coil_volume: int = 10,
                               transfer_coil_flush: int = 500,
                               holding_coil_flush: int = DEFAULT_HOLDING_COIL_VOLUME, 
                               speed: int = DEFAULT_SPEED_SLOW, **port_overrides):
        """
        Prepare system for continuous flow filling operations.
        
        Systém se pročistí solventem z daného portu, naplní se transferlina solventem z portu a vytvoří se oddělující bublinka v holding coil mezi solventem a kapalinou v holding coil.
        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number (default: 50)
            bubble_volume: Air bubble volume in µL (default: 15)
            solvent_holding_coil_volume: objem solventu na konci olding coily
            transfer_coil_flush: Volume for transfer coil flushing in µL (default: 250)
            holding_coil_flush: Volume for holding coil flushing in µL (default: 500)
            speed: Flow rate in µL/min (default: 1500)
            **port_overrides: Optional port overrides
            
        Example:
            >>> workflow.prepare_continuous_flow(
            ...     solvent_port=5,  # Methanol port
            ...     bubble_volume=20,
            ...     speed=2000
            ... )
        """
        ports = self._resolve_ports(**port_overrides)
        
        # Load vial and set speed
        self.load_to_replenishment(waste_vial)
        self.syringe.set_speed_uL_min(speed)

        # Flush holding coil
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(transfer_coil_flush)
        self.valve.position(ports['waste_port'])
        self.syringe.dispense()

        # Create solvent bubble
        self._create_separating_bubble(ports["air_port"], bubble_volume) #vzduchová bublinka
        self._create_separating_bubble(solvent_port, solvent_holding_coil_volume) #solventová bublinka


        # Flush and fill transfer line with solvent
        self.valve.position(solvent_port)
        self.syringe.aspirate(holding_coil_flush)
        self.valve.position(ports['transfer_port'])
        self.syringe.dispense()

    def continuous_fill(self, vial: int, volume: int, solvent_port: int,
                       flush_needle: Optional[int] = None, 
                       wash_vial: int = DEFAULT_WASH_VIAL, 
                       speed: int = DEFAULT_SPEED_NORMAL, **port_overrides):
        """
        Execute continuous flow filling operation.
        
        Dávkování solventu z daného portu v kontinuálním režimu. Tansferlina je naplněná solventem (nutné připravit systém pomocí prepare_continuous_flow daným solventem).
        natáhnutí solventu s portu a nadávkování skrze transfer linu naplněnou solventem. Rychlé a ideální v případě dávkování solventu do více vilkem po sobě.
        V případě potřeby je možnost opláchnutí dávkovací jehly v CE do vialky a malým odpuštěním solventu.
        
        Args:
            vial: Target vial number (1-50)
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent
            flush_needle: Optional needle flush volume in µL
            wash_vial: Vial for needle washing (default: 48)
            speed: Flow rate in µL/min (default: 2000)
            **port_overrides: Optional port overrides
            
        Note:
            Requires prior system preparation with prepare_continuous_flow()
            
        Example:
            >>> workflow.continuous_fill(
            ...     vial=15,
            ...     volume=1500,
            ...     solvent_port=5,
            ...     flush_needle=50
            ... )
        """
        ports = self._resolve_ports(**port_overrides)

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size)
        
        # Load vial and set speed
        self.load_to_replenishment(vial)
        self.syringe.set_speed_uL_min(speed)

        for i, cycle_vol in enumerate(cycle_volumes):
            if i != len(cycle_volumes) - 1:
                # Regular cycles
                self.valve.position(solvent_port) 
                self.syringe.aspirate(cycle_vol)
                self.valve.position(ports['transfer_port'])
                self.syringe.dispense(cycle_vol)
            else:
                # Last cycle with optional needle flush
                if flush_needle is not None:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    self.valve.position(ports['transfer_port'])
                    self.syringe.dispense(cycle_vol - flush_needle)

                    self.load_to_replenishment(wash_vial)
                    self.syringe.dispense()
                else:
                    self.valve.position(solvent_port)
                    self.syringe.aspirate(cycle_vol)
                    self.valve.position(ports['transfer_port'])
                    self.syringe.dispense(cycle_vol)

        self.unload_from_replenishment()

    def prepare_batch_flow(self, solvent_port: int, waste_vial: int = DEFAULT_WASTE_VIAL, 
                          bubble_volume: int = 10, 
                          transfer_coil_volume: int = DEFAULT_TRANSFER_LINE_VOLUME,
                          coil_flush: int = 150,
                          speed: int = DEFAULT_SPEED_SLOW, **port_overrides):
        """
        Prepare system for batch flow (discontinuous) filling operations.
        
        Systém je propláchnutý solventem z daného portu a transferlina je nplněná vzduchem. Na konci holding coily je vytvořena oddělujídí vzduchová bublinka pro zabránění míchání solventů z holding coily.        
        Args:
            solvent_port: Port number connected to solvent reservoir
            waste_vial: Waste vial number (default: 50)
            bubble_volume: Air bubble volume in µL (default: 10)
            transfer_coil_volume: Transfer line volume in µL (default: 500)
            transfer_coil_flush: Volume for transfer coil flushing in µL (default: 150)
            holding_coil_flush: Volume for holding coil flushing in µL (default: 500)
            speed: Flow rate in µL/min (default: 1500)
            **port_overrides: Optional port overrides
            
        Example:
            >>> workflow.prepare_batch_flow(
            ...     solvent_port=3,  # DI water port
            ...     transfer_coil_volume=600
            ... )
        """
        ports = self._resolve_ports(**port_overrides)
        
        # Load vial and set speed
        self.load_to_replenishment(waste_vial)
        self.syringe.set_speed_uL_min(speed)

        # Flush transfer loop
        self.syringe.valve_in()
        self.syringe.aspirate(100)
        self.syringe.valve_out()
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(ports['waste_port'])
        self.syringe.dispense()

        self._create_separating_bubble(ports['air_port'], bubble_volume)

        # Flush and fill transfer line with air
        self.valve.position(ports['air_port'])
        self.syringe.aspirate(transfer_coil_volume)
        self.valve.position(solvent_port)
        self.syringe.aspirate(coil_flush)
        self.valve.position(ports['transfer_port'])
        self.syringe.dispense()

    def batch_fill(self, vial: int, volume: int, solvent_port: int, 
                  transfer_line_volume: int = DEFAULT_TRANSFER_LINE_VOLUME,
                  bubble_volume:int = 10,
                  flush_needle: Optional[int] = None,
                  speed: int = DEFAULT_SPEED_NORMAL,
                  unload: bool = True,
                  wait: Optional[int] = None,
                   **port_overrides):
        """
        Execute batch flow (discontinuous) filling operation.
        
        Plnění vialek v diskontinuálním módu. Solvent je natažený do transferliny a vytlačený vzducehm do vilaky. Výhodné v případě měnění rozpouštědel mezi dávkovánímí nebo jednorázovým dávkováním. Pomalejší než kontinuální plnění.
        V případě možnosti je tu možnost oplachu jehly a následným profouknutím pro zbavení se zbytků solventu.
        
        Args:
            vial: Target vial number (1-50)
            volume: Dispensing volume in µL
            solvent_port: Port number connected to solvent
            transfer_line_volume: Volume of transfer line in µL (default: 500)
            flush_needle: Optional needle flush volume in µL
            wash_vial: Vial for needle washing (default: 48)
            speed: Flow rate in µL/min (default: 2000)
            **port_overrides: Optional port overrides
            
        Note:
            Requires prior system preparation with prepare_batch_flow()
            
        Example:
            >>> workflow.batch_fill(
            ...     vial=22,
            ...     volume=750,
            ...     solvent_port=3,
            ...     transfer_line_volume=600
            ... )
        """
        ports = self._resolve_ports(**port_overrides)

        total_volume = volume + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(total_volume, self.syringe_size - bubble_volume)
        
        # Load vial and set speed
        self.load_to_replenishment(vial)
        self.syringe.set_speed_uL_min(speed)

        self.valve.position(ports['air_port'])
        self.syringe.aspirate(bubble_volume)

        # Fill cycles
        for cycle_vol in cycle_volumes: 
            self.valve.position(solvent_port) 
            self.syringe.aspirate(cycle_vol)
            self.valve.position(ports['transfer_port'])
            self.syringe.dispense(cycle_vol)

        self.syringe.dispense()
        # Push with air
        self.syringe.set_speed_uL_min(DEFAULT_SPEED_AIR)
        self.valve.position(ports['air_port'])
        self.syringe.aspirate(transfer_line_volume)
        self.valve.position(ports['transfer_port'])
        self.syringe.set_speed_uL_min(speed)

        if flush_needle is None:
            self.syringe.dispense()
            if wait:
                time.sleep(wait)
        else:
            self.syringe.dispense(transfer_line_volume - flush_needle)
            if wait:
                time.sleep(wait)
            self.clean_needle(flush_needle)

        if unload:
            self.unload_from_replenishment()

    def homogenize_sample(self, vial: int, speed: int, homogenization_time: float, 
                         flush_needle: Optional[int] = None,
                         unload: bool = True, air_speed:int = 5000,
                        **port_overrides):
        """
        Execute sample homogenization using pneumatic mixing.
        
        Homogenizace roztoku ve vilce pomocí vzduchu. V rámci nastavení si užvatel zvolí délku a intenzitu. V případě překorčení bojemu sříkčky je homogenozace rozdělana na několikrát.
        V případě potřeby je možné provést oplach jehly s profouknutím zbytku kapaliny ve stříkačce.
        
        Args:
            vial: Target vial number (1-48)
            speed: Homogenization speed in µL/min
            homogenization_time: Duration of homogenization in seconds
            flush_vial: Vial for needle washing (default: 48)
            flush_needle: Optional needle flush volume in µL
            **port_overrides: Optional port overrides
            
        Example:
            >>> workflow.homogenize_sample(
            ...     vial=15,
            ...     speed=1000,  # 1 mL/min
            ...     homogenization_time=30,  # 30 seconds
            ...     flush_needle=25
            ... )
        """
        ports = self._resolve_ports(**port_overrides)
        
        # Calculate required air volume
        volume_air = homogenization_time * (speed / 60)
        total_volume = volume_air + (flush_needle if flush_needle is not None else 0)
        cycle_volumes = self._split_volume_to_cycles(int(total_volume), self.syringe_size)

        self.valve.position(ports['air_port'])
        self.syringe.valve_out()
        self.load_to_replenishment(vial)

        for i, cycle_vol in enumerate(cycle_volumes):
            if i != len(cycle_volumes) - 1:
                # Regular cycles
                self.syringe.set_speed_uL_min(air_speed)
                self.valve.position(ports['air_port']) 
                self.syringe.aspirate(cycle_vol)

                self.syringe.set_speed_uL_min(speed)
                self.valve.position(ports['transfer_port'])
                self.syringe.dispense(cycle_vol)
            else:
                # Last cycle with optional needle flush
                if flush_needle is not None:
                    self.syringe.set_speed_uL_min(air_speed)
                    self.valve.position(ports['air_port'])
                    self.syringe.aspirate(cycle_vol)

                    self.syringe.set_speed_uL_min(speed)
                    self.valve.position(ports['transfer_port'])
                    self.syringe.dispense(cycle_vol - flush_needle)
                    
                    self.clean_needle(flush_needle)

                else:
                    self.syringe.set_speed_uL_min(air_speed)
                    self.valve.position(ports['air_port'])
                    self.syringe.aspirate(cycle_vol)

                    self.syringe.set_speed_uL_min(speed)
                    self.valve.position(ports['transfer_port'])
                    self.syringe.dispense(cycle_vol)
        
        if unload:
            self.unload_from_replenishment()