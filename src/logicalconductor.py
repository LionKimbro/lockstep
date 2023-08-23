import constants
import timectrl
import configinfo
import reporting
import commsgate
import messagelogic


g = {"TALKING_TO": None,  # a connid
     "LAST_STATUSREPORT_TIMESTAMP": None}


"""conns  -- dictionary of all connections interacting with

{connid : {"CONNID": number, <id(socket) in real sockets>
           "IDENTIFICATION": None,  -- will be 12 bytes when populated
           "VERSION": None,  -- should be b"1" after populated
           "IPADDR": "xxx.xxx.xxx.xxx",
           "PORT": ####,
           "CONNECTEDAT": <timestamp#>,
           "STATE": <state>,
           "LASTHEARD": <timestamp#>
           "LASTHEARDMSG": <one byte> or None (connection freshly minted)},
 ...}

<state>: "NEW"   -- newly added, never received a message
         "TOLD"  -- has been issued a GO command
         "GOING" -- has acknowledge receipt of the GO command
         "DONE"  -- has reported in as DONE
"""
conns = {}  # connid: {...}


def reset():
    """Used during testing -- restore to original state."""
    conns.clear()


def sanitized_connections():
    """Return list of connections, sanitized for reporting.write_status_txt/json.
    
    That means, no bytes.
    """
    def asc(bytes_or_none):
        if bytes_or_none is None:
            return None
        else:
            return bytes_or_none.decode("ascii")
    L = []
    for D in conns.values():
        L.append({"CONNID": D["CONNID"],
                  "IDENTIFICATION": asc(D["IDENTIFICATION"]),
                  "VERSION": asc(D["VERSION"]),
                  "IPADDR": D["IPADDR"],
                  "PORT": D["PORT"],
                  "CONNECTEDAT": D["CONNECTEDAT"]})
    return L


def talking_to(connid):
    g["TALKING_TO"] = connid

def send():
    assert isinstance(messagelogic.g["MSG"], bytes)
    commsgate.add_outbox(g["TALKING_TO"], messagelogic.g["MSG"])

def send_A_msg():
    messagelogic.new_selfid()
    send()


def new_connection(connid, ipaddr, port):
    now = timectrl.now()
    talking_to(connid)
    D = {"CONNID": connid,
         "IDENTIFICATION": None,
         "VERSION": None,
         "IPADDR": ipaddr,
         "PORT": port,
         "CONNECTEDAT": now,
         "STATE": "NEW",
         "LASTHEARD": now,
         "LASTHEARDMSG": None}
    conns[connid] = D
    reporting.report_new_connection(D)
    
    # Send server's identification to the client
    send_A_msg()


def rm_connection(connid):
    reporting.report_disconnection(conns[connid])
    del conns[connid]


def message_received(connid, msg):
    # Note who I'm talking to.
    talking_to(connid)
    
    # Load info about the message.
    messagelogic.set(msg)
    analysis = messagelogic.analyze_received()
    msg_id = analysis["INFO"]["ID"]
    
    # Note generally that we've heard from the client
    client_info = conns[g["TALKING_TO"]]
    client_info["LASTHEARD"] = timectrl.now()
    client_info["LASTHEARDMSG"] = analysis["INFO"]["BYTE"]
    
    if msg_id == messagelogic.MSG_C_SELFID:
        received_selfid()
    elif msg_id == messagelogic.MSG_C_RECEIVED_SIGNAL:
        received_received_signal()
    elif msg_id == messagelogic.MSG_C_DONE_SIGNAL:
        received_done_signal()

def received_selfid():
    # ONLY TO BE CALLED BY: message_received
    
    # A record -> identification, version
    analysis = messagelogic.g["ANALYSIS"]
    assert "IDENTIFICATION" in analysis
    assert "VERSION" in analysis
    identification = analysis["IDENTIFICATION"]
    version = analysis["VERSION"]
    
    # identification, version -> connections records
    client_info = conns[g["TALKING_TO"]]
    client_info["IDENTIFICATION"] = identification
    client_info["VERSION"] = version
    
    # Output to reporting, that we've identified the client
    reporting.report_client_selfid(client_info)

def received_received_signal():
    # ONLY TO BE CALLED BY: message_received
    client_info = conns[g["TALKING_TO"]]
    assert client_info["STATE"] == "TOLD"
    client_info["STATE"] = "GOING"

def received_done_signal():
    # ONLY TO BE CALLED BY: message_received
    client_info = conns[g["TALKING_TO"]]
    assert client_info["STATE"] == "GOING"
    client_info["STATE"] = "DONE"


def update():
    update_status_files()

def update_status_files():
    current_time = timectrl.now()
    if not g["LAST_STATUSREPORT_TIMESTAMP"] or (current_time - g["LAST_STATUSREPORT_TIMESTAMP"] >= 1):
        g["LAST_STATUSREPORT_TIMESTAMP"] = current_time
        selfid_str = configinfo.config["serverid_12asciibytes"].decode()
        curtime_timestamp = current_time
        start_timestamp = timectrl.g["START_TIMESTAMP"]
        clients_info_list = sanitized_connections()
        reporting.write_status_txt(selfid_str,
                                   curtime_timestamp,
                                   start_timestamp,
                                   clients_info_list)
        reporting.write_status_json(selfid_str,
                                    curtime_timestamp,
                                    start_timestamp,
                                    clients_info_list)


def loop_once():
    while commsgate.newconn:
        D = commsgate.pop_newconn()
        new_connection(D["CONN"], D["IPADDR"], D["PORT"])

    while commsgate.disconn:
        D = commsgate.pop_disconn()
        rm_connection(D["CONN"])

    while commsgate.inbox:
        D = commsgate.pop_inbox()
        message_received(D["CONN"], D["MSG"])

    update()

def loop_terminated():
    for connid in conns:
        talking_to(connid)
        messagelogic.new(messagelogic.MSG_S_BROADCAST_SHUTDOWN)
        send()
        
    selfid_str = configinfo.config["serverid_12asciibytes"].decode()
    curtime_timestamp = timectrl.now()
    start_timestamp = timectrl.g["START_TIMESTAMP"]
    reporting.write_closed_status_txt(selfid_str,
                                      curtime_timestamp,
                                      start_timestamp)
    reporting.write_closed_status_json(selfid_str,
                                       curtime_timestamp,
                                       start_timestamp)
    reporting.report_server_stopped()


def snapshot():
    """Create a JSON-recordable snapshot of conns.
    
    Note that this is much more comprehensive than what goes to reporting.
    Reporting could be expanded, but I think it's okay as it is --
    I don't know that the outside world is interested in every single internal detail.
    Testing, however, is very interested in those details.
    """
    def bytes_replaced(D):
        DRET = {}
        for k, v in D.items():
            DRET[k] = v.decode("ascii") if isinstance(v, bytes) else v
        return DRET
    return {str(connid): bytes_replaced(conns[connid]) for connid in conns}

def compare(prior):
    return prior == snapshot()

