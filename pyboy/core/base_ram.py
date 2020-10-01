import array

# This class should never be initialized.
# use sub classes dmg_ram or cgb_ram
class RAM:
    def __init__(self, random=False):
        if random:
            raise Exception("Random RAM not implemented")

        self.wram = []
        for i in range(2): # 2 banks
            self.wram.append(array.array("B", [0]*4096))
        
        # TODO: Could drop mirror ram, and just redirect all reads and writes
        # to the ram it is a mirror of.
        # self.mirror    = array.array("B", [0]*7680) # E000-FE00
        self.io        = array.array("B", [0]*0x80) # FF00-FF80
        self.hram      = array.array("B", [0]*0x7f) # FF80-FFFF
        self.interrupt = array.array("B", [0]*0x1 ) # FFFF-FFFF

        # self.not_usable = array.array("B", [0]*0x60) Should we define this?

    #TODO: Finish read and write
    def read(self, addr):
        if 0xC000 <= addr and addr < 0xE000:
            offset = 0xC000
            return self.__read_wram(addr-offset)
        elif 0xE000 <= addr and addr < 0xFE00:
            # Redirect to actual ram
            offset = 0x2000 + 0xC000
            return self.__read_wram(addr-offset)
        elif 0xFF00 <= addr and addr < 0xFF80:
            offset = 0xFF00
            return self.__read_io(addr-offset)
        elif 0xFF80 <= addr and addr < 0xFFFF:
            offset = 0xFF80
            return self.__read_hram(addr-offset)
        elif addr == 0xFFFF:
            offset = 0xFFFF
            return self.__read_interrupt(addr-offset)
        else:
            raise Exception("Cannot read address {:x} from ram".format(addr))
    
    def __read_wram(self, addr):
        if 0xC000 <= addr and addr < 0xD000:
            return self.wram[0][addr]
        else:
            return self.wram[1][addr] # only one bank in DMG

    def __read_io(self, addr):
        offset = 0xFF00
        return self.io[addr-offset]
    
    def __read_hram(self, addr):
        offset = 0xFF80
        return self.hram[addr-offset]
    
    def __read_interrupt(self):
        return self.interrupt[0]
    
    def write(self, addr, val):
        if 0xC000 <= addr and addr < 0xE000:
            offset = 0xC000
            self.__write_wram(addr-offset, val)
        elif 0xE000 <= addr and addr < 0xFF00:
            # Redirect to actual ram
            offset = 0x2000 + 0xC000
            self.__write_wram(addr-offset, val)
        elif 0xFF00 <= addr and addr < 0xFF80:
            offset = 0xFF00
            self.__write_io(addr-offset, val)
        elif 0xFF80 <= addr and addr < 0xFFFF:
            offset = 0xFF80
            self.__write_hram(addr-offset, val)
        elif addr == 0xFFFF:
            offset = 0xFFFF
            self.__write_interrupt(addr-offset, val)
        else:
            raise Exception("Cannot read write to {:x} in ram".format(addr))
    
    def __write_wram(self, addr, val):
        if 0xC000 <= addr and addr < 0xD000:
            self.wram[0][addr] = val
        else:
            self.wram[1][addr] = val
    
    def __write_io(self, addr, val):
        self.io[addr] = val

    def __write_hram(self, addr, val):
        self.hram[addr] = val
    
    def __write_interrupt(self, addr, val):
        self.interrupt[addr] = val
    
    # TODO: Måske de ikke skal gemmes i denne række følge
    # Men så igen, hvis de bliver læst samme måde i load, gør
    # det nok ingen forskel
    def save_state(self, f):
        # Save working ram
        for bank in self.wram:
            for byte in range(len(bank)):
                f.write(bank[byte])
        for byte in self.mirror:
            f.write(byte)
        for byte in self.io:
            f.write(byte)
        for byte in self.hram:
            f.write(byte)
        for byte in self.interrupt:
            f.write(byte)
        
    
    def load_state(self, f, state_version): # Why state_version?
        # Load working ram
        for bank in self.wram:
            for byte in range(len(bank)):
                self.wram[byte] = f.read()
        for byte in range(len(self.mirror)):
            self.mirror[byte] = f.read()
        for byte in range(len(self.io)):
            self.io[byte] = f.read()
        for byte in range(len(self.hram)):
            self.hram[byte] = f.read()
        for byte in range(len(self.interrupt)):
            self.interrupt[byte] = f.read()