# LCD 

## LCD CGB vs DMG:
**FF40 - LCD Control Register**:
    Bit 0 has different interpretation for CGB. DMG: enables background. CGB: background lose priority, ie, sprites always displayed on top independently of priority flags in OAM and BG map attributes.

**FF41 - STAT**:
    Same, but during mode 3 can't access CGB palette Data neither


## TODO
-   FF40 Control Register Change
-   FF41 Stat is currently in MB, move to LCD? Does mode 3 need to be extented to account for the      fact that CGB palette data can't be accessed?
-   

## Notes
**Sprites**: 8x8 or 8x16 tiles, 4 bytes

**OAM**: Object (sprite) attribute table: Memory location used to store the information of the sprites to be rendered on screen. 160 bytes so room for 40 sprites

**Sprite bytes**:
    1. Y location
    2. X location
    3. Tile number
    4. Flags

**Flags in 4th sprite byte**:
    1. 7: Render priority
    1. 6: Y Flip
    1. 5: X Flip
    1. 4: Palette number (CGB)
    1. 3: VRAM bank (CGB)
    1. 2: Palette number 3 (CGB)
    1. 1: Palette number 2 (CGB)
    1. 0: Palette number 1 (CGB)

**DMA**: Direct memory access, used to transfer data from ROM or RAM to OAM. Takes 160 cycles and during this time the cpu can only access the HRAM. 
    - CGB: DMA can also be used to transfer DATA to vram (pandocs)

