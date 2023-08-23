"""reporting  -- reporting control

Pretty much anything that would print, or otherwise output status
reports, should go through here.

Print/reporting state can be controlled here.
"""

import json

from configinfo import config

g = {"OUTPUT": None,  # "PRINT", None, or a function
     "WRITESTATUS": None}  # True, or False


def output(s):
    if g["OUTPUT"] == None:  # "I don't want to hear it."
        pass
    elif g["OUTPUT"] == "PRINT":  # default behavior
        print(s, sep='', end='')
    else:
        g["OUTPUT"](s)  # used by probe.py, scripts.py


def report_initial_binding(ip_addr, port):
    output(f"Server started on {ip_addr}:{port}\n")


def report_new_connection(D):
    output(f"client connected -- {D['IPADDR']}:{D['PORT']}\n")

def report_client_selfid(D):
    output(f"client identified -- {D['IPADDR']}:{D['PORT']}: {D['IDENTIFICATION']} (protocol version: {D['VERSION']})\n")

def report_disconnection(D):
    output(f"client disconnected -- {D['IPADDR']}:{D['PORT']} (id was: {D['IDENTIFICATION']})\n")


def report_server_stopped():
    output(f"Server stopped.\n")



def report_messages_summary():
    import commsgate
    out = lambda s: output(s+"\n")
    out("Inbox:")
    out("CONN MSG")
    out("---- ---")
    for message in commsgate.inbox:
        conn = str(message["CONN"])
        msg = message["MSG"].decode("ascii")
        out(f"{conn:<4} {msg}")
    
    out("\nOutbox:")
    out("CONN MSG")
    out("---- ---")
    for message in commsgate.outbox:
        conn = str(message["CONN"])
        msg = message["MSG"].decode("ascii")
        out(f"{conn:<4} {msg}")
    
    out("\nNew Connections:")
    out("CONN IPADDR       PORT")
    out("---- ------------- ----")
    for connection in commsgate.newconn:
        conn = str(connection["CONN"])
        ipaddr = connection["IPADDR"]
        port = str(connection["PORT"])
        out(f"{conn:<4} {ipaddr:<13} {port}")
    
    out("\nDisconnected Connections:")
    out("CONN")
    out("----")
    for connection in commsgate.disconn:
        conn = str(connection["CONN"])
        out(f"{conn}")

def report_connections_summary():
    import logicalconductor
    out = lambda s: output(s+"\n")
    out("Connections:")
    out("CONNID IDENTIFICATION VERSION IPADDR       PORT CONNECTEDAT")
    out("------ -------------- ------- ------------- ---- -----------")
    for connid, connection in logicalconductor.conns.items():
        connid = str(connid)
        identification = connection["IDENTIFICATION"] or ""
        version = connection["VERSION"] or ""
        ipaddr = connection["IPADDR"]
        port = str(connection["PORT"])
        connected_at = str(connection["CONNECTEDAT"])
        out(f"{connid:<6} {identification:<14} {version:<7} {ipaddr:<13} {port:<4} {connected_at}")


def write_status_txt(selfid_str,
                     curtime_timestamp,
                     start_timestamp,
                     clients_info_list):
    status = f"Conductor: {selfid_str} (RUNNING; Timestamp: {curtime_timestamp}) (Started: {start_timestamp})\n"
    
    for client_info in clients_info_list:
        connid = client_info["CONNID"]
        identification = client_info["IDENTIFICATION"] or "(unidentified)"
        version = client_info["VERSION"] or "(unannounced-ver)"
        ip_address = client_info["IPADDR"]
        port = client_info["PORT"]
        connected_at = client_info["CONNECTEDAT"]
        status += f"{identification} #{connid} [{version}] ({ip_address}, {port}) [connected: {connected_at}]\n"

    if not g["WRITESTATUS"]:
        return
    
    with open(config["status.txt"], "w") as txt_file:
        txt_file.write(status)

def write_status_json(selfid_str,
                      curtime_timestamp,
                      start_timestamp,
                      clients_info_list):
    if not g["WRITESTATUS"]:
        return
    
    with open(config["status.json"], "w") as json_file:
        status_json = {"CONDUCTOR": selfid_str,
                       "START_TIMESTAMP": start_timestamp,
                       "TIMESTAMP": curtime_timestamp,
                       "CLIENTS": [],
                       "STATE": "RUNNING"}
        for client_info in clients_info_list:
            connid = client_info["CONNID"]
            identification = client_info["IDENTIFICATION"] or "(unidentified)"
            version = client_info["VERSION"] or "(unidentified)"
            ip_address = client_info["IPADDR"]
            port = client_info["PORT"]
            connected_at = client_info["CONNECTEDAT"]
            D = {"CONNID": connid,
                 "IDENTIFICATION": identification,
                 "VERSION": version,
                 "IPADDR": ip_address,
                 "PORT": port,
                 "CONNECTEDAT": connected_at}
            status_json["CLIENTS"].append(D)
        json.dump(status_json, json_file)


def write_closed_status_txt(selfid_str,
                            curtime_timestamp,
                            start_timestamp):
    status = f"Conductor: {selfid_str} (STOPPED; Timestamp: {curtime_timestamp}) (Started: {start_timestamp})\n"

    if not g["WRITESTATUS"]:
        return
    
    # Write to status.txt
    with open(config["status.txt"], "w") as txt_file:
        txt_file.write(status)

def write_closed_status_json(selfid_str,
                             curtime_timestamp,
                             start_timestamp):
    if not g["WRITESTATUS"]:
        return
    
    with open(config["status.json"], "w") as json_file:
        status_json = {"CONDUCTOR": selfid_str,
                       "START_TIMESTAMP": start_timestamp,
                       "TIMESTAMP": curtime_timestamp,
                       "CLIENTS": [],
                       "STATE": "STOPPED"}
        json.dump(status_json, json_file)


