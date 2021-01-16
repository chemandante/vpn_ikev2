#bin/bash
EXTERNAL_IP=$1
NAME_PREFIX=$2
NUMBER_OF_CERTIFICATES=$3
VPN_NAME=$4

echo "Generating $NUMBER_OF_CERTIFICATES client for external ip = '$EXTERNAL_IP'"
ipsec pki --gen --type rsa --size 4096 --outform pem > private/ca.pem
ipsec pki --self --ca --lifetime 3650 --in private/ca.pem --type rsa --digest sha256 --dn "CN=$EXTERNAL_IP" --outform pem > cacerts/ca.pem
ipsec pki --gen --type rsa --size 4096 --outform pem > private/debian.pem
ipsec pki --pub --in private/debian.pem --type rsa |ipsec pki --issue --lifetime 3650 --digest sha256 --cacert cacerts/ca.pem --cakey private/ca.pem --dn "CN=$EXTERNAL_IP" --san $EXTERNAL_IP --flag serverAuth --outform pem > certs/debian.pem

for i in $(seq 0 1 $NUMBER_OF_CERTIFICATES)
do
	NAME=$NAME_PREFIX$i
	echo $NAME
	ipsec pki --gen --type rsa --size 4096 --outform pem > private/$NAME.pem
	ipsec pki --pub --in private/$NAME.pem --type rsa | ipsec pki --issue --lifetime 3650 --digest sha256 --cacert cacerts/ca.pem --cakey private/ca.pem --dn "CN=$NAME" --san $NAME --flag clientAuth --outform pem > certs/$NAME.pem

	./mobileconfig.sh $NAME $VPN_NAME $EXTERNAL_IP > $NAME.mobileconfig

done

# iptables!
#iptables -A INPUT -p udp --dport  500 -j ACCEPT
#iptables -A INPUT -p udp --dport 4500 -j ACCEPT
#iptables -A FORWARD --match policy --pol ipsec --dir in  --proto esp -s 10.10.10.0/24 -j ACCEPT
#iptables -A FORWARD --match policy --pol ipsec --dir out --proto esp -d 10.10.10.0/24 -j ACCEPT
#iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -m policy --pol ipsec --dir out -j ACCEPT
#iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -j MASQUERADE
#iptables -t mangle -A FORWARD --match policy --pol ipsec --dir in -s 10.10.10.0/24 -o eth0 -p tcp -m tcp --tcp-flags SYN,RST SYN -m tcpmss --mss 1361:1536 -j TCPMSS --set-mss 1360
