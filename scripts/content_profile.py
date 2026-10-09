"""Prepare explicit offline AppContent metadata; SKU is a probe setting, not a license check."""
import argparse
import json
import struct
from pathlib import Path
from prepare import sfo


# SceAppContentAddcontDownloadStatus: the dumped folder is only the entitlement (sce_sys), or it
# also carries extra data.
NO_EXTRA_DATA, INSTALLED = 0, 4


def addons(dlc, title_id):
    """(label, status) for each add-on folder of this title in dlc: <dir>/sce_sys/param.sfo with
    CATEGORY ac and CONTENT_ID XXyyyy-<title id>_00-<16-character entitlement label>."""
    found = []
    for folder in sorted(Path(dlc).iterdir()) if dlc and Path(dlc).is_dir() else []:
        try:
            info = sfo((folder/'sce_sys/param.sfo').read_bytes())
        except (OSError, ValueError, IndexError):
            continue
        content = info.get('CONTENT_ID', '')
        if info.get('CATEGORY') != 'ac' or len(content) != 36 or content[7:16] != title_id:
            continue
        extra = any(p.name != 'sce_sys' for p in folder.iterdir())
        found.append((content[20:], INSTALLED if extra else NO_EXTRA_DATA))
    return found


def prepare(game, out, sku='full', dlc=None):
    values=sfo((game/'sce_sys/param.sfo').read_bytes())
    params=[values.get(f'USER_DEFINED_PARAM_{i}',0) for i in range(1,5)]
    if any(type(v) is not int or not 0<=v<=0xffffffff for v in params):
        raise ValueError('invalid user-defined parameter')
    found=addons(dlc,values.get('TITLE_ID'))[:32]
    profile=dict(title_id=values.get('TITLE_ID'),sku=sku,sku_source='explicit probe setting',
                 user_params=params,addons=[dict(label=l,status=s) for l,s in found],boot_attr=0)
    out.mkdir(parents=True,exist_ok=True)
    data=struct.pack('<8s5I',b'BBCONT02' if found else b'BBCONT01',{'full':3,'trial':1}[sku],*params)
    if found:
        data+=struct.pack('<I',len(found))+b''.join(struct.pack('<16sI',l.encode(),s) for l,s in found)
    (out/'content.bin').write_bytes(data)
    (out/'content-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    print(f'AppContent profile: SKU={sku} (probe setting), user params={params}, '
          f'add-ons={",".join(l for l,_ in found) or "none"}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('game',type=Path)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'out')
    p.add_argument('--sku',choices=['full','trial'],default='full')
    p.add_argument('--dlc',type=Path,help='folder with the dumped add-ons (one folder each)')
    a=p.parse_args();prepare(a.game,a.out,a.sku,a.dlc)
