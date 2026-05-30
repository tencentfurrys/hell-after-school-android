#!/usr/bin/env python3
"""Apply the Hell After School v72L cumulative patch set to libMyGame.so.

Spec: docs/port-knowledge/02-binary-patches.md

Reads `libMyGame.so` (must be the armeabi-v7a flavor from Hot Dog King's
v71 APK), locates each target function via the `.dynsym` table, and
writes the patched bytes at each thumb-mode entry point.

Usage:
    python3 patch_libmygame.py path/to/libMyGame.so -o patched.so
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from elftools.elf.elffile import ELFFile
except ImportError:
    sys.exit("pip install pyelftools")


# Mangled symbol -> (description, patch_bytes_or_callable)
# patch_bytes is what we write at the function's thumb entry point.
# If the value is a callable, it receives the file bytes (mutable) and
# the function's thumb-stripped offset and is responsible for writing.
PATCHES = {
    # #1 - RenderTextureCtrl::isUseShader -> always false
    "_ZN4agtk17RenderTextureCtrl12isUseShaderEv": (
        "RT-shader kill: return false unconditionally",
        bytes([0x00, 0x20, 0x70, 0x47]),  # movs r0,#0 ; bx lr
    ),
    # #2 - SceneLayer::createRenderTexture -> no-op
    "_ZN4agtk10SceneLayer19createRenderTextureEv": (
        "Skip layer RT alloc (~60 MB saved on Tutorial)",
        bytes([0x70, 0x47]),  # bx lr
    ),
    # #3 - Scene::setShader -> patch nop at func+0x108
    # Special case: not at offset 0
    # Mangled name varies by overload; pick the one matching v71's binary.
    # We use the overload taking (ShaderKind, float) which is the one
    # ObjectAction::execActionSceneEffect calls.
    "_ZN4agtk5Scene9setShaderENS_6Shader10ShaderKindEf": (
        "nop the cbz r0 at +0x108 to skip null-controller create branch",
        None,  # special-case below
    ),
    # #4 - TouchGamepad::drawGamepad -> tail-call setVisible(false)
    "_ZN4agtk12TouchGamepad12drawGamepadEv": (
        "Hide TouchGamepad node tree by tail-calling setVisible(false)",
        None,  # special-case below (needs BL operand to setVisible)
    ),
    # #5 - TouchGamepad::drawButtons -> bx lr
    "_ZN4agtk12TouchGamepad11drawButtonsEv": (
        "TouchGamepad drawButtons no-op",
        bytes([0x70, 0x47]),
    ),
    # #6 - TouchGamepad::onTouchBegan -> return false
    "_ZN4agtk12TouchGamepad12onTouchBeganEPN7cocos2d5TouchEPNS1_5EventE": (
        "TouchGamepad onTouchBegan returns false",
        bytes([0x00, 0x20, 0x70, 0x47]),
    ),
    # #7 - TouchGamepad::onTouchMoved -> bx lr
    "_ZN4agtk12TouchGamepad12onTouchMovedEPN7cocos2d5TouchEPNS1_5EventE": (
        "TouchGamepad onTouchMoved no-op",
        bytes([0x70, 0x47]),
    ),
    # #8 - TouchGamepad::onTouchEnded -> bx lr
    "_ZN4agtk12TouchGamepad12onTouchEndedEPN7cocos2d5TouchEPNS1_5EventE": (
        "TouchGamepad onTouchEnded no-op",
        bytes([0x70, 0x47]),
    ),
}


def find_symbols(elf_path: Path) -> dict[str, int]:
    """Return {mangled_name: file_offset_stripped_of_thumb_bit}."""
    found: dict[str, int] = {}
    with elf_path.open("rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if section.name not in (".dynsym", ".symtab"):
                continue
            for sym in section.iter_symbols():
                if sym.name in PATCHES and sym["st_value"]:
                    found[sym.name] = sym["st_value"] & ~1
    return found


def encode_thumb_bl(src_offset: int, target_offset: int) -> bytes:
    """Encode a thumb BL instruction (4 bytes) from src to target."""
    diff = target_offset - (src_offset + 4)
    if diff & 1:
        raise ValueError("BL target must be 2-byte aligned")
    imm = diff >> 1
    if not -(1 << 22) <= imm < (1 << 22):
        raise ValueError(f"BL target out of range: {diff:#x}")
    imm &= 0x7FFFFF
    s = (imm >> 22) & 1
    j1 = ((imm >> 11) & 1) ^ 1 ^ s
    j2 = ((imm >> 10) & 1) ^ 1 ^ s  # noqa: F841 - per ARM ARM encoding
    # Standard cross-reference for the encoding:
    # high half-word: 11110 S imm10
    # low  half-word: 11 J1 1 J2 imm11
    j1_bit = ((imm >> 11) & 1) ^ 1 ^ s
    j2_bit = ((imm >> 10) & 1) ^ 1 ^ s
    imm10 = (imm >> 11) & 0x3FF
    imm11 = imm & 0x7FF
    hi = 0xF000 | (s << 10) | imm10
    lo = 0xD000 | (j1_bit << 13) | (j2_bit << 11) | imm11
    return bytes([hi & 0xFF, (hi >> 8) & 0xFF, lo & 0xFF, (lo >> 8) & 0xFF])


def apply_patches(input_path: Path, output_path: Path) -> None:
    data = bytearray(input_path.read_bytes())
    symbols = find_symbols(input_path)

    missing = [name for name in PATCHES if name not in symbols]
    if missing:
        print("Missing symbols (need to update mangled names):")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    for sym_name, (desc, patch) in PATCHES.items():
        offset = symbols[sym_name]

        if sym_name.endswith("Scene9setShaderENS_6Shader10ShaderKindEf"):
            # Patch #3: nop at +0x108
            poke = offset + 0x108
            data[poke:poke + 2] = b"\x00\xbf"  # thumb nop
            print(f"#3  {sym_name} @ {offset:#x} +0x108: nop ({desc})")
            continue

        if sym_name.endswith("TouchGamepad12drawGamepadEv"):
            # Patch #4: movs r1,#0 ; bl setVisible ; bx lr (8 bytes)
            set_visible = symbols.get(
                "_ZN4agtk12TouchGamepad10setVisibleEb"
            )
            if set_visible is None:
                print("WARN: cannot find TouchGamepad::setVisible, falling back to bx lr")
                data[offset:offset + 2] = b"\x70\x47"
            else:
                # movs r1, #0          ; 00 21
                # bl   setVisible(bool); ?? ?? ?? ??
                # bx   lr              ; 70 47
                prologue = bytes([0x00, 0x21])
                bl = encode_thumb_bl(offset + 2, set_visible)
                epilogue = bytes([0x70, 0x47])
                data[offset:offset + 8] = prologue + bl + epilogue
            print(f"#4  {sym_name} @ {offset:#x}: tail-call setVisible(false) ({desc})")
            continue

        if patch is None:
            print(f"SKIP {sym_name}: no patch defined")
            continue

        data[offset:offset + len(patch)] = patch
        print(f"     {sym_name} @ {offset:#x}: wrote {len(patch)} bytes ({desc})")

    output_path.write_bytes(bytes(data))
    print(f"\nWrote patched libMyGame.so -> {output_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="libMyGame.so (v71 armeabi-v7a)")
    ap.add_argument("-o", "--output", type=Path, default=Path("libMyGame.patched.so"))
    args = ap.parse_args()
    apply_patches(args.input, args.output)


if __name__ == "__main__":
    main()
