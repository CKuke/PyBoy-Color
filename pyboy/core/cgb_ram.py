
import array
from base_ram import RAM

class CgbRam(RAM):
    def __init__(self, random=False):
        super().__init__(random)

        # Initialize CGB 8 WRAM banks
        for i in range(6):
            self.wram.append(array.array("B", [0]*4096))
        
    
    def __read_wram(self, addr):
        if 0xC000 <= addr and addr < 0xD000:
            return self.wram[0][addr]
        else:
            # Read which bank to read from at FF70
            io_offset = 0xFF00
            bank_addr = 0xFF70 - io_offset
            bank = self.__read_io(bank_addr)
            if bank > 0x07:
                bank = 0x01
            return self.wram[bank][addr]
    
    def __write_wram(self, addr, val):
        if 0xC000 <= addr and addr < 0xD000:
            self.wram[0][addr] = val
        else:
            # Read which bank to read from at FF70
            io_offset = 0xFF00
            bank_addr = 0xFF70 - io_offset
            bank = self.__read_io(bank_addr)
            if bank > 0x07:
                bank = 0x01
            self.wram[bank][addr] = val
        

# TODO: Delete all below when finished testing
# ram = CgbRam()
# print(len(ram.wram))
# for i in range(len(ram.wram)):
#     print(len(ram.wram[i]))

# print("----------------------")
# print(ram.read(0xffff))


        