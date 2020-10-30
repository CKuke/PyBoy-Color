import array



# This class represents the added palette ram of the CGB

class PaletteRam:
    def __init__(self):
        # Defined each color as 16 bit types instead of two 8 bits for easier
        # handling.
        self.BG  = array.array('H', [0]*32) # 4 colors * 8 palettes = 32
        self.OBJ = array.array('H', [0]*32)
    
    def get_bg(self, pal):
        if pal < 0 or pal > 7: # TODO: Maybe delete for increased performance
            raise Exception("Cannot read from pallete")
        colors = []
        for col in range(4):
            current = self.BG[pal+col] & 0b0111111111111111 # 15 ones
            colors.append(current) 
        return Pallete(colors)
    
    def get_obj(self):
        # TODO: Should we have a check like in BG method?
        color = []
        for col in range(4):
            current = self.OBJ[pal+col] & 0b0111111111111111 # 15 ones
            colors.append(current) 
        return Palette(colors)


# Wrapper class for easy handling of color palettes
class Pallete:
    def __init__(self, color_data):
        self.color0 = color_data[0]
        self.color1 = color_data[1]
        self.color2 = color_data[2]
        self.color3 = color_data[3]
    
    # TODO: Should we make a get and set method for each color
    # or single method with argument specifying color number?
    # Or any at all. Can also just access them directly where needed
    # will still result in better code. 
    #
    # With either method approach a OBJ and BG palette class could be
    # created as one color of an OBJ palette always has to be transparent.
    # this could however also be handled where the palette is being used
    # (lkely in the new renderer)