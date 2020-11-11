from array import array
from . import lcd

## MAYBE JUST REMOVE ALL THESE?
# CGB registers for background/sprite palettes
BCPS, BCPD, OCPS, OCPD = range(0xFF68, 0xFF6C)
# CGB registers for VRAM DMA transfers
HDMA1, HDMA2, HDMA3, HDMA4, HDMA5 = range(0xFF51, 0xFF56)
# Register used to change VRAM banks
VBK = 0xFF4F
# Palette memory = 4 colors of 2 bytes define colors for a palette, 8 different palettes
PALETTE_MEM_SIZE = 64

class cgbLCD(lcd.LCD):
    def __init__(self):
        lcd.LCD.__init__(self)
        self.VRAM1 = array("B", [0] * lcd.VBANK_SIZE)

        self.vbk = VBKregister()
        self.bcps = PaletteIndexRegister()
        self.bcpd = BCPDRegister()
        self.ocps = PaletteIndexRegister()
        self.ocpd = OCPDRegister()
 
    def setVRAM(self, i, value):
        if self.vbk.active_bank == 0:
            self.VRAM0[i - 0x8000] = value
        else:
            self.VRAM1[i - 0x8000] = value
    
    def getVRAM(self, i):
        if self.vbk.active_bank == 0:
            return self.VRAM0[i - 0x8000]
        else:
            return self.VRAM1[i - 0x8000]

    #TEMPORARY FIX USED IN RENDERER.PY REMOVE THIS
    def NoOffsetgetVRAM(self, i):
        if self.vbk.active_bank == 0:
            return self.VRAM0[i]
        else:
            return self.VRAM1[i]

    def getVBANK(self):
        return self.vbk.active_bank

    def getwindowpos(self):
        return (self.WX - 7, self.WY)

    def getviewport(self):
        return (self.SCX, self.SCY)


class VBKregister:
    def __init__(self, value=0):
        self.active_bank = value

    def set(self, value):
        #when writing to VBK, bit 0 indicates which bank to switch to
        bank = value & 1
        self._switch_bank(bank)

    def get(self):
        #reading from this register returns current VRAM bank in bit 0, other bits = 1
        return self.active_bank | 0xFE

    def _switch_bank(self, bank):
        if bank == self.active_bank:
            return
        else:
            self.active_bank = bank

class PaletteIndexRegister:
    def __init__(self, value = 0):
        self.val = value
        self.index = 0x0
        self.auto_inc = 0

    def set(self, value):
        if self.val == value:
            return

        self.val = value
        #bit 0-5 define index
        self.index = value & 0b111111
        #bit 7 define auto increment
        self.auto_inc = value & 0b10000000 

    def get(self):
        return self.val
    
    def getindex(self):
        return self.index

    def _inc_index(self):
        self.index += 1

    def shouldincrement(self):
        #what happens if increment is set and index is at max 0x3F?
        if self.auto_inc and not self.index == 0x3F:
            self._inc_index()

class BCPDRegister:
    def __init__(self, value = 0):
        #palettes initalized as white
        self.bg_palette_mem = array("B", [0xFF] * PALETTE_MEM_SIZE)
            
    def set(self, value, bcps):
        self.bg_palette_mem[bcps.getindex()] = value
        #check for autoincrement after write
        bcps.shouldincrement()
    
    def get(self, bcps):
        return self.bg_palette_mem[bcps.getindex()]
    
    ### Add functions to get values from BGP0-7 ###

class OCPDRegister:
    def __init__(self, value = 0):
        self.sprite_palette_mem = array("B", [0xFF] * PALETTE_MEM_SIZE)

    def set(self, value, ocps):
        self.sprite_palette_mem[ocps.getindex()] = value
        #check for autoincrement after write
        ocps.shouldincrement()
    
    def get(self, ocps):
        return self.sprite_palette_mem[ocps.getindex()]

    ### Add functions to get values from OPB0-7 ###


#load save functions