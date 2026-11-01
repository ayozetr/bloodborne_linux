# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare explicit offline AppContent metadata; SKU is a probe setting, not a license check.

USER_DEFINED_PARAM_1 is Bloodborne's region (2 the Americas, 13 Europe). A dump without one (0)
gets Europe: with no region the game has no address for its server, and Log In fails with "Unable
to obtain Bloodborne server information" (the Linux fork's issue #9). The text and voice
languages no longer depend on it (bbport.ini game_text_language, game_voice_language)."""
import argparse
import json
import struct
from pathlib import Path
from prepare import sfo

EUROPE=13


def prepare(game, out, sku='full'):
    values=sfo((game/'sce_sys/param.sfo').read_bytes())
    params=[values.get(f'USER_DEFINED_PARAM_{i}',0) for i in range(1,5)]
    if any(type(v) is not int or not 0<=v<=0xffffffff for v in params):
        raise ValueError('invalid user-defined parameter')
    if params[0]==0:
        params[0]=EUROPE
    profile=dict(title_id=values.get('TITLE_ID'),sku=sku,sku_source='explicit probe setting',
                 user_params=params, mounted_addons=[],boot_attr=0)
    out.mkdir(parents=True,exist_ok=True)
    (out/'content.bin').write_bytes(struct.pack('<8s5I',b'BBCONT01',{'full':3,'trial':1}[sku],*params))
    (out/'content-profile.json').write_text(json.dumps(profile,indent=2)+'\n', encoding='utf-8')
    print(f'AppContent profile: SKU={sku} (probe setting), user params={params}, mounted add-ons=0')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('game',type=Path)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'out')
    p.add_argument('--sku',choices=['full','trial'],default='full')
    a=p.parse_args();prepare(a.game,a.out,a.sku)
