
import unittest

import modelsystem as model


class TestModelSystem(unittest.TestCase):
    
    def setUp(self):
        # Perform any setup actions before each test method
        model.init()
    
    def tearDown(self):
        # Perform any cleanup actions after each test method
        pass
    
    def test_basic_connection(self):
        i1 = model.new_client()
        model.connect()
        model.say("HELLO")
        model.simulate_one_loop()
        model.simulate_one_loop()
        
        model.reset_expectations()
        model.expect_connection(i1)
        model.assert_time_order()
    
    def test_connection_and_disconnection(self):
        i1 = model.new_client()
        model.connect()
        model.say("HELLO")
        model.simulate_one_loop()
        
        model.switch_to_client(i1)
        model.disconnect()
        model.simulate_one_loop()

        model.reset_expectations()
        model.expect_connection(i1)
        model.expect_disconnection(i1)
        model.assert_time_order()


if __name__ == '__main__':
    unittest.main()

