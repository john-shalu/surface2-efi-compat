#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run file-parameter logic tests against the patched source; no firmware needed."""
import argparse,pathlib,tempfile,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--cc',default='gcc');a=p.parse_args()
text=(a.source/'drivers/firmware/efi/libstub/file.c').read_text()
tag='// SPDX-License-Identifier: GPL-2.0-only\n/* Surface 2 legacy test.efi compatibility;'
if tag not in text:raise SystemExit('Apply the EFI compatibility patch first')
with tempfile.TemporaryDirectory(prefix='surface2-compat-test-') as d:
    d=pathlib.Path(d);(d/'surface2-file-compat.c').write_text(text[text.index(tag):])
    (d/'test.c').write_bytes((ROOT/'tests/compat_file_io.c').read_bytes())
    for flag in ('0','1'):
        exe=d/('test-'+flag)
        subprocess.run([a.cc,'-std=gnu11','-fshort-wchar','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DCONFIG_EFI_SURFACE2_BOOT_LOG='+flag,'test.c','-o',str(exe)],cwd=d,check=True)
        subprocess.run([str(exe)],check=True)
print('24 logic tests passed. Real firmware boot compatibility needs a device test.')
