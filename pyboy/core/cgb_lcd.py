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
        self.sprite_palette_mem = array("I", [0xFF] * NUM_PALETTES * NUM_COLORS)
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

    def getVRAMbank(self, i, bank):
        if bank == 0:
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
    def __init__(self, val = 0):
        self.value = val
        self.auto_inc = 0
        self.index = 0
        self.hl = 0

    def set(self, val):
#        if self.value == val:
#            return
        self.value = val
        self.hl = val & 0b1
        self.index = (val >> 1) & 0b11111
        self.auto_inc = (val >> 7) & 0b1 

        print("hl: %s" %hex(self.hl))
        print("index: %s" %hex((self.index & 0b11)))
        print("pal: %s" %hex((self.index >>2)))
        print("value: %s\n" %hex(self.value))

    def get(self):
        return self.value
    
    def getindex(self):
        return self.index

    #hl defines which of the two bytes in a color is needed
    def gethl(self):
        return self.hl

    def _inc_index(self):
        #what happens if increment is set and index is at max 0x3F?
        #undefined behavior
        self.index += 1

    def shouldincrement(self):
        if self.auto_inc:
            #ensure autoinc also set for new val
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
        return self.palette[self.index_reg.getindex()]
    
    def getcolor(self, paletteindex, colorindex):
        #each palette = 8 bytes or 4 colors of 2 bytes
        if paletteindex > 7 or colorindex > 3:
            raise IndexError("Palette Mem Index Error, tried: Palette %s color %s" 
                % hex(paletteindex), hex(colorindex))
        
        i = paletteindex * 4 + colorindex
        color = self.palette_mem[i] 

        cgb_col = self._cgbcolor(color)
        return self._convertcolor(cgb_col)


### MOVE TO UTILS?
    #takes 2 bytes from palette memory and gets the cgb color
    #only first 15 bits used
    def _cgbcolor(self, color_bytes):
        #only care about 15 first bits
        mask = 0x7FFF
        return color_bytes & mask

    #takes 15 bit cgb color and converts to standard 24 bit color
    #shifts the individual colors and then or with 3 most sig bits
    def _convertcolor(self, color):
        #colors 5 bits
        color_mask = 0x1F

        red = color & color_mask
        sig_bits = red & 0x07  
        final_red = (red << 3) | sig_bits
        
        green = (color >> 5) & color_mask
        sig_bits = green & 0x07  
        final_green = (green << 3) | sig_bits

        blue = (color >> 10) & color_mask
        sig_bits = blue & 0x07  
        final_blue = (blue << 3) | sig_bits
        
        final_color = (final_red << 16) | (final_green << 8) | final_blue
        #print("Input color: %s", hex(color))
        #print("output color: %s", hex(final_color))


        return (final_red << 16) | (final_green << 8) | final_blue



#load save functions