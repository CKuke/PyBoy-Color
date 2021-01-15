#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import logging

from pyboy.utils import STATE_VERSION

from . import bootrom, cartridge, cpu, interaction, lcd, base_ram, sound, timer, cgb_lcd, cgb_ram, renderer, cgb_renderer, mem_manager, cgb_mem_manager

logger = logging.getLogger(__name__)

VBLANK, LCDC, TIMER, SERIAL, HIGHTOLOW = range(5)
STAT, _, _, LY, LYC = range(0xFF41, 0xFF46)

class Motherboard:
    def __init__(self, gamerom_file, bootrom_file, color_palette, disable_renderer, sound_enabled, dmg, profiling=False):
        if bootrom_file is not None:
            logger.info("Boot-ROM file provided")

        if profiling:
            logger.info("Profiling enabled")
        self.timer = timer.Timer()
        self.interaction = interaction.Interaction()
        self.cartridge = cartridge.load_cartridge(gamerom_file)
        self.bootrom = bootrom.BootROM(bootrom_file, dmg)
        self.cpu = cpu.CPU(self, profiling)

        self.sound_enabled = sound_enabled
        self.sound = sound.Sound()

        self.is_cgb = not dmg
        
        if dmg:
            logger.info("Started as Game Boy")
            self.renderer = renderer.Renderer(color_palette)
            self.lcd = lcd.LCD(self.renderer)
            self.ram = base_ram.RAM(random=False)
            self.mem_manager = mem_manager.MemoryManager(
                self, self.bootrom, self.cartridge, 
                self.lcd, self.timer, self.sound, self.ram,
                self.renderer)
        else:
            logger.info("Started as Game Boy Color")
            if self.cartridge.is_cgb:
                self.renderer = cgb_renderer.CGBRenderer()
            else:
                # Running DMG ROM on CGB hardware
                # use the default palettes
                bg_pal   = (0xFFFFFF, 0x7BFF31, 0x0063C5, 0x000000)
                obj0_pal = (0xFFFFFF, 0xFF8484, 0xFF8484, 0x000000)
                obj1_pal = (0xFFFFFF, 0xFF8484, 0xFF8484, 0x000000)
                self.renderer = renderer.Renderer(bg_pal, obj0_pal, obj1_pal)                
            self.lcd = cgb_lcd.cgbLCD(self.renderer)
            self.ram = cgb_ram.CgbRam(random=False)
            self.mem_manager = cgb_mem_manager.CgbMemoryManager(
                self, self.bootrom, self.cartridge, 
                self.lcd, self.timer, self.sound, self.ram,
                self.renderer) 


        self.disable_renderer = disable_renderer

        self.bootrom_enabled = True
        self.serialbuffer = ""
        self.cycles_remaining = 0

    def getserial(self):
        b = self.serialbuffer
        self.serialbuffer = ""
        return b

    def buttonevent(self, key):
        if self.interaction.key_event(key):
            self.cpu.set_interruptflag(HIGHTOLOW)

    def stop(self, save):
        if self.sound_enabled:
            self.sound.stop()
        if save:
            self.cartridge.stop()

    def save_state(self, f):
        logger.debug("Saving state...")
        f.write(STATE_VERSION)
        f.write(self.bootrom_enabled)
        self.cpu.save_state(f)
        self.lcd.save_state(f)
        if self.sound_enabled:
            self.sound.save_state(f)
        else:
            pass
        self.renderer.save_state(f)
        self.ram.save_state(f)
        self.timer.save_state(f)
        self.cartridge.save_state(f)
        f.flush()
        logger.debug("State saved.")

    def load_state(self, f):
        logger.debug("Loading state...")
        state_version = f.read()
        if state_version >= 2:
            logger.debug(f"State version: {state_version}")
            # From version 2 and above, this is the version number
            self.bootrom_enabled = f.read()
        else:
            logger.debug(f"State version: 0-1")
            # HACK: The byte wasn't a state version, but the bootrom flag
            self.bootrom_enabled = state_version
        self.cpu.load_state(f, state_version)
        self.lcd.load_state(f, state_version)
        if state_version >= 6:
            self.sound.load_state(f, state_version)
        if state_version >= 2:
            self.renderer.load_state(f, state_version)
        self.ram.load_state(f, state_version)
        if state_version >= 5:
            self.timer.load_state(f, state_version)
        self.cartridge.load_state(f, state_version)
        f.flush()
        logger.debug("State loaded.")

        # TODO: Move out of MB
        self.renderer.clearcache = True
        self.renderer.render_screen(self.lcd)

    ###################################################################
    # Coordinator
    #

    # TODO: Move out of MB
    def set_STAT_mode(self, mode):
        self.setitem(STAT, self.getitem(STAT) & 0b11111100) # Clearing 2 LSB
        self.setitem(STAT, self.getitem(STAT) | mode) # Apply mode to LSB

        # Mode "3" is not interruptable
        if self.cpu.test_ramregisterflag(STAT, mode + 3) and mode != 3:
            self.cpu.set_interruptflag(LCDC)

    # TODO: Move out of MB
    def check_LYC(self, y):
        #print("%s" % format(self.getitem(STAT), '#010b'))
        self.setitem(LY, y)
        if self.getitem(LYC) == y:
            self.setitem(STAT, self.getitem(STAT) | 0b100) # Sets the LYC flag
            if self.getitem(STAT) & 0b01000000:
                self.cpu.set_interruptflag(LCDC)
        else:
            self.setitem(STAT, self.getitem(STAT) & 0b11111011)

    def calculate_cycles(self, cycles_period):
        self.cycles_remaining += cycles_period

        # TODO: Temporary hdma transfer
        if self.is_cgb:
            mode = self.getitem(STAT) & 0b11
            if mode == 0:
                self.mem_manager.do_potential_transfer()
                self.cycles_remaining -= 8 # TODO: adjust for double speed
        ##############################

        while self.cycles_remaining > 0:
            cycles = self.cpu.tick()

            # TODO: Benchmark whether 'if' and 'try/except' is better
            if cycles == -1: # CPU has HALTED
                # Fast-forward to next interrupt:
                # VBLANK and LCDC are covered by just returning.
                # Timer has to be determined.
                # As we are halted, we are guaranteed, that our state
                # cannot be altered by other factors than time.
                # For HiToLo interrupt it is indistinguishable whether
                # it gets triggered mid-frame or by next frame
                # Serial is not implemented, so this isn't a concern
                cycles = min(self.timer.cyclestointerrupt(), self.cycles_remaining)

                # Profiling 
                if self.cpu.profiling:
                    self.cpu.hitrate[0x76] += cycles // 4

            if self.sound_enabled:
                self.sound.clock += cycles
            self.cycles_remaining -= cycles

            if self.timer.tick(cycles):
                self.cpu.set_interruptflag(TIMER)

    def tickframe(self):
        lcdenabled = self.lcd.LCDC.lcd_enable
        if lcdenabled:

            # TODO: the 19, 41 and 49._ticks should correct for longer instructions
            # Iterate the 144 lines on screen
            for y in range(144):
                self.check_LYC(y)

                mode0_dots = 206
                mode1_dots = 456
                mode2_dots = 80
                mode3_dots = 170

                if self.is_cgb:
                    if self.mem_manager.is_double_speed:
                        mode0_dots *= 2
                        mode1_dots *= 2
                        mode2_dots *= 2
                        mode3_dots *= 2

                # Mode 2
                # TODO: Move out of MB
                self.set_STAT_mode(2)
                self.calculate_cycles(mode2_dots)

                # Mode 3
                # TODO: Move out of MB
                self.set_STAT_mode(3)
                self.calculate_cycles(mode3_dots)
                self.renderer.scanline(y, self.lcd)

                # Mode 0
                # TODO: Move out of MB
                self.set_STAT_mode(0)
                self.calculate_cycles(mode0_dots)
                
                
            self.cpu.set_interruptflag(VBLANK)
            if not self.disable_renderer:
                self.renderer.render_screen(self.lcd)

            # Wait for next frame
            for y in range(144, 154):
                self.check_LYC(y)

                # Mode 1
                self.set_STAT_mode(1)
                self.calculate_cycles(mode1_dots)
        else:
            # https://www.reddit.com/r/EmuDev/comments/6r6gf3
            # TODO: What happens if LCD gets turned on/off mid-cycle?
            self.renderer.blank_screen()
            # TODO: Move out of MB
            self.set_STAT_mode(0)
            self.setitem(LY, 0)

            for y in range(154):
                self.calculate_cycles(456)
        if self.sound_enabled:
            self.sound.sync()

    ###################################################################
    # MemoryManager
    #
    def getitem(self, i):
        return self.mem_manager.getitem(i)

    def setitem(self, i, value):
        self.mem_manager.setitem(i, value)
