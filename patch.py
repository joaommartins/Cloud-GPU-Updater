import os
import sys
import shutil
import struct
import subprocess


BK_EXT = '.ori'
PREV_EXT = '.prev'
SRV = 'NvStreamUserAgent.exe'
SERVICE = 'NvStreamSvc'
TARGET_DEVID = 0x118A # Manual, for K520 (g2.2xlarge)
N_MATCHES = 2

def search(f, s, bs=4096):
    slen = len(s)
    slenm = slen-1
    
    off = 0
    offs = []
    
    b0 = f.read(bs)
    
    while True:
        b1 = f.read(bs)
        
        b = b0 + b1[:slenm]
        
        idx = 0
        while True:
            idx = b.find(s, idx)
            if idx < 0:
                break
            offs.append(off + idx)
            idx += slen
        
        off += len(b0)
        b0 = b1
        if not b0:
            break
            
    return offs


def main():
    s = struct.pack('@q', TARGET_DEVID)
    assert len(s) == 8
    
    if len(sys.argv) != 2:
        print "Usage: %s DEVID" % sys.argv[0]
        print "Will just search for target devid"
    else:
        print "Searching for target devid"
        try:
            devid = int(sys.argv[1], 16)
        except ValueError:
            print "Invalid devid"
            return
    
    
    BK_SRV = SRV + BK_EXT
    PREV_SRV = SRV + PREV_EXT
    
    use_bk = False
    offs = []
    for fname in (SRV, BK_SRV):
        if not os.path.isfile(fname):
            break
            
        print "Searching in %s" % fname
        with open(fname, 'rb') as f:
            offs = search(f, s)
        
        print "Found %d matches (%d expected)" % (len(offs), N_MATCHES)
        if len(offs) != N_MATCHES:
            continue
        
        use_bk = True
        
    if len(offs) != N_MATCHES:
        return
    
    if len(sys.argv) != 2:
        return
    
    r = struct.pack('@q', devid)
    assert len(r) == len(s)
    
    
    print "Stopping service"
    subprocess.call("net stop %s" % SERVICE) 
    
    
    if not os.path.isfile(BK_SRV):
        print "Making backup of %s in %s" % (SRV, BK_SRV)
        shutil.copy(SRV, BK_SRV)
    else:
        if os.path.isfile(PREV_SRV):
            os.remove(PREV_SRV)
            
        if use_bk:
            print "Using backup %s" % BK_SRV
            os.rename(SRV, PREV_SRV)
            shutil.copy(BK_SRV, SRV)
        else:
            print "Making backup of %s in %s" % (SRV, PREV_SRV)
            shutil.copy(SRV, PREV_SRV)
            

    
    print "Modifying file"
    with open(SRV, 'r+b') as f:
        for off in offs:
            f.seek(off)
            f.write(r)
    
    print "Starting service"
    subprocess.call("net start %s" % SERVICE)
    
    print "Done"
    

if __name__ == '__main__':
    main()
