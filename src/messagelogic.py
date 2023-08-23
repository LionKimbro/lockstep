"""messagelogic.py  -- reading and encoding messages."""

import constants
import exceptions
import configinfo
import struct


g = {"MSG": None,  # a message under consideration
     "ANALYSIS": None}  # last analysis performed (analyze_received())


# Server Messages
MSG_S_SELFID = "MSG_S_SELFID"
MSG_S_GO = "MSG_S_GO"
MSG_S_REFUSE = "MSG_S_REFUSE"
MSG_S_EXIT_SIGNAL = "MSG_S_EXIT_SIGNAL"
MSG_S_ARE_YOU_THERE = "MSG_S_ARE_YOU_THERE"
MSG_S_IM_STILL_HERE = "MSG_S_IM_STILL_HERE"
MSG_S_BROADCAST_TAKING_LONGER = "MSG_S_BROADCAST_TAKING_LONGER"
MSG_S_BROADCAST_SHUTDOWN = "MSG_S_BROADCAST_SHUTDOWN"
MSG_S_BROADCAST_ERROR = "MSG_S_BROADCAST_ERROR"
MSG_S_BROADCAST_CEASE = "MSG_S_BROADCAST_CEASE"

# Client Messages
MSG_C_SELFID = "MSG_C_SELFID"
MSG_C_RECEIVED_SIGNAL = "MSG_C_RECEIVED_SIGNAL"
MSG_C_DONE_SIGNAL = "MSG_C_DONE_SIGNAL"
MSG_C_STILL_WORKING_SIGNAL = "MSG_C_STILL_WORKING_SIGNAL"
MSG_C_I_AM_HERE_BUT_NOT_WORKING = "MSG_C_I_AM_HERE_BUT_NOT_WORKING"
MSG_C_ARE_YOU_THERE = "MSG_C_ARE_YOU_THERE"
MSG_C_EXIT_SIGNAL = "MSG_C_EXIT_SIGNAL"


msg_info = {
    MSG_S_SELFID: {
        "ID": MSG_S_SELFID,
        "BYTE": b"A",
        "ORIGIN": "SERVER",
        "LENGTH": 14,
        "STRUCTURE": "BBS",  # byte, byte, 12-byte string identifier
        "TITLE": "Protocol Version & Self-Identification",
        "DESC": "The server sends 1 character representing the protocol version, followed by 12 bytes of self-identification"
    },
    MSG_S_GO: {
        "ID": MSG_S_GO,
        "BYTE": b"!",
        "ORIGIN": "SERVER",
        "LENGTH": 5,
        "STRUCTURE": "BI",  # byte, integer
        "TITLE": "Go Message",
        "DESC": """The server sends an individual "Go" message to each client, instructing them to proceed with their tasks concurrently.  Attached is a "step count," a 4 byte unsigned little endian integer, that shares which step number (server defined) the Go message is on.  It counts up to some number, than resets to 0.  All clients receive the same number with the same wave of Go messages."""
    },
    MSG_S_REFUSE: {
        "ID": MSG_S_REFUSE,
        "BYTE": b"R",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Refusal Messages",
        "DESC": "The server sends refusal messages to specific client processes, indicating that it will not work with those clients."
    },
    MSG_S_EXIT_SIGNAL: {
        "ID": MSG_S_EXIT_SIGNAL,
        "BYTE": b"X",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Server Exit Signal",
        "DESC": "The server sends a signal to indicate its exit or termination."
    },
    MSG_S_ARE_YOU_THERE: {
        "ID": MSG_S_ARE_YOU_THERE,
        "BYTE": b"?",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Are you still there? Signal",
        "DESC": "The server can inquire if the client is still connected and active."
    },
    MSG_S_IM_STILL_HERE: {
        "ID": MSG_S_IM_STILL_HERE,
        "BYTE": b".",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "I'm still here Signal",
        "DESC": "The server responds to the client's 'Are you still there?' signal, confirming its presence and active connection."
    },
    MSG_S_BROADCAST_TAKING_LONGER: {
        "ID": MSG_S_BROADCAST_TAKING_LONGER,
        "BYTE": b"T",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Broadcast Message: Taking Longer",
        "DESC": 'The server sends a broadcast message to all client processes: "This is taking longer than expected, please hang on..."'
    },
    MSG_S_BROADCAST_SHUTDOWN: {
        "ID": MSG_S_BROADCAST_SHUTDOWN,
        "BYTE": b"S",
        "ORIGIN": "SERVER",
        "LENGTH": 5,
        "STRUCTURE": "BI",  # byte, integer
        "TITLE": "Broadcast Message: Shutdown",
        "DESC": 'The server sends a broadcast message to all client processes: "Shutting down in N seconds" (with 4 bytes unsigned little endian integer countdown value)'
    },
    MSG_S_BROADCAST_ERROR: {
        "ID": MSG_S_BROADCAST_ERROR,
        "BYTE": b"E",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Broadcast Message: Error",
        "DESC": "The server sends a broadcast message to all client processes: 'Shutting down due to error'"
    },
    MSG_S_BROADCAST_CEASE: {
        "ID": MSG_S_BROADCAST_CEASE,
        "BYTE": b"C",
        "ORIGIN": "SERVER",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Broadcast Message: Cease Operation",
        "DESC": "The server sends a broadcast message to all client processes: 'Ceasing operation'"
    },
    # Add more server message entries here as needed

    # Client Messages
    MSG_C_SELFID: {
        "ID": MSG_C_SELFID,
        "BYTE": b"A",
        "ORIGIN": "CLIENT",
        "LENGTH": 14,
        "STRUCTURE": "BBS",  # byte, byte, 12-byte identifier string
        "TITLE": "Protocol Version & Self-Identification",
        "DESC": "The client sends 1 character representing the protocol version, followed by 12 bytes of self-identification.",
        "AUTOPARSE": [(1,2, "VERSION"),  # client protocol version speaking in
                      (2,14, "IDENTIFICATION")]  # client self-identification
    },
    MSG_C_RECEIVED_SIGNAL: {
        "ID": MSG_C_RECEIVED_SIGNAL,
        "BYTE": b"K",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Received Signal",
        "DESC": "The client sends a signal to indicate that it has received the 'Go' message and is ready to proceed."
    },
    MSG_C_DONE_SIGNAL: {
        "ID": MSG_C_DONE_SIGNAL,
        "BYTE": b"!",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Done Signal",
        "DESC": "The client sends a signal to indicate the completion of its tasks."
    },
    MSG_C_STILL_WORKING_SIGNAL: {
        "ID": MSG_C_STILL_WORKING_SIGNAL,
        "BYTE": b"W",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Still Working Signal",
        "DESC": "The client can periodically send a signal to inform the server that it is still actively working on its tasks."
    },
    MSG_C_I_AM_HERE_BUT_NOT_WORKING: {
        "ID": MSG_C_I_AM_HERE_BUT_NOT_WORKING,
        "BYTE": b".",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "I Am Here But Not Working Message",
        "DESC": "The client sends a signal to indicate that it is still connected but not actively working."
    },
    MSG_C_ARE_YOU_THERE: {
        "ID": MSG_C_ARE_YOU_THERE,
        "BYTE": b"?",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Are You Still There? Message",
        "DESC": "The client can inquire if the server is still connected and active."
    },
    MSG_C_EXIT_SIGNAL: {
        "ID": MSG_C_EXIT_SIGNAL,
        "BYTE": b"X",
        "ORIGIN": "CLIENT",
        "LENGTH": 1,
        "STRUCTURE": "B",  # byte
        "TITLE": "Client Exit Signal",
        "DESC": "The client sends a signal to indicate its exit or termination."
    },
    # Add more client message entries here as needed
}



