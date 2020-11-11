


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

    def getitem(self, i):
        if 0x0000 <= i < 0x4000: # 16kB ROM bank #0
            if i <= 0xFF and self.mb.bootrom_enabled:
                return self.bootrom.getitem(i)
            else:
                return self.cartridge.getitem(i)
        elif 0x4000 <= i < 0x8000: # 16kB switchable ROM bank
            return self.cartridge.getitem(i)
        elif 0x8000 <= i < 0xA000: # 8kB Video RAM
            return self.lcd.getVRAM(i)
        elif 0xA000 <= i < 0xC000: # 8kB switchable RAM bank
            return self.cartridge.getitem(i)
        elif 0xC000 <= i < 0xE000: # 8kB Internal RAM
            #return self.ram.internal_ram0[i - 0xC000]
            return self.ram.read(i)
        elif 0xE000 <= i < 0xFE00: # Echo of 8kB Internal RAM
            # Redirect to internal RAM
            #return self.getitem(i - 0x2000)
            return self.ram.read(i)
        elif 0xFE00 <= i < 0xFEA0: # Sprite Attribute Memory (OAM)
            return self.lcd.OAM[i - 0xFE00]
        elif 0xFEA0 <= i < 0xFF00: # Empty but unusable for I/O
            #return self.ram.non_io_internal_ram0[i - 0xFEA0]
            return self.ram.read(i)
        elif 0xFF00 <= i < 0xFF4C: # I/O ports
            if i == 0xFF04:
                return self.timer.DIV
            elif i == 0xFF05:
                return self.timer.TIMA
            elif i == 0xFF06:
                return self.timer.TMA
            elif i == 0xFF07:
                return self.timer.TAC
            elif 0xFF10 <= i < 0xFF40:
                if self.mb.sound_enabled:
                    return self.sound.get(i - 0xFF10)
                else:
                    return 0
            elif i == 0xFF40:
                return self.lcd.LCDC.value
            elif i == 0xFF42:
                return self.lcd.SCY
            elif i == 0xFF43:
                return self.lcd.SCX
            elif i == 0xFF47 and not self.cartridge.is_cgb:
                return self.lcd.BGP.value
            elif i == 0xFF48 and not self.cartridge.is_cgb:
                return self.lcd.OBP0.value
            elif i == 0xFF49 and not self.cartridge.is_cgb:
                return self.lcd.OBP1.value
            elif i == 0xFF4A:
                return self.lcd.WY
            elif i == 0xFF4B:
                return self.lcd.WX
            #Get current VRAM bank, CGB check probably redundant
            elif i == 0xFF4F and self.cartridge.is_cgb:
                return self.lcd.VBK.get()
            else:
                #return self.ram.io_ports[i - 0xFF00]
                return self.ram.read(i)
        elif 0xFF4C <= i < 0xFF80: # Empty but unusable for I/O
            #return self.ram.non_io_internal_ram1[i - 0xFF4C]
            return self.ram.read(i)
        elif 0xFF80 <= i < 0xFFFF: # Internal RAM
            #return self.ram.internal_ram1[i - 0xFF80]
            return self.ram.read(i)
        elif i == 0xFFFF: # Interrupt Enable Register
            #return self.ram.interrupt_register[0]
            return self.ram.read(i)
        else:
            raise IndexError("Memory access violation. Tried to read: %s" % hex(i))





    def setitem(self, i, value):
        assert 0 <= value < 0x100, "Memory write error! Can't write %s to %s" % (hex(value), hex(i))

        if 0x0000 <= i < 0x4000: # 16kB ROM bank #0
            # Doesn't change the data. This is for MBC commands
            self.cartridge.setitem(i, value)
        elif 0x4000 <= i < 0x8000: # 16kB switchable ROM bank
            # Doesn't change the data. This is for MBC commands
            self.cartridge.setitem(i, value)
        elif 0x8000 <= i < 0xA000: # 8kB Video RAM
            self.lcd.setVRAM(i, value) 
            if i < 0x9800: # Is within tile data -- not tile maps
                # Mask out the byte of the tile
                self.renderer.tiles_changed.add(i & 0xFFF0)
        elif 0xA000 <= i < 0xC000: # 8kB switchable RAM bank
            self.cartridge.setitem(i, value)
        elif 0xC000 <= i < 0xE000: # Internal RAM
            self.ram.write(i, value)
        elif 0xE000 <= i < 0xFE00: # Echo of 8kB Internal RAM
            self.ram.write(i, value)
        elif 0xFE00 <= i < 0xFEA0: # Sprite Attribute Memory (OAM)
            self.lcd.OAM[i - 0xFE00] = value
        elif 0xFEA0 <= i < 0xFF00: # Empty but unusable for I/O
            self.ram.write(i, value)
        elif 0xFF00 <= i < 0xFF4C: # I/O ports
            if i == 0xFF00:
                #self.ram.io_ports[i - 0xFF00] = self.interaction.pull(value)
                self.ram.write(i, self.mb.interaction.pull(value))
            elif i == 0xFF01:
                self.mb.serialbuffer += chr(value)
                #self.ram.io_ports[i - 0xFF00] = value
                self.ram.write(i, value)
            elif i == 0xFF04:
                self.timer.DIV = 0
            elif i == 0xFF05:
                self.timer.TIMA = value
            elif i == 0xFF06:
                self.timer.TMA = value
            elif i == 0xFF07:
                self.timer.TAC = value & 0b111
            elif 0xFF10 <= i < 0xFF40:
                if self.mb.sound_enabled:
                    self.sound.set(i - 0xFF10, value)
            elif i == 0xFF40:
                self.lcd.LCDC.set(value)
            elif i == 0xFF42:
                self.lcd.SCY = value
            elif i == 0xFF43:
                self.lcd.SCX = value
            elif i == 0xFF46:
                self.mb.transfer_DMA(value)
            elif i == 0xFF47:
                # TODO: Move out of MB
                self.renderer.clearcache |= self.lcd.BGP.set(value)
            elif i == 0xFF48:
                # TODO: Move out of MB
                self.renderer.clearcache |= self.lcd.OBP0.set(value)
            elif i == 0xFF49:
                # TODO: Move out of MB
                self.renderer.clearcache |= self.lcd.OBP1.set(value)
            elif i == 0xFF4A:
                self.lcd.WY = value
            elif i == 0xFF4B:
                self.lcd.WX = value
            #Switch VRAM bank, redundant CGB check    
            elif i == 0xFF4F and self.cartridge.is_cgb:
                self.lcd.VBK.set(value)
            else:
                #self.ram.io_ports[i - 0xFF00] = value
                self.ram.write(i, value)
        elif 0xFF4C <= i < 0xFF80: # Empty but unusable for I/O
            if self.mb.bootrom_enabled and i == 0xFF50 and value == 0x1 or value == 0x11: #0x11 for gameboy color
                self.mb.bootrom_enabled = False
            #self.ram.non_io_internal_ram1[i - 0xFF4C] = value
            self.ram.write(i, value)
        elif 0xFF80 <= i < 0xFFFF: # Internal RAM
            #self.ram.internal_ram1[i - 0xFF80] = value
            self.ram.write(i, value)
        elif i == 0xFFFF: # Interrupt Enable Register
            #self.ram.interrupt_register[0] = value
            self.ram.write(i, value)
        else:
            raise Exception("Memory access violation. Tried to write: %s" % hex(i))
