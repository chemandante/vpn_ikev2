#!/usr/bin/python3

import subprocess
from sys import argv

argc = len(argv)
if argc == 4:
    clientName = argv[1]
    serverName = argv[2]
    serverAddr = argv[3]
elif argc == 1:
    print("Usage:\n")
    print("./gen_client_keys.py <client name> <server name> <server address>\n")
    exit(1)
else:
    print("Usage:\n")
    print("./gen_client_keys.py <client name> <server name> <server address>\n")
    exit(1)

res = subprocess.run(["sh", "genclientcert.sh", clientName, serverName, serverAddr])
