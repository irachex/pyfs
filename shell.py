import os
import sys

import disk
import segment
import inodemap
import inode
import pfs

def canonicalize(path, curdir):
    if path == "":
        return curdir
    elif path[0] != "/":
        return "%s%s%s" % (curdir, "/" if curdir[-1:]!="/" else "", path)
    else:
        return path
    

class Shell(object):
    def __init__(self):
        self.current_dir = "/"
    
    def help(self, args):
        pass
    
    def mkfs(self, args):
        """usage: mkfs [-r]"""
        brandnew = True
        if len(args)>1:
            if args[1] == "-r":
                brandnew = False
            else:
                print self.mkfs.__doc__
                return
        disk.disk = disk.Disk(brandnew=brandnew)
        segment.segman = segment.SegmentManager()
        inodemap.inodemap = inodemap.InodeMap()
        pfs.fs = pfs.PFS(init=brandnew)
        if brandnew:
            root_inode = inode.Inode(isdir=True)
        else:
            pfs.fs.restore()        
        
    def touch(self, args):
        """usage: touch filename length"""
        fd = pfs.fs.create(canonicalize(args[1], self.current_dir))
        if len(args)<3:
            args.append(100)
        fd.write(" "*int(args[2]))
        fd.close()
    
    def ls(self, args):
        path = canonicalize(args[1] if len(args)>1 else "", self.current_dir)
        dd = pfs.fs.open(path, isdir=True)
        print "name\tinode\ttype\tsize"
        for name, inode in dd.enumerate():
            size, isdir = pfs.fs.stat("%s%s%s" % (path, "/" if path[-1:]!="/" else "", name))
            print "%s\t%d\t%s\t%d" %(name, inode, "dir" if isdir else "file", size)
    
    def cat(self, args):
        fd = pfs.fs.open(canonicalize(args[1], self.current_dir))
        data = fd.read(50000000)
        print data
        fd.close()
    
    def write(self, args):
        """"usage: write filename data"""
        fd = pfs.fs.open(canonicalize(args[1], self.current_dir))
        fd.write(args[2])
        fd.close()
        
    def mkdir(self, args):
        pfs.fs.create(canonicalize(args[1], self.current_dir), isdir=True)
    
    def cd(self, args):
        """usage: cd dirname"""
        dirname = canonicalize(args[1], self.current_dir)
        size, isdir = pfs.fs.stat(dirname)
        if isdir:
            self.current_dir = dirname
        else:
            raise Exception("not a directory")
    
    def sync(self, args):
        pfs.fs.sync()
    
    def rm(self, args):
        """usage: rm path"""
        path = canonicalize(args[1], self.current_dir)
        size, isdir = pfs.fs.stat(path)
        if isdir:
            raise Exception("rm: cannot remove '%s': is a directory, use rmdir instead" % path)
        else:
            pfs.fs.unlink(path)
    
    def rmdir(self, args):
        path = canonicalize(args[1], self.current_dir)
        size, isdir = pfs.fs.stat(path)
        if isdir:
            if size>0:
                raise Exception("rmdir: failed to remove '%s': directory not empty" % path)
            else:
                pfs.fs.unlink(path)
        else:
            raise Exception("rmdir: can not remove '%s': is a file, use rm instead" % path)
    
    def quit(self, args=None):
        print "\nbye.\n"
        os._exit(0)
    
    def exit(self, args=None):
        self.quit(args)


shell = Shell()

def main():
    while True:
        try:
    	    cmd = raw_input("[ifs] " + shell.current_dir + ">")
    	    cmd = cmd.strip()
    	except EOFError:
    	    shell.exit()
    	pieces = cmd.split(" ")

    	try:
    	    func = getattr(shell, pieces[0])
    	except AttributeError:
    	    print "type \"help\" for usage"

    	try:
            func(pieces)
    	except Exception, e:
    	    print "Error: %s" % e
    	    

if __name__ == "__main__":
	main()