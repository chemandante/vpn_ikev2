#!/usr/bin/python3

import os
import subprocess
import sys
from sys import argv

from config_json import GetJSONConfig

CERTS_DIR = "/etc/ipsec.d/certs/"
PRIVATE_DIR = "/etc/ipsec.d/private/"

argc = len(argv)
if argc == 3:
    command = argv[1]
    clientName = argv[2]
    wrongUsage = command[0] != "-"
else:
    wrongUsage = True

if wrongUsage:
    print("Usage:\n")
    print("./gen_client_keys.py -[awk] <client name> <server name> <server address>\n")
    print("Commands:")
    print("    -a - generate .mobileconfig for Apple devices")
    print("    -w - generate .pfx certificate for Windows")
    print("    -k - keep private key")
    sys.exit(1)

if " " in clientName:
    print("No spaces allowed in client and server names, as well as in the address")
    sys.exit(1)

conf = GetJSONConfig("config.json")
serverName = conf["serverName"]
serverAddr = conf["serverAddr"]

privateKeyFileName = PRIVATE_DIR + clientName + ".pem"

res = subprocess.run(["sh", "genclientcert.sh", clientName, serverName, serverAddr], check=True)

if "a" in command:
    if not os.path.isdir("apple"):
        os.mkdir("apple")
    mobileConfig = "apple/" + clientName + ".mobileconfig"
    with open(mobileConfig, "w", encoding="ascii") as f:
        res = subprocess.run(["zsh", "mobileconfig.sh", clientName, serverName, serverAddr], stdout=f, check=True)
    print(f"'{mobileConfig}' was generated successfully")

if "w" in command:
    if not os.path.isdir("win"):
        os.mkdir("win")
    pfxName = "win/" + clientName + ".pfx"
    print("\nGenerating PFX certificate for Windows. Prepare to enter protection pasword.")
    res = subprocess.run(["openssl", "pkcs12", "-export",
                          "-in", CERTS_DIR + clientName + ".pem",
                          "-inkey", privateKeyFileName,
                          "-out", pfxName], check=True)

    psScriptName = "win/" + clientName + ".ps1"

    with open("template/powershell.template", "r", encoding="ascii") as f:
        vpnConnName = conf["serverName"].capitalize() + " IKEv2"

        s = f.read()
        s = s.replace("VPN_CONN_NAME", vpnConnName)
        s = s.replace("SERVER_ADDR", conf["serverAddr"])

        with open(psScriptName, "w", encoding="ascii") as fw:
            fw.write(s)

    print(f"'{pfxName}' and '{psScriptName}' generated successfully")

if "k" not in command:
    os.remove(privateKeyFileName)
    print(f"Private key in '{privateKeyFileName}' removed")
