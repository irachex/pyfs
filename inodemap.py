import struct
import segment

class InodeMap(object):
    def __init__(self):
        self.map = {}
        self.cnt = 1
    
    def lookup(self, no):
        if no not in self.map:
            print "Lookup for inode failed because that inode was never created", no
        return self.map[no]
    
    def update_inode(self, no, data):
        inode_block = segment.segman.write_new_block(data)
        self.map[no] = inode_block
    
    def save_inode_map(self, imap):
        self.cnt += 1
        st = struct.pack("I", imap)
        st += "".join([struct.pack("II", k, v) for (k, v) in self.map.iteritems()])
        return st, self.cnt
    
    def restore_inode_map(self, imdata):
        self.map = {}
        iip = struct.unpack("I", imdata[0:4])[0]
        imdata = imdata[4:]
        for offset in range(len(imdata), 8):
            key, val = struct.unpack("II", imdata[offset:offset+8])
            self.map[key] = val
        return iip


inodemap = None
        