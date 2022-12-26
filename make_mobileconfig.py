#!/usr/bin/python3
import subprocess
import uuid


def MakeMobileconfig(clientName, issuerName, config: dict):
    serverAddr = config["serverAddr"]
    serverName = config["serverName"].capitalize()

    clientNameCap = clientName.capitalize()
    issuerNameCap = issuerName.split(".")[0].capitalize()
    payloadID = ".".join(serverAddr.split(".")[::-1])
    payloadUUID = str(uuid.uuid4())
    payloadCertUUID = str(uuid.uuid4())
    pkcs12Password = str(uuid.uuid4())
    profileDispName = serverName + " IKEv2"

    with open("template/mobileconfig.template", "r", encoding="ascii") as f:
        s = f.read()

        s = s.replace("{CLIENT_NAME}", clientName)
        s = s.replace("{CLIENT_NAME_CAP}", clientNameCap)
        s = s.replace("{CLIENT_NAME_LO}", clientName.lower())
        s = s.replace("{ISSUER_NAME}", issuerName)
        s = s.replace("{ISSUER_NAME_CAP}", issuerNameCap)
        s = s.replace("{ISSUER_NAME_LO}", issuerNameCap.lower())
        s = s.replace("{ORGANIZATION_NAME}", profileDispName + " server")
        s = s.replace("{PAYLOAD_ID}", payloadID)
        s = s.replace("{PAYLOAD_UUID}", payloadUUID)
        s = s.replace("{PAYLOAD_CERT_UUID}", payloadCertUUID)
        s = s.replace("{PAYLOAD_ROOT_CA_UUID}", str(uuid.uuid4()))
        s = s.replace("{PAYLOAD_VPN_UUID}", str(uuid.uuid4()))
        s = s.replace("{PKCS12_PASSWORD}", pkcs12Password)
        s = s.replace("{PROFILE_NAME}", profileDispName)
        s = s.replace("{SERVER_ADDR}", serverAddr)

        output = subprocess.check_output(f"openssl pkcs12 -export -inkey /etc/ipsec.d/private/{clientName}.pem "
                                         f"-in /etc/ipsec.d/certs/{clientName}.pem -name \"{clientName}\" "
                                         f"-certfile /etc/ipsec.d/cacerts/ca.pem -password pass:{pkcs12Password} "
                                         "| base64", shell=True)

        s = s.replace("{PKCS12_DATA}", output.decode(encoding="ascii"))

        output = subprocess.check_output("cat /etc/ipsec.d/cacerts/ca.pem | base64", shell=True)

        s = s.replace("{CA_CERT_DATA}", output.decode(encoding="ascii"))

    with open("apple/" + clientName + ".mobileconfig", "w", encoding="ascii") as f:
        f.write(s)
