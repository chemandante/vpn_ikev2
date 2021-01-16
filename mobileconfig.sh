#!/bin/zsh

CLIENT=$1 #"me"
SERVER=$2 #"AWS London"
FQDN=$3 #"YOUR_LIGHTSAIL_IP"
CA="ca"

# WiFi SSIDs that do not require automatic connection to VPN on network change
TRUSTED_SSIDS=("SSID1" "SSID2")

PAYLOADCERTIFICATEUUID=$( cat /proc/sys/kernel/random/uuid )
PKCS12PASSWORD=$( cat /proc/sys/kernel/random/uuid )

cat << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadDisplayName</key>
    <string>${SERVER} VPN</string>
    <key>PayloadIdentifier</key>
    <string>${(j:.:)${(Oas:.:)FQDN}}</string>
    <key>PayloadUUID</key>
    <string>$( cat /proc/sys/kernel/random/uuid )</string>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadDisplayName</key>
            <string>${SERVER} VPN</string>
            <key>PayloadDescription</key>
            <string>Configure VPN</string>
            <key>UserDefinedName</key>
            <string>${SERVER}</string>
            <key>VPNType</key>
            <string>IKEv2</string>
            <key>IKEv2</key>
            <dict>
                <key>RemoteAddress</key>
                <string>${FQDN}</string>
                <key>RemoteIdentifier</key>
                <string>${FQDN}</string>
                <key>LocalIdentifier</key>
                <string>${CLIENT}</string>
                <key>AuthenticationMethod</key>
                <string>Certificate</string>
                <key>PayloadCertificateUUID</key>
                <string>${PAYLOADCERTIFICATEUUID}</string>
                <key>CertificateType</key>
                <string>RSA</string>
                <key>ServerCertificateIssuerCommonName</key>
                <string>${FQDN}</string>
                <key>EnablePFS</key>
                <integer>1</integer>
                <key>IKESecurityAssociationParameters</key>
                <dict>
                    <key>EncryptionAlgorithm</key>
                    <string>AES-128-GCM</string>
                    <key>IntegrityAlgorithm</key>
                    <string>SHA2-256</string>
                    <key>DiffieHellmanGroup</key>
                    <integer>19</integer>
                </dict>
                <key>ChildSecurityAssociationParameters</key>
                <dict>
                    <key>EncryptionAlgorithm</key>
                    <string>AES-128-GCM</string>
                    <key>IntegrityAlgorithm</key>
                    <string>SHA2-256</string>
                    <key>DiffieHellmanGroup</key>
                    <integer>19</integer>
                </dict>
                <key>OnDemandEnabled</key>
                <integer>0</integer>
                <key>OnDemandRules</key>
                <array>
                    <dict>
                        <key>InterfaceTypeMatch</key>
                        <string>WiFi</string>
                        <key>SSIDMatch</key>
                        <array>
`for x in ${TRUSTED_SSIDS}; echo "                            <string>$x</string>"`
                        </array>
                        <key>Action</key>
                        <string>Disconnect</string>
                    </dict>
                    <dict>
                        <key>InterfaceTypeMatch</key>
                        <string>Cellular</string>
                        <key>Action</key>
                        <string>Connect</string>
                    </dict>
                    <dict>
                        <key>Action</key>
                        <string>Connect</string>
                    </dict>
                </array>
            </dict>
            <key>PayloadType</key>
            <string>com.apple.vpn.managed</string>
            <key>PayloadIdentifier</key>
            <string>com.apple.vpn.managed.${SERVER}</string>
            <key>PayloadUUID</key>
            <string>$( cat /proc/sys/kernel/random/uuid )</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
        <dict>
            <key>PayloadDisplayName</key>
            <string>${CLIENT}.p12</string>
            <key>PayloadDescription</key>
            <string>Add PKCS#12 certificate</string>
            <key>PayloadCertificateFileName</key>
            <string>${CLIENT}.p12</string>
            <key>Password</key>
            <string>${PKCS12PASSWORD}</string>
            <key>PayloadContent</key>
            <data>
$( openssl pkcs12 -export -inkey /etc/ipsec.d/private/${CLIENT}.pem -in /etc/ipsec.d/certs/${CLIENT}.pem -name "${CLIENT}" -certfile /etc/ipsec.d/cacerts/${CA}.pem -password pass:${PKCS12PASSWORD} | base64 )
            </data>
            <key>PayloadType</key>
            <string>com.apple.security.pkcs12</string>
            <key>PayloadIdentifier</key>
            <string>com.apple.security.pkcs12.${CLIENT}</string>
            <key>PayloadUUID</key>
            <string>${PAYLOADCERTIFICATEUUID}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
        <dict>
            <key>PayloadDisplayName</key>
            <string>${SERVER} CA</string>
            <key>PayloadDescription</key>
            <string>Add CA root certificate</string>
            <key>PayloadCertificateFileName</key>
            <string>ca.pem</string>
            <key>PayloadContent</key>
            <data>
$( cat /etc/ipsec.d/cacerts/${CA}.pem | base64 )
            </data>
            <key>PayloadType</key>
            <string>com.apple.security.root</string>
            <key>PayloadIdentifier</key>
            <string>com.apple.security.root.${SERVER}</string>
            <key>PayloadUUID</key>
            <string>$( cat /proc/sys/kernel/random/uuid )</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
</dict>
</plist>
EOF