#bin/bash

tar pcfjv vpn_ike2.tar.bz2 --transform 's,^,vpn_ikev2/,' --exclude=build* *.sh *.py *.json template
