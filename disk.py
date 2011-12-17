import os
import struct
from config import DISKNAME, DISKSIZE, BLOCKSIZE

class Disk(object):
    def __init__(self, brandnew=True):
        if brandnew:
            if os.path.isfile(DISKNAME):
                print "Deleting old disk..."
                os.remove(DISKNAME)
            self.format()
            self.disk = open(DISKNAME, "rb+")
    
    def format(self):
        print "Formating the disk..."
        self.disk = open(DISKNAME, "wb")
        self.disk.write(struct.pack("B", 0) * DISKSIZE)
        self.disk.close()
    
    def block_write(self, no, data):
        if no > self.number_of_blocks:
            raise Exception("block out of bound")
        if len(data)>BLOCKSIZE:
            raise Exception("data exceeds size of block")
        self.disk.seek(no*BLOCKSIZE, 0)
        self.disk.write(data)
        self.disk.flush()
        return 0
    
    def block_read(self, no):
        if no > self.number_of_blocks:
            raise Exception("block out of bound")
        self.disk.seek(no*BLOCKSIZE, 0)
        return self.disk.read(BLOCKSIZE)
    
    @property
    def block_size(self):
        return BLOCKSIZE
        
    @property    
    def capacity(self):
        return DISKSIZE
    
    @property    
    def number_of_blocks(self):
        return DISKSIZE/BLOCKSIZE


disk = None