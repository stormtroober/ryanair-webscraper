#!/bin/bash
# Script to connect to NordVPN with a specified server

# Check if an argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <VPN server>"
    exit 1
fi

# Connect to NordVPN
nordvpn connect "$1"
