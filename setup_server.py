#!/usr/bin/python3

import re
import subprocess
from sys import argv

argc = len(argv)
if argc == 4:
    command = argv[1]
    serverName = argv[2]
    serverAddr = argv[3]
    ipSubnet = argv[4]

    if command[0] == "-":
        if "s" in command:
            command = "cki"
        wrongUsage = False
    else:
        wrongUsage = True
else:
    wrongUsage = True

if wrongUsage:
    print("Usage:\n")
    print("./setup_server.py -[scki] <server name> <server address> <ip subnet>")
    print("Commands:")
    print("    -s - full setup")
    print("    -c - generate root CA keys and certificates")
    print("    -k - generate server keys and certificates")
    print("    -i - make ipsec.conf and ipsec.secrets")
    exit(1)

if " " in serverName + serverAddr:
    print("No spaces allowed in server name and address")
    exit(1)

print(ipSubnet)

#res = subprocess.run(["sh", "genservercerts.sh", serverName, serverAddr])

vpnCertName = serverName + ".pem"

# Making ipsec.conf and ipsec.secrets
if "i" in command:
    with open("ipsec.conf", "r") as f:
        s = f.read()
        s = s.replace("YOUR_VPN_IP", serverAddr)
        s = s.replace("YOUR_VPN_CERT", vpnCertName)

        with open("/etc/ipsec.conf", "w") as fw:
            fw.write(s)

        with open("/etc/ipsec.secrets", "w") as fw:
            fw.write(f"\n: RSA {vpnCertName}\n")
