#!/bin/bash

# Check if the correct number of arguments is provided
if [ $# -ne 4 ]; then
    echo "Usage: $0 <LMAC> <RMAC> <L_IP_address><R_IP_address>"
    exit 1
fi

# Extract MAC addresses and full IP address from command-line arguments
L_MAC="$1"
R_MAC="$2"
L_FULL_IP="$3"
R_FULL_IP="$4"

# Extract the first two octets (IP prefix) from the Left and right full IP address
L_IP_PREFIX=$(echo "$L_FULL_IP" | awk -F. '{print $1"."$2}')
R_IP_PREFIX=$(echo "$R_FULL_IP" | awk -F. '{print $1"."$2}')

# Configure IP neighbors for left traffic generator - Ethernet0 to Ethernet252
i=1
j=0

while [ $i -le 64 ]; do
    ip -4 neigh replace "$L_IP_PREFIX.$i.1" lladdr "$L_MAC" nud permanent dev Ethernet$j
    i=$((i+1))
    j=$((j+4))
done

# Configure IP neighbors for right traffic generator - Ethernet256 to Ethernet508
i=1
j=256

while [ $i -le 64 ]; do
    ip -4 neigh replace "$R_IP_PREFIX.$i.1" lladdr "$R_MAC" nud permanent dev Ethernet$j
    i=$((i+1))
    j=$((j+4))
done
