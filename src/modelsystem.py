
from decimal import Decimal

import snowflakes

import exceptions


g = {
    "TIME": None,  # current time, as a Decimal
    "CLIENT": None,  # current clients instance (or None, if in server role)
    "SIMULATION_LOOP_TIME_AMOUNT_STR": None  # how much to advance time per loop
}


"""server  -- modelling the server

{
  "EVENTS": [{"TYPE": "...", ...}, ...]
  "OUTBOX": []
  "TARGET": #  -- client under current consideration; say(...) will go to this client
}

server events:
  {"TYPE": "CONNECT": "CLIENT": #}  -- when a client initiated a connection
  {"TYPE": "DISCONNECT": "CLIENT": #}  -- when a client initiated a disconnection
  {"TYPE": "MSG", "CLIENT": #, "MSG": {...}}  -- when a client sent a message
"""

server = {
    "EVENTS": [],
    "OUTBOX": [],
    "TARGET": None
}


"""clients  -- state data for each client

{
  "ID": #
  "EVENTS": [{"TYPE": "...", ...}, ...]
}

client events:
  X -- there is NO client event for connecting;
       connecting is ALWAYS initiated by the client,
       and connecting is synchronous for the client,
       so it doesn't get an event for connecting
  "DISCONNECT"  -- when forcibly disconnected from the server
"""

clients = []


"""connections  -- simulation of connection state

It's a list of client #'s that have a connection with the server.
If the client's #
"""
connections = []


"""deletes  -- client objects that need to be deleted

At the end of a round, any client objects listed here will be deleted.
It's a list of client dictionaries.
"""
deletes = []


"""time_track

* kept sequentially
* always write to via a note_... fn

{
  "TIMESTAMP":  Decimal; fractional time stamp
  "SUBJECT":    # (a client) or "S" (server)
  "TYPE":       some std. str code of events type
 ?"DATA":       data particular to the event type
                (only exists if it has any)
}
"""
time_track = []

def advance_time(passtime_amt_str):
    g["TIME"] += Decimal(passtime_amt_str)

def note_connection(i):
    time_track.append({"TIMESTAMP": g["TIME"],
                       "SUBJECT": i,
                       "TYPE": "CONNECT"})

def note_disconnection(i):
    time_track.append({"TIMESTAMP": g["TIME"],
                       "SUBJECT": i,
                       "TYPE": "DISCONNECT"})

def note_client_delete(i):
    time_track.append({"TIMESTAMP": g["TIME"],
                       "SUBJECT": i,
                       "TYPE": "CLIENT-DELETED"})

def note_msg_to_server(from_client_id, msg):
    D = {"TIMESTAMP": g["TIME"],
         "SUBJECT": from_client_id,
         "TYPE": "MSG",
         "DATA": {"SENDER": from_client_id,
                  "RECEIVER": "S",
                  "MSG": msg}}

def note_msg_to_client(to_client_id, msg):
    D = {"TIMESTAMP": g["TIME"],
         "SUBJECT": to_client_id,
         "TYPE": "MSG",
         "DATA": {"SENDER": "S",
                  "RECEIVER": to_client_id,
                  "MSG": msg}}


"""expectations

* kept sequentially
* always write to via an expect_... fn
* test expectations via assert_time_order()

{
  "TYPE": "..."
  ...
 ?"FOUND": <time-track dictionary>  -- added once found
}
"""
expectations = []

def reset_expectations():
    expectations[:] = []

def expect_connection(i):
    expectations.append({"TYPE": "CONNECT",
                         "CLIENT": i})

def expect_disconnection(i):
    expectations.append({"TYPE": "DISCONNECT",
                         "CLIENT": i})



def new_client():
    """Create a new client, and immediately switch to it."""
    D = {"ID": snowflakes.next("CLIENTID"),
         "EVENTS": []}
    clients.append(D)
    switch_to_client(D["ID"])
    return D["ID"]

def find_client(i):
    """Return a client dictionary, given the id for the client dict."""
    for D in clients:
        if D["ID"] == i:
            return D
    else:
        raise ValueError(i)


def switch_to_server():
    g["CLIENT"] = None

def switch_to_client(i):
    g["CLIENT"] = find_client(i)


def in_client_role():
    return g["CLIENT"] is not None

def in_server_role():
    return g["CLIENT"] is None

def my_client_id():
    assert in_client_role()
    return g["CLIENT"]["ID"]


def add_server_evt(D):
    server["EVENTS"].append(D)

def add_client_evt(D):
    find_client(my_target_id())["EVENTS"].append(D)

def evts_queued():
    if in_client_role():
        return len(g["CLIENT"]["EVENTS"]) > 0
    elif in_server_role():
        return len(server["EVENTS"]) > 0
    else:
        raise exceptions.BadState()

