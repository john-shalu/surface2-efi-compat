# SPDX-License-Identifier: GPL-2.0-only
import unittest,pathlib,sys,struct,lzma
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from boot_formats import extract_payload,inspect_pe

def image_with_payload(false_magic=False):
    raw=b'kernel-data'*128;packed=lzma.compress(raw);offset=512
    b=bytearray(offset+len(packed)+4);struct.pack_into('<II',b,0x34,0x45454545,128)
    struct.pack_into('<7I',b,128,6,0x5a534c4b,offset+len(packed),1234,32768,65536,0)
    if false_magic:b[256:262]=b'\xfd7zXZ\0'
    b[offset:offset+len(packed)]=packed;struct.pack_into('<I',b,offset+len(packed),len(raw))
    return b,raw

class FormatChecks(unittest.TestCase):
    def test_valid_payload(self):
        b,raw=image_with_payload();actual,meta=extract_payload(b);self.assertEqual(raw,actual);self.assertEqual(meta['kernel_bss_size'],1234)
    def test_xz_constant_before_real_stream(self):
        b,raw=image_with_payload(True);self.assertEqual(extract_payload(b)[0],raw)
    def test_metadata_outside_image(self):
        b,_=image_with_payload();struct.pack_into('<I',b,0x38,len(b)+1)
        with self.assertRaises(ValueError):extract_payload(b)
    def test_wrong_length(self):
        b,_=image_with_payload();struct.pack_into('<I',b,len(b)-4,1)
        with self.assertRaises(ValueError):extract_payload(b)
    def test_bad_metadata_magic(self):
        b,_=image_with_payload();struct.pack_into('<I',b,132,0)
        with self.assertRaises(ValueError):extract_payload(b)
    def test_not_pe(self):
        with self.assertRaises(ValueError):inspect_pe(b'not a PE')
    def test_truncated_pe_header(self):
        b=bytearray(128);b[:2]=b'MZ';struct.pack_into('<I',b,0x3c,4096)
        with self.assertRaises(ValueError):inspect_pe(b)
if __name__=='__main__':unittest.main()
