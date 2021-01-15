from pyboy.utils import color_code
from array import array
from ctypes import c_void_p

ROWS, COLS = 144, 160

try:
    from cython import compiled
    cythonmode = compiled
except ImportError:
    cythonmode = False

class CGBRenderer:
    def __init__(self):
        self.alphamask = 0xFF
        
        self.color_format = "RGBA"

        self.buffer_dims = (ROWS, COLS)

        self.clearcache = False
        self.tiles_changed0 = set([])
        self.tiles_changed1 = set([])

        tiles_bank = 384
        
        # Init buffers as white
        # *4 because palettes are 4 colors?
        # 1 tile-/spritecache for each bank
        self._screenbuffer_raw = array("B", [0xFF] * (ROWS*COLS*4))
        self._tilecache0_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._tilecache1_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._spritecache0_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._spritecache1_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._col_index0_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._col_index1_raw = array("B", [0xFF] * (tiles_bank*8*8*4))

        if cythonmode:
            self._screenbuffer = memoryview(self._screenbuffer_raw).cast("I", shape=(ROWS, COLS))
            self._tilecache = memoryview(self._tilecache_raw).cast("I", shape=(tiles_bank * 8, 8))
            self._spritecache0 = memoryview(self._spritecache0_raw).cast("I", shape=(tiles_bank * 8, 8))
            self._spritecache1 = memoryview(self._spritecache1_raw).cast("I", shape=(tiles_bank * 8, 8))
        else:
            v = memoryview(self._screenbuffer_raw).cast("I")
            self._screenbuffer = [v[i:i + COLS] for i in range(0, COLS * ROWS, COLS)]
            v = memoryview(self._tilecache0_raw).cast("I")
            v = array("I", self._tilecache0_raw.tolist())
            self.tc0 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._tilecache1_raw).cast("I")
            v = array("I", self._tilecache1_raw.tolist())
            self.tc1 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._spritecache0_raw).cast("I")
            v = array("I", self._spritecache0_raw.tolist())
            self.sc0 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._spritecache1_raw).cast("I")
            v = array("I", self._spritecache1_raw.tolist())
            self.sc1 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._col_index0_raw).cast("I")
            v = array("I", self._col_index0_raw.tolist())
            self._col_index0 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._col_index1_raw).cast("I")
            v = array("I", self._col_index1_raw.tolist())
            self._col_index1 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            self._screenbuffer_ptr = c_void_p(self._screenbuffer_raw.buffer_info()[0])

            # create the 3d lists to hold palettes, 8 palettes
            self._tilecache0 = []
            self._tilecache1 = []
            self._spritecache0 = []
            self._spritecache1 = []

            from copy import deepcopy
            for i in range(8):
                self._tilecache0.append(deepcopy(self.tc0))
                self._tilecache1.append(deepcopy(self.tc1))
                self._spritecache0.append(deepcopy(self.sc0))
                self._spritecache1.append(deepcopy(self.sc1))

        self._scanlineparameters = [[0, 0, 0, 0, 0, 0, 0, 0, 0] for _ in range(ROWS)]
        
        self._backgroundmapattributes = [0, 0, 0, 0, 0]
        self._col_i = [[0] * COLS for _ in range(ROWS)]
        self._bg_priority = [[0] * COLS for _ in range(ROWS)]

    def scanline(self, y, lcd):
        bx, by = lcd.getviewport()
        wx, wy = lcd.getwindowpos()
        self._scanlineparameters[y][0] = bx
        self._scanlineparameters[y][1] = by
        self._scanlineparameters[y][2] = wx
        self._scanlineparameters[y][3] = wy
        self._scanlineparameters[y][4] = lcd.LCDC.tiledata_select
        self._scanlineparameters[y][5] = lcd.LCDC.backgroundmap_select
        self._scanlineparameters[y][6] = lcd.LCDC.windowmap_select
        self._scanlineparameters[y][7] = lcd.LCDC.window_enable
        self._scanlineparameters[y][8] = lcd.LCDC.background_enable


    def getbackgroundmapattributes(self, lcd, i):
        tile_num = lcd.getVRAMbank(i, 1, False)
        palette = tile_num & 0b111  
        vbank = (tile_num >> 3) & 1
        horiflip = (tile_num >> 5) & 1
        vertflip = (tile_num >> 6) & 1
        bgpriority = (tile_num >> 7) & 1 

        self._backgroundmapattributes[0] = palette
        self._backgroundmapattributes[1] = vbank
        self._backgroundmapattributes[2] = horiflip
        self._backgroundmapattributes[3] = vertflip
        self._backgroundmapattributes[4] = bgpriority

    def render_screen(self, lcd):
        self.update_cache(lcd)
        # All VRAM addresses are offset by 0x8000
        # Following addresses are 0x9800 and 0x9C00

        for y in range(ROWS):
            bx, by, wx, wy, tile_data_select, bgmap_select, wmap_select, window_enable, _  = self._scanlineparameters[y]
            background_offset = 0x1800 if bgmap_select == 0 else 0x1C00
            wmap = 0x1800 if wmap_select == 0 else 0x1C00
            
            # Used for the half tile at the left side when scrolling
            offset = bx & 0b111

            for x in range(COLS):
                # WINDOW
                if window_enable and wy <= y and wx <= x:
                    index = wmap + (y-wy) // 8 * 32 % 0x400 + (x-wx) // 8 % 32
                    wt = lcd.getVRAMbank(index, 0, False)
                    
                    #cgb specific map attributes
                    self.getbackgroundmapattributes(lcd, index)
                    palette, vbank, horiflip, vertflip, bgpriority = self._backgroundmapattributes
                    tilecache = (self._tilecache1 if vbank else self._tilecache0)
                    col_index = (self._col_index1 if vbank else self._col_index0)
                    xx = (7 - ((x-wx) % 8)) if horiflip else ((x-wx) % 8)
                    
                    # If using signed tile indices, modify index
                    if not tile_data_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        wt = (wt ^ 0x80) + 128
                    
                    yy = (8*wt + (7 -(y-wy) % 8)) if vertflip else (8*wt + (y-wy) % 8)
                    self._screenbuffer[y][x] = tilecache[palette][yy][xx]
                    self._col_i[y][x] = col_index[yy][xx]
                    self._bg_priority[y][x] = bgpriority

                # BACKGROUND
                else:
                    index = background_offset + (y+by) // 8 * 32 % 0x400 + (x+bx) // 8 % 32
                    bt = lcd.getVRAMbank(index, 0, False)

                    #cgb specific map attributes
                    self.getbackgroundmapattributes(lcd, index)
                    palette, vbank, horiflip, vertflip, bgpriority = self._backgroundmapattributes
                    tilecache = (self._tilecache1 if vbank else self._tilecache0)
                    col_index = (self._col_index1 if vbank else self._col_index0)

                    xx = (7 - ((x+offset) % 8)) if horiflip else ((x+offset) % 8)

                    # If using signed tile indices, modify index
                    if not tile_data_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        bt = (bt ^ 0x80) + 128

                    yy = (8*bt + (7-(y+by) % 8)) if vertflip else (8*bt + (y+by) % 8)
                    self._screenbuffer[y][x] = tilecache[palette][yy][xx]
                    self._col_i[y][x] = col_index[yy][xx]
                    self._bg_priority[y][x] = bgpriority                    
        
        if lcd.LCDC.sprite_enable:
            self.render_sprites(lcd, self._screenbuffer)

    def render_sprites(self, lcd, buffer, ignore_priority = False):
        # Render sprites
        # - Doesn't restrict 10 sprites per scan line
        # - Prioritizes sprite in inverted order
        spriteheight = 16 if lcd.LCDC.sprite_height else 8
        
        # CGB priotizes sprites located first in OAM
        for n in range(0x9C, -0x04, -4):
            y = lcd.OAM[n] - 16 # Documentation states the y coordinate needs to be subtracted by 16
            x = lcd.OAM[n + 1] - 8 # Documentation states the x coordinate needs to be subtracted by 8
            tileindex = lcd.OAM[n + 2]
            attributes = lcd.OAM[n + 3]
            xflip = attributes & 0b00100000
            yflip = attributes & 0b01000000
            OAMbgpriority = (attributes & 0b10000000)

            # bit 3 selects tile vram-bank
            spritecache = (self._spritecache1 if attributes & 0b1000 else self._spritecache0)
            # bits 0-2 selects palette number
            palette = attributes & 0b111

            for dy in range(spriteheight):
                yy = spriteheight - dy - 1 if yflip else dy
                if 0 <= y < ROWS:
                    for dx in range(8):
                        xx = 7 - dx if xflip else dx
                        pixel = spritecache[palette][8*tileindex + yy][xx]
                        if 0 <= x < COLS:
                            use_priority_flags = self._scanlineparameters[y][8]
                            if use_priority_flags:
                                bgmappriority = self._bg_priority[y][x]        
                                col = self._col_i[y][x]
                                if bgmappriority:
                                    if not col == 0:
                                        pixel &= ~self.alphamask
                                elif OAMbgpriority:
                                    if not col == 0:
                                        pixel &= ~self.alphamask                       
                            if pixel & self.alphamask:
                                        buffer[y][x] = pixel
                        x += 1
                    x -= 8
                y += 1

    def update_cache(self, lcd):        
        if self.clearcache:
            self.clear_cache()
        self.update_tiles(lcd, self.tiles_changed0, 0)
        self.update_tiles(lcd, self.tiles_changed1, 1)

        self.tiles_changed0.clear()
        self.tiles_changed1.clear()

    def update_tiles(self, lcd, tiles_changed, bank):
        for t in tiles_changed:
            for k in range(0, 16, 2): # 2 bytes for each line
                byte1 = lcd.getVRAMbank(t + k, bank)
                byte2 = lcd.getVRAMbank(t + k + 1, bank)
                
                y = (t+k-0x8000) // 2

                for x in range(8):
                    #index into the palette for the current pixel
                    colorcode = color_code(byte1, byte2, 7 - x)
                    
                    if bank:
                        self._col_index1[y][x] = colorcode
                    else:
                        self._col_index0[y][x] = colorcode

                    # update for the 8 palettes
                    for p in range(8): 
                        if bank:
                            self._tilecache1[p][y][x] = self.convert_to_rgba(lcd.bcpd.getcolor(p, colorcode))
                            self._spritecache1[p][y][x] = self.convert_to_rgba(lcd.ocpd.getcolor(p, colorcode))

                        else:
                            self._tilecache0[p][y][x] = self.convert_to_rgba(lcd.bcpd.getcolor(p, colorcode))
                            self._spritecache0[p][y][x] = self.convert_to_rgba(lcd.ocpd.getcolor(p, colorcode))
                        
                        # first color transparent for sprites
                        if colorcode == 0:
                            if bank: 
                                self._spritecache1[p][y][x] &= ~self.alphamask
                            else:
                                self._spritecache0[p][y][x] &= ~self.alphamask           

    def clear_cache(self):
        self.tiles_changed0.clear()  
        self.tiles_changed1.clear()  
        for x in range(0x8000, 0x9800, 16):
            self.tiles_changed0.add(x)
            self.tiles_changed1.add(x)
        self.clearcache = False


    def blank_screen(self):
        # If the screen is off, fill it with a color.
        color = 0xFFFFFFFF
        for y in range(ROWS):
            for x in range(COLS):
                self._screenbuffer[y][x] = color

    # converts a 24 bit RGB color to 32 bit RGBA
    def convert_to_rgba(self, color):
        return (color << 8) | self.alphamask

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

            
