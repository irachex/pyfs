import sys
import struct

import segment
import disk
from inode import Inode
import inodemap
from fileobj import File, Directory
from config import FILENAMELEN

def find_parent(path):
    parent, sep, element = path.rpartition("/")
    if parent == "":
        parent = "/"
    return parent

def find_filename(path):
    parent, sep, element = path.rpartition("/")
    return element
    
def get_path_components(path):
    for component in path[1:].strip().split("/"):
        yield component
        

class PFS(object):
    def __init__(self, init=True):
        pass
    
    def open(self, path, isdir=False):
        inode_no = self.search_dir(path)
        if inode_no is None:
            raise Exception("path does not exist")
        if isdir:
            return Directory(inode_no)
        else:
            return File(inode_no)
    
    def create(self, filename, isdir=False):
        inode_no = self.search_dir(filename)
        if inode_no is not None:
            raise Exception("file already exists")
        
        inode = Inode(isdir=isdir)
        
        parent_dir = find_parent(filename)
        parent_inode_no = self.search_dir(parent_dir)
        if parent_inode_no is None:
            raise Exception("parent direntory does not exist")
        parent_inode_block = inodemap.inodemap.lookup(parent_inode_no)
        parent_inode = Inode(data=segment.segman.block_read(parent_inode_block))
        self.append_entry(parent_inode, find_filename(filename), inode)
        
        if isdir:
            return Directory(inode.id)
        else:
            return File(inode.id)
    
    def stat(self, filename):
        inode_no = self.search_dir(filename)
        if inode_no is None:
            raise Exception("file or directory does not exist")
        inode_block = inodemap.inodemap.lookup(inode_no)
        inode = Inode(data=segment.segman.block_read(inode_block))
        return inode.filesize, inode.isdir
    
    def unlink(self, path):
        filename = find_filename(path)
        parent_inode_no = self.search_dir(find_parent(path))
        parent_inode_block = inodemap.inodemap.lookup(parent_inode_no)
        parent_inode = Inode(data=segment.segman.block_read(parent_inode_block))
        parent_old_size = parent_inode.filesize
        parent_dir = Directory(parent_inode_no)
        found_entry = False
        entries = []
        for (name, inode) in parent_dir.enumerate():
            if found_entry:
                entries.append( (name, inode) )
            if name == filename:
                fount = True
                position = parent_dir.position - (FILENAMELEN +4)
        for (name, inode) in entries:
            parent_inode.write(position, struct.pack("%dsI" % FILENAMELEN, name, inode))
            position += (FILENAMELEN +4)
        parent_inode.filesize = parent_old_size - (FILENAMELEN + 4)
        inodemap.inodemap.update_inode(parent_inode_no, parent_inode.serialize())
        
    def sync(self):
        (serialized, imap_num) = inodemap.inodemap.save_inode_map(get_max_inode())
        special_inode = Inode()
        special_inode.write(0, serialized)
        imap_loc = inodemap.inodemap.lookup(special_inode.id)
        segment.segman.update_imap_postion(imap_loc, imap_num)
        segment.segman.flush()
    
    def restore(self):
        imap_loc = segment.segman.locate_lastest_imap()
        iminode = Inode(data = disk.disk.block_read(imap_loc))
        imdata = iminode.read(0, 10000000)
        set_max_inode(inodemap.inodemap.restore_imap(imdata))
    
    def search_dir(self, path):
        #print map(ord, path)
        path = path.strip()
        if path=="/":
            return 1
        current_dir = Directory(1)
        stack = path.split("/")[1:]
        stack.reverse()
        while True:
            name = stack.pop()
            found = False
            for (n, inode) in current_dir.enumerate():
                if n == name:
                    found = True
                    break
            if found:
                if len(stack) == 0:
                    return inode
                else:
                    current_dir = Directory(inode)
            else:
                return None
    
    def append_entry(self, dir_inode, filename, inode):
        dir_inode.write(dir_inode.filesize, struct.pack("%dsI" % FILENAMELEN, filename, inode.id))


fs = None
        