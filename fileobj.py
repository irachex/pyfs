import struct 

import inodemap
import segment
from inode import Inode
from config import FILENAMELEN, MAXFILESIZE

class File(object):
    def __init__(self, inode_no):
        self.inode_no = inode_no
        self.position = 0
        self.isopen = True
    
    def close(self):
        if not self.isopen:
            raise Exception("the file is already closed")
        self.isopen = False
    
    def get_inode(self):
        inode_block_no = inodemap.inodemap.lookup(self.inode_no)
        #print inode_block_no
        inode = Inode(data = segment.segman.block_read(inode_block_no))
        return inode
    
    def length(self):
        inode = self.get_inode()
        return inode.filesize
    
    def read(self, length):
        inode = self.get_inode()
        data = inode.read(self.position, length)
        self.position += len(data)
        return data
    
    def write(self, data):
        if self.position + len(data) > MAXFILESIZE:
            raise Exception("exceeded maximun file size")
        inode = self.get_inode()
        inode.write(self.position, data)
        self.position += len(data)
    

class Directory(File):
    def __init__(self, inode_no):
        super(Directory, self).__init__(inode_no)
        inode = self.get_inode()
        if not inode.isdir:
            raise Exception("not a directory - inode %d" % inode_no)
    
    def enumerate(self):
        length = self.length()
        # a directory entry is a filename and an integer for the inode number
        numentries = length / (FILENAMELEN + 4)
        for i in range(numentries):
            data = self.read(FILENAMELEN + 4)
            name, inode = struct.unpack("%dsI" % (FILENAMELEN,), data[:(FILENAMELEN+4)])
            name = name.strip("\x00")
            yield name, inode

