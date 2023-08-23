
import unittest

import init
import configinfo
import reporting
import commsgate
import logicalconductor
import messagelogic


four_bytes_little_endian_test_data = [(4294967040, b"\x00\xff\xff\xff"),
                                      (16777215, b"\xff\xff\xff\x00"),
                                      (4294967295, b'\xff\xff\xff\xff'),
                                      (0, b'\x00\x00\x00\x00')]

go43 = b'!+\x00\x00\x00'

def four_bytes_little_endian_enctest(testno):
    (i, bb) = four_bytes_little_endian_test_data[testno]
    return messagelogic.create_little_endian_integer(i) == bb

def four_bytes_little_endian_dectest(testno):
    (i, bb) = four_bytes_little_endian_test_data[testno]
    return messagelogic.read_little_endian_integer(bb) == i


class TestMessages(unittest.TestCase):
    def setUp(self):
        # Initialize the system for a fresh run.
        init.init_server_test()

    def tearDown(self):
        # Optional: Perform any cleanup steps after each test method is called
        pass
    
    def test_4byte_encoding_0(self):
        self.assertTrue(four_bytes_little_endian_enctest(0))

    def test_4byte_encoding_1(self):
        self.assertTrue(four_bytes_little_endian_enctest(1))

    def test_4byte_encoding_2(self):
        self.assertTrue(four_bytes_little_endian_enctest(2))
    
    def test_4byte_encoding_3(self):
        self.assertTrue(four_bytes_little_endian_enctest(3))

    def test_4byte_decoding_0(self):
        self.assertTrue(four_bytes_little_endian_dectest(0))

    def test_4byte_decoding_1(self):
        self.assertTrue(four_bytes_little_endian_dectest(1))

    def test_4byte_decoding_2(self):
        self.assertTrue(four_bytes_little_endian_dectest(2))
    
    def test_4byte_decoding_3(self):
        self.assertTrue(four_bytes_little_endian_dectest(3))

    def test_new_server_go(self):
        messagelogic.new_server_go(43)
        self.assertEqual(messagelogic.g["MSG"], go43)
        for (i, bb) in four_bytes_little_endian_test_data:
            messagelogic.new_server_go(i)
            self.assertEqual(messagelogic.g["MSG"], b"!"+bb)


if __name__ == '__main__':
    unittest.main()

