"""scripts.py  -- scripts for testing Lockstep System conductor.py"""

import json
import pprint

import init
import timectrl
import reporting
import configinfo
import commsgate
import logicalconductor


g = {"STATE": "NORMAL",  # "RECORDING", "PLAYBACK", "INCORRECT"
     "CLIENT": 0,  # client number using
     "SCRIPT": None,  # presently selected script index (note: it's an integer turned into a string)
     "IP": None}  # current instruction pointer value

"""scripts

{"#": {
        "TITLE": "...",
        "CREATED": (timestamp),
        "COMMANDS": [ [CMD, arg, arg, ...],
                      ...
                    ]
    }
 ...
}
"""

scripts = {}

pseudo_ip = {
    0: "100.100.100.100",
    1: "200.200.200.200",
    2: "127.0.0.1",
    10: "255.255.255.255",  # buggy on purpose
    11: "0.0.0.0",  # buggy on purpose
    "default": "10.53.16.44"
}

pseudo_port = {
    0: 1045,
    1: 39454,
    2: 453323,
    10: 0,  # buggy on purpose
    11: -1,  # buggy on purpose
    "default": 8000
}

pseudo_selfid = {
    0: b"pseudo0.....",
    1: b"pseudo 1....",
    2: b"pseudo 2....",
    10: b"buggy -- too long",  # buggy on purpose
    11: b"too short",  # buggy on purpose
    "default": b"123456789012"
}


def commands():
    """shortcut to current script's commands"""
    return scripts[g["SCRIPT"]]["COMMANDS"] if g["SCRIPT"] else None


# load
def load():
    with open(configinfo.config["scripts.json"], "r") as scripts_file:
        scripts.clear()
        scripts.update(json.load(scripts_file))


# save
def save():
    with open(configinfo.config["scripts.json"], "w") as scripts_file:
        json.dump(scripts, scripts_file, indent=2)


# do(L)
def do(L):
    if g["STATE"] == "RECORDING":
        commands().append(L)
    cmd = L[0]
    if cmd == "REM":
        pass  # this is just for putting notes into the recording
    elif cmd == "RESET":
        init.init_server_test()
        g["CLIENT"] = 0
    elif cmd == "CLIENT":
        g["CLIENT"] = L[1]
    elif cmd == "CONN":
        ip = pseudo_ip.get(g["CLIENT"], pseudo_ip["default"])
        port = pseudo_port.get(g["CLIENT"], pseudo_port["default"])
        commsgate.add_conn(g["CLIENT"], ip, port)
    elif cmd == "DISCONN":
        commsgate.rm_conn(g["CLIENT"])
    elif cmd == "SIG":
        if L[1] == "A1":
            selfid = pseudo_selfid[g["CLIENT"]]
            commsgate.add_inbox(g["CLIENT"], b"A1" + selfid)
        else:
            commsgate.add_inbox(g["CLIENT"], L[1].encode("ascii"))
    elif cmd == "LOOP":
        logicalconductor.loop_once()
    elif cmd == "LOOPS":
        runs = 0
        maxruns = 20
        while runs < maxruns and commsgate.pending():
            logicalconductor.loop_once()
            runs += 1
        if runs == maxruns:
            raise AssertionError(f"logicalconductor.loop_once() ran {maxruns} time -- aborting",
                                 {"inbox len": len(commsgate.inbox),
                                  "outbox len": len(commsgate.outbox),
                                  "newconn len": len(commsgate.newconn),
                                  "disconn len": len(commsgate.disconn)})
    elif cmd == "CORRECT":
        if g["STATE"] == "RECORDING":
            # when recording, append the current messages state as a kind of argument
            commands()[-1].append(commsgate.snapshot())
            # when recording, append the current connections state as a kind of argument
            commands()[-1].append(logicalconductor.snapshot())
        elif g["STATE"] == "PLAYBACK":
            correct_a = commsgate.compare(L[1])
            correct_b = logicalconductor.compare(L[2])
            if not correct_a or not correct_b:
                g["STATE"] = "INCORRECT"
    elif cmd == "TIMEPASSES":
        timectrl.advance(L[1])
    if g["STATE"] in {"PLAYBACK", "RECORDING"}:
        g["IP"] += 1


def sel_script(n):
    strkey = str(n)
    g["SCRIPT"] = strkey
    g["IP"] = 0
    if strkey not in scripts:
        scripts[strkey] = {"TITLE": "(untitled)",
                           "CREATED": timectrl.now(),
                           "COMMANDS": []}

def set_title(ttl):
    scripts[g["SCRIPT"]]["TITLE"] = ttl

def print_title():
    reporting.output(scripts[g["SCRIPT"]]["TITLE"]+"\n")

def print_scripts():
    for key, data in scripts.items():
        reporting.output(f"""{key}. {scripts[key]["TITLE"]}\n""")


def start_recording():
    g["STATE"] = "RECORDING"
    scripts[g["SCRIPT"]]["COMMANDS"][:] = []

def stop_recording():
    g["STATE"] = "NORMAL"

def play_recording():
    """Playback current scripts' recording.
    
    Return True if it plays back successfully.
    Returns False (and leaves the script at the broken point) if it does not meet expectations.
      -- that is, if the state is INCORRECT, after a CORRECT statement is run.
    """
    g["STATE"] = "PLAYBACK"
    while g["IP"] < len(commands()) and g["STATE"] == "PLAYBACK":
        next_instruction()
    if g["STATE"] == "INCORRECT":
        result = False
    else:
        result = True
    g["STATE"] = "NORMAL"
    return result

def next_instruction():
    # get command at instruction pointer
    cmd = commands()[g["IP"]]
    
    do(cmd)

def list_instructions():
    out = lambda s: reporting.output(s+"\n")
    for (i, L) in enumerate(commands()):
        cue = ">" if i == g["IP"] else "."
        lnstr = f"{i}{cue} "
        if L[0] != "CORRECT":
            out(lnstr+" ".join([str(x) for x in L]))
        else:
            out(lnstr+"CORRECT")
    if g["IP"] == len(commands()):
        out("end>")
#    reporting.output(pprint.pformat(commands())+"\n")

