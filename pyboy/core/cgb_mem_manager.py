from . import mem_manager

class CgbMemoryManager(mem_manager.MemoryManager):
    def __init__(self, mb, bootrom, cartridge, lcd, timer, sound, ram, renderer):
        super().__init__(mb, bootrom, cartridge, lcd, timer, sound, ram, renderer)
    
    def get_io(self, addr):
        #print("%3s %6s" % ("get", hex(addr)))
        if addr == 0xFF04:
            return self.timer.DIV
        elif addr == 0xFF05:
            return self.timer.TIMA
        elif addr == 0xFF06:
            return self.timer.TMA
        elif addr == 0xFF07:
            return self.timer.TAC
        elif 0xFF10 <= addr < 0xFF40:
            if self.mb.sound_enabled:
                return self.sound.get(addr - 0xFF10)
            else:
                return 0
        elif addr == 0xFF40:
            return self.lcd.LCDC.value
        elif addr == 0xFF42:
            return self.lcd.SCY
        elif addr == 0xFF43:
            return self.lcd.SCX
        elif addr == 0xFF47 and not self.cartridge.is_cgb:
            return self.lcd.BGP.value
        elif addr == 0xFF48 and not self.cartridge.is_cgb:
            return self.lcd.OBP0.value
        elif addr == 0xFF49 and not self.cartridge.is_cgb:
            return self.lcd.OBP1.value
        elif addr == 0xFF4A:
            return self.lcd.WY
        elif addr == 0xFF4B:
            return self.lcd.WX
        # CGB registers
        elif addr == 0xFF4F:
            return self.lcd.getVBANK()
        elif addr == 0xFF70:
            return self.ram.read(addr)
        elif addr == 0xFF51:
            print("HDAM1 get")
        elif addr == 0xFF52:
            print("HDAM2 get")
        elif addr == 0xFF53:
            print("HDAM3 get")
        elif addr == 0xFF54:
            print("HDAM4 get")
        elif addr == 0xFF55:
            print("HDAM5 get")
        else:
            return self.ram.read(addr)

    def set_io(self, addr, value):
        #print("%3s %6s %3s" % ("set", hex(addr), hex(value)))
        if addr == 0xFF00:
            self.ram.write(addr, self.mb.interaction.pull(value))
        elif addr == 0xFF01:
            self.mb.serialbuffer += chr(value)
            self.ram.write(addr, value)
        elif addr == 0xFF04:
            self.timer.DIV = 0
        elif addr == 0xFF05:
            self.timer.TIMA = value
        elif addr == 0xFF06:
            self.timer.TMA = value
        elif addr == 0xFF07:
            self.timer.TAC = value & 0b111
        elif 0xFF10 <= addr < 0xFF40:
            if self.mb.sound_enabled:
                self.sound.set(addr - 0xFF10, value)
        elif addr == 0xFF40:
            self.lcd.LCDC.set(value)
        elif addr == 0xFF42:
            self.lcd.SCY = value
        elif addr == 0xFF43:
            self.lcd.SCX = value
        elif addr == 0xFF46:
            self.mb.transfer_DMA(value)
        elif addr == 0xFF47:
            # TODO: Move out of MB
            self.renderer.clearcache |= self.lcd.BGP.set(value)
        elif addr == 0xFF48:
            # TODO: Move out of MB
            self.renderer.clearcache |= self.lcd.OBP0.set(value)
        elif addr == 0xFF49:
            # TODO: Move out of MB
            self.renderer.clearcache |= self.lcd.OBP1.set(value)
        elif addr == 0xFF4A:
            self.lcd.WY = value
        elif addr == 0xFF4B:
            self.lcd.WX = value
        elif addr == 0xFF50 and self.mb.bootrom_enabled and (value == 0x1 or value == 0x11):
            self.mb.bootrom_enabled = False
            self.ram.write(addr, value)
        # CGB registers
        elif addr == 0xFF4F:
            self.lcd.vbk.set(value)
        elif addr == 0xFF70:
            self.ram.write(addr, value)
        elif addr == 0xFF51:
            print("HDAM1 set")
        elif addr == 0xFF52:
            print("HDAM2 set")
        elif addr == 0xFF53:
            print("HDAM3 set")
        elif addr == 0xFF54:
            print("HDAM4 set")
        elif addr == 0xFF55:
            print("HDAM5 set")
        else:
            self.ram.write(addr, value)

