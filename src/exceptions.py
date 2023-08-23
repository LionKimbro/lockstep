"""exceptions.py  -- Exception classes for conductor.py"""


class LockstepException(Exception): pass

class ConductorException(LockstepException): pass


class BadState(LockstepException): pass


class ClientMessageUnrecognized(ConductorException): pass



