"""init.py  -- initialization and run-time control modes

Presently there are roughly four contexts of execution:

1. Server (conductor.py)
2. Client (jackboot.py)
3. Server Test (various unit tests)
4. Client Test (various unit tests)

Initialization and other lifecycle procedures are collected here.

IMPORTANT:
  The test system will be resetting the system over and over and over.
  So initialization is no longer "initialization," but rather, "resetting."
  But I'm still calling the functions "init" functions.

"""

import constants
import timectrl
import reporting
import configinfo
import commsgate
import messagelogic
import logicalconductor


"""operating mode

Server/Client
Real/Test
"""

g = {"OPERATING_MODE": None,  # "SERVER" or "CLIENT"
     "TEST_MODE": None}  # True/False


def init_conductor():
    """Reset system state to Server/Real."""
    g["OPERATING_MODE"] = "SERVER"
    g["TEST_MODE"] = False
    timectrl.init_real()
    reporting.g["OUTPUT"] = "PRINT"
    reporting.g["WRITESTATUS"] = True
    configinfo.load()
    commsgate.reset()
    messagelogic.reset()
    logicalconductor.reset()

def init_server_test():
    """Reset sysystem state for Server/Test."""
    g["OPERATING_MODE"] = "SERVER"
    g["TEST_MODE"] = True
    timectrl.init_virtual(constants.TEST_TIME0)
    reporting.g["OUTPUT"] = None
    reporting.g["WRITESTATUS"] = False
    configinfo.load()
    commsgate.reset()
    messagelogic.reset()
    logicalconductor.reset()
