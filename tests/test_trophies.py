from paths import ROOT  # noqa: F401
import struct
import tempfile
import unittest
from pathlib import Path

import trophies

KEY = bytes.fromhex('2b7e151628aed2a6abf7158809cf4f3c')
COMM_ID = 'NPWR00001_00'


def cbc_encrypt(key, iv, data):
    out, previous = b'', iv
    for i in range(0, len(data), 16):
        previous = trophies.aes_encrypt_block(key, bytes(a ^ b for a, b in zip(data[i:i + 16], previous)))
        out += previous
    return out


def esfm(xml, key=KEY, comm_id=COMM_ID):
    """An ESFM entry as the PS4 makes them: the IV, then the list encrypted with the title's key."""
    title_key = trophies.aes_encrypt_block(key, comm_id.encode().ljust(16, b'\0'))
    iv = bytes(range(16, 32))
    data = xml + b'\0' * (-len(xml) % 16)
    return iv + cbc_encrypt(title_key, iv, data)


def trp(entries):
    """A TRP file with these {name: bytes} entries."""
    header_size, entry_size = 0x60, 64
    offset = header_size + entry_size * len(entries)
    table, blobs = b'', b''
    for name, data in entries.items():
        table += name.encode().ljust(32, b'\0') + struct.pack('>QQ', offset + len(blobs), len(data))
        table += bytes(entry_size - 48)
        blobs += data
    header = struct.pack('>IIQII', trophies.TRP_MAGIC, 3, offset + len(blobs), len(entries), entry_size)
    return header.ljust(header_size, b'\0') + table + blobs


CONF = b'''<!--Sce-Np-Trophy-Signature: x--><?xml version="1.0" encoding="utf-8"?>
<trophyconf version="1.1"><title-name>Game</title-name>
<trophy id="000" hidden="no" ttype="P" pid="-1"><name>All</name><detail>Everything</detail></trophy>
<trophy id="001" hidden="yes" ttype="B" pid="000"><name>First</name><detail>Do one</detail></trophy>
<trophy id="002" hidden="no" ttype="G" pid="-1" gid="001"><name>Extra</name><detail>Add-on</detail></trophy>
</trophyconf>'''
SPANISH = '''<?xml version="1.0" encoding="utf-8"?><trophyconf><title-name>Juego</title-name>
<trophy id="000"><name>Todo</name><detail>Todo hecho</detail></trophy>
<trophy id="001"><name>Primero</name><detail>Hazlo</detail></trophy>
<trophy id="002"><name>Extra</name><detail>Contenido adicional</detail></trophy></trophyconf>'''.encode()


class AesTests(unittest.TestCase):
    def test_fips_197_block(self):
        key, block = bytes(range(16)), bytes.fromhex('00112233445566778899aabbccddeeff')
        cipher = trophies.aes_encrypt_block(key, block)
        self.assertEqual(cipher.hex(), '69c4e0d86a7b0430d8cdb78070b4c55a')
        self.assertEqual(trophies.aes_cbc_decrypt(key, bytes(16), cipher), block)

    def test_sp_800_38a_cbc(self):
        iv = bytes(range(16))
        cipher = bytes.fromhex('7649abac8119b246cee98e9b12e9197d5086cb9b507219ee95db113a917678b2')
        plain = trophies.aes_cbc_decrypt(KEY, iv, cipher)
        self.assertEqual(plain.hex(), '6bc1bee22e409f96e93d7e117393172a'
                                      'ae2d8a571e03ac9c9eb76fac45af8e51')


class TrophyFileTests(unittest.TestCase):
    def game(self, tmp):
        game = Path(tmp) / 'game'
        (game / 'sce_sys' / 'trophy').mkdir(parents=True)
        (game / 'sce_sys' / 'npbind.dat').write_bytes(b'\0\1junk' + COMM_ID.encode() + b'\0more')
        (game / 'sce_sys' / 'trophy' / 'trophy00.trp').write_bytes(trp({
            'ICON0.PNG': b'icon', 'TROP000.PNG': b'png0', 'TROP001.PNG': b'png1',
            'TROP002.PNG': b'png2',
            'TROPCONF.ESFM': esfm(CONF), 'TROP.ESFM': esfm(CONF), 'TROP_03.ESFM': esfm(SPANISH)}))
        return game

    def test_key_text(self):
        self.assertEqual(trophies.parse_key(' 0x' + KEY.hex().upper()), KEY)
        self.assertIsNone(trophies.parse_key('1234'))
        self.assertIsNone(trophies.parse_key(None))

    def test_list_with_the_key_in_a_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.game(tmp)
            self.assertEqual(trophies.np_comm_id(game), COMM_ID)
            entries = trophies.read_trp(game / 'sce_sys' / 'trophy' / 'trophy00.trp')
            listed = trophies.trophy_list(entries, KEY, COMM_ID, 3)
            self.assertEqual(listed[0], {'grade': 'P', 'hidden': False, 'name': 'Todo',
                                         'detail': 'Todo hecho', 'platinum': False})
            self.assertEqual((listed[1]['grade'], listed[1]['hidden'], listed[1]['name']),
                             ('B', True, 'Primero'))
            self.assertEqual(trophies.trophy_list(entries, KEY, COMM_ID, 1)[1]['name'], 'First')

    def test_without_the_key_only_the_icons(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = trophies.read_trp(self.game(tmp) / 'sce_sys' / 'trophy' / 'trophy00.trp')
            self.assertEqual(sorted(trophies.trophy_list(entries)), [0, 1, 2])
            self.assertEqual(trophies.trophy_list(entries)[1]['name'], '')

    def test_add_on_trophies_do_not_count_toward_the_platinum(self):
        with tempfile.TemporaryDirectory() as tmp:
            game, user = self.game(tmp), Path(tmp) / 'user'
            entries = trophies.read_trp(game / 'sce_sys' / 'trophy' / 'trophy00.trp')
            listed = trophies.trophy_list(entries, KEY, COMM_ID, 3)
            self.assertEqual({i: t['platinum'] for i, t in listed.items()}, {0: False, 1: True, 2: False})
            directory = trophies.prepare(game, user, KEY, 3)
            self.assertEqual((directory / 'trophies.tsv').read_text().splitlines()[1],
                             '1\tB\t1\tPrimero\tHazlo\t1')
            self.assertEqual({i: t['platinum'] for i, t in trophies.read_list(directory).items()},
                             {0: False, 1: True, 2: False})
            (directory / 'trophies.tsv').write_text('1\tB\t1\tOld\tFive fields\n')
            self.assertFalse(trophies.read_list(directory)[1]['platinum'])

    def test_wrong_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = trophies.read_trp(self.game(tmp) / 'sce_sys' / 'trophy' / 'trophy00.trp')
            with self.assertRaises(ValueError):
                trophies.trophy_list(entries, bytes(16), COMM_ID, 1)

    def test_prepare_and_the_earned_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            game, user = self.game(tmp), Path(tmp) / 'user'
            directory = trophies.prepare(game, user, KEY, 3)
            self.assertEqual(directory, user / 'trophies' / COMM_ID)
            self.assertEqual((directory / 'icons' / 'TROP001.PNG').read_bytes(), b'png1')
            self.assertEqual(trophies.read_list(directory)[1]['name'], 'Primero')
            (directory / 'earned.tsv').write_text('1\t1700000000\n1\t1800000000\nbad\n')
            self.assertEqual(trophies.read_earned(directory), {1: 1700000000})
            self.assertIsNone(trophies.prepare(Path(tmp) / 'nothing', user))


if __name__ == '__main__':
    unittest.main()
