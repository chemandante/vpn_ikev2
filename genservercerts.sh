#bin/bash
VPN_NAME=$1
EXTERNAL_IP=$2
IPSEC_DIR="/etc/ipsec.d/"
CA_PRIV_NAME=$IPSEC_DIR"private/ca.pem"
CA_CERT_NAME=$IPSEC_DIR"cacerts/ca.pem"
VPN_PRIV_NAME=$IPSEC_DIR"private/$VPN_NAME.pem"
VPN_CERT_NAME=$IPSEC_DIR"certs/$VPN_NAME.pem"

echo "Generating server keys and certificates for external ip = '$EXTERNAL_IP'"

# CA key and cert
ipsec pki --gen --type rsa --size 4096 --outform pem > $CA_PRIV_NAME
ipsec pki --self --ca --lifetime 3650 --in $CA_PRIV_NAME --type rsa --digest sha256 --dn "CN=$EXTERNAL_IP" \
--outform pem > $CA_CERT_NAME
# Server key and cert
ipsec pki --gen --type rsa --size 2048 --outform pem > "$VPN_PRIV_NAME"
ipsec pki --pub --in "$VPN_PRIV_NAME" --type rsa |ipsec pki --issue --lifetime 3650 --digest sha256 \
--cacert $CA_CERT_NAME --cakey $CA_PRIV_NAME --dn "CN=$EXTERNAL_IP" --san "$EXTERNAL_IP" \
--flag serverAuth --outform pem > "$VPN_CERT_NAME"
