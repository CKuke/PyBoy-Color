# LCD 

### LCD CGB vs DMG:
**FF40 - LCD Control Register**:
Bit 0 has different interpretation for CGB. DMG: enables background. CGB: background lose priority, ie, sprites always displayed on top independently of priority flags in OAM and BG map attributes.

**FF41 - STAT**:
Same, but during mode 3 can't access CGB palette Data neither

**Color Registers**
*DMG* uses three registers FF47-FF49: BGP, OBP0 and OPB1 to assign gray shades

*CGB* uses four registers FF68-FF6B: BCPS/BGPI, BCPD/BGPD, OCPS/OBPI and OCPD/OBPD. The first two are used to control background palette memory, the last two is for sprite palettes

**VRAM Tile Data**
CGB supports double the amount of tiles 768 because of the extra VRAM bank

### TODO
- FF40 Control Register change bit 0 implementation
- FF41 Stat is currently in MB, move to LCD? Does mode 3 need to be extented to account for the fact that CGB palette data can't be accessed?
- FF44/45 LY/LYC currently in MB, move to base_lcd?
- FF46 DMA OAM transfers currently in MB, move to base_lcd? Especially because CGB also adds VRAM DMA transfer functionality, where to put that then (cgb_lcd for now) 

### Notes
**Sprites**: 8x8 or 8x16 tiles, 4 bytes

**OAM**: Object (sprite) attribute table: Memory location used to store the information of the sprites to be rendered on screen. 160 bytes so room for 40 sprites

**Sprite bytes**:
1. Y location
2. X location
3. Tile number
4. Flags

**Flags in 4th sprite byte**:
7. Render priority
6. Y Flip
5. X Flip
4. Palette number (CGB)
3. VRAM bank (CGB)
2. Palette number 3 (CGB)
1. 1: Palette number 2 (CGB)
0. 0: Palette number 1 (CGB)

**DMA**: Direct memory access, used to transfer data from ROM or RAM to OAM. Takes 160 cycles and during this time the cpu can only access the HRAM. 
    - CGB: DMA can also be used to transfer DATA to vram (pandocs)

