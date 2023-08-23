
import unittest

import init
import configinfo
import reporting
import commsgate
import logicalconductor
import messagelogic
import scripts
import timectrl


class TestWithScripts(unittest.TestCase):
    def setUp(self):
        # Initialize the system for a fresh run.
        init.init_server_test()
        scripts.load()
    
    def tearDown(self):
        # Optional: Perform any cleanup steps after each test method is called
        pass
    
    @unittest.expectedFailure
    def test_script_0(self):
        scripts.sel_script(0)
        self.assertEqual(scripts.play_recording(), True)

    @unittest.expectedFailure
    def test_script_1(self):
        scripts.sel_script(1)
        self.assertEqual(scripts.play_recording(), True)

    @unittest.expectedFailure
    def test_script_2(self):
        scripts.sel_script(2)
        self.assertEqual(scripts.play_recording(), True)


if __name__ == '__main__':
    unittest.main()

