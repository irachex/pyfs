import math
import struct

import segment
import inodemap
from config import BLOCKSIZE

NUMDIRECTBLOCKS = 100 # can have as many as 252 and still fit an Inode in a 1024 byte block
inodeidpool = 1  # 1 is reserved for the root inode

def get_max_inode():
    global inodeidpool
    return inodeidpool

def set_max_inode(maxi):
    global inodeidpool
    inodeidpool = maxi

class Inode(object):
    def __init__(self, data=None, isdir=False):
        global inodeidpool
        if data is not None:
            self.id = struct.unpack("I", data[:4])[0]
            self.filesize = struct.unpack("I", data[4:8])[0]
            self.fileblocks = [struct.unpack("I", data[8+i*4:12+i*4])[0] for i in range(NUMDIRECTBLOCKS)]
            self.indirectblock = struct.unpack("I", data[8+4*NUMDIRECTBLOCKS:12+4*NUMDIRECTBLOCKS])[0]
            self.isdir = struct.unpack("?", data[12+4*NUMDIRECTBLOCKS])[0]
        else:
            self.id = inodeidpool
            inodeidpool += 1
            self.filesize = 0
            self.fileblocks = [0]*NUMDIRECTBLOCKS
            self.indirectblock = 0
            self.isdir = isdir
            inodemap.inodemap.update_inode(self.id, self.serialize())
    
    def serialize(self):
        st = struct.pack("I", self.id) + struct.pack("I", self.filesize)
        st += "".join([struct.pack("I", self.fileblocks[i]) for i in range(NUMDIRECTBLOCKS)])
        st += struct.pack("I", self.indirectblock) + struct.pack("?", self.isdir)
        return st
    
    def load_indirect_block(self):
        if self.indirectblock == 0:
            address_data = "".join([struct.pack("I", 0) for i in range(BLOCKSIZE/4)])
        else:
            address_data = segment.segman.block_read(self.indirectblock)
        addresses = [struct.unpack("I", address_data[i*4:i*4+4])[0] for i in range(BLOCKSIZE/4)]
        return addresses
    
    def save_indirect_block(self, addresses):
        address_data = "".join([struct.pack("I", addresses[i]) for i in range(BLOCKSIZE/4)])
        self.indirectblock = segment.segman.write_new_block(address_data)
    
    def add_data_block(self, offset, address):
        if offset < len(self.fileblocks):
            self.fileblocks[offset] = address
        else:
            addresses = self.load_indirect_block()
            addresses[offset - len(self.fileblocks)] = address
            self.save_indirect_block(addresses)
        
    def data_block_exists(self, offset):
        if offset < len(self.fileblocks):
            return self.fileblocks[offset] != 0
        else:
            addresses = self.load_indirect_block()
            return addresses[offset - len(self.fileblocks)] != 0
    
    def get_data_block(self, offset):
        if offset < len(self.fileblocks):
            block_no = self.fileblocks[offset]
        else:
            addresses = self.load_indirect_block()
            block_no = addresses[offset - len(self.fileblocks)]
        return segment.segman.block_read(block_no)
    
    def read(self, offset, length):
        current_block = int(math.floor(float(offset)/BLOCKSIZE))
        inblockoffset = offset % BLOCKSIZE
        amount_to_read = min(length, self.filesize - offset)
        more_to_read = amount_to_read
        data = ""
        while more_to_read > 0:
            content = self.get_data_block(current_block)
            new_data = content[inblockoffset:]
            inblockoffset = 0
            more_to_read -= len(new_data)
            data += new_data
            current_block += 1
        return data[0:min(len(data), amount_to_read)]
    
    def write(self, offset, data, skip_inodemap_update=False):
        size = len(data)
        current_block = int(math.floor(float(offset)/BLOCKSIZE))
        inblockoffset = offset % BLOCKSIZE
        more_to_write = size
        while more_to_write > 0:
            if self.data_block_exists(current_block):
                old_data = self.get_data_block(current_block)
                new_data = old_data[:inblockoffset] +  data[:(BLOCKSIZE - inblockoffset)] + old_data[inblockoffset+len(data):]
            else:
                new_data = data[:BLOCKSIZE]
            data_block = segment.segman.write_new_block(new_data)
            self.add_data_block(current_block, data_block)
            more_to_write -= (BLOCKSIZE-inblockoffset)
            data = data[(BLOCKSIZE-inblockoffset):]
            inblockoffset = 0
            current_block += 1
        self.filesize = max(self.filesize, offset+size)
        if not skip_inodemap_update:
            inodemap.inodemap.update_inode(self.id, self.serialize())
            
                