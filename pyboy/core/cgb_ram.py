import array
from . import base_ram

class CgbRam(base_ram.RAM):
    def __init__(self, random=False):
        super().__init__(random)
        self.svbk = SVBKregister()

        # Initialize CGB 8 WRAM banks
        for i in range(6):
            self.wram.append(array.array("B", [0]*4096))
        
    
    def read_wram(self, addr):
        if 0xC000 <= addr and addr < 0xD000:
            offset = 0xC000
            return self.wram[0][addr-offset]
        else:
            # Read which bank to read from at FF70
            io_offset = 0xFF00
            bank_addr = 0xFF70 - io_offset
            bank = self.read_io(bank_addr)
            bank &= 0b111
            if bank == 0x0:
                bank = 0x01
            offset = 0xD000
            return self.wram[bank][addr-offset]
        
    def write_wram(self, addr, val):
        if 0xC000 <= addr and addr < 0xD000:
            offset = 0xC000
            self.wram[0][addr-offset] = val
        else:
            # Read which bank to read from at FF70
            io_offset = 0xFF00
            bank_addr = 0xFF70 - io_offset
            bank = self.read_io(bank_addr)
            bank &= 0b111
            if bank == 0x0:
                bank = 0x01
            offset = 0xD000
            self.wram[bank][addr-offset] = val




class SVBKregister:
    def __init__(self):
        self.active_bank = 1

    def set_bank(bank):
        self.active_bank = bank

    def get_bank():
        if self.active_bank == 0:
            return 1
        else:
            return active_bank   