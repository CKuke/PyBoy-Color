from array import array
from ctypes import c_void_p

from pyboy.utils import color_code

VBANK_SIZE = 8 * 1024
OBJECT_ATTRIBUTE_MEMORY = 0xA0
#Cut BGP, OBP0, OBP1 for CGB
LCDC, STAT, SCY, SCX, LY, LYC, DMA, BGP, OBP0, OBP1, WY, WX = range(0xFF40, 0xFF4C)

# CGB registers for background/sprite palettes
BCPS, BCPD, OCPS, OCPD = range(0xFF68, 0xFF6C)
# CGB registers for VRAM DMA transfers
HDMA1, HDMA2, HDMA3, HDMA4, HDMA5 = range(0xFF51, 0xFF56)
# Register used to change VRAM banks
VBK = 0xFF4F

ROWS, COLS = 144, 160
TILES = 768


class cgbLCD:
    def __init__(self):
        self.VRAM0 = array("B", [0] * VBANK_SIZE)
        self.VRAM1 = array("B", [0] * VBANK_SIZE)
        self.OAM = array("B", [0] * OBJECT_ATTRIBUTE_MEMORY)

        self.LCDC = LCDCRegister(0)
        # self.STAT = 0x00
        self.SCY = 0x00
        self.SCX = 0x00
        # self.LY = 0x00
        # self.LYC = 0x00
        # self.DMA = 0x00
        
        #Cut for CGB
        self.BGP = PaletteRegister(0xFC)
        self.OBP0 = PaletteRegister(0xFF)
        self.OBP1 = PaletteRegister(0xFF)
        
        self.WY = 0x00
        self.WX = 0x00
        
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

    #update for CGB
    # def save_state(self, f):
    #     for n in range(VIDEO_RAM):
    #         f.write(self.VRAM[n])

    #     for n in range(OBJECT_ATTRIBUTE_MEMORY):
    #         f.write(self.OAM[n])

    #     f.write(self.LCDC.value)
    #     f.write(self.BGP.value)
    #     f.write(self.OBP0.value)
    #     f.write(self.OBP1.value)

    #     f.write(self.SCY)
    #     f.write(self.SCX)
    #     f.write(self.WY)
    #     f.write(self.WX)

    # def load_state(self, f, state_version):
    #     for n in range(VIDEO_RAM):
    #         self.VRAM[n] = f.read()

    #     for n in range(OBJECT_ATTRIBUTE_MEMORY):
    #         self.OAM[n] = f.read()

    #     self.LCDC.set(f.read())
    #     self.BGP.set(f.read())
    #     self.OBP0.set(f.read())
    #     self.OBP1.set(f.read())

    #     self.SCY = f.read()
    #     self.SCX = f.read()
    #     self.WY = f.read()
    #     self.WX = f.read()

    def getwindowpos(self):
        return (self.WX - 7, self.WY)

    def getviewport(self):
        return (self.SCX, self.SCY)
    
#Cut for CGB
class PaletteRegister:
    def __init__(self, value):
        self.value = 0
        self.lookup = [0] * 4
        self.set(value)

    def set(self, value):
        # Pokemon Blue continuously sets this without changing the value
        if self.value == value:
            return False

        self.value = value
        for x in range(4):
            self.lookup[x] = (value >> x * 2) & 0b11
        return True

    def getcolor(self, i):
        return self.lookup[i]


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

class LCDCRegister:
    def __init__(self, value):
        self.set(value)

    def set(self, value):
        self.value = value

        # No need to convert to bool. Any non-zero value is true.
        # yapf: disable
        self.lcd_enable           = value & (1 << 7)
        self.windowmap_select     = value & (1 << 6)
        self.window_enable        = value & (1 << 5)
        self.tiledata_select      = value & (1 << 4)
        self.backgroundmap_select = value & (1 << 3)
        self.sprite_height        = value & (1 << 2)
        self.sprite_enable        = value & (1 << 1)
        self.background_enable    = value & (1 << 0)
        # yapf: enable