def pop_evt():
    if in_client_role():
        return g["CLIENT"]["EVENTS"].pop(0)
    elif in_server_role():
        return server["EVENTS"].pop(0)
    else:
        raise exceptions.BadState()


def connect():
    """Connection simulator: connecting a client.
    
    This is always called from the standpoint of a client.
    """
    assert in_client_role()
    i = my_client_id()
    assert i not in connections
    connections.append(i)
    add_server_evt({"TYPE": "CONNECT",
                    "CLIENT": i})
    note_connection(i)

def disconnect():
    """Connection simulator: disconnecting a client.
    
    This can come from either the client or the server role.
    If the client, the client has chosen to disconnect.
    If the server, the server has chosen to disconnect.
    """
    if in_server_role():
        i = my_target_id()
    elif in_client_role():
        i = my_client_id()
    else:
        raise exceptions.BadState()
    assert i in connections
    connections.remove(i)
    time_track.append({"TIMESTAMP": g["TIME"],
                       "SUBJECT": i,
                       "TYPE": "DISCONNECT"})
    if in_client_role():
        add_server_evt({"TYPE": "DISCONNECT",
                        "CLIENT": i})
    if in_server_role():
        add_client_evt({"TYPE": "DISCONNECT"})


def target_client(i):
    assert in_server_role()
    server["TARGET"] = i

def my_target_id():
    assert in_server_role()
    return server["TARGET"]


def say(msg):
    if in_server_role():
        # Send the Message to the Client
        D = {"TYPE": "MSG",
             "MSG": msg}
        add_client_evt(D)
        
        # Note in the Time Track
        note_msg_to_client(my_target_id(), msg)
    
    elif in_client_role():
        assert my_client_id() in connections
        
        # Send the Message to the Server
        D = {"TYPE": "MSG",
             "MSG": msg,
             "CLIENT": my_client_id()}
        add_server_evt(D)

        # Note in the Time Track
        note_msg_to_server(my_client_id(), msg)


def live_server():
    switch_to_server()
    while evts_queued():
        D = pop_evt()
        if D["TYPE"] == "CONNECT":
            target_client(D["CLIENT"])
            say("HELLO")
        elif D["TYPE"] == "DISCONNECT":
            pass  # What it actually does, is drop info about the client
        elif D["TYPE"] == "MSG":
            if D["MSG"] == "HELLO":
                pass  # what it actually does, is note down some info about the client
            else:
                raise NotImplementedError("Server doesn't know how to handle this important message, yet.", D)
        else:
            raise NotImplementedError("Server doesnt't know how to handle this important event, yet.", D)

def live_client(client_id):
    switch_to_client(client_id)
    while evts_queued():
        D = pop_evt()
        if D["TYPE"] == "DISCONNECT":
            schedule_delete(client_id)  # it's as good as done
        elif D["TYPE"] == "MSG":
            if D["MSG"] == "HELLO":
                pass  # what it actually does, is note down some info about the server
            else:
                raise NotImplementedError("Client doesn't know how to handle this important message, yet.")
        else:
            raise NotImplementedError("Client doesn't know how to handle this important event, yet.")


def schedule_delete(client_id):
    deletes.append(client_id)
    note_client_delete(client_id)

def perform_deletes():
    for D in deletes:
        clients.remove(D)


def init():
    g["TIME"] = Decimal("0")
    g["ROLE"] = None
    g["SIMULATION_LOOP_TIME_AMOUNT_STR"] = "0.1"
    clients[:] = []
    connections[:] = []
    deletes[:] = []
    time_track[:] = []
    if not snowflakes.defined("CLIENTID"):
        snowflakes.define({"NAME": "CLIENTID", "DEFAULT": 0, "POLICY": "SESSION"})
    server["EVENTS"] = []
    server["OUTBOX"] = []
    reset_expectations()


def simulate_one_loop():
    live_server()
    for client_dict in clients:
        live_client(client_dict["ID"])
    perform_deletes()
    advance_time(g["SIMULATION_LOOP_TIME_AMOUNT_STR"])



def assert_time_order():
    """Check that the time track matches the current expectations list."""
    expi = 0  # expectation 
    tti = 0  # time track iterator
    while tti < len(time_track):
        eD = expectations[expi]  # current expectation dictionary
        tD = time_track[tti]  # current time-track dictionary
        match = False
        if eD["TYPE"] == "CONNECT":
            if tD["TYPE"] == "CONNECT":
                if tD["SUBJECT"] == eD["CLIENT"]:
                    match = True
        elif eD["TYPE"] == "DISCONNECT":
            if tD["TYPE"] == "DISCONNECT":
                if tD["SUBJECT"] == eD["CLIENT"]:
                    match = True
        if match:
            eD["FOUND"] = tD
            expi += 1
        tti += 1
        if expi == len(expectations):
            return
    raise AssertionError("not all expectations found on the time track")

