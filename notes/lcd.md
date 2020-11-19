# LCD 

### LCD CGB vs DMG:
**FF40 - LCD Control Register**:
Bit 0 has different interpretation for CGB. DMG: enables background. CGB: background lose priority, ie, sprites always displayed on top independently of priority flags in OAM and BG map attributes.

**FF41 - STAT**:
Same, but during mode 3 can't access CGB palette Data neither

**Color Registers**
*DMG* uses three registers FF47-FF49: BGP, OBP0 and OPB1 to assign gray shades. *NOTE* these are actually also used in CGB to assign colors to monochrome game boy games, using the table located in the boot-ROM. Can also be chosen by user input. *Source*: https://tcrf.net/Notes:Game_Boy_Color_Bootstrap_ROM#Assigned_Palette_Configurations

*CGB* uses four registers FF68-FF6B: BCPS/BGPI, BCPD/BGPD, OCPS/OBPI and OCPD/OBPD. The first two are used to control background palette memory, the last two is for sprite palettes

**VRAM Tile Data**
CGB supports double the amount of tiles 768 because of the extra VRAM bank

**Background Map Attributes**
CGB stores an additional bg map of 32x32 bytes in VRAM bank 1. Each byte defines attributes for the corresponding tile-number map entry in VRAM bank 0:
- Bit 0-2 Background palette number
- Bit 3: Tile VRAM Bank number
- Bit 4: Not used
- Bit 5: Horizontal flip
- Bit 6: Vertical flip
- Bit 7: BG-to-OAM Priority

### TODO
- REMEMBER TO REMOVE: Added temporary NoOffsetgetVRAM methods to lcd classes to avoid out of range error when fetching wt and bt values in render_screen in renderer.py
- LCDC FF40 Control Register change bit 0 implementation: render_screen method in renderer class currently uses the background_enable bit, change this to make background rendering loose priority when CGB 
- FF41 Stat is currently in MB, move to LCD? Does mode 3 need to be extented to account for the fact that CGB palette data can't be accessed?
- FF44/45 LY/LYC currently in MB, move to base_lcd?
- FF46 DMA OAM transfers currently in MB, move to base_lcd? Especially because CGB also adds VRAM DMA transfer functionality, where to put that then
- maybe delete the VBK def at top of cgb_lcd, not used? 
- save/load state methods for CGB
- måske cgb_lcd ikke skal nedarve fra lcd - der er efteråhnden meget få ligheder
- Tilføjet tiles_changed for hver bank, men clearcache er stadig samlet, kunne nok godt opdateres så det kun er den relevante bank der bliver clearet og ikke begge to, ville i hvert fald være hurtigere. Clearcache sættes i memory manager

### Notes
**Sprites**: 8x8 or 8x16 tiles, 4 bytes

**OAM**: Object (sprite) attribute table: Memory location used to store the information of the sprites to be rendered on screen. 160 bytes so room for 40 sprites. Mostly same for both CGB and DMG, however byte 3 of each entry that defines the attributes/flags differ, where bit4 is only used for DMG to choose between the two sprite palettes stored in OBP0 and OBP1. For CGB only: Bit3 indicates the tile VRAM-bank, bits2-0 the CGB palette number. 

**Sprite bytes**:
1. Y location
2. X location
3. Tile number
4. Flags

**Flags in 4th sprite byte**:
0. 0: Palette number 1 (CGB)
1. 1: Palette number 2 (CGB)
2. Palette number 3 (CGB)
3. VRAM bank (CGB)
4. Palette number (CGB)
5. X Flip
6. Y Flip
7. Render priority


**DMA**: Direct memory access, used to transfer data from ROM or RAM to OAM. Takes 160 cycles and during this time the cpu can only access the HRAM. 
    - CGB: DMA can also be used to transfer DATA to vram (pandocs)

**VRAM Indexing Method**: Currently only method 8000 (using $8000 as base pointer) is implemented, but there is also a method 8800 (using $9000 as base pointer), might have to implement this. BG and window can use both modes controlled by LCDC bit 4. 

**Update_cache**: tile = 16 bytes af 8*8 pixels, hver pixel er altså 8 bits stor, angiver hvilke farver der skal til. 
tilecache:
    y: 



### Changes made
- Added cgb_lcd class for CGB lcd
- Added CGB variable to base_mbc, can be used to check if the loaded ROM is a CGB rom
- Added check in motherboard init if should load CGB or DMG LCD
- Added register FF4F set/get to memory manager
- Added set/get VRAM to mem manager 
- moved renderer to own class
- cgb_lcd inherits from and initializes lcd.py
- added palette memory and appropriate registers to cgb_lcd (needed memory is added to the specific registers, maybe change)
- added cgb checks to memory manager when trying to use DMG palette registers
- updated setVRAM methods to return the bank that was set in order to compensate for mm
- instead of tiles_changed then keep track of tiles_changed_bank0/!


FIND FORHOLD MELLEM FARVER:
PÅ EN MODERNE MASKINE: 24 BIT
PÅ CGB: 15 BIT

ADD CLEAR CACHE IN MEM_MANAGER VED DE NYE FARVE REGISTRE?
    - SLET DE DMG FARVE REGISTRE?