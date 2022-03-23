#!/usr/bin/python3

import os
import subprocess

from config_json import GetJSONConfig

IPSEC_KEYS_DIR = "/etc/ipsec.d/"
CA_CERT_FILENAME = IPSEC_KEYS_DIR + "cacerts/ca.pem"
CA_PRIV_FILENAME = IPSEC_KEYS_DIR + "private/ca.pem"


def GenCARootCertificate(config: dict):
    print(f"\nGenerating CA root certificate for '{config['serverAddr']}'...")
    with open(CA_PRIV_FILENAME, "w", encoding="ascii") as fp:
        subprocess.run(["ipsec", "pki", "--gen", "--type", "rsa", "--size", "4096", "--outform", "pem"],
                       stdout=fp, check=True)

    with open(CA_CERT_FILENAME, "w", encoding="ascii") as fp:
        subprocess.run(["ipsec", "pki", "--self", "--ca", "--lifetime", "3650", "--in", CA_PRIV_FILENAME,
                        "--type", "rsa", "--digest", "sha256", "--dn", f"CN={config['serverAddr']}",
                        "--outform", "pem"], stdout=fp, check=True)
    print("Done")


def GenServerCertificate(config: dict):
    VPNCertFileName = IPSEC_KEYS_DIR + f"certs/{config['serverName']}.pem"
    VPNPrivFileName = IPSEC_KEYS_DIR + f"private/{config['serverName']}.pem"

    print(f"\nGenerating server certificate for '{config['serverAddr']}'...")
    with open(VPNPrivFileName, "w", encoding="ascii") as fp:
        subprocess.run(["ipsec", "pki", "--gen", "--type", "rsa", "--size", "2048", "--outform", "pem"],
                       stdout=fp, check=True)

    output = subprocess.check_output(f"ipsec pki --pub --in {VPNPrivFileName} --type rsa | "
                                     f"ipsec pki --issue --lifetime 3650 --digest sha256 --cacert {CA_CERT_FILENAME} "
                                     f"--cakey {CA_PRIV_FILENAME} --dn \"CN={config['serverAddr']}\" "
                                     f"--san \"{config['serverAddr']}\" --flag serverAuth --outform pem", shell=True)

    with open(VPNCertFileName, "w", encoding="ascii") as fp:
        fp.write(output.decode(encoding="ascii"))

    print("Done")


#
# Reading config.json
#
conf = GetJSONConfig("config.json")

#
# Generating CA self-signed certificate
#
regenerateCA = True
if os.path.isfile(IPSEC_KEYS_DIR + "private/ca.pem") and os.path.isfile(IPSEC_KEYS_DIR + "cacerts/ca.pem"):
    ans = input("CA root certificate already exists. Would you like to regenerate CA key? [y/N] ")
    if ans.capitalize() != "Y":
        regenerateCA = False

if regenerateCA:
    GenCARootCertificate(conf)

#
# Generating server certificate
#
regenerateServer = True
if not regenerateCA:
    if os.path.isfile(IPSEC_KEYS_DIR + "private/" + conf["serverName"] + ".pem") and \
            os.path.isfile(IPSEC_KEYS_DIR + "private/" + conf["serverName"] + ".pem"):

        ans = input(f"Server private key for '{conf['serverName']}' already exists. "
                    "Would you like to regenerate key? [y/N] ")
        if ans.capitalize() != "Y":
            regenerateServer = False

if regenerateServer:
    GenServerCertificate(conf)

#
# Making ipsec.conf and ipsec.secrets
#
ans = input("\nWould you like to make 'ipsec.conf' and 'ipsec.secrets'? [Y/n] ")
if ans == "" or ans.capitalize() == "Y":
    with open("template/ipsec.conf", "r", encoding="ascii") as f:
        vpnCertName = conf["serverName"] + ".pem"

        s = f.read()
        s = s.replace("YOUR_VPN_IP", conf["serverAddr"])
        s = s.replace("YOUR_VPN_CERT", vpnCertName)
        s = s.replace("VPN_SUBNET", conf["ipSubnet"])

        with open("/etc/ipsec.conf", "w", encoding="ascii") as fw:
            fw.write(s)

        with open("/etc/ipsec.secrets", "w", encoding="ascii") as fw:
            fw.write(f"\n: RSA {vpnCertName}\n")

        print("Done")

    subprocess.run(["ipsec", "restart"], check=True)
