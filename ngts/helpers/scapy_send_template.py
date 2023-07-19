#! /usr/bin/env python
from scapy.all import *


def send_packet(packet, num_of_packets, interface):
    sendp(packet, count=num_of_packets, iface=interface)
