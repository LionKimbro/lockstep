"""timectrl  -- time functionality

I do this so that, for testing purposes, I can CONTROL TIME.

Though I don't have any such tests at present.
"""

import time


g = {"START_TIMESTAMP": None,
     "TIMEOVERRIDE": None}


def init_real():
    g["START_TIMESTAMP"] = int(time.time())
    g["TIMEOVERRIDE"] = None

def init_virtual(t):
    g["START_TIMESTAMP"] = t
    g["TIMEOVERRIDE"] = t


def now():
    if g["TIMEOVERRIDE"] is not None:
        return g["TIMEOVERRIDE"]
    else:
        return int(time.time())


def advance(n):
    g["TIMEOVERRIDE"] += n

