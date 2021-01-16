#FROM debian:10.7
FROM ubuntu:20.04

# more info about how does it works:
# https://vc.ru/dev/66942-sozdaem-svoy-vpn-server-poshagovaya-instrukciya

ARG EXTERNAL_IP
ARG NUMBER_OF_CERTIFICATES=1
ARG PREFIX=me
ARG VPN_NAME=VPN
RUN  : "${EXTERNAL_IP:?Build argument needs to be set and non-empty.}" echo "Use EXTERNAL_IP = $EXTERNAL_IP"
RUN apt update && apt upgrade -y && apt install -y strongswan strongswan-pki zsh net-tools iptables-persistent

WORKDIR /etc/ipsec.d

COPY ./gencerts.sh .
COPY ./mobileconfig.sh .
COPY ./genconfig.sh .
RUN ls -al

RUN ./gencerts.sh $EXTERNAL_IP $PREFIX $NUMBER_OF_CERTIFICATES $VPN_NAME

RUN ./genconfig.sh $EXTERNAL_IP > /etc/ipsec.conf
RUN cat /etc/ipsec.secrets
RUN echo "\n : RSA debian.pem" >> /etc/ipsec.secrets
RUN cat /etc/ipsec.secrets

COPY ./sysctl.conf /etc/sysctl.conf
RUN cat /etc/sysctl.conf


#CMD ipsec start


#
#RUN ./mobileconfig.sh $PREFIX VPN $EXTERNAL_IP




