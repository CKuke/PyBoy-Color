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
        
        self.io         = array.array("B", [0]*0x80) # FF00-FF80
        self.hram       = array.array("B", [0]*0x7f) # FF80-FFFF
        self.interrupt  = array.array("B", [0]*0x1 ) # FFFF-FFFF
        self.not_usable = array.array("B", [0]*0x60)

    #TODO: Finish read and write
    def read(self, addr):
        if 0xC000 <= addr and addr < 0xE000:
            return self.read_wram(addr)
        elif 0xE000 <= addr and addr < 0xFE00:
            # Redirect to actual ram
            offset = 0x2000
            return self.read_wram(addr-offset)
        elif 0xFF00 <= addr and addr < 0xFF80:
            offset = 0xFF00
            return self.read_io(addr-offset)
        elif 0xFEA0 <= addr and addr < 0xFF00:
            offset = 0xFEA0
            return self.not_usable[addr-offset]
        elif 0xFF80 <= addr and addr < 0xFFFF:
            offset = 0xFF80
            return self.read_hram(addr-offset)
        elif addr == 0xFFFF:
            return self.read_interrupt()
        else:
            raise Exception("Cannot read address {:x} from ram".format(addr))
    
    def read_wram(self, addr):
        if 0xC000 <= addr and addr < 0xD000:
            offset = 0xC000
            return self.wram[0][addr-offset]
        else:
            offset = 0xD000
            return self.wram[1][addr-offset] # only one bank in DMG

    def read_io(self, addr):
        return self.io[addr]
    
    def read_hram(self, addr):
        return self.hram[addr]
    
    def read_interrupt(self):
        return self.interrupt[0]
    
    def write(self, addr, val):
        if 0xC000 <= addr and addr < 0xE000:
            #offset = 0xC000
            self.write_wram(addr, val)
        elif 0xE000 <= addr and addr < 0xFF00:
            # Redirect to actual ram
            offset = 0x2000
            self.write_wram(addr-offset, val)
        elif 0xFF00 <= addr and addr < 0xFF80:
            offset = 0xFF00
            self.write_io(addr-offset, val)
        elif 0xFEA0 <= addr and addr < 0xFE00:
            offset = 0xFEA0
            self.not_usable[addr-offset] = val
        elif 0xFF80 <= addr and addr < 0xFFFF:
            offset = 0xFF80
            self.write_hram(addr-offset, val)
        elif addr == 0xFFFF:
            self.write_interrupt(val)
        else:
            raise Exception("Cannot read write to {:x} in ram".format(addr))
    
    def write_wram(self, addr, val):
        if 0xC000 <= addr and addr < 0xD000:
            offset = 0xC000
            self.wram[0][addr-offset] = val
        else:
            offset = 0xD000
            self.wram[1][addr-offset] = val
    
    def write_io(self, addr, val):
        self.io[addr] = val

    def write_hram(self, addr, val):
        self.hram[addr] = val
    
    def write_interrupt(self, val):
        self.interrupt[0] = val
    
    ############################
    # State saving and loading #
    ############################
    def save_state(self, f):
        # Save working ram
        for bank in self.wram:
            for byte in range(len(bank)):
                f.write(bank[byte])
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
        for byte in range(len(self.io)):
            self.io[byte] = f.read()
        for byte in range(len(self.hram)):
            self.hram[byte] = f.read()
        for byte in range(len(self.interrupt)):
            self.interrupt[byte] = f.read()