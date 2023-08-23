
import unittest

import init
import configinfo
import reporting
import commsgate
import logicalconductor
import messagelogic


TEST_CONNID_1 = 1
TEST_CONNID_2 = 2
TEST_IPADDR_1 = "100.100.100.100"
TEST_IPADDR_2 = "200.200.200.200"
TEST_PORT_1 = 1000
TEST_PORT_2 = 20000

TEST_SOCKETSELFID_1 = b"test conn 1 "
TEST_SOCKETSELFID_2 = b"test conn 2"


def connect_1():
    commsgate.add_conn(TEST_CONNID_1, TEST_IPADDR_1, TEST_PORT_1)

def connect_2():
    commsgate.add_conn(TEST_CONNID_2, TEST_IPADDR_2, TEST_PORT_2)

def send_1_good_A_packet():
    commsgate.add_inbox(TEST_CONNID_1, b"A1" + TEST_SOCKETSELFID_1)

def disconnect_1():
    commsgate.rm_conn(TEST_CONNID_1)

def disconnect_2():
    commsgate.rm_conn(TEST_CONNID_2)

def expect(conn, msg):
    D = commsgate.pop_outbox()
    if D["CONN"] != conn or D["MSG"] != msg:
        raise AssertionError(f"""expected {conn}, {msg}, got {D["CONN"]}, {D["MSG"]} instead""")

def expect_A_for(conn):
    expect(conn, b"A1"+configinfo.config["serverid_12asciibytes"])


def run_logicalconductor():
    runs = 0
    maxruns = 20
    while runs < maxruns and commsgate.pending():
        logicalconductor.loop_once()
        runs += 1
    if runs == maxruns:
        raise AssertionError(f"logicalconductor.loop_once() ran {maxruns} time -- aborting",
                             {"inbox len": len(commsgate.inbox),
                              "outbox len": len(commsgate.outbox),
                              "newconn len": len(commsgate.newconn),
                              "disconn len": len(commsgate.disconn)})


class TestBasics(unittest.TestCase):
    def setUp(self):
        # Initialize the system for a fresh run.
        init.init_server_test()

    def tearDown(self):
        # Optional: Perform any cleanup steps after each test method is called
        pass

    def test_connecting(self):
        # Create a new connection, ...
        connect_1()
        run_logicalconductor()
        
        # Verify that the connection shows up, and that it's empty (no identifier.)
        self.assertIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["IDENTIFICATION"], None)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["VERSION"], None)
        
        # Then send a properly formatted A packet.
        send_1_good_A_packet()
        run_logicalconductor()
        
        # Verify that the identification is correct, in the system, now that it's processed.
        self.assertIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["IDENTIFICATION"], TEST_SOCKETSELFID_1)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["VERSION"], b"1")

        # Also verify that the server sent out its own A1ID message.
        expect_A_for(TEST_CONNID_1)
    
    def test_disconnecting(self):
        # Create a new connection, ...
        connect_1()
        run_logicalconductor()
        
        # Verify that the connection shows up, and that it's empty (no identifier.)
        self.assertIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["IDENTIFICATION"], None)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["VERSION"], None)

        # Also verify that the server sent out its own A1ID message.
        expect_A_for(TEST_CONNID_1)

        # Now disconnect!
        disconnect_1()
        run_logicalconductor()

        # Verify that the connection doesn't show up any longer.
        self.assertNotIn(TEST_CONNID_1, logicalconductor.conns)
    
    def test_two_connections(self):
        # Create a connection, with two items, ...
        connect_1()
        connect_2()
        run_logicalconductor()
        
        # Verify that the connections shows up, and that they are empty.
        self.assertIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["IDENTIFICATION"], None)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["VERSION"], None)
        self.assertIn(TEST_CONNID_2, logicalconductor.conns)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_2]["IDENTIFICATION"], None)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_2]["VERSION"], None)

        # Verify that the server sent out it's own messages.
        expect_A_for(TEST_CONNID_1)
        expect_A_for(TEST_CONNID_2)

        # Disconnect 1
        disconnect_1()
        run_logicalconductor()

        # Verify that the connection doesn't show up any longer.
        self.assertNotIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertIn(TEST_CONNID_2, logicalconductor.conns)

        # Disconnect 2
        disconnect_2()
        run_logicalconductor()
        
        # Verify that the connection doesn't show up any longer.
        self.assertNotIn(TEST_CONNID_1, logicalconductor.conns)
        self.assertNotIn(TEST_CONNID_2, logicalconductor.conns)
        
    def test_basic_lockstep(self):
        # Create a connection, with two items, ...
        connect_1()
        connect_2()
        run_logicalconductor()

        # Verify that the connections shows up, and that they are non-empty.
        # Verify that the connection shows up, and that it's empty (no identifier.)
        self.assertIn(TEST_CONNID_1, logicalconductor.conns)
        
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["IDENTIFICATION"], None)
        self.assertEqual(logicalconductor.conns[TEST_CONNID_1]["VERSION"], None)

if __name__ == '__main__':
    unittest.main()

