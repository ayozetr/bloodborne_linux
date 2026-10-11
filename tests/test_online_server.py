from paths import ROOT  # noqa: F401
import socket
import struct
import threading
import unittest

import online


class ServerChoiceTests(unittest.TestCase):
    def test_kind_of_settings_from_before_the_choice(self):
        self.assertEqual(online.server_kind({'online_server': online.SHADNET_SERVER}), 'public')
        self.assertEqual(online.server_kind({'online_server': ''}), 'public')
        self.assertEqual(online.server_kind({'online_server': '100.64.0.7:31313'}), 'own')
        self.assertEqual(online.server_kind({'online_server_kind': 'public',
                                             'online_server': '100.64.0.7:31313'}), 'public')

    def test_public_server_ignores_the_own_server_fields(self):
        server, webapi, community = online.addresses({
            'online_server_kind': 'public', 'online_server': '100.64.0.7',
            'online_webapi': 'http://100.64.0.7:9999', 'online_community': ''})
        self.assertEqual((server, webapi, community), (online.SHADNET_SERVER,
                                                       'http://srv.shadps4.net:31315',
                                                       online.COMMUNITY_SERVER))

    def test_own_server_gets_the_default_ports(self):
        settings = {'online_server_kind': 'own', 'online_server': '100.64.0.7'}
        self.assertEqual(online.addresses(settings)[:2],
                         ('100.64.0.7:31313', 'http://100.64.0.7:31315'))
        settings['online_webapi'] = 'http://100.64.0.7:8080'
        self.assertEqual(online.addresses(settings)[1], 'http://100.64.0.7:8080')

    def test_own_server_left_empty_is_the_public_one(self):
        self.assertEqual(online.addresses({'online_server_kind': 'own', 'online_server': ''})[0],
                         online.SHADNET_SERVER)

    def test_environment(self):
        env = online.environment({
            'online_server_kind': 'own', 'online_server': '100.64.0.7', 'online_npid': ' Hunter ',
            'online_password': 'secret', 'online_upnp': False, 'online_p2p_port': 3658,
            'online_seamless': True})
        self.assertEqual(env['BB_SHADNET_SERVER'], '100.64.0.7:31313')
        self.assertEqual(env['BB_SHADNET_NPID'], 'Hunter')
        self.assertEqual(env['BB_UPNP'], '0')
        self.assertEqual(env['SHADPS4_P2P_PORT'], '3658')
        self.assertEqual(env['SHADPS4_BLOODBORNE_SEAMLESS_COOP'], '1')

    def test_random_port_and_seamless_only_with_an_own_server(self):
        env = online.environment({'online_server_kind': 'public', 'online_p2p_port': 0,
                                  'online_seamless': True})
        self.assertNotIn('SHADPS4_P2P_PORT', env)
        self.assertNotIn('SHADPS4_BLOODBORNE_SEAMLESS_COOP', env)


class StunTests(unittest.TestCase):
    """The connection test's UDP ping against a stand-in for shadnet-p2p's StunServer, which
    answers the 21-byte ping behind the 0xffff signaling header with the sender's address."""

    def serve(self, answer=True):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(('127.0.0.1', 0))
        self.addCleanup(server.close)
        received = []

        def run():
            data, sender = server.recvfrom(64)
            received.append(data)
            if answer:
                server.sendto(b'\xff\xff\xff\xff' + socket.inet_aton(sender[0])
                              + struct.pack('!H', sender[1]), sender)
        threading.Thread(target=run, daemon=True).start()
        return server.getsockname()[1], received

    def test_public_address_from_the_answer(self):
        port, received = self.serve()
        address, public_port = online.stun_ping('127.0.0.1', port, timeout=2)
        self.assertEqual(address, '127.0.0.1')
        self.assertGreater(public_port, 0)
        ping = received[0]
        self.assertEqual(len(ping), 4 + 21)
        self.assertEqual(ping[:5], b'\xff\xff\xff\xff\x01')
        self.assertEqual(ping[5:21].rstrip(b'\0'), online.STUN_TEST_ID)

    def test_no_answer(self):
        port, _received = self.serve(answer=False)
        with self.assertRaises(TimeoutError):
            online.stun_ping('127.0.0.1', port, timeout=0.2, attempts=1)


if __name__ == '__main__':
    unittest.main()
