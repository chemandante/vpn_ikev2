#bin/bash
EXTERNAL_IP=$1

echo "
config setup
        uniqueids=never
        charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2,  mgr 2"

conn %default
        keyexchange=ikev2
        ike=aes128gcm16-sha2_256-prfsha256-ecp256!
        esp=aes128gcm16-sha2_256-ecp256!
        fragmentation=yes
        rekey=no
        compress=yes
        dpdaction=clear
        left=%any
        leftauth=pubkey
        leftsourceip=$EXTERNAL_IP
        leftid=$EXTERNAL_IP
        leftcert=debian.pem
        leftsendcert=always
        leftsubnet=0.0.0.0/0
        right=%any
        rightauth=pubkey
        rightsourceip=10.10.10.0/24
        rightdns=8.8.8.8,8.8.4.4

conn ikev2-pubkey
        auto=add"