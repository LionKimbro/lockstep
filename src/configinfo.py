"""configinfo.py  -- conductor.py config information

During testing, config may be overwritten by test processes.
"""


CONFIG_FILE = "config.json"


"""config  -- generally, read from CONFIG_FILE

{
    "ipaddress": "xxx.xxx.xxx.xxx"              -- IP address to bind to
    "port": ####                                -- port to bind to
    "status.txt": "C:/.../.../status.txt"       -- path to status.txt
    "status.json": "C:/.../.../status.json"     -- path to status.json
    "serverid_12asciibytes": "conductor v1"     -- self-ID for server
    "scripts.json": "C:/.../.../scripts.json"   -- scripts.json location (if using)
}
"""

import json


keys = ["ipaddress",
        "port",
        "status.txt",
        "status.json",
        "serverid_12asciibytes",
        "scripts.json"]

config = {key: None for key in keys}  # will be replaced at load time


def load():
    with open(CONFIG_FILE, "r") as config_file:
        config.clear()
        config.update(json.load(config_file))
        for key in keys:
            assert key in config
        config["serverid_12asciibytes"] = config["serverid_12asciibytes"].encode("ascii")
        assert len(config["serverid_12asciibytes"]) == 12

