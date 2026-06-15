import struct
data=open("mfx/AndroidManifest.xml","rb").read()
def u16(o): return struct.unpack_from('<H',data,o)[0]
def u32(o): return struct.unpack_from('<I',data,o)[0]
filesize=u32(4); pos=8; resmap=None; spool=None
# parse string pool to resolve names (for debugging)
while pos<filesize:
    ctype=u16(pos); hsize=u16(pos+2); chsize=u32(pos+4)
    if ctype==0x0180:
        n=(chsize-8)//4
        resmap=[u32(pos+8+i*4) for i in range(n)]
        print("RESMAP count",n, [hex(x) for x in resmap[:25]])
    elif ctype==0x0102:
        body=pos+8
        ns=u32(body+8); name=u32(body+12)
        attrStart=u16(body+16); attrCount=u16(body+20)
        attrs_off=body+8+attrStart
        print("START elem name_idx",name,"attrCount",attrCount)
        for i in range(attrCount):
            a=attrs_off+i*20
            name_idx=u32(a+4); dtype=data[a+15]; val=u32(a+16)
            resid=resmap[name_idx] if (resmap and name_idx<len(resmap)) else None
            print("   attr name_idx",name_idx,"resid",hex(resid) if resid else None,"dtype",dtype,"val",val)
    pos+=chsize
