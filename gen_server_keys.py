#!/usr/bin/python3

import subprocess
from sys import argv

argc = len(argv)
if argc == 3:
    serverName = argv[1]
    serverAddr = argv[2]
elif argc == 1:
    print("Usage:\n")
    print("./gen_server_keys.py <server name> <server address>")
else:
    print("Usage:\n")
    print("./gen_server_keys.py <server name> <server address>")

res = subprocess.run(["sh", "genservercerts.sh", serverName, serverAddr])

