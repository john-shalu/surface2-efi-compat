# SPDX-License-Identifier: GPL-2.0-only
"""ARM32 zImage metadata and PE validation. No third-party bootloader is needed."""
import struct, lzma, hashlib

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def extract_payload(data):
    if len(data) < 64 or struct.unpack_from('<I',data,0x34)[0] != 0x45454545:
        raise ValueError('missing ARM zImage metadata marker')
    table = struct.unpack_from('<I',data,0x38)[0]
    if table + 28 > len(data):
        raise ValueError('metadata outside image')
    meta = struct.unpack_from('<7I',data,table)
    if meta[:2] != (6,0x5a534c4b) or meta[2]+4 > len(data):
        raise ValueError('invalid metadata table')
    length = struct.unpack_from('<I',data,meta[2])[0]
    found=[]; pos=0
    while True:
        offset=data.find(b'\xfd7zXZ\x00',pos)
        if offset<0: break
        pos=offset+1
        try:
            decoder=lzma.LZMADecompressor(); image=decoder.decompress(data[offset:])
        except lzma.LZMAError:
            continue
        if decoder.eof and len(image)==length:
            used=len(data[offset:])-len(decoder.unused_data)
            if offset+used==meta[2]: found.append((offset,image))
    if len(found)!=1:
        raise ValueError('expected one valid XZ payload ending at the size trailer')
    offset,image=found[0]
    return image,{'xz_offset':offset,'metadata_offset':table,'kernel_bss_size':meta[3],
                  'text_offset':meta[4],'malloc_size':meta[5],'payload_size':length,
                  'payload_sha256':sha256(image)}

def inspect_pe(data):
    if len(data)<64 or data[:2]!=b'MZ': raise ValueError('not a PE image')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if pe+96>len(data) or data[pe:pe+4]!=b'PE\0\0': raise ValueError('invalid PE header')
    machine,count=struct.unpack_from('<HH',data,pe+4); opt=pe+24
    if machine!=0x1c2 or struct.unpack_from('<H',data,opt+68)[0]!=10:
        raise ValueError('expected ARM32 EFI application')
    entry=struct.unpack_from('<I',data,opt+16)[0]
    table=opt+struct.unpack_from('<H',data,pe+20)[0]
    if not count or count>16 or table+40*count>len(data): raise ValueError('invalid PE sections')
    executable=0
    for i in range(count):
        _,vs,va,rs,rp,_,_,_,flags=struct.unpack_from('<8s8I',data,table+40*i)
        if rp+rs>len(data): raise ValueError('section outside image')
        if flags&0x20000000 and flags&0x80000000: raise ValueError('writable executable section')
        executable += int(va<=entry<va+vs and bool(flags&0x20000000))
    if entry%4 or executable!=1: raise ValueError('invalid ARM entry')
    return {'machine':hex(machine),'subsystem':10,'entry_rva':entry,'section_count':count}