def reset():
    """used by test code"""
    g["MSG"] = None
    g["ANALYSIS"] = None


def set(msg):
    assert isinstance(msg, bytes)
    g["MSG"] = msg

def get():
    return g["MSG"]


def new(msg_type, addl_bytes=b""):
    info = msg_info[msg_type]
    assert info["ORIGIN"] == "SERVER"
    g["MSG"] = info["BYTE"]+addl_bytes
    assert len(g["MSG"]) == info["LENGTH"]


def new_selfid():
    new(MSG_S_SELFID, constants.PROTOCOL_VERSION+configinfo.config["serverid_12asciibytes"])

def new_server_go(i):
    new(MSG_S_GO, create_little_endian_integer(i))

def new_broadcast_shutdown(i):
    new(MSG_S_BROADCAST_SHUTDOWN, create_little_endian_integer(i))


def analyze_received():
    """Returns info on message received.
    
    Returns:
    {
      "INFO": (info dictionary)
      "PROTOCOL-VERSION": (version byte)  -- for MSG_C_SELFID
      "CLIENT-IDENTIFICATION": (12 byte client ID)  -- for MSG_C_SELFID
    }
    """
    assert len(g["MSG"]) > 0
    assert isinstance(g["MSG"], bytes)
    for info in msg_info.values():
        if info["ORIGIN"] != "CLIENT":
            continue
        if info["BYTE"][0] != g["MSG"][0]:
            continue
        break
    else:
        raise exceptions.ClientMessageUnrecognized(g["MSG"])
    g["ANALYSIS"] = D = {"INFO": info}
    if "AUTOPARSE" in info:
        for (a,b,key) in info["AUTOPARSE"]:
            D[key] = g["MSG"][a:b]
    return D


def create_little_endian_integer(i):
    # Pack the integer as a little-endian 32-bit integer
    assert i <= constants.MAXINT
    
    packed_bytes = struct.pack('<I', i)

    return packed_bytes

def read_little_endian_integer(bb):
    # Unpack the little-endian byte representation as a 32-bit integer
    unpacked_value = struct.unpack('<I', bb)

    return unpacked_value[0]



