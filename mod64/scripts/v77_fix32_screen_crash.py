#!/usr/bin/env python3
# v77 32-bit crash fix: neutralize the desktop-only GLView getters in the stock
# armeabi-v7a libMyGame.so.
#
# Crash (user report, v77): SIGILL at agtk::GetScreenResolutionSize+0x5b called
# from agtk::Scene::start. Root cause: the stock 32-bit engine kept the desktop
# window-resolution code that our arm64 build removes via the v34 source patch
# (`#if ... && !defined(__ANDROID__)` in Scene.cpp). On Android the real GLView
# is NOT an IMGUIGLViewImpl, so `static_cast<IMGUIGLViewImpl*>(glview)` yields a
# bogus pointer; GetScreenResolutionSize reads garbage vtable ptr at [x+140],
# survives via a debug-printf branch, then GetFrameSize (next call in the same
# Scene::start block) does `blx r1` through the garbage slot -> illegal
# instruction whose PC lands inside GetScreenResolutionSize+0x5b (data
# executed as code, PC between the two symbols). The porter already stubbed
# IsFullScreen/ChangeScreen/RestoreScreen/FocusWindow to `bx lr` in the stock
# lib but left both size getters live.
#
# Fix: overwrite both functions with a 22-byte Thumb-2 stub implementing the
# REAL calling convention discovered from the disassembly: Scene::start calls
# these with a hidden sret pointer in r0 (`add r0, sp, #36; blx
# GetScreenResolutionSize` at 0x8613cc) because cocos2d::Size has a non-trivial
# copy ctor (AAPCS: always sret on this ABI; both originals discard r0 as the
# hidden pointer). The stub writes Size{1024.0f, 768.0f} (the project design
# resolution, ProjectData screenWidth/screenHeight) through the sret pointer
# and returns it (r0 unchanged). Fits inside each function's original
# footprint (GetScreenResolutionSize: 0x50 to its successor; GetFrameSize:
# 0x30+ to the next symbol). Idempotent via prologue signature check.
#
# Usage: python3 v77_fix32_screen_crash.py <libMyGame.so> [--write]
import struct, sys

path = sys.argv[1]
WRITE = "--write" in sys.argv
d = bytearray(open(path, "rb").read())

# Thumb-2 (NDK-verified encoding): movw r1,#0 / movt r1,#0x4480 /
# movw r2,#0 / movt r2,#0x4440 / str r1,[r0] / str r2,[r0,#4] / bx lr
#   r0 = sret ptr in, returned as-is
# (0x44800000 = 1024.0f, 0x44400000 = 768.0f)
STUB = bytes.fromhex("40f20001c4f2804140f20002c4f24042016042607047")
assert len(STUB) == 22


def file_offset(vaddr):
    e_phoff = struct.unpack_from("<I", d, 0x1C)[0]
    e_phentsize = struct.unpack_from("<H", d, 0x2A)[0]
    e_phnum = struct.unpack_from("<H", d, 0x2C)[0]
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type, p_offset, p_vaddr = struct.unpack_from("<III", d, off)
        p_filesz = struct.unpack_from("<I", d, off + 0x10)[0]
        if p_type == 1 and p_vaddr <= vaddr < p_vaddr + p_filesz:
            return p_offset + (vaddr - p_vaddr)
    raise AssertionError(f"vaddr {vaddr:#x} not in any PT_LOAD")


SYMS = {
    "GetScreenResolutionSize": (0x0088B338, b"\xbc\xb5\x04\xaf"),
    "GetFrameSize": (0x0088B388, b"\xbc\xb5\x04\xaf"),
}

for name, (vaddr, magic) in SYMS.items():
    off = file_offset(vaddr)
    cur = bytes(d[off:off + len(STUB)])
    if cur.startswith(STUB[:8]):
        print(f"{name}: already patched, skipping")
        continue
    assert cur.startswith(magic), f"{name}: unexpected prologue {cur[:4].hex()}"
    if WRITE:
        d[off:off + len(STUB)] = STUB
        print(f"{name}: patched at file offset {off:#x} (vaddr {vaddr:#x})")
    else:
        print(f"{name}: would patch at file offset {off:#x} (vaddr {vaddr:#x})")

if WRITE:
    open(path, "wb").write(d)
    print("written:", path)
else:
    print("dry run: no changes written (pass --write)")
