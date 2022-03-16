#!/usr/bin/python3

import os
import subprocess
from sys import argv

CERTS_DIR = "/etc/ipsec.d/certs/"
PRIVATE_DIR = "/etc/ipsec.d/private/"

argc = len(argv)
if argc == 5:
    command = argv[1]
    clientName = argv[2]
    serverName = argv[3]
    serverAddr = argv[4]
else:
    print("Usage:\n")
    print("./gen_client_keys.py <commands> <client name> <server name> <server address>\n")
    print("Commands:")
    print("    a - generate .mobileconfig for Apple devices")
    print("    w - generate .pfx certificate for Windows")
    print("    k - keep private key")

    exit(1)

if " " in clientName + serverName + serverAddr:
    print("No spaces allowed in client and server names, as well as in the address")
    exit(1)

privateKeyFileName = PRIVATE_DIR + clientName + ".pem"

res = subprocess.run(["sh", "genclientcert.sh", clientName, serverName, serverAddr])

if "a" in command:
    mobileConfig = clientName + ".mobileconfig"
    with open(mobileConfig, "w") as f:
        res = subprocess.run(["zsh", "mobileconfig.sh", clientName, serverName, serverAddr], stdout=f)
    print(f"{mobileConfig} was generated successfully")

if "w" in command:
    pfxName = clientName + ".pfx"
    print("\nGenerating PFX certificate for Windows. Prepare to enter protection pasword.")
    res = subprocess.run(["openssl", "pkcs12", "-export",
                          "-in", CERTS_DIR + clientName + ".pem",
                          "-inkey", privateKeyFileName,
                          "-out", pfxName])
    print(f"{pfxName} was generated successfully")

if "k" not in command:
    os.remove(privateKeyFileName)
    print(f"{privateKeyFileName} was removed")
