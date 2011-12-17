import os
import sys
import struct

import disk
from config import BLOCKSIZE, DISKSIZE, SEGMENTSIZE, NUMSEGMENTS

NUMBLOCKS = SEGMENTSIZE - 1 # one less than SEGMENTSIZE because of the superblock

class SuperBlock:
    def __init__(self, data=None):
        if data is None:
            self.block_in_use = [False]*(NUMBLOCKS)
            self.imap_num = -1
            self.imap = -1
        else:
            self.block_in_use = [struct.unpack("?", data[i])[0] for i in range(NUMBLOCKS)]
            self.imap_num = struct.unpack('I', data[NUMBLOCKS:NUMBLOCKS+4])[0]
            self.imap = struct.unpack('I', data[NUMBLOCKS+4:NUMBLOCKS+8])[0]
    
    def serialize(self):
        st = "".join([struct.pack('?', self.block_in_use[i]) for i in range(NUMBLOCKS)])
        st += struct.pack("II", self.imap_num, self.imap)
        return st
    
    def update_imap_position(self, imap, imap_num):
        self.imap_num = imap_num
        self.imap = imap
        
        
class Segment(object):
    def __init__(self, no):
        self.base = no * SEGMENTSIZE
        self.superblock = SuperBlock(data=disk.disk.block_read(self.base))
        self.blocks = [disk.disk.block_read(i) for i in range(self.base+1, self.base+1+NUMBLOCKS)]
    
    def write_new_block(self, data):
        for i in range(NUMBLOCKS):
            if not self.superblock.block_in_use[i]:
                if len(data) > BLOCKSIZE:
                    print "Assertion error 2: data being written to segment is not the right size (%d != %d)" % (len(data), len(self.blocks[i]))
                    print data
                    os._exit(1)
                self.blocks[i] = data + self.blocks[i][len(data):]
                self.superblock.block_in_use[i] = True
                return i+1
        return -1
    
    def flush(self):
        disk.disk.block_write(self.base, self.superblock.serialize())
        for i in range(NUMBLOCKS):
            disk.disk.block_write(self.base+1+i, self.blocks[i])


class SegmentManager(object):
    def __init__(self):
        self.seg_cnt = 0
        self.current_seg = Segment(self.seg_cnt)
    
    def write_new_block(self, data):
        block_no = self.current_seg.write_new_block(data)
        if block_no == -1:
            self.flush()
            for i in range((self.seg_cnt+1)%NUMSEGMENTS, NUMSEGMENTS):
                self.current_seg = Segment(i)
                block_no = self.current_seg.write_new_block(data)
                if block_no != -1:
                    self.seg_cnt = i
                    break
            if block_no == -1:
                raise Exception()
        return self.current_seg.base + block_no
        
    def block_read(self, no):
        if self.is_in_memory(no):
            return self.read_in_place(no)
        else:
            return disk.disk.block_read(no)
    
    def block_write(self, no, data):
        if self.is_in_memory(no):
            self.update_in_place(no, data)
        else:
            disk.disk.block_write(no, data)
    
    def is_in_memory(self, block_no):
        return block_no >= self.current_seg.base and block_no < (self.current_seg.base + SEGMENTSIZE)
    
    def update_in_place(self, block_no, data):
        block_offset = block_no - 1 - self.current_seg.base
        if len(data) != len(self.current_seg.blocks[blockoffset]):
            print "Assertion error 1: data being written to segment is not the right size (%d != %d)" % (len(data), len(self.current_seg.blocks[block_offset]))
    
    def read_in_place(self, block_no):
        block_offset = block_no - 1 - self.current_seg.base
        return self.current_seg.blocks[block_offset]
    
    def update_imap_position(self, imap, imap_num):
        self.current_seg.siperblock.update_imap_position(imap, imap_num)
    
    def flush(self):
        self.current_seg.flush()
    
    def locate_latest_imap(self):
        max_num = -1
        imap = -1
        for seg_no in range(NUMSEGMENTS):
            superblock = SuperBlock(data=disk.disk.block_read(seg_no*SEGMENTSIZE))
            if superblock.imap_num>0 and superblock.imap_num > max_num:
                max_num = superblock.imap_num
                imap = superblock.imap
        return imap
        

segman = None
        
        