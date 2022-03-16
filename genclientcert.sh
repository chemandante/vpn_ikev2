#bin/bash
NAME=$1
SERVER_NAME=$2
SERVER_ADDR=$3
IPSEC_DIR="/etc/ipsec.d/"
CA_PRIV_NAME=$IPSEC_DIR"private/ca.pem"
CA_CERT_NAME=$IPSEC_DIR"cacerts/ca.pem"
CLI_PRIV_NAME=$IPSEC_DIR"private/"$NAME".pem"
CLI_CERT_NAME=$IPSEC_DIR"certs/"$NAME".pem"

echo "Generating key and certificate for '$NAME', VPN '$SERVER_NAME' ('$SERVER_ADDR')"
ipsec pki --gen --type rsa --size 2048 --outform pem > "$CLI_PRIV_NAME"
ipsec pki --pub --in "$CLI_PRIV_NAME" --type rsa | ipsec pki --issue --lifetime 3650 --digest sha256 \
--cacert "$CA_CERT_NAME" --cakey "$CA_PRIV_NAME" --dn "CN=$NAME" --san "$NAME" --flag clientAuth \
--outform pem > "$CLI_CERT_NAME"

