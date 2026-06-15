import struct, sys
SRC="mfx/AndroidManifest.xml"; OUT="mfx/AndroidManifest_patched.xml"
NEW_TARGET=30
TARGETSDK_RESID=0x01010270
MINSDK_RESID=0x0101020c
data=bytearray(open(SRC,'rb').read())
# top-level: type(2) headerSize(2) size(4)
assert struct.unpack_from('<H',data,0)[0]==0x0003, "not AXML"
pos=8
resmap=None
patched=[]
def u16(o): return struct.unpack_from('<H',data,o)[0]
def u32(o): return struct.unpack_from('<I',data,o)[0]
filesize=u32(4)
while pos < filesize:
    ctype=u16(pos); chsize=u32(pos+4)
    if ctype==0x0180:  # RESOURCE_MAP
        n=(chsize-8)//4
        resmap=[u32(pos+8+i*4) for i in range(n)]
    elif ctype==0x0102:  # START_ELEMENT
        attrStart=u16(pos+8+12)  # after line(4)+comment(4)+ns(4)
        attrCount=u16(pos+8+16)
        base=pos+8+8+attrStart  # element body starts at pos+8+? -> compute carefully
        # START_ELEMENT body: line(4) comment(4) ns(4) name(4) attrStart(2) attrSize(2) attrCount(2) idIdx(2) classIdx(2) styleIdx(2)
        body=pos+8
        attrStart=u16(body+16); attrSize=u16(body+18); attrCount=u16(body+20)
        attrs_off=body+8+attrStart
        for i in range(attrCount):
            a=attrs_off+i*20
            name_idx=u32(a+4)
            data_off=a+16
            val=u32(data_off)
            resid=resmap[name_idx] if (resmap and name_idx < len(resmap)) else None
            if resid==TARGETSDK_RESID:
                struct.pack_into('<I',data,data_off,NEW_TARGET)
                patched.append(('targetSdkVersion',val,NEW_TARGET))
    pos+=chsize
open(OUT,'wb').write(data)
print("patched:",patched)
