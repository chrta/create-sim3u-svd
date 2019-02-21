#!/bin/env python3


class RegisterBits:
    def __init__(self, offset, width, name):
        self.offset = offset
        self.width = width
        self.name = name
        self.function = ""

class Register:
    def __init__(self, name, title, address, has_set=False, has_clr=False, has_msk=False):
        self.name = name
        self.title = title
        self.description = None
        self.address = address
        self.has_set = has_set
        self.has_clr = has_clr
        self.has_msk = has_msk
        self.bits = None

    def set_bits(self, bits):
        self.bits = bits

    def add_bit_info(self, bit_index, name, function):
        self.bits.add_bit_info(bit_index, name, function)
        
    def __str__(self):
        return "Register {0}\t\t {1:#010X}\t{2} {3} {4}\n\t\t{5}\n".format(self.name, self.address, self.has_set, self.has_clr, self.has_msk, self.bits)

class RegisterBitTableEntry:
    def __init__(self, column):
        self.column = column
        self.bits = []
        self.name = ""
        self.access = ""
        self.reset = []
        self.function = ""
        self._parse_column()

    def _parse_column(self):
        if len(self.column[0]):
            self.bits = [int(x) for x in self.column[0].split()]
        if len(self.column[1]):
            self.name = self.column[1]
        if len(self.column[2]):
            self.access = self.column[2]
        if len(self.column[3]):
            # handle reset value X as 0
            f = lambda x: 0 if x == 'X' else int(x)
            self.reset = [f(x) for x in self.column[3].split()]
        if '[' in self.name:
            #remove the bit range from the name, e.g. DATA[31:16]
            self.name = self.name.split('[')[0]
            
    def merge(self, entry):
        self.bits.extend(entry.bits)
        if len(entry.name) and (self.name != entry.name):
            raise Exception("Merging with sth that has a different name!!")
        if self.access and entry.access and (self.access != entry.access):
            print("")
            print(self)
            raise Exception("Merging {} '{}' with sth that has a different access {} vs {}!!".format(self.name, self.bits, self.access, entry.access))
        if not self.access:
            self.access = entry.access
        self.reset.extend(entry.reset)

    def move_bits_to(self, to_entry):
        to_entry.name = self.name
        keep_bits = self.bits[:len(self.reset)]
        to_entry.bits = self.bits[len(self.reset):]
        self.bits = keep_bits
        
    def verify(self):
        if not self.bits:
            raise Exception("No bits are defined")
        if len(self.bits) != len(self.reset):
            raise Exception("Length of bits and reset values do not match")
        if not self.access:
            raise Exception("No access specified")
        if not self.name:
            raise Exception("No name given")

    def is_entry(self, bits, name):
        if not set(self.bits) <= set(bits):
            return False
        if self.name != name:
            print("Bits match, but name does not: {} vs {}".format(self.name, name))
            return False
        return True

    def add_info(self, function):
        self.function = function
    
    def __str__(self):
        bits = ",".join(map(str, self.bits))
        reset = ",".join(map(str, self.reset))
        return """Register Bits: {}
    Name: {}
    Access: {}
    Reset: {}
    Function: {}
        """.format(bits, self.name, self.access, reset, self.function)

    def __repr__(self):
        return self.__str__()

class RegisterBitTableEntryCollection:
    def __init__(self):
        self.entries = []

    def _merge_with_last(self, entry):
        if not self.entries:
            self.entries.append(entry)
            return True

        if len(entry.name) and (entry.name != self.entries[-1].name):
            return False

        if len(entry.access) and (entry.access != self.entries[-1].access):
            return False

        self.entries[-1].merge(entry)
        return True

    def _should_distribute_bits(self):
        if self.entries[-1].name:
            return False
        if self.entries[-2].name != 'Reserved':
            return False
        return True

    def _distribute_bits(self):
        self.entries[-2].move_bits_to(self.entries[-1])
    
    def append(self, entry):
        if not self.entries:
            self.entries.append(entry)
            return

        if not self._merge_with_last(entry):
            self.entries.append(entry)
            if self._should_distribute_bits():
                self._distribute_bits()

    def verify(self):
        for e in self.entries:
            try:
                e.verify()
            except:
                print(e)
                print("----")
                print(self)
                raise

    def add_bit_info(self, bit_index, name, function):
        #print(self)
        #print("Add bit info for {}".format(bit_index))
        #print("  Name {}".format(name))
        #print("  Function {}\n\n".format(function))
        found = False
        for e in self.entries:
            if e.is_entry(bit_index, name):
                e.add_info(function)
                found = True
        if found:
            return
        print(self)
        print("Add bit info for {}".format(bit_index))
        print("  Name {}".format(name))
        print("  Function {}\n\n".format(function))
        raise Exception("Bit not found!!")

    
    def __str__(self):
        entries = "\n\t".join(map(str, self.entries))
        return """RegisterBitTableEntryCollection:
   len: {}
   Entries:
   {}
""".format(len(self.entries), entries)
