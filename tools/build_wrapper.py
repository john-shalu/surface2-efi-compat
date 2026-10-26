#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Rebuild only the ARM32 EFI stub/decompressor around the pinned kernel payload."""
import argparse,json,pathlib,subprocess,shutil,sys,re
from boot_formats import extract_payload,inspect_pe,sha256
ROOT=pathlib.Path(__file__).resolve().parents[1]
PINS=json.loads((ROOT/'pins.json').read_text())

def run(command,cwd):
    print('+',' '.join(map(str,command)),flush=True)
    subprocess.run(list(map(str,command)),cwd=cwd,check=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=pathlib.Path,required=True,help='dedicated libre-tegra source tree')
    parser.add_argument('--vmlinuz',type=pathlib.Path,required=True,help='original linux-postmarketos-grate 7.0.1-r4 vmlinuz')
    parser.add_argument('--config',type=pathlib.Path,default=ROOT/'config-7.0.1-r4.armv7')
    parser.add_argument('--output',type=pathlib.Path,required=True)
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--cross-compile',default='')
    parser.add_argument('--hostcc',default='gcc')
    parser.add_argument('--diagnostic',action='store_true',help='enable pre-ExitBootServices file checkpoints')
    args=parser.parse_args();src=args.source.resolve();out=args.output.resolve()
    if not 1<=args.jobs<=16:parser.error('jobs must be 1..16; use 1 or 2 on a 2 GiB tablet')
    for path in (src,out,ROOT):
        if not re.fullmatch(r'[A-Za-z0-9_./+-]+',str(path)):parser.error('use plain ASCII Kbuild paths without shell metacharacters or spaces')
    original=args.vmlinuz.read_bytes();config=args.config.read_bytes()
    if sha256(original)!=PINS['original_vmlinuz_sha256']:parser.error('unsupported input kernel SHA-256')
    if sha256(config)!=PINS['config_sha256']:parser.error('use the pinned package configuration')
    if sha256((src/'Makefile').read_bytes())!=PINS['source_makefile_sha256']:parser.error('wrong source baseline')
    files=json.loads((ROOT/'patches/efi-file-hashes.json').read_text());states=[]
    for name,expected in files.items():
        digest=sha256((src/name).read_bytes())
        states.append('original' if digest==expected['original_sha256'] else 'patched' if digest==expected['modified_sha256'] else 'unknown')
    if 'unknown' in states or len(set(states))!=1:parser.error('source files are modified or partially patched')
    if states[0]=='original':
        patch=ROOT/'patches/0001-surface2-efi-file-parameters.patch'
        run(['patch','--dry-run','-p1','-i',patch],src);run(['patch','-p1','-i',patch],src)
    image,metadata=extract_payload(original)
    if metadata['payload_sha256']!=PINS['kernel_image_sha256']:parser.error('wrong uncompressed kernel payload')
    out.mkdir(parents=True,exist_ok=True)
    (src/'.config').write_bytes(config+b'\nCONFIG_EFI_SURFACE2_COMPAT=y\n'+(b'CONFIG_EFI_SURFACE2_BOOT_LOG=y\n' if args.diagnostic else b'# CONFIG_EFI_SURFACE2_BOOT_LOG is not set\n'))
    image_path=src/'arch/arm/boot/Image'
    if not image_path.exists() or sha256(image_path.read_bytes())!=metadata['payload_sha256']:image_path.write_bytes(image)
    if not re.fullmatch(r'[A-Za-z0-9_./+-]*',args.cross_compile) or not re.fullmatch(r'[A-Za-z0-9_./+-]+',args.hostcc):parser.error('compiler names must be simple executable paths')
    cc=args.cross_compile+'gcc';nm=args.cross_compile+'nm'
    common=['ARCH=arm','CC='+cc,'HOSTCC='+args.hostcc]
    if args.cross_compile:common+=['CROSS_COMPILE='+args.cross_compile]
    makefile=out/'surface2-wrapper.mk'
    makefile.write_text('''.PHONY: surface2-wrapper
surface2-wrapper: prepare
	$(MAKE) $(build)=drivers/firmware/efi/libstub drivers/firmware/efi/libstub/lib.a
	$(MAKE) $(build)=arch/arm/boot/compressed arch/arm/boot/compressed/vmlinux
	$(OBJCOPY) -O binary -R .comment -S arch/arm/boot/compressed/vmlinux $(SURFACE2_OUTPUT)
''')
    result_path=out/'surface2-compat.efi'
    run(['make',*common,'olddefconfig'],src)
    resolved=(src/'.config').read_text()
    if 'CONFIG_EFI_SURFACE2_COMPAT=y' not in resolved:raise RuntimeError('compatibility option not enabled')
    run(['make','--no-print-directory','-j'+str(args.jobs),'-f','Makefile','-f',makefile,*common,'KBSS_SZ='+str(metadata['kernel_bss_size']),'SURFACE2_OUTPUT='+str(result_path),'surface2-wrapper'],src)
    result=result_path.read_bytes();raw,rebuilt=extract_payload(result)
    if raw!=image:raise RuntimeError('kernel payload changed')
    for field in ('kernel_bss_size','text_offset','malloc_size'):
        if rebuilt[field]!=metadata[field]:raise RuntimeError('boot metadata changed: '+field)
    undefined=subprocess.check_output([nm,'-u',str(src/'arch/arm/boot/compressed/vmlinux')],text=True)
    if undefined.strip():raise RuntimeError('unresolved wrapper symbols: '+undefined)
    report={'source_commit':PINS['source_commit'],'input_vmlinuz_sha256':sha256(original),
            'output_efi_sha256':sha256(result),'output_size':len(result),'kernel_payload_byte_identical':True,
            'metadata':rebuilt,'pe':inspect_pe(result),'diagnostic_file_logging':args.diagnostic,
            'firmware_boot_tested_by_this_command':False,
            'compiler':subprocess.check_output([cc,'--version'],text=True).splitlines()[0]}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.diagnostic:(out/'boot-stage.log').write_bytes((b' '*126+b'\r\n')*32)
    print(json.dumps(report,indent=2),flush=True)
    print('Built and checked. No boot files were installed.',flush=True)
if __name__=='__main__':main()
