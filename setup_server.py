#!/usr/bin/python3

import json
import os
import re
import subprocess
from sys import argv

CONF_FIELDS = ("serverName", "serverAddr", "ipSubnet")
IPSEC_KEYS_DIR = "/etc/ipsec.d/"


def GenCARootCertificate(config: dict, gen_private_key: bool):
    CAPrivName = IPSEC_KEYS_DIR + "private/ca.pem"

    if gen_private_key:
        print(f"\nGenerating CA root certificate for '{config['serverAddr']}'...")
        with open(CAPrivName, "w") as fp:
            subprocess.run(["ipsec", "pki", "--gen", "--type", "rsa", "--size", "4096", "--outform", "pem"], stdout=fp)

    with open(IPSEC_KEYS_DIR + "cacerts/ca.pem", "w") as fp:
        subprocess.run(["ipsec", "pki", "--self", "--ca", "--lifetime", "3650", "--in", CAPrivName,
                        "--type", "rsa", "--digest", "sha256", "--dn", f"CN={config['serverAddr']}",
                       "--outform", "pem"], stdout=fp)
    print("Done")


def GenServerCertificate(config: dict, gen_private_key: bool):
    CACertFileName = IPSEC_KEYS_DIR + f"cacerts/ca.pem"
    CAPrivFileName = IPSEC_KEYS_DIR + f"private/ca.pem"
    VPNCertFileName = IPSEC_KEYS_DIR + f"certs/{config['serverName']}.pem"
    VPNPrivFileName = IPSEC_KEYS_DIR + f"private/{config['serverName']}.pem"

    if gen_private_key:
        print(f"\nGenerating server certificate for '{config['serverAddr']}'...")
        with open(VPNPrivFileName, "w") as fp:
            subprocess.run(["ipsec", "pki", "--gen", "--type", "rsa", "--size", "2048", "--outform", "pem"], stdout=fp)

    output = subprocess.check_output(f"ipsec pki --pub --in {VPNPrivFileName} --type rsa | "
                                     f"ipsec pki --issue --lifetime 3650 --digest sha256 --cacert {CACertFileName} " 
                                     f"--cakey {CAPrivFileName} --dn \"CN={config['serverAddr']}\" "
                                     f"--san \"{config['serverAddr']}\" --flag serverAuth --outform pem", shell=True)

    with open(VPNCertFileName, "w") as fp:
        fp.write(output.decode(encoding="ascii"))

    print("Done")


conf = {}

#
# Reading config.json
#
with open("config.json", "r") as f:
    conf = json.load(f)
    wrongConfig = False

    for field in CONF_FIELDS:
        if field not in conf:
            print(f"No '{field}' field in config.json")
            wrongConfig = True

    if wrongConfig:
        exit(1)

#
# Generating CA self-signed certificate
#
regenerateCA = True
if os.path.isfile(IPSEC_KEYS_DIR + "private/ca.pem"):
    ans = input("CA private key already exists. Would you like to regenerate CA key? [y/N] ")
    if ans.capitalize() != "Y":
        regenerateCA = False

GenCARootCertificate(conf, regenerateCA)

#
# Generating server certificate
#
regenerateServer = True
if not regenerateCA:
    if os.path.isfile(IPSEC_KEYS_DIR + "private/" + conf["serverName"] + ".pem"):
        ans = input(f"Server private key for '{conf['serverName']}' already exists. "
                    "Would you like to regenerate key? [y/N] ")
        if ans.capitalize() != "Y":
            regenerateServer = False

GenServerCertificate(conf, regenerateServer)

#
# Making ipsec.conf and ipsec.secrets
#
ans = input("\nWould you like to make 'ipsec.conf' and 'ipsec.secrets'? [Y/n] ")
if ans == "" or ans.capitalize() == "Y":
    with open("template/ipsec.conf", "r") as f:
        vpnCertName = conf["serverName"] + ".pem"

        s = f.read()
        s = s.replace("YOUR_VPN_IP", conf["serverAddr"])
        s = s.replace("YOUR_VPN_CERT", vpnCertName)
        s = s.replace("VPN_SUBNET", conf["ipSubnet"])

        with open("/etc/ipsec.conf", "w") as fw:
            fw.write(s)

        with open("/etc/ipsec.secrets", "w") as fw:
            fw.write(f"\n: RSA {vpnCertName}\n")

        print("Done")

    subprocess.run(["ipsec", "restart"])
