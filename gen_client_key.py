#!/usr/bin/python3

import os
import re
import subprocess
import sys
from shutil import copy2
from sys import argv

from py.config_json import GetJSONConfig
from py.make_mobileconfig import MakeMobileconfig

CA_CERT_NAME = "/etc/ipsec.d/cacerts/ca.pem"
CERTS_DIR = "/etc/ipsec.d/certs/"
PRIVATE_DIR = "/etc/ipsec.d/private/"


def GetCASubjectCN():
    """
    Extracting issuer common name from CA certificate
    :return: issuer common name without "CN=" prefix
    """
    output = subprocess.check_output(f"ipsec pki --print --in {CA_CERT_NAME}", shell=True)
    output = output.decode(encoding="ascii")

    m = re.search(r"subject:\s+\"CN=([\w.]+)\"", output)
    if m.lastindex == 1:
        return m.group(1)

    return ""


argc = len(argv)
if argc == 3:
    command = argv[1]
    clientName = argv[2]
    wrongUsage = command[0] != "-"
else:
    wrongUsage = True

if wrongUsage:
    print("Usage:\n")
    print("./gen_client_keys.py -[awk] <client name>\n")
    print("Commands:")
    print("    -a - generate .mobileconfig for Apple devices")
    print("    -w - generate .pfx certificate for Windows")
    print("    -k - keep pem-certificate and private key")
    sys.exit(1)

if " " in clientName:
    print("No spaces allowed in client name")
    sys.exit(1)

conf = GetJSONConfig("config.json")
serverName = conf["serverName"]
serverAddr = conf["serverAddr"]

certKeyFileName = CERTS_DIR + clientName + ".pem"
privateKeyFileName = PRIVATE_DIR + clientName + ".pem"

res = subprocess.run(["sh", "genclientcert.sh", clientName, serverName, serverAddr], check=True)

# Preparing output folder
if not os.path.isdir("clients"):
    os.mkdir("clients")

outDir = "clients/" + clientName
if not os.path.isdir(outDir):
    os.mkdir(outDir)
outDir += '/'

# Generating certs for Apple devices
if "a" in command:
    mobileConfig = outDir + clientName + ".mobileconfig"
    issuerName = GetCASubjectCN()

    MakeMobileconfig(mobileConfig, clientName, issuerName if issuerName != "" else serverName, conf)

    print(f"'{mobileConfig}' was generated successfully")

# Generating certs for Windows devices
if "w" in command:
    pfxName = outDir + clientName + ".pfx"
    print("\nGenerating PFX certificate for Windows. Prepare to enter protection password.")
    res = subprocess.run(["openssl", "pkcs12", "-export",
                          "-in", certKeyFileName,
                          "-inkey", privateKeyFileName,
                          "-out", pfxName], check=True)

    psScriptName = outDir + clientName + ".ps1"

    with open("template/powershell.template", "r", encoding="ascii") as f:
        vpnConnName = conf["serverName"].capitalize() + " IKEv2"

        s = f.read()
        s = s.replace("VPN_CONN_NAME", vpnConnName)
        s = s.replace("SERVER_ADDR", conf["serverAddr"])

        with open(psScriptName, "w", encoding="ascii") as fw:
            fw.write(s)

    copy2(CA_CERT_NAME, outDir)

    print(f"'{pfxName}' and '{psScriptName}' generated successfully")

if "k" not in command:
    os.remove(certKeyFileName)
    os.remove(privateKeyFileName)
    print("Certificate and private key removed")
