#!/usr/bin/python3

import json

CONF_FIELDS = ("serverName", "serverAddr", "ipSubnet")


def GetJSONConfig(filename: str):
    """
    Reading JSON config file
    :param filename:
    :return: Dict of parameters
    """
    with open(filename, "r", encoding="ascii") as f:
        conf = json.load(f)
        wrongConfig = False

        for field in CONF_FIELDS:
            if field not in conf:
                print(f"No '{field}' field in config.json")
                wrongConfig = True

        if wrongConfig:
            raise ValueError()

    return conf
