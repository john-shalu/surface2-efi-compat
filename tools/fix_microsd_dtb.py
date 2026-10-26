#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fix only the Surface 2 microSD properties in the pinned 7.0.1 EFI DTB."""
import pathlib,struct,subprocess,hashlib,json,shutil,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dtb',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args=parser.parse_args();source=args.dtb.resolve();stage=args.output.resolve();stage.mkdir(parents=True,exist_ok=True)
data=source.read_bytes()
assert hashlib.sha256(data).hexdigest()=='781e4e8b3e53c3c444b89e6fe08f36def636c7959b190233a23512b78b0fd9db'

def parse(data):
    h=struct.unpack_from('>10I',data);assert h[0]==0xd00dfeed and h[1]<=len(data)
    i=h[2];strings=h[3];stack=[];nodes={}
    while i<h[2]+h[9]:
        token,=struct.unpack_from('>I',data,i);i+=4
        if token==1:
            end=data.index(0,i);stack.append(data[i:end].decode());i=(end+4)&~3
            nodes['/'+'/'.join(x for x in stack if x)]={}
        elif token==2:stack.pop()
        elif token==3:
            size,off=struct.unpack_from('>II',data,i);i+=8;end=data.index(0,strings+off)
            nodes['/'+'/'.join(x for x in stack if x)][data[strings+off:end].decode()]=data[i:i+size];i=(i+size+3)&~3
        elif token==4:pass
        elif token==9:break
        else:raise ValueError(token)
    reserved=[];i=h[4]
    while True:
        pair=struct.unpack_from('>QQ',data,i);i+=16
        if pair==(0,0):break
        reserved.append(pair)
    return nodes,reserved,h[7]
before,reserve,bootcpu=parse(data)
expected={n:dict(p) for n,p in before.items()}
phandle=max(int.from_bytes(p['phandle'],'big') for p in before.values() if 'phandle' in p)+1
supply_io='/i2c@7000d000/pmic@58/pmic/regulators/ldo9'
supply_card='/i2c@7000d000/pmic@48/regulators/fet6'
assert 'phandle' not in before[supply_io] and 'phandle' not in before[supply_card]
working=stage/'surface2-microsd-edit.dtb';shutil.copyfile(source,working)
def put(node,prop,values,kind):
    subprocess.run(['fdtput','-p','-t',kind,str(working),node,prop,*[str(v) for v in values]],check=True,capture_output=True,text=True)
    expected.setdefault(node,{})[prop]=(b'\0'.join(str(v).encode() for v in values)+b'\0') if kind=='s' else b''.join(struct.pack('>I',int(v,16)) for v in values)
def number(node,prop,*values):put(node,prop,[format(v,'x') for v in values],'x')
def string(node,prop,*values):put(node,prop,values,'s')
number(supply_io,'phandle',phandle);number(supply_card,'phandle',phandle+1)
sd='/mmc@78000400'
string(sd,'status','okay');number(sd,'vqmmc-supply',phandle);number(sd,'vmmc-supply',phandle+1)
pin='/pinmux@70000868/pinmux'
cmd=pin+'/sdmmc3_cmd_pa7';dat=pin+'/sdmmc3_dat1_pb6';clk=pin+'/sdmmc3_clk_pa6'
string(cmd,'nvidia,pins','sdmmc3_cmd_pa7','sdmmc3_dat0_pb7','sdmmc3_dat1_pb6','sdmmc3_dat2_pb5','sdmmc3_dat3_pb4','sdmmc3_clk_lb_out_pee4','sdmmc3_clk_lb_in_pee5')
string(cmd,'nvidia,function','sdmmc3');number(cmd,'nvidia,pull',2);number(cmd,'nvidia,tristate',0);number(cmd,'nvidia,enable-input',1)
subprocess.run(['fdtput','-r',str(working),dat],check=True,capture_output=True,text=True);del expected[dat]
string(clk,'nvidia,pins','sdmmc3_clk_pa6');string(clk,'nvidia,function','sdmmc3');number(clk,'nvidia,pull',0);number(clk,'nvidia,tristate',0);number(clk,'nvidia,enable-input',1)
# Decompile and rebuild with the standard compiler, then compare every node and property.
dts=stage/'surface2-microsd-fixed.dts';fixed=stage/'surface2-microsd-fixed.dtb'
subprocess.run(['dtc','-q','-I','dtb','-O','dts','-o',str(dts),str(working)],check=True,capture_output=True,text=True)
subprocess.run(['dtc','-q','-I','dts','-O','dtb','-b',str(bootcpu),'-o',str(fixed),str(dts)],check=True,capture_output=True,text=True)
after,reserve2,bootcpu2=parse(fixed.read_bytes());assert after==expected;assert reserve2==reserve and bootcpu2==bootcpu
changes=[]
for node in sorted(set(before)|set(after)):
    a=before.get(node,{});b=after.get(node,{})
    for prop in sorted(set(a)|set(b)):
        if a.get(prop)!=b.get(prop):changes.append({'node':node,'property':prop,'before':a.get(prop,b'').hex() if prop in a else None,'after':b.get(prop,b'').hex() if prop in b else None})
# All modifications must belong to the SD slot or its suppliers / pin groups.
assert all(c['node'] in [sd,supply_io,supply_card,cmd,dat,clk] for c in changes)
assert after['/aliases']==before['/aliases']
assert after['/host1x@50000000/dsi@54300000/panel@0']==before['/host1x@50000000/dsi@54300000/panel@0']
manifest={'base_sha256':hashlib.sha256(data).hexdigest(),'fixed_sha256':hashlib.sha256(fixed.read_bytes()).hexdigest(),'fixed_size':fixed.stat().st_size,'compiler':subprocess.check_output(['dtc','--version'],text=True).strip(),'all_unrelated_properties_unchanged':True,'reserved_memory_unchanged':True,'boot_cpu_unchanged':True,'changes':changes}
(stage/'validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='changes'},indent=2),flush=True)
print('MODIFIED_PROPERTIES',len(changes),'OUTPUT_ONLY; NO_BOOT_FILES_INSTALLED',flush=True)
