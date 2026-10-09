from paths import ROOT
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import content_profile

EXE=ROOT/'out/content-test'

class ProfileTests(unittest.TestCase):
    def test_sfo_parameters_and_explicit_trial_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'sce_sys').mkdir();(p/'sce_sys/param.sfo').write_bytes(b'fixture')
            with patch.object(content_profile,'sfo',return_value={'USER_DEFINED_PARAM_1':13,'USER_DEFINED_PARAM_4':0xffffffff}):
                content_profile.prepare(p,p,'trial')
            self.assertEqual(struct.unpack('<8s5I',(p/'content.bin').read_bytes()),(b'BBCONT01',1,13,0,0,0xffffffff))

    def test_dlc_folders_of_this_title_become_addons(self):
        infos={'game':{'TITLE_ID':'CUSA00900'},
               'SPEXPANSIONDLC03':{'CATEGORY':'ac','CONTENT_ID':'UP9000-CUSA00900_00-SPEXPANSIONDLC03'},
               'SPDLCMESSENGER00':{'CATEGORY':'ac','CONTENT_ID':'UP9000-CUSA00900_00-SPDLCMESSENGER00'},
               'OTHERREGION00000':{'CATEGORY':'ac','CONTENT_ID':'UP9000-CUSA03173_00-OTHERREGION00000'},
               'PATCH':{'CATEGORY':'gp','CONTENT_ID':'UP9000-CUSA00900_00-BLOODBORNE000000'}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for name in infos:
                (p/name/'sce_sys').mkdir(parents=True);(p/name/'sce_sys/param.sfo').write_bytes(name.encode())
            (p/'SPDLCMESSENGER00/data').mkdir()
            (p/'broken').mkdir()
            with patch.object(content_profile,'sfo',side_effect=lambda b:infos[b.decode()]):
                content_profile.prepare(p/'game',p/'out',dlc=p)
            data=(p/'out/content.bin').read_bytes()
            self.assertEqual(struct.unpack('<8s6I',data[:32]),(b'BBCONT02',3,0,0,0,0,2))
            self.assertEqual([struct.unpack('<16sI',data[i:i+20]) for i in (32,52)],
                             [(b'SPDLCMESSENGER00',4),(b'SPEXPANSIONDLC03',0)])

    def test_invalid_sfo_parameter_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'sce_sys').mkdir();(p/'sce_sys/param.sfo').write_bytes(b'fixture')
            with patch.object(content_profile,'sfo',return_value={'USER_DEFINED_PARAM_1':'13'}):
                with self.assertRaisesRegex(ValueError,'invalid user-defined'):
                    content_profile.prepare(p,p)

@unittest.skipUnless(EXE.exists(),'run bash build.sh --test first')
class ContentTests(unittest.TestCase):
    def run_case(self,*args):
        return subprocess.run([str(EXE.resolve()),*args],capture_output=True,text=True,timeout=5)

    def test_lifecycle_and_output_boundaries(self):
        r=self.run_case();self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_missing_profile_does_not_report_loaded(self):
        r=self.run_case('--missing');self.assertEqual(r.returncode,21)
        self.assertIn('needs --content-profile',r.stderr)

    def test_addon_list(self):
        r=self.run_case('--addons');self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('add-on SPEXPANSIONDLC03 (status 0)',r.stdout)

    def test_other_modules_are_counted_independently(self):
        r=self.run_case('--unknown');self.assertEqual(r.returncode,0,r.stdout+r.stderr)
