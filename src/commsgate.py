"""commsgate.py  -- abstract message gateway

I'm abstracting messaging, for testing purposes.
"""

from copy import deepcopy


"""inbox/outbox
{
  "CONN": unique identifier for the connection
  "MSG": (bytes)
}
"""
inbox = []
outbox = []

"""newconn
{
  "CONN": unique id for connection
  "IPADDR": "xxx.xxx.xxx.xxx"
  "PORT": #
}
"""
newconn = []

"""disconn
{
  "CONN": unique id for disconnection
}
"""
disconn = []


def reset():
    """Used in test."""
    del inbox[:]
    del outbox[:]
    del newconn[:]
    del disconn[:]


def add_inbox(conn, msg):
    assert isinstance(msg, bytes)
    inbox.append({"CONN": conn, "MSG": msg})

def add_outbox(conn, msg):
    assert isinstance(msg, bytes)
    outbox.append({"CONN": conn, "MSG": msg})

def add_conn(conn, ipaddr, port):
    newconn.append({"CONN": conn, "IPADDR": ipaddr, "PORT": port})

def rm_conn(conn):
    disconn.append({"CONN": conn})


def pop_inbox():
    return inbox.pop(0)

def pop_outbox():
    return outbox.pop(0)

def pop_newconn():
    return newconn.pop(0)

def pop_disconn():
    return disconn.pop(0)


def pending():
    return inbox or newconn or disconn

def snapshot():
    """Create a JSON-recordable snapshot of inbox, outbox, newconn, disconn."""
    def bytes_replaced(D):
        DRET = {}
        for k, v in D.items():
            DRET[k] = v.decode("ascii") if isinstance(v, bytes) else v
        return DRET
    return [[bytes_replaced(D) for D in inbox],
            [bytes_replaced(D) for D in outbox],
            [bytes_replaced(D) for D in newconn],
            [bytes_replaced(D) for D in disconn]]

def compare(prior):
    return prior == snapshot()

