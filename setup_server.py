#!/usr/bin/python3

import os
import subprocess
import sys

from py.config_json import GetJSONConfig
from py.eth_interfaces import SelectInterface
from py.get_ssh_port import GetSSHPort

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
            os.path.isfile(IPSEC_KEYS_DIR + "certs/" + conf["serverName"] + ".pem"):

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
    with open("template/ipsec.conf.template", "r", encoding="ascii") as f:
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

#
# Configuring iptable
#
ssh_port = GetSSHPort()
ans = input(f"\nEnter port used by SSH (or press Enter to use detected value [{ssh_port}]): ")
if ans != "":
    ssh_port = int(ans)

ans = input("\nWould you like to configure iptables? [Y/n] ")
with open("template/confiptables.sh.template", "r", encoding="ascii") as f:

    ethInterfaceName = SelectInterface()
    if not ethInterfaceName:
        sys.exit(-1)

    s = f.read()
    s = s.replace("{VPN_SUBNET}", conf["ipSubnet"])
    s = s.replace("{ETH_INTERFACE}", ethInterfaceName)
    s = s.replace("{SSH_PORT}", str(ssh_port))

    fName = "confiptables.sh"
    with open(fName, "w", encoding="ascii") as fw:
        fw.write(s)

    if ans == "" or ans.capitalize() == "Y":
        subprocess.run(["bash", fName], check=True)

        print(f"Script '{fName}' was ran successfully, iptables was configured")
    else:
        print(f"Script '{fName}' was prepared. Check it and run")
