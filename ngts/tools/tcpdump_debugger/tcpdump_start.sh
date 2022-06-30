#!/bin/sh

rm -f nohup.out
nohup tcpdump $1 &

# Write tcpdump's PID to a file
echo $! > /var/run/$2.pid
sleep 1
echo 'Started tcpdump'
