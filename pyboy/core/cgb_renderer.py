from pyboy.utils import color_code
from array import array
from ctypes import c_void_p

ROWS, COLS = 144, 160

try:
    from cython import compiled
    cythonmode = compiled
except ImportError:
    cythonmode = False

class Renderer:
    def __init__(self, color_palette):
        self.alphamask = 0xFF
        
        ############ TESTING TESTING TESTING TESTING TESTING #################        
        self.test = [0xFFFFFF, 0x999999, 0x555555, 0x000000]
        self.color_palette = [(c << 8) | self.alphamask for c in self.test]
        ############ TESTING TESTING TESTING TESTING TESTING #################
        
        self.color_format = "RGBA"

        self.buffer_dims = (ROWS, COLS)

        self.clearcache = False
        self.tiles_changed = set([])

        tiles_bank = 384
        
        # Init buffers as white
        # *4 because palettes are 4 colors?
        # 1 tile-/spritecache for each bank
        self._screenbuffer_raw = array("B", [0xFF] * (ROWS*COLS*4))
        self._tilecache0_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._tilecache1_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        
        self._spritecache0_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
        self._spritecache1_raw = array("B", [0xFF] * (tiles_bank*8*8*4))

        if cythonmode:
            self._screenbuffer = memoryview(self._screenbuffer_raw).cast("I", shape=(ROWS, COLS))
            self._tilecache = memoryview(self._tilecache_raw).cast("I", shape=(tiles_bank * 8, 8))
            self._spritecache0 = memoryview(self._spritecache0_raw).cast("I", shape=(tiles_bank * 8, 8))
            self._spritecache1 = memoryview(self._spritecache1_raw).cast("I", shape=(tiles_bank * 8, 8))
        else:
            v = memoryview(self._screenbuffer_raw).cast("I")
            self._screenbuffer = [v[i:i + COLS] for i in range(0, COLS * ROWS, COLS)]
            v = memoryview(self._tilecache0_raw).cast("I")
            self.tc0 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._tilecache1_raw).cast("I")
            self.tc1 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._spritecache0_raw).cast("I")
            self.sc0 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            v = memoryview(self._spritecache1_raw).cast("I")
            self.sc1 = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            self._screenbuffer_ptr = c_void_p(self._screenbuffer_raw.buffer_info()[0])

            #create the 3d lists to hold palettes, 8 palettes
            self._tilecache0 = []
            self._tilecache1 = []
            self._spritecache0 = []
            self._spritecache1 = []
            for i in range(8):
                self._tilecache0.append(self.tc0)
                self._tilecache1.append(self.tc1)
                self._spritecache0.append(self.sc0)
                self._spritecache1.append(self.sc1)

            ### TESTING TESTING TESTING TESTING TESTING TESTING TESTING ####
            self._tilecache_raw = array("B", [0xFF] * (tiles_bank*8*8*4))
            v = memoryview(self._tilecache_raw).cast("I")
            self._testtilecache = [v[i:i + 8] for i in range(0, tiles_bank * 8 * 8, 8)]
            ### TESTING TESTING TESTING TESTING TESTING TESTING TESTING ####

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
                #CGB only bg map attributes


                if lcd.LCDC.window_enable and wy <= y and wx <= x:
                    wt = lcd.NoOffsetgetVRAM(wmap + (y-wy) // 8 * 32 % 0x400 + (x-wx) // 8 % 32)
                    # If using signed tile indices, modify index
                    if not lcd.LCDC.tiledata_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        wt = (wt ^ 0x80) + 128
                    self._screenbuffer[y][x] = self._testtilecache[8*wt + (y-wy) % 8][(x-wx) % 8]
                elif lcd.LCDC.background_enable:
                    bt = lcd.NoOffsetgetVRAM(background_offset + (y+by) // 8 * 32 % 0x400 + (x+bx) // 8 % 32)
                    # If using signed tile indices, modify index
                    if not tile_data_select:
                        # (x ^ 0x80 - 128) to convert to signed, then
                        # add 256 for offset (reduces to + 128)
                        bt = (bt ^ 0x80) + 128
                    self._screenbuffer[y][x] = self._testtilecache[8*bt + (y+by) % 8][(x+offset) % 8]
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

            #bit 3 selects tile vram-bank
            spritecache = (self._spritecache1 if attributes & 0b1000 else self._spritecache0)
            #bits 0-2 selects palette number
            palette = attributes & 0b111

            for dy in range(spriteheight):
                yy = spriteheight - dy - 1 if yflip else dy
                if 0 <= y < ROWS:
                    for dx in range(8):
                        xx = 7 - dx if xflip else dx
                        pixel = spritecache[palette][8*tileindex + yy][xx]
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

#REMOVE ME: CLEAR CACHE SET ON UPDATE TO PALETTE REGISTERS IN MB MEMORY MANAGER?
    def update_cache(self, lcd):
        if self.clearcache:
            self.tiles_changed.clear()  
            for x in range(0x8000, 0x9800, 16):
                self.tiles_changed.add(x)
            self.clearcache = False

        for t in self.tiles_changed:
            for k in range(0, 16, 2): # 2 bytes for each line
                byte1 = lcd.getVRAM(t + k)
                byte2 = lcd.getVRAM(t + k + 1)
                y = (t+k-0x8000) // 2

                for x in range(8):
                    #index into the palette for the current pixel
                    colorcode = color_code(byte1, byte2, 7 - x)

                    #update for the 8 palettes
                    for p in range(8): 
                        #self._tilecache0[p][y][x] = lcd.bcpd.getcolor(p, colorcode)
                        #self._tilecache1[p][y][x] = lcd.bcpd.getcolor(p, colorcode)

                        self._spritecache0[p][y][x] = self.rgba_converter(lcd.ocpd.getcolor(p, colorcode))
                        self._spritecache1[p][y][x] = self.rgba_converter(lcd.ocpd.getcolor(p, colorcode))


                    ### TESTING TESTING TESTING TESTING TESTING TESTING TESTING ####
                    self._testtilecache[y][x] = self.color_palette[lcd.BGP.getcolor(colorcode)]
                    ### TESTING TESTING TESTING TESTING TESTING TESTING TESTING ####

                    # if colorcode == 0:
                    #     #simply sets to 0?
                    #     self._testspritecache0[y][x] &= ~self.alphamask
                    #     self._testspritecache1[y][x] &= ~self.alphamask

        self.tiles_changed.clear()

    def blank_screen(self):
        # If the screen is off, fill it with a color.
        color = self.color_palette[0]
        for y in range(ROWS):
            for x in range(COLS):
                self._screenbuffer[y][x] = color

    #MOVE FROM HERE
    #converts a 24 bit RGB color to 32 bit RGBA
    def rgba_converter(self, color):
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

            