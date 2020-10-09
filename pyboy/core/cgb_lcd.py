from array import array
from ctypes import c_void_p

from pyboy.utils import color_code

VBANK_SIZE = 8 * 1024
OBJECT_ATTRIBUTE_MEMORY = 0xA0
LCDC, STAT, SCY, SCX, LY, LYC, DMA, BGP, OBP0, OBP1, WY, WX = range(0xFF40, 0xFF4C)

# CGB registers for background/sprite palettes
BCPS, BCPD, OCPS, OCPD = range(0xFF68, 0xFF6C)
# CGB registers for VRAM DMA transfers
HDMA1, HDMA2, HDMA3, HDMA4, HDMA5 = range(0xFF51, 0xFF56)
# Register used to change VRAM banks
VBK = 0xFF4F

ROWS, COLS = 144, 160
TILES = 768


class LCD:
    def __init__(self):
        self.VRAM0 = array("B", [0] * VBANK_SIZE)
        self.VRAM1 = array("B", [0] * VBANK_SIZE)
        self.vbk = VBKregister()

    def setVRAM(self, i, value):
        if self.vbk.__active_bank == 0:
            self.VRAM0[i - 0x8000] = value
        else:
            self.VRAM1[i - 0x8000] = value
    
    def getVRAM(self, i):
        if self.vbk.__active_bank == 0:
            return self.VRAM0[i - 0x8000]
        else:
            return self.VRAM1[i - 0x8000]

class VBKregister:
    def __init(self, value):
        self.__active_bank = 0

    def set(self, value):
        #when writing to VBK, bit 0 indicates which bank to switch to
        bank = value & 1
        self.__switch_bank(bank)
        self.__active_bank = bank

    def get(self):
        #reading from this register returns current VRAM bank in bit 0, other bits = 1
        return self.__active_bank | 0xFE

    def __switch_bank(self, bank):
        if bank == self.__active_bank:
            #trying to switch to the already active bank
            return
        else:
            self.__active_bank = bank ^ 1
