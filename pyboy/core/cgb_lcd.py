from array import array
from . import lcd

# Palette memory = 4 colors of 2 bytes define colors for a palette, 8 different palettes
PALETTE_MEM_MAX_INDEX = 0x3f
NUM_PALETTES = 8
NUM_COLORS = 4

class cgbLCD(lcd.LCD):
    def __init__(self):
        lcd.LCD.__init__(self)
        self.VRAM1 = array("B", [0] * lcd.VBANK_SIZE)

        #8 palettes of 4 colors each 2 bytes
        self.sprite_palette_mem = array("I", [0x0] * NUM_PALETTES * NUM_COLORS)
        self.bg_palette_mem = array("I", [0xFF] * NUM_PALETTES * NUM_COLORS)

        self.vbk = VBKregister()
        self.bcps = PaletteIndexRegister()
        self.bcpd = PaletteColorRegister(self.bg_palette_mem, self.bcps)
        self.ocps = PaletteIndexRegister()
        self.ocpd = PaletteColorRegister(self.sprite_palette_mem, self.ocps)

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

    def getVRAMbank(self, i, bank = 0, offset = True):
        i_off = 0x8000 if offset else 0x0
        if bank == 0:
            return self.VRAM0[i - i_off]
        else:
            return self.VRAM1[i - i_off]

class VBKregister:
    def __init__(self, value=0):
        self.active_bank = value

    def set(self, value):
        # when writing to VBK, bit 0 indicates which bank to switch to
        bank = value & 1
        self._switch_bank(bank)

    def get(self):
        # reading from this register returns current VRAM bank in bit 0, other bits = 1
        return self.active_bank | 0xFE

    def _switch_bank(self, bank):
        if bank == self.active_bank:
            return
        else:
            self.active_bank = bank

class PaletteIndexRegister:
    def __init__(self, val = 0):
        self.value = val
        self.auto_inc = 0
        self.index = 0
        self.hl = 0

    def set(self, val):
        if self.value == val:
            return
        self.value = val
        self.hl = val & 0b1
        self.index = (val >> 1) & 0b11111
        self.auto_inc = (val >> 7) & 0b1 

    def get(self):
        return self.value
    
    def getindex(self):
        return self.index

    # hl defines which of the two bytes in a color is needed
    def gethl(self):
        return self.hl

    def _inc_index(self):
        # what happens if increment is set and index is at max 0x3F?
        # undefined behavior
        self.index += 1

    def shouldincrement(self):
        if self.auto_inc:
            # ensure autoinc also set for new val
            new_val = 0x80 | (self.value + 1) 
            self.set(new_val)

class PaletteColorRegister:
    def __init__(self, palette_mem, i_reg):
        self.palette_mem = palette_mem
        self.index_reg = i_reg

    def set(self, val):
        hl = self.index_reg.gethl()
        i_val = self.palette_mem[self.index_reg.getindex()]
        if hl:                
            self.palette_mem[self.index_reg.getindex()] = (i_val & 0x00FF) | (val << 8)
        else:
            self.palette_mem[self.index_reg.getindex()] = (i_val & 0xFF00) | val

        #check for autoincrement after write
        self.index_reg.shouldincrement()
    
    def get(self):
        return self.palette_mem[self.index_reg.getindex()]

    def getcolor(self, paletteindex, colorindex):
        #each palette = 8 bytes or 4 colors of 2 bytes
        if paletteindex > 7 or colorindex > 3:
            raise IndexError("Palette Mem Index Error, tried: Palette %s color %s" 
                % paletteindex, colorindex)
        
        i = paletteindex * 4 + colorindex
        color = self.palette_mem[i] 

        cgb_col = self._cgbcolor(color)
        return self._convert15bitcol(cgb_col)


### MOVE TO UTILS?
    # takes 2 bytes from palette memory and gets the cgb color
    # only first 15 bits used
    def _cgbcolor(self, color_bytes):
        #only care about 15 first bits
        mask = 0x7FFF
        return color_bytes & mask

    # converts 15 bit color to 24 bit
    def _convert15bitcol(self, color):
        # colors 5 bits
        color_mask = 0x1F

        red = (color & color_mask) << 3        
        green = ((color >> 5) & color_mask) << 3
        blue = ((color >> 10) & color_mask) << 3
        
        final_color = (red << 16) | (green << 8) | blue
        return final_color



#load save functions