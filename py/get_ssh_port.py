#!/usr/bin/python3

import subprocess


def GetSSHPort() -> int:
    try:
        res = subprocess.check_output("grep -i -P " + r"'\s*port\s+(\d+)'" + " /etc/ssh/sshd_config", shell=True)
        return int(res.decode().split()[1])
    except subprocess.CalledProcessError as e:
        return 22
