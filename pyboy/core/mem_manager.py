


class MemoryManager:
    def __init__(self ,mb, bootrom, cartridge, lcd, timer, sound, ram, renderer):
        self.mb        = mb
        self.bootrom   = bootrom
        self.cartridge = cartridge
        self.lcd       = lcd
        self.timer     = timer
        self.sound     = sound
        self.ram       = ram
        self.renderer  = renderer

    def getitem(self, addr):
        if 0x0000 <= addr < 0x4000:
            if addr <= 0xFF and self.mb.bootrom_enabled:
                return self.bootrom.getitem(addr)
            else:
                return self.cartridge.getitem(addr)
        elif 0x4000 <= addr < 0x8000:
            return self.cartridge.getitem(addr)
        elif 0x8000 <= addr < 0xA000:
            return self.lcd.getVRAM(addr)
        elif 0xA000 <= addr < 0xC000:
            return self.cartridge.getitem(addr)
        elif self.is_in_ram(addr):
            return self.ram.read(addr)
        elif 0xFE00 <= addr < 0xFEA0:
            return self.lcd.OAM[addr- 0xFE00]       # TODO: shouldn't this be encapuslated?
        elif 0xFEA0 <= addr < 0xFF00:
            return self.ram.read(addr)
        elif 0xFF00 <= addr < 0xFF80:
            return self.get_io(addr)
        elif addr == 0xFFFF:
            return self.ram.read(addr)              # TODO: Eiter move this call to other ram read and/or implement interrupt register class
        else:
            raise IndexError("Memory violation. Read: %s" % hex(addr))
            

    def get_io(self, addr):
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
        elif addr == 0xFF47:
            return self.lcd.BGP.value
        elif addr == 0xFF48:
            return self.lcd.OBP0.value
        elif addr == 0xFF49:
            return self.lcd.OBP1.value
        elif addr == 0xFF4A:
            return self.lcd.WY
        elif addr == 0xFF4B:
            return self.lcd.WX
        else:
            return self.ram.read(addr)
            # TODO: Should we throw exception here instead?


    def setitem(self, addr, value):
        assert 0 <= value < 0x100, "Memory write error! Can't write %s to %s" % (hex(value), hex(addr))
        if 0x0000 <= addr < 0x8000:
            self.cartridge.setitem(addr, value)
        elif 0x8000 <= addr < 0xA000:
            self.lcd.setVRAM(addr, value)
        elif 0xA000 <= addr < 0xC000:
            self.cartridge.setitem(addr, value)
        elif self.is_in_ram(addr):
            self.ram.write(addr, value)
        elif 0xFE00 <= addr < 0xFEA0:
            self.lcd.OAM[addr - 0xFE00] = value     # TODO: encapsulation?
        elif 0xFEA0 <= addr < 0xFF00:
            self.ram.write(addr, value)
        elif 0xFF00 <= 0xFF80:
            self.set_io(addr, value)
        elif addr == 0xFFFF:
            self.ram.write(addr, value)
        

    def set_io(self, addr, value):
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
        else:
            self.ram.write(addr, value)
            # TODO: exception?

    def transfer_DMA(self, src):
        # http://problemkaputt.de/pandocs.htm#lcdoamdmatransfers
        # TODO: Add timing delay of 160µs and disallow access to RAM!
        dst = 0xFE00
        offset = src * 0x100
        for n in range(0xA0):
            self.setitem(dst + n, self.getitem(n + offset))

    # Helper function to make getitem/setitem cleaner
    def is_in_ram(self, addr):
        return 0xC000 <= addr < 0xFE00 or 0xFF80 <= addr < 0xFFFF