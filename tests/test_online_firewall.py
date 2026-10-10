from paths import ROOT  # noqa: F401
import tempfile
import unittest
from pathlib import Path

import online


class FirewallTests(unittest.TestCase):
    def test_ufw_enabled_or_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / 'ufw.conf'
            for text, expected in (('ENABLED=yes\n', ['ufw']), ('ENABLED=no\n', []),
                                   ('# ENABLED=yes\nENABLED=no\n', [])):
                with self.subTest(text=text):
                    conf.write_text(text)
                    self.assertEqual(online.active_firewalls(conf, '/bin/false'), expected)
            self.assertEqual(online.active_firewalls(Path(tmp) / 'missing', '/bin/false'), [])

    def test_firewalld_from_its_service(self):
        missing = Path('/nonexistent/ufw.conf')
        self.assertEqual(online.active_firewalls(missing, '/bin/true'), ['firewalld'])
        self.assertEqual(online.active_firewalls(missing, '/nonexistent/systemctl'), [])

    def test_default_gateway(self):
        with tempfile.TemporaryDirectory() as tmp:
            route = Path(tmp) / 'route'
            route.write_text(
                'Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\n'
                'enp5s0\t0000A8C0\t00000000\t0001\t0\t0\t100\t00FFFFFF\n'
                'enp5s0\t00000000\t0100A8C0\t0003\t0\t0\t100\t00000000\n')
            self.assertEqual(online.default_gateway(route), '192.168.0.1')
            self.assertIsNone(online.default_gateway(Path(tmp) / 'missing'))

    def test_commands(self):
        self.assertEqual(online.firewall_commands('ufw', '192.168.0.1'),
                         ('sudo ufw allow 3658/udp', 'sudo ufw allow from 192.168.0.1 proto udp'))
        self.assertEqual(online.firewall_commands('ufw')[1], None)
        self.assertIn('--add-port=3658/udp', online.firewall_commands('firewalld')[0])


if __name__ == '__main__':
    unittest.main()
