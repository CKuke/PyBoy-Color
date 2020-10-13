from array import array
from . import lcd

## MAYBE JUST REMOVE ALL THESE?
# CGB registers for background/sprite palettes
BCPS, BCPD, OCPS, OCPD = range(0xFF68, 0xFF6C)
# CGB registers for VRAM DMA transfers
HDMA1, HDMA2, HDMA3, HDMA4, HDMA5 = range(0xFF51, 0xFF56)
# Register used to change VRAM banks
VBK = 0xFF4F


class cgbLCD(lcd.LCD):
    def __init__(self):
        lcd.LCD.__init__(self)
        self.VRAM1 = array("B", [0] * lcd.VBANK_SIZE)        
        self.vbk = VBKregister()

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
        self.active_bank = bank

    def get(self):
        #reading from this register returns current VRAM bank in bit 0, other bits = 1
        return self.active_bank | 0xFE

    def _switch_bank(self, bank):
        if bank == self.active_bank:
            return
        else:
            self.active_bank = bank ^ 1
