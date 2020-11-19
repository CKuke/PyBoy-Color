from . import mem_manager

class CgbMemoryManager(mem_manager.MemoryManager):
    def __init__(self, mb, bootrom, cartridge, lcd, timer, sound, ram, renderer):
        super().__init__(mb, bootrom, cartridge, lcd, timer, sound, ram, renderer)

        self.hdma1 = 0
        self.hdma2 = 0
        self.hdma3 = 0
        self.hdma4 = 0
        self.hdma5 = 0
    
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
            return self.lcd.vbk.get()
        elif addr == 0xFF68:
            return self.lcd.bcps.get()
        elif addr == 0xFF69:
            return self.lcd.bcpd.get() 
        elif addr == 0xFF6A:
            return self.lcd.ocps.get()
        elif addr == 0xFF6B:
            return self.lcd.ocpd.get()
        elif addr == 0xFF70:
            return self.ram.read(addr)
        elif 0xFF51 <= addr <= 0xFF55:
            return self.get_hdma(addr)
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
            self.transfer_DMA(value)
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
        elif addr == 0xFF68:
            return self.lcd.bcps.set()
        elif addr == 0xFF69:
            return self.lcd.bcpd.set() 
        elif addr == 0xFF6A:
            return self.lcd.ocps.set()
        elif addr == 0xFF6B:
            return self.lcd.ocpd.set()        
        elif addr == 0xFF70:
            self.ram.write(addr, value)
        elif 0xFF51 <= addr <= 0xFF54:
            self.set_hdma(addr, value)
        elif addr == 0xFF55:
            self.transfer_hdma(value)
        else:
            self.ram.write(addr, value)


    def transfer_hdma(self, value):
        src = (((self.hdma1 << 8) + self.hdma2) & 0xFFF0)
        dst = (((self.hdma3 << 8) + self.hdma4) & 0x1FF0) + 0x8000
        data_len = ((value & 0x7F) + 1) * 16
        transfer_type = (value & 0x80) >> 7

        if transfer_type == 0:
            for n in range(data_len):
                self.setitem(dst + n, self.getitem(src + n))
        elif transfer_type == 1:
            for n in range(data_len):
                self.setitem(dst + n, self.getitem(src + n))
                




    def get_hdma(self, reg):
        if 0xFF51 <= reg <= 0xFF54:
            raise Exception("Can not read HDMA1-HDMA4")
        else:
            return self.hdma5

    def set_hdma(self, reg, value):
        if reg == 0xFF51:
            self.hdma1 = value
        elif reg == 0xFF52:
            self.hdma2 = value
        elif reg == 0xFF53:
            self.hdma3 = value
        elif reg == 0xFF54:
            self.hdma4 = value
