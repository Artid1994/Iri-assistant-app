#!/usr/bin/env python3
"""
Patch ELF64 .so files: set p_align of PT_LOAD segments to 0x4000 (16KB).
Uses CORRECT offset: p_align is at ph_off + 48 in Elf64_Phdr.
"""
import struct, sys, os

PT_LOAD = 1
ELFCLASS64 = 2
ELFDATA2LSB = 1

def patch_so(path, new_align=0x4000):
    if not os.path.isfile(path):
        print(f"SKIP (not file): {path}")
        return False
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    if len(data) < 64 or data[:4] != b'\x7fELF':
        print(f"SKIP (not ELF): {path}")
        return False
    if data[4] != ELFCLASS64 or data[5] != ELFDATA2LSB:
        print(f"SKIP (not 64-bit LE): {path}")
        return False

    e_phoff = struct.unpack_from('<Q', data, 32)[0]
    e_phentsize = struct.unpack_from('<H', data, 54)[0]
    e_phnum = struct.unpack_from('<H', data, 56)[0]

    if e_phoff == 0 or e_phnum == 0 or e_phentsize == 0:
        print(f"SKIP ({path}: no phdrs)")
        return False
    if e_phoff + e_phnum * e_phentsize > len(data):
        print(f"SKIP ({path}: phdrs overflow)")
        return False

    # CORRECT offset for p_align in Elf64_Phdr = 48
    patched = 0
    ph_off = e_phoff
    for i in range(e_phnum):
        if ph_off + 56 > len(data):
            break
        p_type = struct.unpack_from('<I', data, ph_off)[0]
        old_align = struct.unpack_from('<Q', data, ph_off + 48)[0]  # CORRECT: +48
        if p_type == PT_LOAD and old_align != new_align:
            struct.pack_into('<Q', data, ph_off + 48, new_align)
            patched += 1
            print(f"  PT_LOAD seg {i}: p_align {hex(old_align)} -> {hex(new_align)}")
        ph_off += e_phentsize

    if patched > 0:
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  WROTE {patched} patch(es)")
    else:
        print(f"  OK (already aligned): {path}")
    return True

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.so> [...]")
        sys.exit(1)
    ok = fail = 0
    for p in sys.argv[1:]:
        print(f"[{os.path.basename(p)}]")
        if patch_so(p):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: {ok} ok, {fail} skipped")
    sys.exit(0 if fail == 0 else 1)

if __name__ == "__main__":
    main()
