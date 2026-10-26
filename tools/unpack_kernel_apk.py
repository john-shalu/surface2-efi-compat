#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Extract only the three pinned public inputs from the official APK."""
import argparse,pathlib,json,tarfile
from boot_formats import sha256
ROOT=pathlib.Path(__file__).resolve().parents[1]
pins=json.loads((ROOT/'pins.json').read_text())
p=argparse.ArgumentParser(description=__doc__);p.add_argument('apk',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
if sha256(a.apk.read_bytes())!=pins['kernel_package_sha256']:p.error('APK SHA-256 does not match pins.json')
a.output.mkdir(parents=True,exist_ok=True)
expected={'vmlinuz':('vmlinuz',pins['original_vmlinuz_sha256']),'config':('config',pins['config_sha256']),'tegra114-microsoft-surface-2-efi.dtb':('surface2-efi-original.dtb',pins['original_dtb_sha256'])};found=set()
with tarfile.open(a.apk,'r:gz',ignore_zeros=True) as t:
    for member in t:
        name=pathlib.PurePosixPath(member.name).name
        if not member.isfile() or name not in expected:continue
        target,digest=expected[name];data=t.extractfile(member).read()
        if sha256(data)!=digest:continue
        (a.output/target).write_bytes(data);found.add(name)
if found!=set(expected):raise SystemExit('Missing pinned files: '+str(set(expected)-found))
print('Extracted verified vmlinuz, config and Surface 2 EFI DTB. No package installed.')
