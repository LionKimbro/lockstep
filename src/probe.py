import menus
from menus import g
from menus import out, inp, say
from menus import ACTION, CMD, PARTS, REST, DONE
from menus import LOCALS, GLOBALS
from menus import defaultfn

import timectrl
import configinfo
import reporting
import commsgate
import logicalconductor
import messagelogic
import scripts


help_str = """
Lockstep System -- conductor.py Probe                               (command handling)   alias
                                                                    ------------------   -----
RESET  -- reset logicalconductor, commsgate                         passthrough          0

CLIENT #   -- simulate operations as a specific connection          passthrough          C
CONN  -- simulate connecting                                        passthrough          CON
DISCONN  -- simulate disconnecting                                  passthrough          X
SIG A1  -- simulate sending an A1 record                            passthrough            -
SIG <letter>  -- simulate sending a single character record         passthrough            -

LOOP  -- have the server process a single round of messages         passthrough          L
LOOPS  -- have the server process until there are no more messages  passthrough          LL

MSGS  -- output summary of commsgate.py messages in current state   (probe-internal)     M
         (not recorded)
CONNS  -- output summary of logicalconductor.py connections         (probe-internal)     CC
         in current state (not recorded)
STATE  -- (MSGS + CONNS)                                            (probe-internal)
CORRECT  -- when recording:  asserts that the messages in current state are correct      Y
            when playing back:  checks that the messages match what is expected
                                                                    passthrough
REM  -- does nothing, but attaches a note into the recording        passthrough          ;
TIMEPASSES #  -- cause # seconds of pseudo-time to pass             passthrough          TIME

SCRIPTS  -- list all scripts (#, title)                             callthrough          SS
SCRIPT #  -- select a script by number                              callthrough          S
TITLE! <...>  -- set a title for the script                         callthrough          T!
TITLE?  -- print the title for the script                           callthrough          T

REC!  -- begin recording for the script                             callthrough          R!
REC.  -- cease recording for the script                             callthrough          R.
PLAY  -- playback a script; output success or failure, remain at state of failure        P
                                                                    callthrough
NEXT  -- attempt to execute next instruction                        callthrough          .
LIST  -- list commands of current script (pretty-print)             callthrough          ??

LOAD  -- reload scripts (scripts.json)                              callthrough            -
SAVE  -- save scripts (scripts.json)                                callthrough            -
"""

initial_locals = {"SZIN": None,
                  "SZOUT": None,
                  "SZNEW": None,
                  "SZDIS": None}

initial_aliases = {"0": "RESET",
                   "C": "CLIENT",
                   "CON": "CONN",
                   "X": "DISCONN",
                   "XCON": "DISCONN",
                   "L": "LOOP",
                   "LL": "LOOPS",
                   "M": "MSGS",
                   "CC": "CONNS",
                   "CONNECTIONS": "CONNS",
                   "YES": "CORRECT",
                   "Y": "CORRECT",
                   ";": "REM",
                   "TIME": "TIMEPASSES",
                   "S": "SCRIPT",
                   "SS": "SCRIPTS",
                   "T": "TITLE?",
                   "T?": "TITLE?",
                   "T!": "TITLE!",
                   "R!": "REC!",
                   "R.": "REC.",
                   "P": "PLAY",
                   "RUN": "PLAY",
                   ".": "NEXT",
                   "??": "LIST"}

strings = {
    "HELP": help_str,
    "COMMANDNOTFOUND": "command not found: $CMD\n",
    "STATUS": "probe -- inbox: $SZIN  outbox: $SZOUT  newconn: $SZNEW  disconn: $SZDIS\n",
    "PROMPT": "probe ($SZIN/$SZOUT/$SZNEW/$SZDIS)> ",
    "PLAYBACKFAILED": "playback failed!  -- system state NOT reset, you're at the crash point; MSGS to see messages state; NOT recording",
    "INCORRECT": "next instruction execution failed test  -- MSGS to see messages state; NOT recording"
}


pass_to_scripts = {
    "RESET": "C",    # "C": just the cmd
    "CLIENT": "C#",  # "C#": cmd, one numerical arg
    "CONN": "C",
    "DISCONN": "C",
    "SIG": "Cs",  # "Cs": cmd, one string arg
    "LOOP": "C",
    "LOOPS": "C",
    "CORRECT": "C",
    "REM": "C-",  # "C-": cmd, rest
    "TIMEPASSES": "C#"
}

def state_cmd():
    reporting.output("\n\nSTATE:\n\n")
    reporting.report_messages_summary()
    reporting.output("\n\n")
    reporting.report_connections_summary()
    reporting.output("\n")

exec_fn = {
    "SCRIPTS": (scripts.print_scripts, "!"),
    "SCRIPT": (scripts.sel_script, "!#"),
    "TITLE!": (scripts.set_title, "!s"),
    "TITLE?": (scripts.print_title, "!"),
    "REC!": (scripts.start_recording, "!"),
    "REC.": (scripts.stop_recording, "!"),
    "PLAY": (scripts.play_recording, "!"),
    "NEXT": (scripts.next_instruction, "!"),
    "LIST": (scripts.list_instructions, "!"),
    "LOAD": (scripts.load, "!"),
    "SAVE": (scripts.save, "!"),
    
    "MSGS": (reporting.report_messages_summary, "!"),
    "CONNS": (reporting.report_connections_summary, "!"),
    "STATE": (state_cmd, "!")
}


def update_size_vars():
    # values used in status display, prompt display
    g[LOCALS]["SZIN"] = len(commsgate.inbox)
    g[LOCALS]["SZOUT"] = len(commsgate.outbox)
    g[LOCALS]["SZNEW"] = len(commsgate.newconn)
    g[LOCALS]["SZDIS"] = len(commsgate.disconn)

def playback_script_failed():
    # called when playback didn't meet expectations
    say("PLAYBACKFAILED")

def main_menu():
    update_size_vars()
    if g[ACTION] == CMD:
        if mode := pass_to_scripts.get(g[CMD]):
            if mode == "C":
                scripts.do([g[CMD]])
            elif mode == "C#":
                scripts.do([g[CMD], int(g[PARTS][0])])
            elif mode == "Cs":
                scripts.do([g[CMD], g[PARTS][0]])
            elif mode == "C-":
                scripts.do([g[CMD], g[REST]])
            g[DONE] = True
        elif found := exec_fn.get(g[CMD]):
            (fn, mode) = found
            if mode == "!":
                result = fn()
            elif mode == "!#":
                fn(int(g[PARTS][0]))
            elif mode == "!s":
                fn(g[PARTS][0])
            if g[CMD] == "PLAY" and result == False:
                playback_script_failed()
            g[DONE] = True
    if g[DONE] is False:
        defaultfn()

def setup():
    timectrl.g["TIMEOVERRIDE"] = 1688936040  # fixed so that scripts don't freak out
    configinfo.load()
    scripts.load()
    reporting.g["OUTPUT"] = out  # use the menu system's output function
    logicalconductor.reset()
    logicalconductor.setup()
    commsgate.reset()
    menus.register("main-menu", main_menu, initial_locals, strings, initial_aliases)

if __name__ == "__main__":
    setup()
    menus.run("main-menu")
