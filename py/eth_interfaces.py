#!/usr/bin/python3

import re
import subprocess


def SelectInterface():
    # Run 'ip link show' and save stdout for parsing
    output = subprocess.check_output("ip link show", shell=True).decode(encoding="ascii")

    ethList = []
    eth = {}
    i = 0

    # Parse stdout to enumerate all interfaces
    for line in output.splitlines():
        m = re.match(r"\d+:\s+(\w+):", line)
        if m:
            eth["name"] = m.group(1)
        else:
            m = re.match(r"\s*link/(\w+)\s+([0-9a-f:]+)", line)
            if m and m.group(1) == "ether":
                eth["mac"] = m.group(2)
                if "name" in eth:
                    i += 1
                    ethList.append(eth)
                    eth = {}

    if i > 1:
        print(f"{i} network interfaces found:")
        for i, eth in enumerate(ethList):
            print(f"{i + 1}. '{eth['name']}' ({eth['mac']})")

        ethIdx = int(input(f"Select interface [1-{i}]: "))
        if 0 < ethIdx <= i:
            ethIdx -= 1
        else:
            print("Wrong selection, script stopped")
            return None

    elif i == 1:
        print(f"The only network interface found is '{ethList[0]['name']}' ({ethList[0]['mac']})")
        ethIdx = 0

    else:
        print("No network interface found, script stopped")
        return None

    return ethList[ethIdx]["name"]