class Renderer:
    def __init__(self, color_palette):
        self.alphamask = 0xFF
        self.color_palette = [(c << 8) | self.alphamask for c in color_palette]
        self.color_format = "RGBA"

        self.buffer_dims = (160, 144)

        self.clearcache = False
        self.tiles_changed = set([])

        # Init buffers as white
        self._screenbuffer_raw = array("B", [0xFF] * (ROWS*COLS*4))
        self._tilecache_raw = array("B", [0xFF] * (TILES*8*8*4))
        self._spritecache0_raw = array("B", [0xFF] * (TILES*8*8*4))
        self._spritecache1_raw = array("B", [0xFF] * (TILES*8*8*4))

        if cythonmode:
            self._screenbuffer = memoryview(self._screenbuffer_raw).cast("I", shape=(ROWS, COLS))
            self._tilecache = memoryview(self._tilecache_raw).cast("I", shape=(TILES * 8, 8))
            self._spritecache0 = memoryview(self._spritecache0_raw).cast("I", shape=(TILES * 8, 8))
            self._spritecache1 = memoryview(self._spritecache1_raw).cast("I", shape=(TILES * 8, 8))
        else:
            v = memoryview(self._screenbuffer_raw).cast("I")
            self._screenbuffer = [v[i:i + COLS] for i in range(0, COLS * ROWS, COLS)]
            v = memoryview(self._tilecache_raw).cast("I")
            self._tilecache = [v[i:i + 8] for i in range(0, TILES * 8 * 8, 8)]
            v = memoryview(self._spritecache0_raw).cast("I")
            self._spritecache0 = [v[i:i + 8] for i in range(0, TILES * 8 * 8, 8)]
            v = memoryview(self._spritecache1_raw).cast("I")
            self._spritecache1 = [v[i:i + 8] for i in range(0, TILES * 8 * 8, 8)]
            self._screenbuffer_ptr = c_void_p(self._screenbuffer_raw.buffer_info()[0])

        self._scanlineparameters = [[0, 0, 0, 0, 0] for _ in range(ROWS)]

    def scanline(self, y, lcd):
        bx, by = lcd.getviewport()
        wx, wy = lcd.getwindowpos()
        self._scanlineparameters[y][0] = bx
        self._scanlineparameters[y][1] = by
        self._scanlineparameters[y][2] = wx
        self._scanlineparameters[y][3] = wy
        self._scanlineparameters[y][4] = lcd.LCDC.tiledata_select

    def render_screen(self, lcd):
        self.update_cache(lcd)
        # All VRAM addresses are offset by 0x8000
        # Following addresses are 0x9800 and 0x9C00
        background_offset = 0x1800 if lcd.LCDC.backgroundmap_select == 0 else 0x1C00
        wmap = 0x1800 if lcd.LCDC.windowmap_select == 0 else 0x1C00

        for y in range(ROWS):
            bx, by, wx, wy, tile_data_select = self._scanlineparameters[y]
            # Used for the half tile at the left side when scrolling
            offset = bx & 0b111

            for x in range(COLS):
                if lcd.LCDC.window_enable and wy <= y and wx <= x:
                    wt = lcd.VRAM[wmap + (y-wy) // 8 * 32 % 0x400 + (x-wx) // 8 % 32]
                    # If using signed tile indices, modify index
                    if not lcd.LCDC.tiledata_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        wt = (wt ^ 0x80) + 128
                    self._screenbuffer[y][x] = self._tilecache[8*wt + (y-wy) % 8][(x-wx) % 8]
                elif lcd.LCDC.background_enable:
                    bt = lcd.VRAM[background_offset + (y+by) // 8 * 32 % 0x400 + (x+bx) // 8 % 32]
                    # If using signed tile indices, modify index
                    if not tile_data_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        bt = (bt ^ 0x80) + 128
                    self._screenbuffer[y][x] = self._tilecache[8*bt + (y+by) % 8][(x+offset) % 8]
                else:
                    # If background is disabled, it becomes white
                    self._screenbuffer[y][x] = self.color_palette[0]

        if lcd.LCDC.sprite_enable:
            self.render_sprites(lcd, self._screenbuffer, False)

    def render_sprites(self, lcd, buffer, ignore_priority):
        # Render sprites
        # - Doesn't restrict 10 sprites per scan line
        # - Prioritizes sprite in inverted order
        spriteheight = 16 if lcd.LCDC.sprite_height else 8
        bgpkey = self.color_palette[lcd.BGP.getcolor(0)]

        for n in range(0x00, 0xA0, 4):
            y = lcd.OAM[n] - 16 # Documentation states the y coordinate needs to be subtracted by 16
            x = lcd.OAM[n + 1] - 8 # Documentation states the x coordinate needs to be subtracted by 8
            tileindex = lcd.OAM[n + 2]
            attributes = lcd.OAM[n + 3]
            xflip = attributes & 0b00100000
            yflip = attributes & 0b01000000
            spritepriority = (attributes & 0b10000000) and not ignore_priority
            spritecache = (self._spritecache1 if attributes & 0b10000 else self._spritecache0)

            for dy in range(spriteheight):
                yy = spriteheight - dy - 1 if yflip else dy
                if 0 <= y < ROWS:
                    for dx in range(8):
                        xx = 7 - dx if xflip else dx
                        pixel = spritecache[8*tileindex + yy][xx]
                        if 0 <= x < COLS:
                            # import pdb; pdb.set_trace()
                            # TODO: Checking `buffer[y][x] == bgpkey` is a bit of a hack
                            if (spritepriority and not buffer[y][x] == bgpkey):
                                # Add a fake alphachannel to the sprite for BG pixels. We can't just merge this
                                # with the next 'if', as sprites can have an alpha channel in other ways
                                pixel &= ~self.alphamask

                            if pixel & self.alphamask:
                                buffer[y][x] = pixel
                        x += 1
                    x -= 8
                y += 1

    def update_cache(self, lcd):
        if self.clearcache:
            self.tiles_changed.clear()
            for x in range(0x8000, 0x9800, 16):
                self.tiles_changed.add(x)
            self.clearcache = False

        for t in self.tiles_changed:
            for k in range(0, 16, 2): # 2 bytes for each line
                byte1 = lcd.VRAM[t + k - 0x8000]
                byte2 = lcd.VRAM[t + k + 1 - 0x8000]
                y = (t+k-0x8000) // 2

                for x in range(8):
                    colorcode = color_code(byte1, byte2, 7 - x)

                    self._tilecache[y][x] = self.color_palette[lcd.BGP.getcolor(colorcode)]
                    self._spritecache0[y][x] = self.color_palette[lcd.OBP0.getcolor(colorcode)]
                    self._spritecache1[y][x] = self.color_palette[lcd.OBP1.getcolor(colorcode)]

                    if colorcode == 0:
                        self._spritecache0[y][x] &= ~self.alphamask
                        self._spritecache1[y][x] &= ~self.alphamask

        self.tiles_changed.clear()

    def blank_screen(self):
        # If the screen is off, fill it with a color.
        color = self.color_palette[0]
        for y in range(ROWS):
            for x in range(COLS):
                self._screenbuffer[y][x] = color

    def save_state(self, f):
        for y in range(ROWS):
            f.write(self._scanlineparameters[y][0])
            f.write(self._scanlineparameters[y][1])
            # We store (WX - 7). We add 7 and mask 8 bits to make it easier to serialize
            f.write((self._scanlineparameters[y][2] + 7) & 0xFF)
            f.write(self._scanlineparameters[y][3])
            f.write(self._scanlineparameters[y][4])

    def load_state(self, f, state_version):
        for y in range(ROWS):
            self._scanlineparameters[y][0] = f.read()
            self._scanlineparameters[y][1] = f.read()
            # Restore (WX - 7) as described above
            self._scanlineparameters[y][2] = (f.read() - 7) & 0xFF
            self._scanlineparameters[y][3] = f.read()
            if state_version > 3:
                self._scanlineparameters[y][4] = f.read()
